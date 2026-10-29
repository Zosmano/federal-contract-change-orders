"""Project controls on the contract portfolio: cost and schedule performance at close, reference-class
forecasting, PERT three-point estimates, Monte Carlo contingency, an expected-monetary-value risk register,
a probability-impact matrix and change-control metrics.

Each contract is treated as a small project. Its signed value is the cost baseline (budget at completion, BAC)
and its value after three years of amendments is its cost at completion (EAC). The data has no progress
reporting, so in-flight earned value (EV, CPI, SPI during delivery) cannot be measured; the indices here are
close-out analogues, named as such.

    CV  = BAC - EAC              cost variance at completion (negative = over baseline)
    CPI = BAC / EAC              cost performance at close (below 1 = over baseline)
    VAC% = (BAC - EAC) / BAC     variance at completion as a share of baseline
    SPI(t) = PD / (PD + slip)    schedule performance at close, from planned duration and end-date slip
    PERT mean = (O + 4M + P) / 6,   PERT sigma = (P - O) / 6
    EMV = probability x impact
"""
import numpy as np
import pandas as pd

from . import config as C

CLASS_DURATIONS = ["Under 3 months", "3–12 months", "1–3 years", "3+ years"]


def _perf(g):
    bac, eac = g.v0.sum(), g.final_value.sum()
    t = g[g.duration_days > 0]
    pd_, slip = t.duration_days, t.slip_days.clip(lower=0)
    return pd.Series({
        "contracts": len(g), "bac": bac, "eac": eac, "cv": bac - eac, "cpi": bac / eac, "vac_pct": (bac - eac) / bac,
        "over_baseline": (g.growth > 0.001).mean(), "material_overrun": (g.growth >= C.MATERIAL_GROWTH).mean(),
        "spi_t": pd_.sum() / (pd_ + slip).sum(), "on_schedule": (t.slip_days <= 0).mean(),
        "late_90": (t.slip_days >= C.SCHEDULE_SLIP_DAYS).mean(),
    })


def performance(p):
    """Cost and schedule performance at close, for the portfolio and by the planning factors."""
    out = {"portfolio": _perf(p).to_dict()}
    for dim in ["commodity", "procedure", "duration_band", "value_band", "fiscal_year"]:
        g = p[p[dim].astype(str) != "Not reported"].groupby(dim).apply(_perf, include_groups=False).reset_index()
        out[dim] = g.to_dict("records")
    cost_over, late = p.growth >= C.MATERIAL_GROWTH, p.slip_days >= C.SCHEDULE_SLIP_DAYS
    out["quadrants"] = {"on_track": int((~cost_over & ~late).sum()), "cost_only": int((cost_over & ~late).sum()),
                        "schedule_only": int((~cost_over & late).sum()), "both": int((cost_over & late).sum())}
    return out


def reference_classes(p):
    """Reference-class forecasting (Flyvbjerg): the uplift on a new baseline needed to reach a chosen confidence
    of not overrunning, read from what happened to similar contracts. Classes are major contracts ($1M+) by
    commodity x planned length; most small contracts never change, which would flatten every percentile to zero."""
    p = p[(p.v0 >= C.WATCH_MIN_VALUE) & p.commodity.isin(["Goods", "Services", "Construction"]) & p.duration_band.isin(CLASS_DURATIONS)]
    rows = []
    for (com, dur), g in p.groupby(["commodity", "duration_band"]):
        if len(g) < C.MIN_CLASS_SIZE:
            continue
        ratio = g.final_value / g.v0
        o, m, pe = np.percentile(ratio, C.PERT_POINTS)
        rows.append({"commodity": com, "duration_band": dur, "contracts": len(g), "bac": g.v0.sum(),
                     "p_material": (g.growth >= C.MATERIAL_GROWTH).mean(), "mean_uplift": ratio.mean() - 1,
                     "dollar_uplift": g.final_value.sum() / g.v0.sum() - 1,
                     **{f"p{q}": float(np.percentile(ratio, q) - 1) for q in C.CONFIDENCE_LEVELS},
                     "pert_o": o, "pert_m": m, "pert_p": pe, "pert_mean": (o + 4 * m + pe) / 6, "pert_sd": (pe - o) / 6})
    t = pd.DataFrame(rows)
    t["duration_band"] = pd.Categorical(t.duration_band, CLASS_DURATIONS, ordered=True)
    return t.sort_values(["commodity", "duration_band"]).reset_index(drop=True)


