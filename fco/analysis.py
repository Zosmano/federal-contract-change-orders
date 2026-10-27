"""Where cost growth happens: rates and dollars by procurement method, commodity, size, duration,
competition, department and award timing."""
import numpy as np
import pandas as pd

from . import config as C


def bands(c):
    c = c.copy()
    vl = ["$10K–25K", "$25K–100K", "$100K–1M", "$1M–10M", "$10M+"]
    c["value_band"] = pd.cut(c.v0, C.VALUE_BANDS, labels=vl, right=False).astype(str)
    dl = ["Under 3 months", "3–12 months", "1–3 years", "3+ years"]
    c["duration_band"] = pd.cut(c.duration_days, C.DURATION_BANDS_DAYS, labels=dl, right=False).astype(str).replace("nan", "Not reported")
    c["bids_band"] = np.select([c.bids.isna(), c.bids <= 0, c.bids == 1, c.bids <= 3], ["Not reported", "None reported", "1 bid", "2–3 bids"], "4+ bids")
    c["award_month"] = np.where(c.year_end_rush, "March (fiscal year-end)", "April–February")
    return c


def cohort(c):
    """Awards with full follow-up; implausible values (likely unit errors) left out."""
    co = c[(c.contract_date >= C.COHORT_START) & (c.contract_date <= C.COHORT_END)]
    return bands(co[co.plausible]), int((~co.plausible).sum())


def _summ(g):
    added = (g.final_value - g.v0)
    return pd.Series({"contracts": len(g), "amended": (g.amendments > 0).mean(),
                      "material_growth": (g.growth >= C.MATERIAL_GROWTH).mean(),
                      "slipped": (g.slip_days >= C.SCHEDULE_SLIP_DAYS).mean(),
                      "awarded": g.v0.sum(), "net_added": added.sum(),
                      "growth_pct": added.sum() / g.v0.sum()})


def breakdowns(p):
    out = {}
    for dim in ["procedure", "commodity", "value_band", "duration_band", "bids_band", "entity", "award_month", "fiscal_year"]:
        out[dim] = p.groupby(dim).apply(_summ, include_groups=False).reset_index()
    org = p.groupby(["owner_org", "owner_org_title"]).apply(_summ, include_groups=False).reset_index()
    out["department"] = org[org.contracts >= C.MIN_ORG_CONTRACTS].sort_values("net_added", ascending=False)
    return out


def headline(p, excluded):
    added = (p.final_value - p.v0)
    pos = added.clip(lower=0).sort_values(ascending=False)
    n = len(p)
    curve = [{"top_pct": q, "share_added": float(pos.head(max(1, int(n * q / 100))).sum() / pos.sum())}
             for q in [0.1, 0.5, 1, 2, 5, 10, 20, 50, 100]]
    amended = p[p.amendments > 0]
    return {
        "contracts": n, "excluded_implausible": excluded,
        "window": [C.COHORT_START, C.COHORT_END], "follow_up_years": C.FOLLOW_UP_YEARS,
        "amended": float((p.amendments > 0).mean()), "grew": float((p.growth > 0.001).mean()),
        "material_growth": float((p.growth >= C.MATERIAL_GROWTH).mean()), "doubled": float((p.growth >= 1).mean()),
        "shrank": float((p.growth < -0.001).mean()), "slipped": float((p.slip_days >= C.SCHEDULE_SLIP_DAYS).mean()),
        "median_growth_when_grew": float(p.loc[p.growth > 0.001, "growth"].median()),
        "median_slip_when_slipped": float(p.loc[p.slip_days > 0, "slip_days"].median()),
        "awarded": float(p.v0.sum()), "final": float(p.final_value.sum()), "net_added": float(added.sum()),
        "gross_added": float(pos.sum()), "concentration": curve,
        "option_share_of_amended": float(amended.option_mentioned.mean()),
        "amendments_per_amended": float(amended.amendments.mean()),
    }


def biggest(p, n=40):
    t = p.assign(added=p.final_value - p.v0).sort_values("added", ascending=False).head(n)
    return t[["owner_org_title", "vendor_name", "procurement_id", "contract_date", "description_en", "procedure",
              "commodity", "v0", "final_value", "growth", "amendments", "slip_days"]]
