"""Phase 0: descriptive analysis of BTC 4H, TRAIN window only (Sep 2024 - Oct 2026)."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parents[1]))
import numpy as np, pandas as pd
from scipy import stats
from data_loader import load
from backtest import WINDOWS

df = load("BTC")
s, e = (pd.Timestamp(x, tz="UTC") for x in WINDOWS["TRAIN"])
d = df[(df.index >= s) & (df.index < e)].copy()
r = np.log(d.close).diff().dropna()
P = lambda *a: print(*a)
P(f"bars={len(d)}  from {d.index[0]} to {d.index[-1]}")

P("\n== 1. Return distribution (4H log returns)")
P(f"mean={r.mean()*1e4:.2f}bp sd={r.std()*1e4:.1f}bp ann.vol={r.std()*np.sqrt(2190):.1%} skew={stats.skew(r):.2f} exkurt={stats.kurtosis(r):.1f}")
z = (r - r.mean()) / r.std()
P(f"|z|>3: {np.mean(np.abs(z)>3):.2%} (normal 0.27%);  |z|>4: {np.mean(np.abs(z)>4):.2%}")
P("quantiles(bp):", {q: round(r.quantile(q)*1e4, 1) for q in [.01, .05, .5, .95, .99]})
for k, name in [(6, "daily"), (42, "weekly")]:
    rk = np.log(d.close).diff(k).dropna()[::k]
    P(f"{name}: sd={rk.std():.2%} skew={stats.skew(rk):.2f} exkurt={stats.kurtosis(rk):.1f}")

P("\n== 2. Volatility clustering: ACF of |r| and r^2")
acf = lambda x, l: x.autocorr(l)
P("lag   1     2     6     12    42    180")
P("|r| ", " ".join(f"{acf(r.abs(), l):.3f}" for l in [1, 2, 6, 12, 42, 180]))
P("r^2 ", " ".join(f"{acf(r**2, l):.3f}" for l in [1, 2, 6, 12, 42, 180]))
rv = r.rolling(180).std() * np.sqrt(2190)
P(f"rolling 30d vol: min={rv.min():.0%} median={rv.median():.0%} max={rv.max():.0%}")

P("\n== 3. Time-of-day (bar open UTC) and day-of-week")
tod = pd.DataFrame({"r": r, "h": r.index.hour, "dow": r.index.dayofweek, "v": d.volume.reindex(r.index)})
g = tod.groupby("h").agg(mean_bp=("r", lambda x: x.mean()*1e4), sd_bp=("r", lambda x: x.std()*1e4), t=("r", lambda x: x.mean()/x.std()*np.sqrt(len(x))), vol_rel=("v", "mean"))
g["vol_rel"] /= g.vol_rel.mean(); P(g.round(2).to_string())
g = tod.groupby("dow").agg(mean_bp=("r", lambda x: x.mean()*1e4), sd_bp=("r", lambda x: x.std()*1e4), t=("r", lambda x: x.mean()/x.std()*np.sqrt(len(x))), vol_rel=("v", "mean"))
g["vol_rel"] /= g.vol_rel.mean(); P(g.round(2).to_string())

P("\n== 4. Drawdown profile (buy & hold close)")
eq = d.close / d.close.iloc[0]; dd = eq / eq.cummax() - 1
P(f"total ret={eq.iloc[-1]-1:.1%} maxDD={dd.min():.1%}  time in DD>10%: {(dd<-.1).mean():.0%}, >20%: {(dd<-.2).mean():.0%}")
under = dd < 0; runs = (under != under.shift()).cumsum()
lens = under.groupby(runs).sum(); lens = lens[lens > 0] / 6
P(f"underwater spells: n={len(lens)} longest={lens.max():.0f}d median={lens.median():.1f}d")
# DD episodes > 10%: depth
ep = []; pk = 0
for i in range(len(dd)):
    pass

P("\n== 5. Serial dependence")
P("ACF r lag1..6:", " ".join(f"{acf(r, l):+.3f}" for l in range(1, 7)), f" (2SE={2/np.sqrt(len(r)):.3f})")
lp = np.log(d.close)
for k, name in [(6, "1d"), (42, "1w"), (180, "30d")]:
    rk = lp.diff(k).dropna()[::k]
    P(f"ACF of non-overlapping {name} returns lag1={rk.autocorr(1):+.3f} lag2={rk.autocorr(2):+.3f} (n={len(rk)}, 2SE={2/np.sqrt(len(rk)):.2f})")
def vr(x, q):
    x = x.values; n = len(x); mu = x.mean()
    s1 = ((x-mu)**2).sum()/(n-1)
    xq = np.convolve(x, np.ones(q), "valid")
    m = q*(n-q+1)*(1-q/n)
    sq = ((xq-q*mu)**2).sum()/m
    v = sq/s1
    phi = 2*(2*q-1)*(q-1)/(3*q*n)
    return v, (v-1)/np.sqrt(phi)
P("Variance ratio (Lo-MacKinlay, homosk. z):")
for q in [2, 6, 12, 42, 84, 180, 360]:
    v, zz = vr(r, q); P(f"  q={q:4d} ({q/6:5.1f}d) VR={v:.3f} z={zz:+.2f}")
def hurst_rs(x, ns=(12, 24, 48, 96, 192, 384, 768)):
    out = []
    for n in ns:
        rs = []
        for i in range(0, len(x)-n+1, n):
            c = x[i:i+n]; y = np.cumsum(c-c.mean()); R = y.max()-y.min(); S = c.std()
            if S > 0: rs.append(R/S)
        out.append(np.mean(rs))
    return np.polyfit(np.log(ns), np.log(out), 1)[0]
P(f"Hurst (R/S, 2d..128d blocks) = {hurst_rs(r.values):.3f}")

P("\n== 6. Time-series momentum: corr(past L-bar ret, next H-bar ret), non-overlapping on H")
for L, H in [(6, 6), (42, 6), (42, 42), (120, 42), (180, 42), (360, 42), (180, 180)]:
    past = lp.diff(L); fut = lp.shift(-H) - lp
    x = pd.concat([past, fut], axis=1).dropna().iloc[::H]
    c = x.corr().iloc[0, 1]; hit = (np.sign(x.iloc[:, 0]) == np.sign(x.iloc[:, 1])).mean()
    up = x[x.iloc[:, 0] > 0].iloc[:, 1].mean(); dn = x[x.iloc[:, 0] <= 0].iloc[:, 1].mean()
    P(f"  L={L/6:5.1f}d H={H/6:4.1f}d corr={c:+.3f} hit={hit:.2f} fut|up={up*1e2:+.2f}% fut|down={dn*1e2:+.2f}% n={len(x)}")
P("Price vs SMA(N): forward 7d log-return (mean %) when above vs below")
for N in [60, 120, 300, 600, 1200]:
    sma = d.close.rolling(N).mean() if False else df.close.rolling(N).mean().reindex(d.index)
    fut = (lp.shift(-42) - lp)
    a = fut[d.close > sma].mean(); b = fut[d.close <= sma].mean()
    cross = ((d.close > sma) != (d.close.shift() > sma.shift())).sum()
    P(f"  N={N:5d} ({N/6:4.0f}d): above={a*100:+.2f}% below={b*100:+.2f}% time_above={(d.close>sma).mean():.0%} crosses={cross} (~{len(d)/max(cross,1)/6:.1f}d apart)")

P("\n== 7. Behaviour after large 4H moves (|r| > 2.5x rolling 30d sd)")
sd = r.rolling(180).std().shift(1)
big = (r.abs() > 2.5*sd)
for side, m in [("up", big & (r > 0)), ("down", big & (r < 0))]:
    out = []
    for H in [1, 6, 42]:
        f = (lp.shift(-H) - lp).reindex(r.index)[m]
        out.append(f"H={H/6:.1f}d mean={f.mean()*100:+.2f}% t={f.mean()/f.std()*np.sqrt(f.count()):+.1f}")
    P(f"  {side}: n={m.sum()}  " + " | ".join(out))
P("Next-bar |r| after big move vs unconditional (vol persistence):",
  f"{r.abs().shift(-1)[big].mean()*1e4:.0f}bp vs {r.abs().mean()*1e4:.0f}bp")
# daily-scale: 1-day move > 2.5 sd of daily
r6 = lp.diff(6); sd6 = r6.rolling(180).std().shift(6)
for side, m in [("up", r6 > 2.0*sd6), ("down", r6 < -2.0*sd6)]:
    f = (lp.shift(-42) - lp)[m]; f2 = (lp.shift(-6) - lp)[m]
    P(f"  1d move >2sd {side}: bars={m.sum()} next1d={f2.mean()*100:+.2f}% next7d={f.mean()*100:+.2f}%")

P("\n== 8. Volume")
v = d.volume; lv = np.log(v)
P(f"corr(log vol, |r|) = {np.corrcoef(lv.reindex(r.index), r.abs())[0,1]:.2f};  ACF log vol lag1={lv.autocorr(1):.2f} lag6={lv.autocorr(6):.2f}")
rel = v / v.rolling(180).median()
fut6 = (lp.shift(-6) - lp); fut42 = (lp.shift(-42) - lp)
for lo, hi in [(0, .7), (.7, 1.5), (1.5, 3), (3, 99)]:
    m = (rel >= lo) & (rel < hi)
    P(f"  rel.vol [{lo},{hi}): {m.mean():.0%} bars, next1d={fut6[m].mean()*100:+.2f}% next7d={fut42[m].mean()*100:+.2f}%")
# volume confirmation: up bar with high volume vs low volume
for lab, m in [("up&hiVol", (r > 0) & (rel.reindex(r.index) > 1.5)), ("up&loVol", (r > 0) & (rel.reindex(r.index) < .7)),
               ("dn&hiVol", (r < 0) & (rel.reindex(r.index) > 1.5)), ("dn&loVol", (r < 0) & (rel.reindex(r.index) < .7))]:
    P(f"  {lab}: n={m.sum()} next7d={fut42.reindex(r.index)[m].mean()*100:+.2f}%")
