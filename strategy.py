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


# ---------------------------------------------------------------- candidate strategy
PARAMS = {"sma_n": 300, "atr_n": 84, "k": 1.0}  # 50d SMA, 14d ATR, band = 1 ATR


def atr(df, n):
    pc = df.close.shift()
    tr = pd.concat([df.high - df.low, (df.high - pc).abs(), (df.low - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def trend_band(df, sma_n=PARAMS["sma_n"], atr_n=PARAMS["atr_n"], k=PARAMS["k"]):
    """Long/flat trend filter with volatility-scaled hysteresis.
    Enter long when close > SMA + k*ATR; exit to flat when close < SMA - k*ATR; otherwise hold."""
    m = df.close.rolling(sma_n).mean()
    a = atr(df, atr_n)
    sig = pd.Series(np.nan, index=df.index)
    sig[df.close < m - k * a] = 0.0
    sig[df.close > m + k * a] = 1.0
    return sig.ffill().fillna(0.0)
