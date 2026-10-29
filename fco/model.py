"""Award-time risk model: the chance a new contract grows by 25% or more within three years.

A regularised logistic regression on banded features known on the day of award, so every factor reads
as an odds ratio and the app can score any contract live. Gradient boosting is fitted alongside as a
benchmark. Validation is out-of-time: train on fiscal 2017-18 to 2020-21, test on 2021-22 and 2022-23."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from . import analysis as A
from . import config as C

FEATURES = ["org", "procedure", "commodity", "entity", "value_band", "duration_band", "bids_band", "award_month", "category"]
LABELS = {"org": "Department", "procedure": "How it was bought", "commodity": "What was bought", "entity": "Who awarded it",
          "value_band": "Award value", "duration_band": "Planned length", "bids_band": "Bids received",
          "award_month": "Award month", "category": "Spending category"}


def prepare(c, orgs=None, cats=None):
    c = A.bands(c)
    if orgs is None:
        n = c.owner_org.value_counts()
        orgs = set(n[n >= C.MIN_ORG_CONTRACTS].index)
    if cats is None:
        n = c.description_en.value_counts()
        cats = set(n[n >= C.MIN_ORG_CONTRACTS].index)
    c["org"] = c.owner_org.where(c.owner_org.isin(orgs), "other")
    c["category"] = c.description_en.where(c.description_en.isin(cats), "Other")
    for f in FEATURES:      # pandas keeps missing values missing through astype(str)
        c[f] = c[f].astype(object).where(c[f].notna(), "Not reported").astype(str)
    return c, orgs, cats


def _org_names(reason, org_en):
    """'Department: esdc-edsc' -> 'Department: Employment and Social Development Canada'."""
    return "; ".join(f"Department: {org_en.get(p.split(': ', 1)[1], p.split(': ', 1)[1])}" if p.startswith("Department: ") else p
                     for p in reason.split("; "))


def _X(c, cols=None):
    X = pd.get_dummies(c[FEATURES].astype(str), prefix_sep="=", dtype=float)
    return X if cols is None else X.reindex(columns=cols, fill_value=0.0)


def _metrics(y, p):
    order = np.argsort(-p)
    top = order[: int(0.1 * len(y))]
    cal = pd.DataFrame({"p": p, "y": y}).assign(b=lambda d: pd.qcut(d.p.rank(method="first"), 10, labels=False)) \
        .groupby("b").agg(pred=("p", "mean"), obs=("y", "mean"))
    return {"auc": float(roc_auc_score(y, p)), "pr_auc": float(average_precision_score(y, p)),
            "brier": float(brier_score_loss(y, p)), "base_rate": float(y.mean()),
            "recall_top10": float(y[top].sum() / y.sum()), "lift_top10": float(y[top].mean() / y.mean()),
            "calibration": cal.to_dict("records"),
            "gains": [{"pct": q, "caught": float(y[order[: int(q / 100 * len(y))]].sum() / y.sum())} for q in range(0, 101, 5)]}


def run(c):
    co = c[(c.contract_date >= C.COHORT_START) & (c.contract_date <= C.COHORT_END) & c.plausible]
    co, orgs, cats = prepare(co)
    co["y"] = (co.growth >= C.MATERIAL_GROWTH).astype(int)
    tr, te = co[co.contract_date <= C.TRAIN_END], co[co.contract_date > C.TRAIN_END]
    Xtr = _X(tr)
    Xte = _X(te, Xtr.columns)
    lr = LogisticRegression(C=0.5, max_iter=3000).fit(Xtr, tr.y)
    gb = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, random_state=0).fit(Xtr, tr.y)
    m = {"logistic": _metrics(te.y.values, lr.predict_proba(Xte)[:, 1]),
         "boosting": _metrics(te.y.values, gb.predict_proba(Xte)[:, 1]),
         "train": {"n": int(len(tr)), "from": str(tr.contract_date.min().date()), "to": str(tr.contract_date.max().date())},
         "test": {"n": int(len(te)), "from": str(te.contract_date.min().date()), "to": str(te.contract_date.max().date())}}

    # Refit on the whole cohort for the calculator and the watch list.
    Xall = _X(co)
    lr = LogisticRegression(C=0.5, max_iter=3000).fit(Xall, co.y)
    coef = dict(zip(Xall.columns, lr.coef_[0]))
    levels = {f: sorted(co[f].astype(str).unique()) for f in FEATURES}
    # Odds ratio of each level against the feature's most common level.
    base = {f: co[f].astype(str).mode()[0] for f in FEATURES}
    factors = [{"feature": f, "label": LABELS[f], "level": lv, "n": int((co[f].astype(str) == lv).sum()),
                "rate": float(co.loc[co[f].astype(str) == lv, "y"].mean()),
                "odds_ratio": float(np.exp(coef.get(f"{f}={lv}", 0) - coef.get(f"{f}={base[f]}", 0)))}
               for f in FEATURES for lv in levels[f]]

    # Watch list: recent large awards, too new to have an outcome, ranked by predicted risk.
    new = c[(c.contract_date >= C.SCORE_FROM) & c.plausible]
    new, _, _ = prepare(new, orgs, cats)
    Xn = _X(new, Xall.columns)
    new["risk"] = lr.predict_proba(Xn)[:, 1]
    avg_growth = float(co.loc[co.y == 1, "growth"].median())
    contrib = Xn.values * lr.coef_[0]
    names = np.array(Xall.columns)
    top = new[new.v0 >= C.WATCH_MIN_VALUE].sort_values(["risk", "v0"], ascending=False).head(C.WATCH_LIST_SIZE)
    reasons = []
    for i in top.index:
        row = contrib[new.index.get_loc(i)]
        idx = [j for j in np.argsort(-row)[:3] if row[j] > 0]
        reasons.append("; ".join(f"{LABELS[names[j].split('=')[0]]}: {names[j].split('=', 1)[1]}" for j in idx))
    org_en = dict(zip(c.owner_org, c.owner_org_title.fillna("").str.split("|").str[0].str.strip()))
    reasons = [_org_names(x, org_en) for x in reasons]
    top = top.assign(reasons=reasons)
    # No vendor names: the score describes the kind of contract, not the supplier.
    watch = top[["owner_org_title", "procurement_id", "contract_date", "description_en", "procedure",
                 "commodity", "duration_band", "v0", "risk", "reasons"]]
    model = {"intercept": float(lr.intercept_[0]), "coef": {k: float(v) for k, v in coef.items()},
             "levels": levels, "labels": LABELS, "base": base, "median_growth_material": avg_growth,
             "scored_recent": int(len(new)), "expected_material_recent": float(new.risk.sum())}
    # Every recent award of $1M+ with its score, for the portfolio contingency simulation.
    scored = new[new.v0 >= C.WATCH_MIN_VALUE][["key", "contract_date", "owner_org_title", "description_en", "procedure",
                                              "commodity", "duration_band", "v0", "risk"]]
    return m, factors, model, watch, scored
