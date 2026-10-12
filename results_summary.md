# Results summary: TrendBand v1 (frozen, commit b044057)

**Strategy:** 4H long/flat. Long when close > SMA(300) + 1·ATR(84), flat when close < SMA(300) − 1·ATR(84), otherwise hold. Signal on close, fill at next open. Same parameters for every coin. Full logic and worked examples are in [STRATEGY.md](STRATEGY.md); TradingView version in [pine/TrendBand.pine](pine/TrendBand.pine).
**Benchmarks (fixed in advance):** buy-and-hold; SMA200 (close > 1,200-bar SMA); SMA50/200 cross (300 vs 1,200 bars). `TrendBand_LS` = same rule with `allow_short=True` (information only, not the default).
**Costs per side:** Coinbase 0.25% taker + 5 bp slippage (BTC/ETH) or 10 bp (alts); Binance (BNB) 0.10% + 5 bp. Shorts pay 5%/yr carry. Annualisation 2,190 bars/yr; Sharpe and Sortino use rf = 0.
**Reproduce:** `python data_loader.py && python run_all.py --tag final --robust --rolling` → `results/final.md` (full metric tables: CAGR, vol, Sharpe, Sortino, Calmar, MaxDD and duration, win rate, PF, trades, avg hold, exposure, turnover, cost drag) and `charts/final_<ASSET>_<WINDOW>.png` (equity + drawdown vs benchmarks).

## Data and windows (important deviation from the original plan)
- Source: TradingView MCP, 4H. History starts **2024-01-01** for every symbol, and pre-2024 sources (exchange APIs) are blocked in this environment. Cache frozen at bar 2026-10-11 20:00 UTC. One missing bar on every Coinbase pair (2025-10-25 16:00).
- After the 200-day warm-up, the only usable window is **TRAIN = Sep 2024 – Oct 2026**. VALIDATION (Sep 23–Aug 24) and HOLDOUT A/B (2021–23) **could not be run**.
- TRAIN_Y1 (Sep 24–Aug 25, mostly bull) and TRAIN_Y2 (Sep 25–Oct 26, mostly bear) are in-sample stability splits, **not** out-of-sample.
- The only genuine out-of-sample test is **cross-asset**: SOL, BNB (Binance, USDT quote), XRP, DOGE, ADA, AVAX, LINK, LTC, XLM, BCH were never run with the strategy before the freeze (EXP-011, run once).

