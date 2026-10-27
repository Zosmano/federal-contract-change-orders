"""Build the federal contract cost-growth analysis end to end: contracts file -> one row per contract ->
breakdowns -> risk model -> app.

    python run_all.py              # reuse the parsed contracts cache when present
    python run_all.py --rebuild    # re-read contracts.csv
"""
import argparse
import json

from fco import analysis as A
from fco import app, data, model
from fco import config as C


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args()
    d = data.read(rebuild=a.rebuild)
    c = data.contracts(d)
    unlinked = data.unlinked_amendments(d, c)
    p, excluded = A.cohort(c)
    head = A.headline(p, excluded)
    br = A.breakdowns(p)
    big = A.biggest(p)
    metrics, factors, mdl, watch = model.run(c)

    C.OUT.mkdir(parents=True, exist_ok=True)
    p.to_csv(C.OUT / "contracts_cohort.csv.gz", index=False)
    for k, v in br.items():
        v.to_csv(C.OUT / f"by_{k}.csv", index=False)
    big.to_csv(C.OUT / "largest_growth.csv", index=False)
    watch.to_csv(C.OUT / "watch_list.csv", index=False)
    (C.OUT / "model_metrics.json").write_text(json.dumps(metrics, indent=2))
    summary = head | {"model_auc": metrics["logistic"]["auc"], "benchmark_auc": metrics["boosting"]["auc"],
                      "unlinked_amendments": unlinked}
    (C.OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    print(json.dumps({k: v for k, v in summary.items() if k != "concentration"}, indent=2, default=float))
    app.build(app.payload(head, br, big, metrics, factors, mdl, watch, unlinked))


if __name__ == "__main__":
    main()
