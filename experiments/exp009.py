import sys; sys.path.insert(0, ".")
import numpy as np, pandas as pd
from research import evaluate
from strategy import trend_band, atr

def short_midline(d, sma_n=300, atr_n=84, k=1.0):
    m = d.close.rolling(sma_n).mean(); a = atr(d, atr_n)
    long_ = trend_band(d, sma_n, atr_n, k)              # long/flat leg
    s = pd.Series(np.nan, index=d.index)
    s[d.close > m] = 0.0; s[d.close < m - k * a] = -1.0  # short leg: enter below band, cover at SMA
    s = s.ffill().fillna(0.0)
    return long_.where(long_ > 0, s)

if __name__ == "__main__":
    S = {"LongOnly": trend_band, "A_symm": lambda d: trend_band(d, allow_short=True), "B_midline": short_midline}
    for cm in [1, 2]:
        print(f"--- cost x{cm}")
        evaluate(S, ["BTC", "ETH"], ["TRAIN", "TRAIN_Y1", "TRAIN_Y2"], bench=(cm == 1), cost_mult=cm)
