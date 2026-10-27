"""Every assumption and input path in one place."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
CACHE = ROOT / "data" / "cache"
OUT = ROOT / "outputs"
CONTRACTS_CSV = RAW / "contracts.csv"          # open.canada.ca, Proactive Publication - Contracts over $10,000

# --- Study population ------------------------------------------------------------------------------
# Instrument types start in 2017; earlier rows cannot tell an amendment from an award.
COHORT_START = "2017-04-01"      # first award date (fiscal 2017-18)
COHORT_END = "2023-03-31"        # last award date (fiscal 2022-23): every contract has 3+ years of follow-up
FOLLOW_UP_YEARS = 3              # amendments reported within this many years of award count
REPORTING_GRACE_DAYS = 92        # amendments are published by quarter; allow one quarter of lag
MIN_VALUE = 10_000               # publication threshold

# Contracts whose final value is more than this multiple of the award are treated as data errors
# (unit slips such as cents for dollars) and left out of dollar totals and the model.
MAX_PLAUSIBLE_GROWTH = 20

# --- Outcomes --------------------------------------------------------------------------------------
MATERIAL_GROWTH = 0.25           # "material cost growth": final value at least 25% above the award
SCHEDULE_SLIP_DAYS = 90          # "material schedule extension"

# --- Risk model ------------------------------------------------------------------------------------
TRAIN_END = "2021-03-31"         # train on awards to fiscal 2020-21; test out-of-time on 2021-22 and 2022-23
SCORE_FROM = "2024-04-01"        # watch list: awards from fiscal 2024-25, too recent to have an outcome
WATCH_LIST_SIZE = 50
WATCH_MIN_VALUE = 1_000_000      # watch list covers awards of $1M or more
MIN_ORG_CONTRACTS = 300          # smaller departments are grouped as "Other"
VALUE_BANDS = [10_000, 25_000, 100_000, 1_000_000, 10_000_000, float("inf")]
DURATION_BANDS_DAYS = [0, 90, 365, 3 * 365, float("inf")]
