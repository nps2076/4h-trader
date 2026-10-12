"""Vectorised long/flat backtest engine for 4H bars.

Timing convention (no look-ahead):
  * target[t] is computed from data up to and including the CLOSE of bar t.
  * It is executed at the OPEN of bar t+1, so the position held over bar t+1
    (open[t+1] -> open[t+2]) is pos[t+1] = target[t].
  * Returns are open-to-open; costs are charged on |change in position| at each open.
Window handling: indicators use the full history (incl. warm-up); P&L and trades only
count inside the window. The book starts flat at the window's first open, so an
initial long signal is bought (and costed) at that open. No forced liquidation at window end
(positions are marked to market) — same rule for strategies and benchmarks.
"""
import numpy as np
import pandas as pd

BARS_PER_YEAR = 365 * 6  # 2190, crypto trades 24/7

WINDOWS = {
    "TRAIN": ("2024-09-01", "2026-10-12"),
    # stability splits of TRAIN (NOT out-of-sample; TradingView 4H data starts 2024-01-01)
    "TRAIN_Y1": ("2024-09-01", "2025-09-01"),
    "TRAIN_Y2": ("2025-09-01", "2026-10-12"),
    "VALIDATION": ("2023-09-01", "2024-09-01"),
    "HOLDOUT_A": ("2022-09-01", "2023-09-01"),
    "HOLDOUT_B": ("2021-09-01", "2022-09-01"),
}
WARMUP_BARS = 1200

# Per-side cost in decimal (taker fee + slippage). See README/results_summary for rationale.
#   Coinbase Advanced, ~$100k-1M 30d-volume tier: taker 0.25%; slippage 5 bps BTC/ETH, 10 bps alts.
#   Binance spot: taker 0.10%; slippage 5 bps.
FEE = {"COINBASE": 0.0025, "BINANCE": 0.0010}
# Shorts (optional): assumed via perpetual futures/margin. Same per-side cost, plus a carry cost on the
# short notional of 5%/yr (conservative: perp funding is usually positive, i.e. shorts often RECEIVE it).
SHORT_CARRY = 0.05


def cost_per_side(asset: str, symbol: str) -> float:
    exch = symbol.split("_")[0]
    slip = 0.0005 if asset in ("BTC", "ETH") or exch == "BINANCE" else 0.0010
    return FEE[exch] + slip


def window_slice(df: pd.DataFrame, window: str):
    """Return (df incl. warm-up, start, end) or None if the window lacks warm-up/data."""
    start, end = (pd.Timestamp(x, tz="UTC") for x in WINDOWS[window])
    in_win = (df.index >= start) & (df.index < end)
    if in_win.sum() == 0:
        return None
    first = np.argmax(in_win)
    if first < WARMUP_BARS:
        return None
    return df.iloc[first - WARMUP_BARS: np.where(in_win)[0][-1] + 1], start, end


def run(df: pd.DataFrame, target: pd.Series, start, end, cost: float, delay: int = 0,
        short_carry: float = SHORT_CARRY) -> pd.DataFrame:
    """Simulate. target in [-1,1] indexed like df (negative = short). delay = extra bars of execution lag."""
    op = df["open"]
    ret = op.shift(-1) / op - 1.0                     # open[t] -> open[t+1], held with pos[t]
    pos = target.shift(1 + delay).fillna(0.0).clip(-1, 1)
    win = (df.index >= start) & (df.index < end)
    # the last bar of data has no next open; drop it from the evaluation
    win &= ret.notna().values
    pos = pos.where(win, 0.0)
    prev = pos.shift(1).fillna(0.0).where(win, 0.0)
    prev.iloc[np.argmax(win)] = 0.0                   # start flat
    trade = (pos - prev).abs()
    c = trade * cost + (-pos).clip(lower=0) * short_carry / BARS_PER_YEAR
    r = pos * ret.fillna(0.0) - c
    out = pd.DataFrame({"pos": pos, "ret": r, "gross": pos * ret.fillna(0.0), "cost": c,
                        "turn": trade, "mkt": ret})[win]
    out["equity"] = (1 + out["ret"]).cumprod()
    return out


def _trades(res: pd.DataFrame):
    """Episodes of constant-sign non-zero position -> list of (compounded net return, bars held)."""
    side = np.sign(res["pos"])
    inpos = side != 0
    grp = (side != side.shift()).cumsum()
    out = []
    for _, g in res[inpos].groupby(grp[inpos]):
        out.append(((1 + g["ret"]).prod() - 1, len(g)))
    return out


def metrics(res: pd.DataFrame) -> dict:
    r = res["ret"]
    n = len(r)
    eq = res["equity"]
    years = n / BARS_PER_YEAR
    cagr = eq.iloc[-1] ** (1 / years) - 1 if eq.iloc[-1] > 0 else -1.0
    sd = r.std()
    vol = sd * np.sqrt(BARS_PER_YEAR)
    sharpe = r.mean() / sd * np.sqrt(BARS_PER_YEAR) if sd > 0 else 0.0
    dd_dev = np.sqrt((np.minimum(r, 0) ** 2).mean())
    sortino = r.mean() / dd_dev * np.sqrt(BARS_PER_YEAR) if dd_dev > 0 else 0.0
    peak = eq.cummax()
    dd = eq / peak - 1
    mdd = dd.min()
    # longest time under water (bars) -> days
    under = dd < 0
    runs = (under != under.shift()).cumsum()
    dur = under.groupby(runs).sum().max() if under.any() else 0
    tr = _trades(res)
    rets = np.array([t[0] for t in tr]) if tr else np.array([])
    wins, losses = rets[rets > 0].sum(), -rets[rets < 0].sum()
    return {
        "CAGR": cagr, "Vol": vol, "Sharpe": sharpe, "Sortino": sortino,
        "Calmar": cagr / abs(mdd) if mdd < 0 else np.nan, "MaxDD": mdd,
        "DD_days": dur / 6, "Trades": len(tr),
        "WinRate": (rets > 0).mean() if len(rets) else np.nan,
        "PF": wins / losses if losses > 0 else np.nan,
        "AvgHold_d": np.mean([t[1] for t in tr]) / 6 if tr else 0.0,
        "Exposure": (res["pos"] != 0).mean(), "AvgPos": res["pos"].mean(),
        "ShortPct": (res["pos"] < 0).mean(),
        "Turnover": res["turn"].sum() / years,          # sum|dpos| per year (1.0 = one full side)
        "CostDrag": res["cost"].sum() / years,          # simple sum of costs per year
    }
