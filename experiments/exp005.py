import sys; sys.path.insert(0, ".")
import numpy as np, pandas as pd
from research import evaluate

def atr(d, n):
    pc = d.close.shift()
    tr = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def hyst(enter, exit_):
    sig = pd.Series(np.nan, index=enter.index)
    sig[exit_] = 0.0; sig[enter] = 1.0
    return sig.ffill().fillna(0.0)

def sma_band(N, k, an=84):
    def f(d):
        m = d.close.rolling(N).mean(); a = atr(d, an)
        return hyst(d.close > m + k * a, d.close < m - k * a)
    return f

if __name__ == "__main__":
    rows = []
    for N in [180, 300, 600, 1200]:
        for k in [0, 0.5, 1, 1.5, 2]:
            t = evaluate({"x": sma_band(N, k)}, ["BTC"], ["TRAIN"], bench=False, show=False).iloc[0]
            rows.append(dict(N=N, k=k, Sh=t.Sharpe, Cal=t.Calmar, DD=t.MaxDD, Tr=t.Trades, TO=t.Turnover))
    t = pd.DataFrame(rows)
    for c in ["Sh", "Cal", "Tr"]:
        print(c); print(t.pivot(index="N", columns="k", values=c).round(2).to_string())