## Results: Sharpe / Calmar / MaxDD (all coins x windows x strategies)
| window   | asset      | B&H                  | SMA200               | SMA50/200            | TrendBand            | TrendBand_LS         |   TB_trades | TB_expo   |
|:---------|:-----------|:---------------------|:---------------------|:---------------------|:---------------------|:---------------------|------------:|:----------|
| TRAIN    | BTC        | 0.59 / 0.33 / -54%   | 0.52 / 0.31 / -39%   | 0.16 / 0.00 / -42%   | 0.81 / 0.67 / -32%   | 0.42 / 0.23 / -41%   |          18 | 54%       |
| TRAIN    | ETH        | 0.33 / 0.00 / -68%   | 0.28 / 0.08 / -43%   | -0.17 / -0.30 / -48% | 1.07 / 1.22 / -35%   | 0.96 / 1.04 / -50%   |          14 | 49%       |
| TRAIN    | SOL        | 0.25 / -0.11 / -78%  | 0.41 / 0.17 / -50%   | -0.26 / -0.36 / -67% | 0.49 / 0.24 / -52%   | 0.33 / -0.05 / -65%  |          18 | 48%       |
| TRAIN    | BNB        | 0.58 / 0.30 / -60%   | -0.02 / -0.18 / -49% | 0.55 / 0.39 / -40%   | 0.71 / 0.55 / -40%   | 0.45 / 0.23 / -47%   |          18 | 57%       |
| TRAIN    | XRP        | 0.93 / 0.74 / -73%   | 1.03 / 1.18 / -51%   | 0.95 / 0.84 / -61%   | 0.86 / 0.57 / -71%   | 0.31 / -0.09 / -87%  |          21 | 41%       |
| TRAIN    | DOGE       | 0.35 / -0.08 / -85%  | 0.29 / -0.02 / -72%  | -0.11 / -0.28 / -76% | 0.92 / 0.79 / -58%   | 0.91 / 0.73 / -70%   |          12 | 41%       |
| TRAIN    | ADA        | 0.30 / -0.15 / -89%  | -0.27 / -0.36 / -88% | -0.35 / -0.46 / -81% | -0.01 / -0.21 / -81% | -0.35 / -0.59 / -94% |          24 | 38%       |
| TRAIN    | AVAX       | 0.03 / -0.33 / -89%  | 0.07 / -0.15 / -70%  | -0.49 / -0.44 / -77% | 0.11 / -0.12 / -75%  | 0.09 / -0.33 / -80%  |          21 | 44%       |
| TRAIN    | LINK       | 0.53 / 0.12 / -76%   | 0.55 / 0.26 / -61%   | -0.12 / -0.32 / -73% | 0.49 / 0.20 / -61%   | 0.12 / -0.29 / -78%  |          21 | 49%       |
| TRAIN    | LTC        | 0.38 / -0.00 / -72%  | 0.07 / -0.19 / -69%  | 0.05 / -0.21 / -63%  | -0.40 / -0.41 / -83% | -1.04 / -0.70 / -95% |          27 | 48%       |
| TRAIN    | XLM        | 0.86 / 0.59 / -77%   | 0.56 / 0.17 / -80%   | 0.15 / -0.18 / -79%  | 0.64 / 0.30 / -74%   | 0.14 / -0.30 / -88%  |          26 | 42%       |
| TRAIN    | BCH        | 0.31 / -0.08 / -72%  | -0.64 / -0.48 / -75% | -0.12 / -0.34 / -53% | 0.26 / -0.01 / -48%  | 0.01 / -0.40 / -61%  |          17 | 48%       |
| TRAIN    | BASKET(12) | 0.53 / 0.21 / -68%   | 0.34 / 0.11 / -53%   | 0.03 / -0.14 / -54%  | 0.65 / 0.39 / -49%   | 0.24 / -0.02 / -58%  |           0 | nan%      |
| TRAIN_Y1 | BTC        | 1.54 / 2.75 / -31%   | 0.56 / 0.40 / -39%   | 0.40 / 0.22 / -37%   | 1.45 / 2.25 / -25%   | 0.58 / 0.44 / -40%   |           7 | 67%       |
| TRAIN_Y1 | ETH        | 1.15 / 1.18 / -65%   | 1.02 / 1.05 / -41%   | 0.32 / 0.08 / -48%   | 1.64 / 2.74 / -35%   | 0.98 / 1.14 / -50%   |           9 | 52%       |
| TRAIN_Y1 | SOL        | 0.91 / 0.77 / -66%   | 0.31 / 0.02 / -50%   | 0.01 / -0.31 / -59%  | 1.03 / 1.80 / -30%   | 0.49 / 0.14 / -44%   |           8 | 56%       |
| TRAIN_Y1 | BNB        | 1.19 / 1.93 / -32%   | -0.18 / -0.33 / -49% | 0.85 / 1.01 / -32%   | 0.74 / 0.73 / -33%   | -0.08 / -0.35 / -47% |          10 | 67%       |
| TRAIN_Y1 | XRP        | 2.13 / 7.87 / -50%   | 1.78 / 4.71 / -50%   | 1.73 / 4.50 / -50%   | 1.48 / 2.13 / -65%   | 0.29 / -0.20 / -86%  |          13 | 53%       |
| TRAIN_Y1 | DOGE       | 1.25 / 1.58 / -72%   | 0.89 / 0.83 / -59%   | 0.08 / -0.30 / -68%  | 1.56 / 2.84 / -53%   | 1.08 / 1.14 / -70%   |           6 | 51%       |
| TRAIN_Y1 | ADA        | 1.31 / 2.29 / -60%   | 0.12 / -0.30 / -79%  | -0.12 / -0.61 / -67% | 0.25 / -0.14 / -72%  | -1.00 / -0.90 / -92% |          14 | 48%       |
| TRAIN_Y1 | AVAX       | 0.52 / 0.06 / -73%   | -0.02 / -0.31 / -61% | -0.58 / -0.63 / -67% | 0.31 / -0.03 / -59%  | -0.13 / -0.62 / -71% |           8 | 51%       |
| TRAIN_Y1 | LINK       | 1.26 / 1.73 / -66%   | 0.92 / 0.92 / -56%   | 0.18 / -0.24 / -59%  | 0.64 / 0.36 / -61%   | -0.32 / -0.71 / -78% |          14 | 54%       |
| TRAIN_Y1 | LTC        | 1.04 / 1.25 / -55%   | 0.40 / 0.03 / -51%   | 0.08 / -0.34 / -55%  | -0.27 / -0.54 / -71% | -1.52 / -0.92 / -89% |          14 | 61%       |
| TRAIN_Y1 | XLM        | 1.75 / 4.29 / -66%   | 1.40 / 2.47 / -62%   | 0.38 / -0.12 / -69%  | 1.57 / 3.02 / -62%   | 0.91 / 0.65 / -77%   |          12 | 50%       |
| TRAIN_Y1 | BCH        | 1.04 / 1.12 / -60%   | -0.05 / -0.32 / -62% | -0.08 / -0.36 / -53% | 0.86 / 0.93 / -44%   | 0.19 / -0.31 / -54%  |           5 | 60%       |
| TRAIN_Y1 | BASKET(12) | 1.52 / 2.44 / -54%   | 0.89 / 0.90 / -44%   | 0.38 / 0.13 / -45%   | 1.26 / 1.47 / -43%   | 0.14 / -0.15 / -58%  |           0 | nan%      |
| TRAIN_Y2 | BTC        | -0.36 / -0.39 / -54% | 0.59 / 0.47 / -21%   | -0.25 / -0.23 / -27% | -0.03 / -0.11 / -29% | 0.24 / 0.04 / -36%   |          11 | 43%       |
| TRAIN_Y2 | ETH        | -0.55 / -0.58 / -68% | -0.65 / -0.53 / -42% | -0.77 / -0.63 / -44% | 0.41 / 0.29 / -30%   | 0.97 / 1.29 / -38%   |           6 | 47%       |
| TRAIN_Y2 | SOL        | -0.49 / -0.55 / -75% | 0.62 / 0.59 / -29%   | -0.65 / -0.55 / -51% | -0.24 / -0.26 / -52% | 0.18 / -0.14 / -65%  |          11 | 42%       |
| TRAIN_Y2 | BNB        | 0.00 / -0.19 / -60%  | 0.16 / -0.02 / -47%  | 0.25 / 0.06 / -40%   | 0.70 / 0.52 / -40%   | 0.98 / 1.16 / -37%   |           9 | 49%       |
| TRAIN_Y2 | XRP        | -0.65 / -0.67 / -69% | -0.47 / -0.51 / -35% | -0.75 / -0.62 / -38% | -0.23 / -0.37 / -35% | 0.34 / 0.03 / -43%   |           8 | 29%       |
| TRAIN_Y2 | DOGE       | -0.84 / -0.72 / -77% | -0.96 / -0.59 / -52% | -0.46 / -0.44 / -47% | -0.08 / -0.25 / -42% | 0.69 / 0.81 / -33%   |           6 | 33%       |
| TRAIN_Y2 | ADA        | -1.00 / -0.76 / -85% | -1.25 / -0.67 / -56% | -1.02 / -0.66 / -50% | -0.42 / -0.47 / -47% | 0.51 / 0.27 / -39%   |          11 | 29%       |
| TRAIN_Y2 | AVAX       | -0.49 / -0.60 / -83% | 0.21 / -0.01 / -51%  | -0.37 / -0.43 / -56% | -0.09 / -0.22 / -65% | 0.34 / -0.05 / -77%  |          14 | 38%       |
| TRAIN_Y2 | LINK       | -0.38 / -0.55 / -72% | 0.02 / -0.17 / -44%  | -0.55 / -0.60 / -50% | 0.34 / 0.14 / -41%   | 0.72 / 0.51 / -59%   |           8 | 45%       |
| TRAIN_Y2 | LTC        | -0.43 / -0.54 / -70% | -0.50 / -0.45 / -52% | 0.02 / -0.22 / -37%  | -0.68 / -0.56 / -53% | -0.49 / -0.67 / -60% |          13 | 37%       |
| TRAIN_Y2 | XLM        | -0.25 / -0.60 / -66% | -0.77 / -0.72 / -62% | -0.24 / -0.45 / -42% | -0.72 / -0.85 / -50% | -0.83 / -0.89 / -70% |          14 | 34%       |
| TRAIN_Y2 | BCH        | -0.47 / -0.61 / -72% | -1.55 / -0.82 / -60% | -0.19 / -0.52 / -33% | -0.46 / -0.58 / -46% | -0.18 / -0.51 / -61% |          12 | 38%       |
| TRAIN_Y2 | BASKET(12) | -0.60 / -0.57 / -68% | -0.58 / -0.46 / -37% | -0.51 / -0.52 / -34% | -0.25 / -0.26 / -38% | 0.36 / 0.15 / -41%   |           0 | nan%      |

