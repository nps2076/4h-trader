"""Reproduce every table and chart from the frozen cache.
Usage:  python run_all.py [--windows TRAIN VALIDATION ...] [--assets BTC ETH ...] [--tag name]
Writes results/<tag>_metrics.csv, results/<tag>_*.md tables, charts/<tag>_<asset>_<window>.png."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from data_loader import load, SYMBOLS
from backtest import WINDOWS, window_slice, run, metrics, cost_per_side, BARS_PER_YEAR
from strategy import BENCHMARKS, trend_band, PARAMS

ROOT = Path(__file__).parent
RES, CH = ROOT / "results", ROOT / "charts"
STRATS = dict(BENCHMARKS, **{"TrendBand": trend_band,
                             "TrendBand_LS": lambda d: trend_band(d, allow_short=True)})  # info only
SHOW = ["CAGR", "Vol", "Sharpe", "Sortino", "Calmar", "MaxDD", "DD_days", "WinRate", "PF", "Trades",
        "AvgHold_d", "Exposure", "Turnover", "CostDrag"]
COLORS = {"B&H": "#9aa0a6", "SMA200": "#e8a33d", "SMA50/200": "#7b61c4", "TrendBand": "#1f6feb", "TrendBand_LS": "#d1495b"}


def sim(asset, window, fn, cost_mult=1.0, delay=0):
    ws = window_slice(load(asset), window)
    if ws is None:
        return None
    d, s, e = ws
    return run(d, fn(d), s, e, cost_per_side(asset, SYMBOLS[asset]) * cost_mult, delay)


def fmt_table(t):
    t = t.copy()
    pct = ["CAGR", "Vol", "MaxDD", "WinRate", "Exposure", "CostDrag"]
    for c in t.columns:
        if c in pct:
            t[c] = t[c].map(lambda x: f"{x:.0%}" if pd.notna(x) else "")
        elif c in ("Trades",):
            t[c] = t[c].map(lambda x: f"{int(x)}")
        elif t[c].dtype.kind == "f":
            t[c] = t[c].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
    return t.to_markdown(index=False)


def chart(asset, window, results, tag):
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    for name, res in results.items():
        lw = 2.0 if name == "TrendBand" else 1.0
        a1.plot(res.index, res.equity, label=name, color=COLORS[name], lw=lw)
        a2.plot(res.index, res.equity / res.equity.cummax() - 1, color=COLORS[name], lw=lw)
    a1.set_yscale("log"); a1.set_ylabel("Equity (log)"); a1.legend(frameon=False, ncol=5, fontsize=8, loc="upper left")
    a2.set_ylabel("Drawdown"); a2.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    for a in (a1, a2):
        a.grid(alpha=0.3); a.spines[["top", "right"]].set_visible(False)
    a1.set_title(f"{asset} {window} (net of costs)")
    fig.tight_layout(); fig.savefig(CH / f"{tag}_{asset}_{window}.png", dpi=90); plt.close(fig)


def main_table(assets, windows, tag, charts=True):
    rows, basket = [], {}
    for w in windows:
        for a in assets:
            results = {}
            for name, fn in STRATS.items():
                res = sim(a, w, fn)
                if res is None:
                    continue
                results[name] = res
                rows.append(dict(window=w, asset=a, strat=name, **metrics(res)))
                basket.setdefault((w, name), []).append(res["ret"].rename(a))
            if results and charts:
                chart(a, w, results, tag)
    # equal-weight basket: per-bar average of asset net returns (constant mix, rebalance cost ignored)
    for (w, name), rs in basket.items():
        if len(rs) < 2:
            continue
        r = pd.concat(rs, axis=1, sort=True).dropna().mean(axis=1)
        fake = pd.DataFrame({"ret": r, "pos": 1.0, "turn": 0.0, "cost": 0.0})
        fake["equity"] = (1 + r).cumprod()
        m = metrics(fake)
        for k in ["Trades", "WinRate", "PF", "AvgHold_d", "Exposure", "AvgPos", "ShortPct", "Turnover", "CostDrag"]:
            m[k] = np.nan
        m["Trades"] = 0
        rows.append(dict(window=w, asset=f"BASKET({len(rs)})", strat=name, **m))
    return pd.DataFrame(rows)


def verdict(t):
    """Success: beat B&H and SMA200 on Sharpe and Calmar; MaxDD not materially worse than B&H (≤ +5pp)."""
    out = []
    for (w, a), g in t.groupby(["window", "asset"], sort=False):
        g = g.set_index("strat")
        if "TrendBand" not in g.index:
            continue
        s, b, m = g.loc["TrendBand"], g.loc["B&H"], g.loc["SMA200"]
        ok = (s.Sharpe > b.Sharpe and s.Sharpe > m.Sharpe and s.Calmar > b.Calmar and s.Calmar > m.Calmar
              and s.MaxDD >= b.MaxDD - 0.05)
        out.append(dict(window=w, asset=a, pass_=("PASS" if ok else "FAIL"),
                        weak=("<20 trades" if 0 < s.Trades < 20 else ""),
                        beats_5050_200=bool(s.Sharpe > g.loc["SMA50/200"].Sharpe and s.Calmar > g.loc["SMA50/200"].Calmar)))
    return pd.DataFrame(out)


def robustness(assets, windows, tag):
    lines = []
    # cost and delay
    rows = []
    for w in windows:
        for a in assets:
            for lab, cm, dl in [("1x cost", 1, 0), ("2x cost", 2, 0), ("+1 bar delay", 1, 1)]:
                res = sim(a, w, trend_band, cm, dl)
                if res is None:
                    continue
                m = metrics(res)
                rows.append(dict(window=w, asset=a, case=lab, Sharpe=m["Sharpe"], Calmar=m["Calmar"],
                                 MaxDD=m["MaxDD"], CAGR=m["CAGR"], Trades=m["Trades"]))
    if rows:
        lines += ["### Cost and execution-delay sensitivity (TrendBand)", fmt_table(pd.DataFrame(rows)), ""]
    # parameter plateau
    for w in windows:
        for a in assets:
            if window_slice(load(a), w) is None:
                continue
            grid = []
            for n in [200, 250, 300, 400, 500, 600]:
                for k in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]:
                    res = sim(a, w, lambda d, n=n, k=k: trend_band(d, sma_n=n, k=k))
                    grid.append(dict(sma_n=n, k=k, Sharpe=metrics(res)["Sharpe"]))
            g = pd.DataFrame(grid).pivot(index="sma_n", columns="k", values="Sharpe")
            lines += [f"### Parameter plateau: Sharpe, {a} {w} (atr_n=84; chosen sma_n=300, k=1)",
                      g.round(2).to_markdown(), ""]
            ga = []
            for an in [42, 84, 168]:
                res = sim(a, w, lambda d, an=an: trend_band(d, atr_n=an))
                ga.append(f"atr_n={an}: {metrics(res)['Sharpe']:.2f}")
            lines += [f"ATR window sensitivity ({a} {w}, Sharpe): " + ", ".join(ga), ""]
    return "\n".join(lines)


def rolling_btc(tag):
    """Rolling 365-day windows, stepped every 90 days, over all BTC history with full warm-up."""
    df = load("BTC")
    tgt = {n: f(df) for n, f in STRATS.items()}
    start0 = df.index[1200]
    rows = []
    s = start0
    while s + pd.Timedelta(days=365) <= df.index[-1]:
        e = s + pd.Timedelta(days=365)
        row = {"start": s.date()}
        for n in STRATS:
            res = run(df, tgt[n], s, e, cost_per_side("BTC", SYMBOLS["BTC"]))
            m = metrics(res)
            row[f"{n} Sh"] = m["Sharpe"]
            row[f"{n} DD"] = m["MaxDD"]
        rows.append(row)
        s += pd.Timedelta(days=90)
    t = pd.DataFrame(rows)
    t["TB beats B&H&SMA200 (Sh)"] = (t["TrendBand Sh"] > t["B&H Sh"]) & (t["TrendBand Sh"] > t["SMA200 Sh"])
    return t


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--windows", nargs="+", default=["TRAIN", "TRAIN_Y1", "TRAIN_Y2"])
    ap.add_argument("--assets", nargs="+", default=list(SYMBOLS))
    ap.add_argument("--tag", default="all")
    ap.add_argument("--robust", action="store_true")
    ap.add_argument("--rolling", action="store_true")
    ap.add_argument("--nocharts", action="store_true")
    a = ap.parse_args()
    RES.mkdir(exist_ok=True); CH.mkdir(exist_ok=True)
    t = main_table(a.assets, a.windows, a.tag, charts=not a.nocharts)
    t.to_csv(RES / f"{a.tag}_metrics.csv", index=False)
    md = [f"Params: {PARAMS}", ""]
    for w in a.windows:
        tw = t[t.window == w]
        if len(tw):
            md += [f"## {w}", fmt_table(tw[["asset", "strat"] + SHOW]), ""]
    v = verdict(t)
    if len(v):
        md += ["## Verdict (TrendBand vs B&H and SMA200: Sharpe & Calmar; DD ≤ B&H+5pp)", v.to_markdown(index=False), ""]
    if a.robust:
        md += ["## Robustness", robustness(["BTC", "ETH"], [w for w in a.windows if w == "TRAIN"], a.tag)]
    if a.rolling:
        r = rolling_btc(a.tag)
        md += ["## Rolling 365d windows, BTC (step 90d)", fmt_table(r),
               f"TrendBand beats both on Sharpe in {r.iloc[:, -1].mean():.0%} of {len(r)} windows", ""]
    (RES / f"{a.tag}.md").write_text("\n".join(md))
    print("\n".join(md))
