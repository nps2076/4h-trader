# TrendBand: strategy logic, explained with examples

**One sentence:** Hold the coin while price is clearly above its 50-day average, step aside (or, optionally, go short) when it is clearly below, and do nothing while price sits inside a "no-man's land" around the average. "Clearly" is measured in units of the coin's own volatility (ATR).

Code: `strategy.trend_band` (Python) · `pine/TrendBand.pine` (TradingView) · frozen version v1 (commit `b044057`).

---

## 1. Inputs and parameters

| Parameter | Value | Meaning |
|---|---|---|
| Timeframe | 4H bars (UTC), 6 bars per day | All indicators are computed on the 4H series |
| `sma_n` | 300 bars (= 50 days) | Trend anchor: simple moving average of close |
| `atr_n` | 84 bars (= 14 days) | Volatility yardstick: simple average of True Range |
| `k` | 1.0 | Half-width of the no-trade band, in ATRs |
| `allow_short` | `False` (default) | If `True`, the "below band" state is short (−1) instead of flat (0) |

The same four values are used for every coin and every period. There are no dates and no per-asset constants.

## 2. Indicators

```
TR[t]    = max(high[t] − low[t], |high[t] − close[t−1]|, |low[t] − close[t−1]|)
ATR[t]   = mean(TR[t−83 … t])                     # 84-bar simple average (not Wilder's RMA)
SMA[t]   = mean(close[t−299 … t])                 # 300-bar simple average
Upper[t] = SMA[t] + k · ATR[t]
Lower[t] = SMA[t] − k · ATR[t]
```

## 3. The rule (a three-zone state machine, evaluated at each 4H close)

```
if   close[t] > Upper[t]:  state = LONG (+1)
elif close[t] < Lower[t]:  state = FLAT (0)        # or SHORT (−1) when allow_short = True
else:                      state = state[t−1]      # inside the band: keep whatever you had
```

```
  price
    │            ┌──── close above Upper → go / stay LONG
    │ Upper ─────┼───────────────────────────────
    │            │  band (2·k·ATR wide): HOLD previous state, no trade
    │ SMA   ─────┼───────────────────────────────
    │            │
    │ Lower ─────┼───────────────────────────────
    │            └──── close below Lower → go / stay FLAT (or SHORT)
```

**Why the band?** Phase 0 found that price crosses its 50-day SMA about once a week, and most crossings are noise. A plain "close > SMA" rule therefore trades about 50 times a year and pays roughly 15% a year in costs. Requiring price to clear the SMA by one ATR before switching (*hysteresis*) cut BTC trades about 3× and turned a mediocre rule into one that beats both benchmarks on BTC/ETH (EXP-005). Because the band is measured in ATR, it widens automatically when the market is wild and narrows when it is calm. That is why the same `k` works on BTC (σ ≈ 44%/yr) and on DOGE (σ ≈ 80%/yr).

## 4. Execution and sizing

- The signal is computed on the **close** of bar *t* and executed at the **open of bar t+1**. There is no look-ahead.
- Position is 100% of equity when long, 0% when flat (−100% when short, if enabled). No leverage, no pyramiding.
- Assumed costs per side: Coinbase 0.25% taker + 0.05% slippage (0.10% for alts); Binance 0.10% + 0.05%. A full round trip on BTC costs about 0.60%. Shorts also pay an assumed 5%/yr carry (perpetual-futures funding/borrow).
- Warm-up: at least 300 bars are needed before the first signal. The backtests use 1,200 bars so the SMA200 benchmark is also formed.

## 5. Worked examples (real Coinbase BTC 4H bars)

### Example A: a trend captured (entry 21 Apr 2025, exit 20 Jun 2025)

| 4H bar close (UTC) | Close | SMA300 | ATR84 | Upper | Lower | Zone → state |
|---|---|---|---|---|---|---|
| 2025-04-21 00:00 | 87,206 | 84,181 | 1,360 | 85,541 | 82,822 | above Upper → **LONG** |
| … ~60 days … | | | | | | mostly above Upper or inside the band → stay LONG |
| 2025-06-20 16:00 | 103,326 | 104,480 | 1,069 | 105,549 | 103,411 | below Lower (by 85) → **FLAT** |

