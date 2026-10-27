"""Export the analysis and build the self-contained app (outputs/change_orders.html)."""
import datetime as dt
import json

import numpy as np
import pandas as pd

from . import config as C

TEMPLATE = C.ROOT / "fco" / "app_template.html"


def _en(s):
    """'National Defence | Défense nationale' -> 'National Defence'."""
    return s.fillna("").astype(str).str.split("|").str[0].str.strip()


def _rec(df, cols=None):
    d = df if cols is None else df[cols]
    d = d.copy()
    for c in d.columns:
        if pd.api.types.is_datetime64_any_dtype(d[c]):
            d[c] = d[c].dt.strftime("%Y-%m-%d")
    return json.loads(d.replace({np.nan: None}).to_json(orient="records", double_precision=4))


def payload(head, br, biggest, metrics, factors, model, watch, unlinked):
    dept = br["department"].assign(owner_org_title=lambda d: _en(d.owner_org_title))
    big = biggest.assign(owner_org_title=lambda d: _en(d.owner_org_title))
    wl = watch.assign(owner_org_title=lambda d: _en(d.owner_org_title))
    org_names = dict(zip(dept.owner_org, dept.owner_org_title))
    return {
        "generated": dt.date.today().isoformat(),
        "head": head, "unlinked": {"amendments": unlinked[0], "of": unlinked[1]},
        "cfg": {"material": C.MATERIAL_GROWTH, "slip_days": C.SCHEDULE_SLIP_DAYS, "watch_min": C.WATCH_MIN_VALUE,
                "train_end": C.TRAIN_END, "score_from": C.SCORE_FROM, "max_growth": C.MAX_PLAUSIBLE_GROWTH},
        "breakdowns": {k: _rec(v) for k, v in br.items() if k != "department"},
        "department": _rec(dept),
        "biggest": _rec(big),
        "metrics": metrics, "factors": factors,
        "model": model | {"org_names": org_names},
        "watch": _rec(wl),
    }


def build(data):
    body = TEMPLATE.read_text(encoding="utf-8")
    blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False, default=float).replace("</", "<\\/")
    body = body.replace("/*__DATA__*/null", blob)
    C.OUT.mkdir(parents=True, exist_ok=True)
    head, rest = body.split("<style>", 1)
    full = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            + head + "<style>" + rest.replace("</style>", "</style></head><body>", 1) + "\n</body></html>")
    for name, html in [("change_orders.html", full), ("change_orders_artifact.html", body)]:
        (C.OUT / name).write_text(html, encoding="utf-8")
    out = C.OUT / "change_orders.html"
    print(f"-> {out} ({out.stat().st_size / 1e6:.2f} MB)")
    return out