**Success criterion** (beat B&H and SMA200 on Sharpe and Calmar, MaxDD no worse than B&H + 5 pp):
- Full TRAIN: PASS on BTC, ETH (development coins) and on 4/10 unseen coins (SOL, BNB, DOGE, AVAX). FAIL on XRP, ADA, LINK, LTC, XLM, BCH. The 12-coin equal-weight basket PASSES (Sharpe 0.65 vs 0.53/0.34, MaxDD −49% vs −68%).
- TRAIN_Y1 (bull): PASS on ETH, SOL, DOGE only; the basket fails (B&H Sharpe 1.52 vs TB 1.26).
- TRAIN_Y2 (bear): PASS on 7/12 coins and the basket (TB −0.25 vs B&H −0.60).
- MaxDD below buy-and-hold on 11/12 coins over full TRAIN (exception LTC).

## Robustness
### Cost and execution-delay sensitivity (TrendBand)
| window   | asset   | case         |   Sharpe |   Calmar | MaxDD   | CAGR   |   Trades |
|:---------|:--------|:-------------|---------:|---------:|:--------|:-------|---------:|
| TRAIN    | BTC     | 1x cost      |     0.81 |     0.67 | -32%    | 21%    |       18 |
| TRAIN    | BTC     | 2x cost      |     0.64 |     0.42 | -37%    | 16%    |       18 |
| TRAIN    | BTC     | +1 bar delay |     0.86 |     0.71 | -33%    | 23%    |       18 |
| TRAIN    | ETH     | 1x cost      |     1.07 |     1.22 | -35%    | 43%    |       14 |
| TRAIN    | ETH     | 2x cost      |     0.98 |     1.03 | -36%    | 37%    |       14 |
| TRAIN    | ETH     | +1 bar delay |     1.05 |     1.27 | -33%    | 42%    |       14 |

