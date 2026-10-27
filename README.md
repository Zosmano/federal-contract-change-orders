# Change Orders: Federal Contract Cost Growth

**Signed at one price. Finished at another.** How often do Government of Canada contracts grow after they are signed, by how much, and which new contracts are most likely to? This project follows every federal contract over $10,000 awarded from April 2017 to March 2023 through three years of amendments. It finds where cost growth and schedule extensions concentrate, and builds an explainable award-day risk score for change control.

Independent analysis of public data. Not produced by or affiliated with the Government of Canada.

## Findings

| | |
|---|---|
| Contracts followed (awarded Apr 2017 – Mar 2023, $10K+) | 351,872 |
| Amended within 3 years | 13% (1.7 amendments each) |
| Grew 25% or more | 7.7% (4.2% at least doubled) |
| End date pushed back 90+ days | 6.2% (median extension one year) |
| Value at signing → after amendments | $83.7B → $98.7B (+$15.0B, +18%) |

- **Growth is concentrated.** The top 1% of contracts account for 81% of all dollars added after award, and the top 0.1% (about 350 contracts) for 51%. Most contracts finish at or near their signed value, so change control should focus on the few large, long contracts.
- **Length and size matter most.** Holding other factors constant, contracts planned for 1–3 years have 4.5 times the odds of 25%+ growth of those under 3 months. Awards of $10M or more have 3.1 times the odds of $10K–25K awards.
- **How and what was bought matters too.**
  - **Sole-source and central awards:** sole-source awards under an Advance Contract Award Notice (ACAN) have 2.1 times the odds of traditional competitive ones, and contracts awarded by PSPC on a department's behalf have 2.3 times the odds of standing-offer call-ups.
  - **Goods vs services:** services contracts grow 25%+ six times as often as goods contracts (12.0% vs 2.1%).
- **The fiscal year-end rush is a myth for cost growth.** Contracts awarded in March grow no more often than the rest (odds ratio 0.99).
- **Dollars added by department:** Shared Services Canada ($2.5B, +24%), National Defence ($2.3B, +8%) and PSPC ($1.9B, +27%) added the most. Employment and Social Development Canada has the highest share of contracts growing 25%+, at 23%.

**Risk model.** It's trained on 2017–2021 awards and tested on 2021–2023 awards it never saw. It scores an AUC of 0.81, against 0.82 for a gradient-boosting benchmark. Reviewing the riskiest 10% of new contracts catches 39% of those that go on to grow 25% or more, 3.9 times better than chance.

**Live app:** [Open Change Orders](https://claude.ai/artifact/4z9ZPCezsJwN5r1m1py6Wy)

## The app

`outputs/change_orders.html` is self-contained and works offline. It has seven tabs:
- **Overview:** headline numbers, how concentrated growth is, and the trend by award year.
- **What drives growth:** raw rates and model-adjusted odds by procurement method, commodity, value, length, awarding body, bids and award month.
- **Departments:** a sortable table of every department with 300+ contracts.
- **Risk check:** describe a contract on its award day and get the chance of 25%+ growth, with the factors that push it up or down. It computes live in the browser.
- **Watch list:** the 50 highest-risk awards of $1M+ since April 2024, too recent to have an outcome. Suppliers are not named, because the score describes the kind of contract, not the supplier.
- **Largest increases:** the 40 contracts with the most dollars added.
- **Method:** how the numbers are built, and their limits.

## Run it

```bash
python -m pip install -r requirements.txt
```

Download the input file (642 MB, not in this repository): [Proactive Publication – Contracts over $10,000](https://open.canada.ca/data/en/dataset/d8f85d91-7dec-4fd1-8055-483b77225d8b), saved as `data/raw/contracts.csv`. Then:

```bash
python run_all.py
```

The first run takes a few minutes to parse the file, which is cached in `data/cache/`. Use `--rebuild` to re-read it.

## Method

1. **One row per contract.** Award rows (instrument type C) are joined to their amendments (type A) by department and normalised procurement number.
   - **Signed value:** the award's total contract value.
   - **Final value:** the total contract value on the latest amendment reported within 3 years of award, plus one quarter for reporting lag.
   - **Schedule extension:** how far the latest amended end date moved past the original one.
2. **Population.** Awards from April 2017 to March 2023, so every contract has a full three years of follow-up. Earlier records don't distinguish amendments from awards.
3. **Data errors.** The 1,062 contracts (0.3%) whose final value is zero or more than 20 times the award are excluded as likely errors, such as cents entered as dollars or cancellations.
4. **Risk model.** An L2-regularised logistic regression on banded factors known at award:
   - department and spending category (economic object)
   - procurement method, commodity, and who awarded it
   - value, planned length, number of bids, and award month

   Each factor reads as an odds ratio. Validation is out-of-time: train on awards to March 2021, test on April 2021 to March 2023. The calculator and watch list use the model refitted on all years.

All assumptions are in `fco/config.py`.

## Code

| File | What it does |
|---|---|
| `fco/config.py` | Study window, thresholds and model settings |
| `fco/data.py` | Reads the contracts file and builds one row per contract with its growth and extension |
| `fco/analysis.py` | Headline numbers, concentration, and breakdowns by factor and department |
| `fco/model.py` | Risk model, out-of-time validation, odds ratios, and the watch list |
| `fco/app.py`, `fco/app_template.html` | The self-contained app |
| `run_all.py` | Runs everything and writes `outputs/` |

## Limits

- **Change is not the same as an overrun.** Amendments include planned options and phases (6% of amended contracts mention an option), added scope and corrections. This measures change after signing, which change control governs, not mismanagement.
- **Rates are a floor.** 66,000 of 205,000 amendments (32%) don't match a published award, mostly because the contract started under $10,000.
- **Data quality varies by department.** Procurement numbers, end dates and bid counts are sometimes missing; most contracts don't report bids.
- **Some growth isn't visible.** Standing offers and supply arrangements appear as individual call-ups, so growth in the underlying arrangement isn't measured.
- **Associations are not causes.** Long, large and sole-source contracts grow more often, partly because they are the kind of work that changes.

## Data licence

Contains information licensed under the [Open Government Licence – Canada](https://open.canada.ca/en/open-government-licence-canada).
