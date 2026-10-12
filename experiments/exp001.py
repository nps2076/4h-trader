import sys; sys.path.insert(0, ".")
from research import evaluate
def tsmom(L):
    return lambda d: (d.close.pct_change(L) > 0).astype(float)
evaluate({f"TSMOM{L}": tsmom(L) for L in [120, 180, 240, 360]}, ["BTC"], ["TRAIN"])
