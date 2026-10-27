"""Load the federal contracts file and build one row per contract: what it was awarded at, what it grew
to within the follow-up window, and how far its end date moved."""
import numpy as np
import pandas as pd

from . import config as C

COLS = ["reference_number", "procurement_id", "vendor_name", "contract_date", "contract_period_start", "delivery_date",
        "contract_value", "original_value", "amendment_value", "instrument_type", "commodity_type", "commodity_code",
        "solicitation_procedure", "limited_tendering_reason", "number_of_bids", "owner_org", "owner_org_title",
        "reporting_period", "economic_object_code", "description_en", "contracting_entity", "comments_en"]
CACHE_FILE = C.CACHE / "contracts.pkl"

PROCEDURE = {"TC": "Competitive (traditional)", "OB": "Competitive (open bidding)", "ST": "Competitive (selective)",
             "TN": "Non-competitive", "AC": "Advance notice (ACAN)"}
COMMODITY = {"G": "Goods", "S": "Services", "C": "Construction"}
ENTITY = {"DC": "Department", "OGDC": "Other department", "PWC": "PSPC", "SSCC": "SSC",
          "DSOSA": "Call-up", "PWSOSA": "Call-up", "SSCSOSA": "Call-up"}


def _quarter_end(rp):
    """'2019-2020-Q1' -> 2019-06-30 (fiscal year starts April 1)."""
    y = pd.to_numeric(rp.str[:4], errors="coerce")
    q = pd.to_numeric(rp.str[-1], errors="coerce")
    month_end = 3 + 3 * q                     # Q1 -> June, Q4 -> March of the next year
    year = y + (month_end > 12)
    month = ((month_end - 1) % 12) + 1
    return pd.to_datetime(pd.DataFrame({"year": year, "month": month, "day": 1}), errors="coerce") + pd.offsets.MonthEnd(0)


def _date(s):
    return pd.to_datetime(s, errors="coerce", format="%Y-%m-%d")


def read(rebuild=False):
    if CACHE_FILE.exists() and not rebuild:
        return pd.read_pickle(CACHE_FILE)
    d = pd.read_csv(C.CONTRACTS_CSV, usecols=COLS, dtype=str, encoding="utf-8-sig", low_memory=False)
    d = d[d.instrument_type.isin(["C", "A"])].copy()
    for c in ["contract_value", "original_value", "amendment_value"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["key"] = d.owner_org + "|" + d.procurement_id.fillna("").str.upper().str.replace(r"[^0-9A-Z]", "", regex=True).str.lstrip("0")
    for c in ["contract_date", "contract_period_start", "delivery_date"]:
        d[c] = _date(d[c])
    d["reported"] = _quarter_end(d.reporting_period.fillna(""))
    C.CACHE.mkdir(parents=True, exist_ok=True)
    d.to_pickle(CACHE_FILE)
    return d


def contracts(d):
    """One row per published award, with growth and schedule extension within the follow-up window."""
    c = d[(d.instrument_type == "C") & (d.key.str.split("|").str[1] != "")].copy()
    c = c.sort_values(["key", "reported", "reference_number"]).drop_duplicates("key")
    c["v0"] = c.contract_value.where(c.contract_value > 0, c.original_value)
    c = c[(c.v0 >= C.MIN_VALUE) & c.contract_date.notna()]

    a = d[(d.instrument_type == "A") & d.key.isin(c.key)].merge(c[["key", "contract_date"]].rename(
        columns={"contract_date": "award"}), on="key")
    limit = a.award + pd.DateOffset(years=C.FOLLOW_UP_YEARS) + pd.Timedelta(days=C.REPORTING_GRACE_DAYS)
    a = a[a.reported.isna() | (a.reported <= limit)].sort_values(["key", "reported", "reference_number"])
    opt = a.comments_en.fillna("").str.contains(r"\boption", case=False)
    g = a.assign(option=opt).groupby("key").agg(
        amendments=("amendment_value", "size"), sum_amend=("amendment_value", "sum"),
        last_cv=("contract_value", "last"), last_delivery=("delivery_date", "max"),
        option_mentioned=("option", "any"), first_amended=("reported", "min"))
    c = c.join(g, on="key")
    c["amendments"] = c.amendments.fillna(0).astype(int)
    c["final_value"] = np.where(c.amendments == 0, c.v0,
                                c.last_cv.where(c.last_cv > 0, c.v0 + c.sum_amend.fillna(0)))
    c["growth"] = c.final_value / c.v0 - 1
    c["slip_days"] = (c.last_delivery - c.delivery_date).dt.days.clip(lower=0).where(c.amendments > 0, 0).fillna(0)
    c["duration_days"] = (c.delivery_date - c.contract_period_start.fillna(c.contract_date)).dt.days
    c["plausible"] = (c.growth > -1) & (c.growth <= C.MAX_PLAUSIBLE_GROWTH)
    c["procedure"] = c.solicitation_procedure.map(PROCEDURE).fillna("Not reported")
    c["commodity"] = c.commodity_type.map(COMMODITY).fillna("Not reported")
    c["entity"] = c.contracting_entity.map(ENTITY).fillna("Not reported")
    c["bids"] = pd.to_numeric(c.number_of_bids, errors="coerce")
    c["fiscal_year"] = (c.contract_date.dt.year - (c.contract_date.dt.month < 4)).astype(int)
    c["year_end_rush"] = c.contract_date.dt.month == 3
    c["option_mentioned"] = c.option_mentioned.fillna(False).astype(bool)
    return c[["key", "owner_org", "owner_org_title", "vendor_name", "procurement_id", "contract_date", "fiscal_year",
              "contract_period_start", "delivery_date", "duration_days", "v0", "final_value", "growth", "amendments",
              "slip_days", "option_mentioned", "plausible", "procedure", "commodity", "entity", "bids",
              "year_end_rush", "economic_object_code", "description_en", "commodity_code"]].reset_index(drop=True)


def unlinked_amendments(d, c):
    """Amendments that cannot be tied to a published award (most were first awarded under $10,000)."""
    a = d[d.instrument_type == "A"]
    return int((~a.key.isin(c.key)).sum()), int(len(a))
