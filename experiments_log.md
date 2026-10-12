# Experiments log

**Trial counter:** 5 experiments, 36 parameter combinations evaluated.

## Ideas rejected
| Idea | Reason | EXP |
|---|---|---|
| Raw TSMOM sign(L-bar ret) | no plateau, 40–100 trades/yr eaten by costs | EXP-001 |
| Donchian N/N÷2 standalone | only N=120 works, neighbours ~0 Sharpe | EXP-002 |
| Multi-horizon sign ensemble | still flips near zero, high turnover | EXP-003 |

## Data / process issues
- D-001: TradingView 4H history starts 2024-01-01 for every symbol (1H only from 2026-01-01). VALIDATION and HOLDOUT A/B can't come from TradingView. User chose to open network access to the Coinbase/Binance public APIs; still blocked (403) at the time of writing.
- D-002: Cache frozen at last complete bar 2026-10-11 20:00 UTC (the 2026-10-12 00:00 bar was still forming). 10 symbols cached. One missing bar 2025-10-25 16:00 on all Coinbase pairs (left as is; that return spans 8h). No misaligned stamps, no bad OHLC, no zero volume.

## Entries
### EXP-000 Phase 0 (BTC TRAIN descriptive analysis) — commit see git
See LEARNINGS.md §Data findings; script `analysis/phase0.py`, output `analysis/phase0_output.txt`.

### EXP-001 Time-series momentum (TSMOM), long if L-bar return > 0
Hypothesis: BTC trends at multi-week horizons (VR>1 beyond 30d), so being long only when the trailing 20–60d return is positive should avoid the deep drawdown legs and beat SMA200, which has the same intent but lags more. Scan L ∈ {120, 180, 240, 360} bars (20/30/40/60d) on BTC TRAIN.
Result (BTC TRAIN; B&H Sh 0.59/Cal 0.33/DD −54%; SMA200 0.52/0.31/−39%):
| L | 120 | 180 | 240 | 360 |
|---|---|---|---|---|
| Sharpe/Calmar | −0.32/−0.22 | 0.06/−0.05 | 0.59/0.36 | 0.42/0.22 |
| MaxDD, trades, turnover/yr | −59%, 106, 100 | −53%, 85, 80 | −39%, 63, 59 | −38%, 44, 41 |
Decision: REJECTED. No plateau (Sharpe swings 0.9 across neighbours), and turnover of 40–100/yr at 30 bp/side means 12–30%/yr cost drag. Lesson: a raw sign-of-return signal flips too often near zero. Hysteresis is needed.

### EXP-002 Donchian breakout (enter on N-bar high close, exit on N/2-bar low close)
Hypothesis: post-shock continuation plus multi-week trend. Entering only on new N-bar highs and exiting only on N/2-bar lows builds in hysteresis, so turnover should drop several-fold vs TSMOM. Scan N ∈ {120, 180, 240, 360}.

### EXP-003 Multi-horizon trend ensemble: position = fraction of lookbacks {L, 2L, 4L} with positive return, rebalanced in steps of 1/3
Hypothesis: averaging several horizons smooths flips (one horizon flips at a time, so each flip trades only 1/3) and removes the single-lookback fragility. Scan base L ∈ {60, 90, 120, 180}.
Result EXP-002 (Sh/Cal/DD/trades): DON120 0.62/0.45/−30%/17; DON180 0.05/−0.05/−40%/14; DON240 0.02/−0.06/−42%/12; DON360 0.36/0.14/−43%/8. Turnover 7–16/yr.
Decision: REJECTED as a standalone. Turnover is fine, but there's no plateau: only N=120 beats B&H, with 17 trades. Fragile.
Result EXP-003: ENS60/90/120/180 Sharpe −0.23/0.06/0.27/0.22, turnover 50–93/yr. REJECTED: smoothing across horizons doesn't stop flips near zero, and cost drag dominates.
Note: TRAIN is a trend-up / long-sideways / deep-bear / recovery path. Pure trend rules whipsaw in the sideways part.

### EXP-004 Volatility-scaling overlay: w = min(1, σ_ref/σ_30d) × base signal; σ_ref = rolling 365d median of σ_30d (asset's own norm); no-trade band 0.2
Hypothesis: vol clusters and rises in sell-offs (leverage effect), so cutting size when vol is above its own norm should raise Sharpe and cut drawdown for any base signal, B&H included. The band limits rebalancing churn. Bases tested: B&H, SMA200, DON120/240.
Result EXP-004 (Sh/Cal/DD): VS_BH 0.51/0.24/−56%; VS_SMA200 0.56/0.36/−38%; VS_DON120 0.67/0.53/−27%; VS_DON240 0.07/−0.03/−40%.
Decision: PARKED. It adds a small, consistent gain to trend bases (+0.04–0.05 Sharpe), but it can't rescue a weak base and it hurt B&H, because σ_ref is the asset's own median so B&H is scaled ~half the time with no timing edge. Revisit as an overlay on the final base.

### EXP-005 SMA with ATR hysteresis band: long when close > SMA(N)+k·ATR(84), flat when close < SMA(N)−k·ATR(84)
Hypothesis: the 50d SMA separates forward returns best in Phase 0, but noise crossings cost a lot. A volatility-scaled band (in ATR units, so no asset-specific constant) should filter noise crossings and keep the trend signal. Grid N ∈ {180, 300, 600, 1200} × k ∈ {0, 0.5, 1, 1.5, 2} = 20 combos. Looking for a plateau, not the best cell.
Result EXP-005 (BTC TRAIN), Sharpe grid (rows N, cols k=0/0.5/1/1.5/2):
N180 .30 .47 .33 .41 .40 | N300 .56 .74 .81 .74 .91 | N600 .64 .82 1.00 1.05 1.05 | N1200 .52 .55 .67 .68 .53
Calmar N300: .33 .54 .67 .53 .78; N600: .42 .78 1.10 1.20 1.12. Trades fall from 53 (N300,k0) to 6 (N600,k2).
Decision: ACCEPTED as base. Chosen N=300 (50d), k=1: Sh 0.81, Cal 0.67, DD −32%, 18 trades, TO 16.6/yr (2× cost: 0.64/0.42). Reason: a broad plateau (N 300–600 × k ≥ 0.5 all beat both benchmarks), and the band is in vol units, so it's portable. I picked a round cell inside the plateau, not the best one (N600 has <10 trades). It adds 1 parameter (k) over a plain SMA.