### Parameter plateau: Sharpe, BTC TRAIN (atr_n=84; chosen sma_n=300, k=1)
|   sma_n |   0.5 |   0.75 |   1.0 |   1.25 |   1.5 |   2.0 |
|--------:|------:|-------:|------:|-------:|------:|------:|
|     200 |  0.59 |   0.6  |  0.52 |   0.41 |  0.52 |  0.6  |
|     250 |  0.52 |   0.57 |  0.94 |   0.9  |  0.95 |  0.93 |
|     300 |  0.74 |   0.93 |  0.81 |   0.71 |  0.74 |  0.91 |
|     400 |  0.93 |   0.98 |  0.9  |   0.86 |  0.94 |  0.96 |
|     500 |  1.09 |   1.05 |  1.03 |   0.98 |  1.06 |  0.9  |
|     600 |  0.82 |   1.01 |  1    |   1    |  1.05 |  1.05 |

ATR window sensitivity (BTC TRAIN, Sharpe): atr_n=42: 0.95, atr_n=84: 0.81, atr_n=168: 0.81

### Parameter plateau: Sharpe, ETH TRAIN (atr_n=84; chosen sma_n=300, k=1)
|   sma_n |   0.5 |   0.75 |   1.0 |   1.25 |   1.5 |   2.0 |
|--------:|------:|-------:|------:|-------:|------:|------:|
|     200 |  1.16 |   1.02 |  1.05 |   1.1  |  1.31 |  1.11 |
|     250 |  1.24 |   1.35 |  1.33 |   1.28 |  1.21 |  1.06 |
|     300 |  1.17 |   1.1  |  1.07 |   0.96 |  1.07 |  0.94 |
|     400 |  1.16 |   1.13 |  1.25 |   1.27 |  1.18 |  1.15 |
|     500 |  1.02 |   1.02 |  1.02 |   0.97 |  0.96 |  0.87 |
|     600 |  0.61 |   0.7  |  0.8  |   0.82 |  0.76 |  0.86 |

ATR window sensitivity (ETH TRAIN, Sharpe): atr_n=42: 1.11, atr_n=84: 1.07, atr_n=168: 1.12

