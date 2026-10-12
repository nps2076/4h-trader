import sys; sys.path.insert(0, ".")
import numpy as np, pandas as pd
from research import evaluate

def donchian(N, M=None):
    M = M or N // 2
    def f(d):
        hi = d.close.rolling(N).max().shift(1); lo = d.close.rolling(M).min().shift(1)
        sig = pd.Series(np.nan, index=d.index)
        sig[d.close > hi] = 1.0; sig[d.close < lo] = 0.0
        return sig.ffill().fillna(0.0)
    return f

def ensemble(L):
    def f(d):
        return sum((d.close.pct_change(k) > 0).astype(float) for k in (L, 2*L, 4*L)) / 3
    return f

if __name__ == "__main__":
    evaluate({f"DON{N}": donchian(N) for N in [120, 180, 240, 360]}, ["BTC"], ["TRAIN"])
    evaluate({f"ENS{L}": ensemble(L) for L in [60, 90, 120, 180]}, ["BTC"], ["TRAIN"], bench=False)
