"""Extend the cache before 2024-01-01 (TradingView's 4H limit) from the exchanges' public APIs.

* Coinbase Exchange API has no 4H granularity -> pull 1H candles and resample to 4H buckets
  aligned to 00/04/08/12/16/20 UTC (open=first, high=max, low=min, close=last, volume=sum).
* Binance (BNBUSDT) -> native 4H klines from data-api.binance.vision.
Output: data/raw/<SYMBOL>_4h_api.json in the same column layout as the TradingView dumps.
TradingView bars take precedence wherever both exist (data_loader merges with keep="last"
and the TV file sorts after the _api file). Run once; results are cached and frozen.
"""
import json
import sys
import time
from pathlib import Path
import pandas as pd
import requests

RAW = Path(__file__).parent / "data" / "raw"
START = pd.Timestamp("2021-01-01", tz="UTC")
END = pd.Timestamp("2024-03-01", tz="UTC")   # overlap with TradingView for cross-checking
CB = {"BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD", "XRP": "XRP-USD", "DOGE": "DOGE-USD",
      "ADA": "ADA-USD", "AVAX": "AVAX-USD", "LINK": "LINK-USD", "LTC": "LTC-USD"}


def _get(url, params):
    for i in range(6):
        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(2 ** i); continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            if i == 5:
                raise
            time.sleep(2 ** i)


def coinbase_1h(product):
    rows, t = [], START
    while t < END:
        t2 = min(t + pd.Timedelta(hours=300), END)
        data = _get(f"https://api.exchange.coinbase.com/products/{product}/candles",
                    {"granularity": 3600, "start": t.isoformat(), "end": t2.isoformat()})
        rows += data  # [time, low, high, open, close, volume]
        t = t2
        time.sleep(0.15)
    df = pd.DataFrame(rows, columns=["t", "low", "high", "open", "close", "volume"]).drop_duplicates("t")
    df.index = pd.to_datetime(df.t, unit="s", utc=True)
    return df.sort_index()[["open", "high", "low", "close", "volume"]]


def resample_4h(h):
    g = h.resample("4h", origin="epoch", label="left", closed="left")
    out = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(),
                        "close": g.close.last(), "volume": g.volume.sum(), "n": g.open.count()})
    return out[out.n > 0]


def binance_4h(symbol):
    rows, t = [], int(START.timestamp() * 1000)
    end = int(END.timestamp() * 1000)
    while t < end:
        data = _get("https://data-api.binance.vision/api/v3/klines",
                    {"symbol": symbol, "interval": "4h", "startTime": t, "endTime": end, "limit": 1000})
        if not data:
            break
        rows += data
        t = data[-1][0] + 1
        time.sleep(0.1)
    df = pd.DataFrame([r[:6] for r in rows], columns=["t", "open", "high", "low", "close", "volume"]).astype(float)
    df.index = pd.to_datetime(df.t.astype("int64"), unit="ms", utc=True)
    df["n"] = 4
    return df[["open", "high", "low", "close", "volume", "n"]]


def save(df, name):
    t = (df.index.astype("int64") // 10**9).tolist()
    j = {"symbol": name, "source": "exchange public API", "bars": {
        "t": t, "o": df.open.tolist(), "h": df.high.tolist(), "l": df.low.tolist(),
        "c": df.close.tolist(), "v": df.volume.tolist()}, "partial_bars": int((df.n < 4).sum())}
    (RAW / f"{name}_4h_api.json").write_text(json.dumps(j))
    print(name, len(df), df.index[0], df.index[-1], "partial(<4h) buckets:", int((df.n < 4).sum()))


if __name__ == "__main__":
    which = sys.argv[1:] or list(CB) + ["BNB"]
    for a in which:
        if a == "BNB":
            save(binance_4h("BNBUSDT"), "BINANCE_BNBUSDT")
        else:
            save(resample_4h(coinbase_1h(CB[a])), f"COINBASE_{CB[a].replace('-', '')}")