## Rolling 365d windows, BTC (step 90d)
| start      |   B&H Sh |   B&H DD |   SMA200 Sh |   SMA200 DD |   SMA50/200 Sh |   SMA50/200 DD |   TrendBand Sh |   TrendBand DD |   TrendBand_LS Sh |   TrendBand_LS DD | TB beats B&H&SMA200 (Sh)   |
|:-----------|---------:|---------:|------------:|------------:|---------------:|---------------:|---------------:|---------------:|------------------:|------------------:|:---------------------------|
| 2024-07-19 |     1.46 |    -0.31 |        0.54 |       -0.39 |           0.46 |          -0.37 |           1.21 |          -0.25 |              0.2  |             -0.4  | False                      |
| 2024-10-17 |     1.25 |    -0.31 |        0.61 |       -0.39 |           0.38 |          -0.37 |           1.02 |          -0.25 |              0.23 |             -0.4  | False                      |
| 2025-01-15 |     0.22 |    -0.34 |       -0.58 |       -0.39 |          -0.88 |          -0.41 |           0.4  |          -0.19 |              0.15 |             -0.29 | True                       |
| 2025-04-15 |    -0.12 |    -0.5  |        0.61 |       -0.2  |          -0.44 |          -0.25 |           0.18 |          -0.31 |              0.25 |             -0.36 | False                      |
| 2025-07-14 |    -1.34 |    -0.54 |       -0.86 |       -0.2  |          -0.96 |          -0.25 |          -1.09 |          -0.31 |              0.19 |             -0.36 | False                      |
TrendBand beats both on Sharpe in 20% of 5 windows


## Final assessment

**Where it helps.** It reliably cuts drawdowns: max DD is lower than B&H on 11/12 coins, and the basket's is −49% vs −68%. It beats both benchmarks on the two development coins and on the trending unseen coins (SOL, BNB, DOGE), and it clearly beats the SMA50/200 cross almost everywhere. Results survive 2× costs and a 1-bar entry delay on BTC/ETH. The parameter surface is a plateau, not a spike.

**Where it doesn't.**
1. Strong bull years: it is invested only ~50% of the time and re-enters late after shakeouts, so it lags B&H (BTC, XRP, XLM, BNB in Y1).
2. Choppy, trendless coins with V-shaped reversals (LTC, ADA, BCH): the band gets whipsawed.
3. Bear phases on BTC: plain SMA200 did better in Y2.

In rolling 1-year BTC windows it beats both benchmarks only 1/5 times. Its value is in the full cycle, not in any given year.

**Shorts (`allow_short`).** Three variants were tested (EXP-009/010). Shorts improved results in the bear half-year (11/12 coins) but were worse over the full sample on 11/12 coins (BTC Sharpe 0.81 → 0.42; basket 0.65 → 0.24), because of squeezes in bull/sideways markets and doubled costs. They are kept as a configurable flag, off by default.

**Known weaknesses.**
- About 2 years of data. One bull-to-bear cycle doesn't make a robust test.
- There was no time-based out-of-sample test.
- 6–13 trades/yr per coin. Every Y1/Y2 window and half of the full-TRAIN coin windows have <20 trades, which is statistically weak.
- BNB is quoted in USDT on Binance, the rest in USD on Coinbase (minor).
- The basket ignores rebalancing costs.
- The cost model assumes a mid-volume Coinbase tier. Retail Coinbase fees (0.6–1.2%) would roughly double to quadruple drag, making the strategy marginal: see the 2× cost row.
- The Pine script mirrors the Python logic but hasn't been compiled or reconciled against TradingView's backtester.

**Search effort.** 11 logged experiments and 91 parameter combinations evaluated on BTC/ETH TRAIN, plus a 36-cell (×2 coins) plateau check and a 3-value ATR check.
- Accepted: SMA + ATR hysteresis band (EXP-005).
- Rejected: raw TSMOM (cost-dominated, no plateau), Donchian (fragile), multi-horizon ensemble (turnover), vol-scaling overlay (BTC-only, extra params), three short variants (worse overall). See `experiments_log.md`.

**How inflated are these numbers?** BTC/ETH TRAIN results are fully in-sample. The structure (band, k, SMA length) was chosen after ~90 trials on that same data, so selection bias is material. A haircut of perhaps 0.2–0.4 Sharpe on BTC/ETH would be prudent, given the plateau's spread and the number of trials. The 10 unseen coins are the honest estimate. There the strategy beat B&H on Sharpe in 4/10 coins and on drawdown in 9/10, and the basket edge was modest (+0.12 Sharpe, +0.18 Calmar). The fair conclusion is that TrendBand is a **drawdown-control overlay** with a small, uncertain risk-adjusted edge, not a strong alpha source. It should be validated on pre-2024 data (2021–22 bear, 2023 recovery) before any capital is committed.
