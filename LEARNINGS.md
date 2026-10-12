# LEARNINGS (re-read at session start; keep ≤ ~60 lines)

## Data findings (Phase 0, BTC 4H TRAIN only: Sep 2024 – Oct 2026, 4,625 bars)
- Returns: 4H σ ≈ 94 bp (ann. vol ≈ 44%), roughly symmetric, fat tails (excess kurtosis 6; |z|>3 is 7× normal). Tails thin out at daily/weekly horizons.
- Volatility clusters strongly and persistently: ACF of |r| ≈ 0.17 at lags 1–42 bars; rolling 30d vol ranges 24–70%. → vol-scaled sizing/thresholds should help.
- Short horizons are noise or slightly mean-reverting: return ACF ≈ 0; variance ratio < 1 up to ~1 week (not significant). → no edge in 4H/1d momentum; costs would eat it.
- Trend appears only at multi-week horizons: VR(30d) = 1.18, VR(60d) = 1.36, Hurst 0.56. Past 20–30d return mildly predicts the next week (corr ≈ +0.1).
- Price above the 50d SMA (300 bars) separates forward 7d returns best (+0.9% vs −0.3%). Slower SMAs separate less but whipsaw less (50d crossed every ~7d, 200d every ~20d). Crossings are frequent, so plain MA crosses pay a lot in costs → need hysteresis/bands.
- After large 1-day shocks: about one day of bounce, then continuation over a week (down shock: next 7d −2.3%; up shock: +1.2%). Supports breakout/trend logic, not fading.
- Time-of-day/day-of-week: volume and vol peak 12–20 UTC and drop on weekends; mean returns show no significant pattern (|t| < 1.8). Don't use calendar effects.
- Volume: correlates with |r| (0.53), but carries little directional information. Low priority.
- Drawdowns: B&H max DD −54% within TRAIN; under water 62% of the time by >10%. Avoiding the deep leg matters more than catching the top.
- Data: TradingView 4H history starts 2024-01-01, and pre-2024 sources are unreachable. TRAIN is all the usable data, so out-of-sample = unseen coins only; Y1/Y2 splits are in-sample stability checks. One missing Coinbase bar (2025-10-25 16:00, all pairs).

## First hypotheses
- H1: Slow trend signal (≈20–60d lookback) with hysteresis beats SMA200 after costs.
- H2: Vol-targeted sizing raises Sharpe and cuts MDD (exploits clustering).
- H3: Donchian-style breakout entry with a tighter exit captures post-shock continuation.
- H4: Short-term mean reversion won't survive ~30 bp/side Coinbase costs.

## What works
- Hysteresis is the single biggest lever: a ±k·ATR band around a 50–100d SMA turns a whipsawing MA rule into a robust one (plateau over N 300–600 bars, k 0.5–2). It cuts trades ~3× and keeps the trend signal.
- Expressing the band in ATR units makes it portable: the same rule works on ETH with no change.

## What doesn't
- Raw sign-of-return / MA-cross signals at 4H: flip near zero, so 40–100 trades/yr × 30 bp/side wipes out the edge (EXP-001/003).
- Donchian breakout alone: parameter-fragile on 2 years of data (EXP-002).
- Shorting (symmetric, midline cover, or 200d-regime gated): helps only in the bear half-year, loses more in bull/sideways squeezes, doubles costs (EXP-009/010). Kept as an off-by-default flag.
- Vol-scaling vs the asset's own median vol: small, asset-inconsistent gain, not worth 2–3 extra params (EXP-004/006).

## Current accepted strategy
`trend_band`: long/flat on 4H. Enter long at the next open when close > SMA(300) + 1·ATR(84); exit to flat when close < SMA(300) − 1·ATR(84); otherwise keep the current state. Full size, no leverage; `allow_short` flag (default off). Frozen as v1-frozen. BTC TRAIN Sh 0.81/Cal 0.67/DD −32% (B&H 0.59/0.33/−54%); ETH TRAIN 1.07/1.22/−35% (B&H 0.33/0.00/−68%). ~15 trades/yr, so per-window statistics are weak (<20 trades).

## Open ideas
Multi-timeframe (daily/weekly from completed bars) trend filter; ATR trailing stop; vol-regime filter.
