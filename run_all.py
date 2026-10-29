"""Build the federal contract cost-growth analysis end to end: contracts file -> one row per contract ->
breakdowns -> risk model -> project controls -> app and report dashboards.

    python run_all.py              # reuse the parsed contracts cache when present
    python run_all.py --rebuild    # re-read contracts.csv
    python run_all.py --report     # only redraw the six report dashboards from outputs/app_data.json
"""
import argparse
import json

from fco import analysis as A
from fco import app, data, model, pm, report
from fco import config as C


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.report:
        return print("->", report.from_cache()[0].parent)
    d = data.read(rebuild=a.rebuild)
    c = data.contracts(d)
    unlinked = data.unlinked_amendments(d, c)
    p, excluded = A.cohort(c)
    head = A.headline(p, excluded)
    br = A.breakdowns(p)
    big = A.biggest(p)
    metrics, factors, mdl, watch, scored = model.run(c)
    controls, ref_classes, portfolio, register = pm.run(p, scored, metrics)

    C.OUT.mkdir(parents=True, exist_ok=True)
    p.to_csv(C.OUT / "contracts_cohort.csv.gz", index=False)
    for k, v in br.items():
        v.to_csv(C.OUT / f"by_{k}.csv", index=False)
    big.to_csv(C.OUT / "largest_growth.csv", index=False)
    watch.to_csv(C.OUT / "watch_list.csv", index=False)
    ref_classes.to_csv(C.OUT / "reference_classes.csv", index=False)
    portfolio.to_csv(C.OUT / "portfolio_risk_scored.csv", index=False)
    register.to_csv(C.OUT / "risk_register.csv", index=False)
    (C.OUT / "project_controls.json").write_text(json.dumps(controls, indent=2, default=float))
    (C.OUT / "model_metrics.json").write_text(json.dumps(metrics, indent=2))
    summary = head | {"model_auc": metrics["logistic"]["auc"], "benchmark_auc": metrics["boosting"]["auc"],
                      "unlinked_amendments": unlinked}
    (C.OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    print(json.dumps({k: v for k, v in summary.items() if k != "concentration"}, indent=2, default=float))
    pf, sim = controls["performance"]["portfolio"], controls["simulation"]
    print(f"Portfolio CPI at close {pf['cpi']:.3f}, SPI(t) {pf['spi_t']:.3f}; recent $1M+ awards: "
          f"P80 contingency {sim['contingency_pct']:.1%} of ${sim['bac'] / 1e9:.2f}B")
    payload = app.payload(head, br, big, metrics, factors, mdl, watch, unlinked)
    app.build(payload)
    payload["controls"] = json.loads(json.dumps(controls, default=float))
    (C.OUT / "app_data.json").write_text(json.dumps(payload, ensure_ascii=False, default=float), encoding="utf-8")
    report.build(payload)


if __name__ == "__main__":
    main()
