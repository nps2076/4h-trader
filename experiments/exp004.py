import sys; sys.path.insert(0, ".")
import numpy as np, pandas as pd
from research import evaluate
from strategy import bench_bh, bench_sma200
from experiments.exp002_003 import donchian

def band(target, b):
    t = target.values; out = np.empty_like(t); cur = 0.0
    for i, x in enumerate(t):
        if np.isnan(x): out[i] = cur; continue
        if abs(x - cur) > b or (x == 0 and cur > 0) or (x >= 1 and cur < 1 and x - cur > 1e-9 and cur > 1 - b):
            cur = x
        out[i] = cur
    return pd.Series(out, index=target.index)

def volscale(d, vol_n=180, ref_n=2190):
    r = np.log(d.close).diff()
    s = r.rolling(vol_n).std()
    ref = s.rolling(ref_n, min_periods=vol_n * 3).median()
    return (ref / s).clip(upper=1.0)

def vs(base, b=0.2):
    return lambda d: band(base(d) * volscale(d), b)

if __name__ == "__main__":
    evaluate({"VS_BH": vs(bench_bh), "VS_SMA200": vs(bench_sma200),
              "VS_DON120": vs(donchian(120)), "VS_DON240": vs(donchian(240))}, ["BTC"], ["TRAIN"])
