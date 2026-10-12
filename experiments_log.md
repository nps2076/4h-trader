# Experiments log

**Trial counter:** 8 experiments, 79 parameter combinations evaluated.

Commit for each entry = the commit whose message carries its EXP ID (`git log --grep EXP-0NN`); log and code go in together.

## Ideas rejected
| Idea | Reason | EXP |
|---|---|---|
| Raw TSMOM sign(L-bar ret) | no plateau, 40–100 trades/yr eaten by costs | EXP-001 |
| Donchian N/N÷2 standalone | only N=120 works, neighbours ~0 Sharpe | EXP-002 |
| Vol-scaling overlay (own-median σ target) | BTC-only gain, ETH neutral, +2–3 params | EXP-004/006 |
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

### EXP-006 Vol-scaling overlay on the accepted SMA-band base (σ_ref = own 365d median of σ_30d, cap 1, band 0.2)
Hypothesis: within long periods, cutting size when vol runs above its norm (stress, crashes) should lift Sharpe and cut DD further. Risk: extra rebalancing trades eat the gain at 30 bp/side.
Result (Sh/Cal/DD/trades, 1× cost): BTC base 0.81/0.67/−32%/18 → VS 0.87/0.79/−30%/18; ETH base 1.07/1.22/−35%/14 → VS 1.05/1.24/−33%/14.
Decision: REJECTED. The gain is BTC-only (ETH flat), and in practice the overlay only resizes entries (band 0.2 vs 0.35 identical: no mid-trade rebalances fire). It adds 2–3 parameters for ~0.03 Sharpe on average.

### EXP-007 Step 4: base (SMA300 ± 1·ATR84 band) on ETH TRAIN, no changes
Result: ETH Sh 1.07, Cal 1.22, DD −35%, 14 trades, TO 13/yr vs B&H 0.33/0.00/−68%, SMA200 0.28/0.08/−43%, SMA50/200 −0.17/−0.30. At 2× cost: 0.98/1.03. PASS. Flag: <20 trades on both BTC (18) and ETH (14), so statistically weak per window.
Code moved to strategy.trend_band (PARAMS sma_n=300, atr_n=84, k=1).
- D-003: Added fetch_history.py (Coinbase 1H→4H resample, Binance 4H) for pre-2024 history; loader fixed so TradingView bars win on overlap. Not run yet (403).

### EXP-008 TRAIN robustness snapshot (no strategy change) — run_all.py --windows TRAIN --robust --rolling
Plateau (Sharpe): BTC sma_n 250–600 × k 0.5–2 all ≥ 0.71 except one cell (B&H 0.59); ETH sma_n 200–500 all ≥ 0.87 (B&H 0.33). ATR 42/84/168: BTC .95/.81/.81, ETH 1.11/1.07/1.12. 2× cost: BTC .64/Cal .42 (still > B&H), ETH .98. +1 bar delay: BTC .86, ETH 1.05. BTC+ETH basket: TB Sh 1.07/Cal 1.13 vs B&H .46/.18.
Rolling 365d BTC (5 windows, TRAIN-era data only): TB beats both benchmarks on Sharpe in only 1/5. It trails B&H in strong-uptrend years (lower exposure) and SMA200 in the bear year. Expect per-window failures in strong bull windows. Not acting on this (no new information beyond TRAIN; avoid over-fitting).
