import sys; sys.path.insert(0, ".")
from research import evaluate
from strategy import trend_band

def regime_short(d):
    ls = trend_band(d, allow_short=True)
    bear = d.close < d.close.rolling(1200).mean()
    return ls.where(ls >= 0, ls.where(bear, 0.0))   # keep shorts only in the 200d bear regime

if __name__ == "__main__":
    for cm in [1, 2]:
        print(f"--- cost x{cm}")
        evaluate({"LongOnly": trend_band, "C_regime": regime_short}, ["BTC", "ETH"], ["TRAIN", "TRAIN_Y1", "TRAIN_Y2"], bench=False, cost_mult=cm)
