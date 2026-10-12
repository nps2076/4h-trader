# Experiments log

**Trial counter:** 0 experiments, 0 parameter combinations evaluated.

## Ideas rejected
| Idea | Reason | EXP |
|---|---|---|

## Data / process issues
- D-001: TradingView 4H history starts 2024-01-01 for every symbol (1H only from 2026-01-01). VALIDATION and HOLDOUT A/B can't come from TradingView. User chose to open network access to the Coinbase/Binance public APIs; still blocked (403) at the time of writing.
- D-002: Cache frozen at last complete bar 2026-10-11 20:00 UTC (the 2026-10-12 00:00 bar was still forming). 10 symbols cached. One missing bar 2025-10-25 16:00 on all Coinbase pairs (left as is; that return spans 8h). No misaligned stamps, no bad OHLC, no zero volume.

## Entries
### EXP-000 Phase 0 (BTC TRAIN descriptive analysis) — commit see git
See LEARNINGS.md §Data findings; script `analysis/phase0.py`, output `analysis/phase0_output.txt`.
