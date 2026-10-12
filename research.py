"""Research harness: evaluate a target function vs benchmarks on assets x windows.
Usage (in experiments): from research import evaluate; evaluate(fn, ["BTC"], ["TRAIN"])"""
import pandas as pd
from data_loader import load, SYMBOLS
from backtest import window_slice, run, metrics, cost_per_side
from strategy import BENCHMARKS

COLS = ["Sharpe", "Calmar", "MaxDD", "CAGR", "Trades", "Turnover", "Exposure"]


def eval_one(fn, asset, window, cost_mult=1.0, delay=0):
    df = load(asset)
    ws = window_slice(df, window)
    if ws is None:
        return None
    d, s, e = ws
    res = run(d, fn(d), s, e, cost_per_side(asset, SYMBOLS[asset]) * cost_mult, delay)
    return res


def evaluate(strats: dict, assets, windows, cost_mult=1.0, delay=0, bench=True, show=True):
    allfn = dict(BENCHMARKS) if bench else {}
    allfn.update(strats)
    rows = []
    for a in assets:
        for w in windows:
            for name, fn in allfn.items():
                res = eval_one(fn, a, w, cost_mult, delay)
                if res is None:
                    continue
                m = metrics(res)
                rows.append(dict(asset=a, window=w, strat=name, **m))
    t = pd.DataFrame(rows)
    if show and len(t):
        print(t[["asset", "window", "strat"] + COLS].to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    return t
