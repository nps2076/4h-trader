# 4h-trader: TrendBand, a 4H crypto trend strategy

Rules-based, technical-only, long/flat strategy for 4H crypto candles (TradingView data).
- **Logic and worked examples:** [STRATEGY.md](STRATEGY.md)
- **Results, robustness, honest assessment:** [results_summary.md](results_summary.md)
- **TradingView Pine script:** [pine/TrendBand.pine](pine/TrendBand.pine)
- Research record: [experiments_log.md](experiments_log.md) · distilled knowledge: [LEARNINGS.md](LEARNINGS.md)

| File | Role |
|---|---|
| `data/raw/*.json`, `data/*.parquet` | Frozen TradingView 4H cache (2024-01-01 → 2026-10-11 20:00 UTC) |
| `data_loader.py` | Builds the parquet cache from raw dumps and prints a data audit |
| `strategy.py` | Benchmarks + `trend_band` signal (`allow_short` flag) |
| `backtest.py` | Engine: next-open execution, costs per exchange, windows, metrics |
| `run_all.py` | Reproduces every table and chart (`results/`, `charts/`) |
| `baselines.py` | Fixed benchmark reference numbers |
| `analysis/phase0.py` | Phase 0 descriptive analysis (BTC TRAIN) |
| `experiments/` | Scripts for each logged experiment |
| `fetch_history.py` | Pre-2024 exchange-API fetcher (unused: network blocked in this environment) |

```bash
pip install -r requirements.txt
python data_loader.py
python run_all.py --tag final --robust --rolling
```
