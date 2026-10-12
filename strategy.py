"""Signal logic. Every function maps an OHLCV frame (4H, UTC) to a target position in [0,1]
computed on bar CLOSE; backtest.run executes it at the next bar's open.
No dates, no asset-specific constants."""
import numpy as np
import pandas as pd

# ---------------------------------------------------------------- benchmarks (fixed, do not change)
def bench_bh(df):
    return pd.Series(1.0, index=df.index)


def bench_sma200(df):
    """Long when close > 200-day SMA (1,200 4H bars), else flat."""
    return (df.close > df.close.rolling(1200).mean()).astype(float)


def bench_sma50_200(df):
    """Long when 50-day SMA (300 bars) > 200-day SMA (1,200 bars), else flat."""
    return (df.close.rolling(300).mean() > df.close.rolling(1200).mean()).astype(float)


BENCHMARKS = {"B&H": bench_bh, "SMA200": bench_sma200, "SMA50/200": bench_sma50_200}
