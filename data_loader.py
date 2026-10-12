"""Load cached 4H OHLCV data.

Raw source of record: TradingView MCP (`get_ohlcv`, 4h) dumps in data/raw/*.json.
Normalised cache: data/<SYMBOL>_4h.parquet (UTC index, open-time stamped).
Run `python data_loader.py` to (re)build the parquet cache from the raw dumps and print an audit.
"""
from pathlib import Path
import json
import pandas as pd

DATA = Path(__file__).parent / "data"
RAW = DATA / "raw"
BAR = pd.Timedelta(hours=4)

# asset -> exchange symbol (one exchange per asset, never mixed)
SYMBOLS = {
    "BTC": "COINBASE_BTCUSD",
    "ETH": "COINBASE_ETHUSD",
    "SOL": "COINBASE_SOLUSD",
    "BNB": "BINANCE_BNBUSDT",   # not listed on Coinbase; USDT quote
    "XRP": "COINBASE_XRPUSD",
    "DOGE": "COINBASE_DOGEUSD",
    "ADA": "COINBASE_ADAUSD",
    "AVAX": "COINBASE_AVAXUSD",
    "LINK": "COINBASE_LINKUSD",
    "LTC": "COINBASE_LTCUSD",
}
# Frozen cache: last bar used by every run (open time, UTC). Bars after this are ignored.
FREEZE_LAST_BAR = pd.Timestamp("2026-10-11 20:00", tz="UTC")


def _raw_to_df(path: Path) -> pd.DataFrame:
    j = json.loads(path.read_text())
    b = j["bars"]
    df = pd.DataFrame({k: b[k] for k in ["o", "h", "l", "c", "v"]})
    df.columns = ["open", "high", "low", "close", "volume"]
    df.index = pd.to_datetime(b["t"], unit="s", utc=True)
    df.index.name = "time"
    return df


def build_cache():
    """Merge all raw dumps per symbol (later files override overlaps), freeze, save parquet."""
    for asset, sym in SYMBOLS.items():
        files = sorted(RAW.glob(f"{sym}_4h*.json"))
        if not files:
            continue
        df = pd.concat([_raw_to_df(f) for f in files])
        df = df[~df.index.duplicated(keep="last")].sort_index()
        df = df[df.index <= FREEZE_LAST_BAR]
        df.to_parquet(DATA / f"{sym}_4h.parquet")


def load(asset: str) -> pd.DataFrame:
    return pd.read_parquet(DATA / f"{SYMBOLS[asset]}_4h.parquet")


def audit(asset: str) -> dict:
    df = load(asset)
    idx = df.index
    full = pd.date_range(idx[0], idx[-1], freq=BAR)
    missing = full.difference(idx)
    misaligned = int(((idx.hour % 4) != 0).sum() + (idx.minute != 0).sum())
    bad = int(((df.high < df[["open", "close"]].max(axis=1)) | (df.low > df[["open", "close"]].min(axis=1))).sum())
    zero_vol = int((df.volume <= 0).sum())
    return dict(asset=asset, symbol=SYMBOLS[asset], first=idx[0], last=idx[-1], bars=len(df),
                missing=len(missing), misaligned=misaligned, bad_ohlc=bad, zero_vol=zero_vol,
                missing_list=[str(m) for m in missing[:10]])


if __name__ == "__main__":
    build_cache()
    rows = [audit(a) for a in SYMBOLS if (DATA / f"{SYMBOLS[a]}_4h.parquet").exists()]
    print(pd.DataFrame(rows).drop(columns="missing_list").to_string(index=False))
    for r in rows:
        if r["missing"]:
            print(r["asset"], "missing bars (first 10):", r["missing_list"])