def _calibrate(risk, calibration):
    """Map model scores to observed rates using the out-of-time calibration table (the model runs high at the top)."""
    cal = pd.DataFrame(calibration).sort_values("pred")
    return np.interp(risk, cal.pred, cal.obs, left=cal.obs.iloc[0], right=cal.obs.iloc[-1])


def _class_draws(p):
    """Empirical growth for each commodity x length class of $1M+ contracts, split into material growers and the
    rest. Size-matched: small contracts swing far more in proportion, so they would overstate large-award risk."""
    p = p[p.v0 >= C.WATCH_MIN_VALUE]
    grow, rest = {}, {}
    for key, g in p.groupby(["commodity", "duration_band"]):
        grow[key] = g.loc[g.growth >= C.MATERIAL_GROWTH, "growth"].to_numpy()
        rest[key] = g.loc[g.growth < C.MATERIAL_GROWTH, "growth"].to_numpy()
    allg = p.loc[p.growth >= C.MATERIAL_GROWTH, "growth"].to_numpy()
    allr = p.loc[p.growth < C.MATERIAL_GROWTH, "growth"].to_numpy()
    pick = lambda d, k, fb: d[k] if k in d and len(d[k]) >= 30 else fb
    return lambda k: (pick(grow, k, allg), pick(rest, k, allr))


def _monte_carlo(rng, v0, prob, keys, draws):
    S = C.SIMULATIONS
    hit = rng.random((S, len(v0))) < prob
    growth = np.empty((S, len(v0)))
    for j, k in enumerate(keys):
        g, r = draws(k)
        growth[:, j] = np.where(hit[:, j], rng.choice(g, S), rng.choice(r, S))
    return growth @ v0


def backtest(p):
    """Out-of-time check of the simulation: build it from 2017-21 awards of $1M+ (class rates and change sizes),
    run it on the 2021-23 awards of $1M+, and compare with the cost growth that actually happened."""
    rng = np.random.default_rng(C.SEED)
    big = p[p.v0 >= C.WATCH_MIN_VALUE]
    tr, te = big[big.contract_date <= C.TRAIN_END], big[big.contract_date > C.TRAIN_END]
    rate = tr.assign(y=tr.growth >= C.MATERIAL_GROWTH).groupby(["commodity", "duration_band"]).y.mean()
    keys = list(zip(te.commodity, te.duration_band))
    prob = np.array([rate.get(k, (tr.growth >= C.MATERIAL_GROWTH).mean()) for k in keys])
    added = _monte_carlo(rng, te.v0.to_numpy(), prob, keys, _class_draws(tr)) / te.v0.sum()
    actual = float(te.final_value.sum() / te.v0.sum() - 1)
    lo, mid, hi = (float(np.percentile(added, q)) for q in (10, 50, 90))
    return {"awards": int(len(te)), "bac": float(te.v0.sum()), "actual": actual, "p10": lo, "p50": mid, "p90": hi,
            "expected": float(added.mean()), "within_p10_p90": bool(lo <= actual <= hi),
            "percentile_of_actual": float((added <= actual).mean() * 100)}