1. At the 00:00 close on 21 Apr, BTC closed at 87,206, which is 3,025 above the SMA and 1,665 above the Upper band. The signal flips to LONG.
2. The order fills at the **next bar's open** (04:00 bar, 87,206).
3. During the following weeks BTC pulled back several times toward the SMA. Each time it stayed *above Lower*, so the band kept the position and no trades were made.
4. On 20 Jun at the 16:00 close, price (103,326) dropped below Lower (103,411). The signal flips to FLAT, and the sell fills at the next open (103,326).
5. Result: +18.5% gross, about **+17.8% net** of 2 × 0.30% costs.

### Example B: a whipsaw (the cost of the method)

| 4H bar close (UTC) | Close | Upper | Lower | Action |
|---|---|---|---|---|
| 2025-02-03 00:00 | 94,111 | 101,166 | 97,415 | below Lower → sell (was long) |
| 2025-02-03 16:00 | 102,094 | 101,016 | 97,441 | above Upper → **buy** at 102,094 |
| 2025-02-05 20:00 | 96,638 | 100,664 | 97,167 | below Lower → **sell** at 96,636 |

A violent V-shaped swing crossed the whole band twice in three days. The round trip lost 5.3% gross, about **−5.9% net**. The band reduces whipsaws but can't remove them. This is why the strategy struggles on choppy, trendless coins (LTC, ADA, BCH in the tests).

### Example C: toy numbers for the "hold" zone

Suppose SMA = 100, ATR = 2, k = 1, so Upper = 102 and Lower = 98.

| Bar | Close | Zone | State (long/flat) | State (allow_short) | Trade at next open |
|---|---|---|---|---|---|
| 1 | 101 | inside band | 0 (start flat) | 0 | none |
| 2 | 103 | above 102 | **+1** | **+1** | buy 100% |
| 3 | 99.5 | inside band | +1 (hold) | +1 (hold) | none: a plain SMA rule would have sold here |
| 4 | 101 | inside band | +1 | +1 | none |
| 5 | 97 | below 98 | **0** | **−1** | sell 100% (long/flat) / sell 200% = flip to short |
| 6 | 99 | inside band | 0 | −1 (hold) | none |
| 7 | 102.5 | above 102 | **+1** | **+1** | buy 100% / buy 200% |

## 6. Shorts (`allow_short = True`)

The rule mirrors the long side: below Lower means short, above Upper means long, so you are always in the market. Tested in EXP-009/010 (symmetric, cover at SMA, and 200d-bear-regime gated). Shorting helped in the 2025–26 bear half-year on 11/12 coins but lost more in bull or sideways stretches through short squeezes and doubled trading costs. Over the full sample it was worse than long/flat on 11/12 coins (BTC Sharpe 0.81 → 0.42). It is kept as a switch, **off by default**. Practical note: Coinbase spot can't be shorted, so shorts assume a perpetual-futures or margin venue.

## 7. When it works / when it doesn't

- **Works:** coins with persistent multi-week trends and deep bear legs (BTC, ETH, SOL, BNB, DOGE). The main benefit is **drawdown control**: max DD was lower than buy-and-hold on 11/12 coins.
- **Lags:** steady bull markets. It is only invested about 50% of the time and re-enters late after shakeouts (BTC/XRP/XLM in Sep 2024–Aug 2025).
- **Fails:** trendless, mean-reverting chop with V-shaped reversals (LTC, ADA, BCH).
- **Statistical caveat:** about 7–9 trades per coin per year. Every per-coin window has fewer than 20 trades, so single-window results are noisy.

## 8. Parameter sensitivity (BTC TRAIN Sharpe; B&H = 0.59)

| sma_n \ k | 0.5 | 0.75 | 1.0 | 1.25 | 1.5 | 2.0 |
|---|---|---|---|---|---|---|
| 250 | 0.52 | 0.57 | 0.94 | 0.90 | 0.95 | 0.93 |
| **300** | 0.74 | 0.93 | **0.81** | 0.71 | 0.74 | 0.91 |
| 400 | 0.93 | 0.98 | 0.90 | 0.86 | 0.94 | 0.96 |
| 500 | 1.09 | 1.05 | 1.03 | 0.98 | 1.06 | 0.90 |

The chosen cell is not the best one. It sits inside a broad plateau where nearly every neighbour beats buy-and-hold.
