"""Step 2: fixed benchmark reference numbers (B&H, SMA200, SMA50/200) for every asset x window with data."""
from pathlib import Path
from research import evaluate
from data_loader import SYMBOLS
from backtest import WINDOWS

if __name__ == "__main__":
    t = evaluate({}, list(SYMBOLS), list(WINDOWS), show=False)
    Path("results").mkdir(exist_ok=True)
    t.to_csv("results/baselines.csv", index=False)
    cols = ["window", "asset", "strat", "CAGR", "Sharpe", "Sortino", "Calmar", "MaxDD", "Trades", "Turnover", "CostDrag"]
    Path("results/baselines.md").write_text(t[cols].to_markdown(index=False, floatfmt=".2f"))
    print(t.groupby("window").asset.unique())