def simulate(p, scored, calibration):
    """Monte Carlo of the recent $1M+ portfolio: each award grows 25%+ with its calibrated probability, and the
    size of its change is drawn from what happened to past contracts of the same kind."""
    rng = np.random.default_rng(C.SEED)
    s = scored.copy()
    s["p"] = _calibrate(s.risk.to_numpy(), calibration)
    draws = _class_draws(p)
    n = len(s)
    added = _monte_carlo(rng, s.v0.to_numpy(), s.p.to_numpy(), list(zip(s.commodity, s.duration_band)), draws)
    bac = float(s.v0.sum())
    q = {f"p{k}": float(np.percentile(added, k)) for k in (10, 50, 80, 90, 95)}
    hist, edges = np.histogram(added / bac, bins=60, range=(0, float(np.percentile(added, 99)) / bac))
    # Impact for the register: the class median change among growers, a typical outcome rather than the tail.
    typical = {k: float(np.median(draws(k)[0])) for k in set(zip(s.commodity, s.duration_band))}
    s["impact"] = [v * typical[(c, d)] for v, c, d in zip(s.v0, s.commodity, s.duration_band)]
    s["emv"] = s.p * s.impact
    return {"awards": n, "bac": bac, "expected": float(added.mean()), **q,
            "contingency": q[f"p{C.CONTINGENCY_LEVEL}"], "contingency_pct": q[f"p{C.CONTINGENCY_LEVEL}"] / bac,
            "expected_material": float(s.p.sum()), "raw_expected_material": float(s.risk.sum()),
            "histogram": {"counts": hist.tolist(), "edges": edges.tolist()}}, s


def risk_register(s, n=15):
    """Expected monetary value of each award's cost-growth risk, and the probability-impact matrix."""
    s = s.copy()
    s["prob_band"] = pd.cut(s.p, C.PROB_BANDS, labels=False, include_lowest=True)
    s["impact_band"] = pd.cut(s.impact, C.IMPACT_BANDS, labels=False, include_lowest=True)
    grid = s.groupby(["prob_band", "impact_band"]).agg(awards=("emv", "size"), emv=("emv", "sum")).reset_index()
    top = s.sort_values("emv", ascending=False).head(n)
    top = top.assign(department=top.owner_org_title.str.split("|").str[0].str.strip())
    reg = top[["department", "description_en", "procedure", "commodity", "duration_band", "contract_date", "v0", "p", "impact", "emv"]]
    return reg, grid, {"emv_total": float(s.emv.sum()), "emv_top10_share": float(top.head(10).emv.sum() / s.emv.sum())}


def change_control(p):
    am = p[p.amendments > 0]
    bins = [0, 1, 2, 3, 4, 6, 10_000]
    labels = ["0", "1", "2", "3", "4–5", "6+"]
    dist = pd.cut(p.amendments, bins, labels=labels, right=False).value_counts().reindex(labels)
    by = am.groupby("commodity").first_change_days.median().drop("Not reported", errors="ignore")
    big = am[am.v0 >= C.WATCH_MIN_VALUE]
    return {"amended": int(len(am)), "amendments_total": int(am.amendments.sum()),
            "per_amended": float(am.amendments.mean()), "median_first_change_days": float(am.first_change_days.median()),
            "first_change_by_commodity": {k: float(v) for k, v in by.items()},
            "distribution": [{"amendments": k, "contracts": int(v)} for k, v in dist.items()],
            "large_amended_rate": float((p[p.v0 >= C.WATCH_MIN_VALUE].amendments > 0).mean()),
            "large_per_amended": float(big.amendments.mean()),
            "option_share": float(am.option_mentioned.mean())}


def run(p, scored, metrics):
    perf = performance(p)
    rc = reference_classes(p)
    sim, s = simulate(p, scored, metrics["logistic"]["calibration"])
    sim["backtest"] = backtest(p)
    reg, grid, emv = risk_register(s)
    cc = change_control(p)
    out = {"performance": perf, "reference_classes": rc.astype({"duration_band": str}).to_dict("records"),
           "simulation": sim, "register": reg.assign(contract_date=reg.contract_date.astype(str)).to_dict("records"),
           "pi_grid": grid.to_dict("records"), "emv": emv, "change_control": cc}
    return out, rc, s, reg
