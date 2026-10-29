"""Nine report dashboards (KPI cards, side panel, titled chart cards) as 16:9 PNGs and one PDF.

Built from the app payload, so the pages show exactly the numbers in the app.

    python run_all.py --report     # redraw from outputs/app_data.json in seconds
"""
import json
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, Rectangle

from fco import config as C

# engraved-certificate palette, shared with the app: claret band, gold rules, parchment sheets
BG, SHEET, EDGE, INK, MUTED, CHIP = "#EFE6D2", "#FFFBF2", "#DFD1B3", "#2B1B1E", "#76646A", "#F3EAD6"
BAND, BAND2, CLARET, GOLD, ROSE, SAGE = "#4A1B2A", "#5E2436", "#7A2E44", "#B8913A", "#D9A7B4", "#6E8B74"
ICON = "Segoe MDL2 Assets"
plt.rcParams.update({"font.family": "Segoe UI", "font.size": 9, "text.color": INK, "text.parse_math": False})
I = {"doc": "", "edit": "", "up": "", "history": "", "card": "", "trend": "",
     "chart": "", "bank": "", "people": "", "warn": "", "check": "", "calc": "",
     "flag": "", "layers": "", "eye": "", "list": "", "pie": "", "chevron": ""}
PAGES = [("Overview", "chart", "All contracts"), ("What drives growth", "layers", "All contracts"),
         ("Risk factors", "calc", "Model, all years"), ("Departments", "bank", "300+ contracts"),
         ("Risk model", "check", "Out-of-time test"), ("Largest & watch list", "eye", "$1M+ awards"),
         ("Cost & schedule control", "trend", "EVM at close"), ("Estimating", "list", "$1M+ reference classes"),
         ("Risk & contingency", "warn", "$1M+ since Apr 2024")]
FILES = ["P1_overview", "P2_what_drives_growth", "P3_risk_factors", "P4_departments", "P5_risk_model", "P6_largest_and_watch_list",
         "P7_cost_and_schedule_control", "P8_estimating", "P9_risk_and_contingency"]
R1 = [(0.135, 0.455, 0.274, 0.335), (0.4205, 0.455, 0.274, 0.335), (0.706, 0.455, 0.284, 0.335)]
R2 = [(0.135, 0.045, 0.415, 0.335), (0.561, 0.045, 0.429, 0.335)]
R3 = [(x, 0.045, w, h) for x, _, w, h in R1]
NOTE = "Independent analysis of public data. Not produced by or affiliated with the Government of Canada."


# ---------------------------------------------------------------------------------------- page furniture
def rbox(fig, x, y, w, h, fc=SHEET, ec=EDGE, r=0.012, shadow=True):
    ax = fig.add_axes([x, y, w, h], zorder=-2)
    ax.axis("off")
    asp = (w * fig.get_figwidth()) / (h * fig.get_figheight())
    if shadow:
        ax.add_patch(FancyBboxPatch((0.004, -0.012), 1, 1, boxstyle=f"round,pad=0,rounding_size={r*3}", mutation_aspect=asp,
                                    transform=ax.transAxes, fc="#D8C9A8", ec="none", alpha=0.5, clip_on=False))
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle=f"round,pad=0,rounding_size={r*3}", mutation_aspect=asp,
                                transform=ax.transAxes, fc=fc, ec=ec, lw=0.9, clip_on=False))
    return ax


def frame(page_no, kpis, source):
    fig = plt.figure(figsize=(16, 9), facecolor=BG)
    title, _, scope = PAGES[page_no - 1]
    rbox(fig, 0.008, 0.02, 0.118, 0.96, fc=BAND, ec=BAND, shadow=False)
    ax = fig.add_axes([0.008, 0.02, 0.118, 0.96], zorder=-1)
    ax.axis("off")
    for inset, lw in ((0.035, 1.2), (0.05, 0.5)):          # double gold rule, like an engraved border
        ax.add_patch(Rectangle((inset, inset * 0.55), 1 - 2 * inset, 1 - 1.1 * inset, fill=False, ec=GOLD, lw=lw))
    fig.text(0.067, 0.900, I["doc"], family=ICON, fontsize=28, color=GOLD, ha="center")
    fig.text(0.067, 0.866, "Change Orders", fontsize=12.5, family="Georgia", color="#FBF4E6", ha="center")
    fig.text(0.067, 0.847, "Federal contract cost growth", fontsize=7.6, color="#E2CDBF", ha="center")
    fig.text(0.067, 0.812, f"Page {page_no} of {len(PAGES)}", fontsize=7.5, color="#E2CDBF", ha="center")
    fig.text(0.067, 0.792, title, fontsize=10, family="Georgia", weight="bold", color=GOLD, ha="center")
    boxes = [("Contracts", "$10K+, Government of Canada"), ("Awarded", "Apr 2017 – Mar 2023"),
             ("Follow-up", "3 years of amendments"), ("Scope", scope)]
    for i, (lab, val) in enumerate(boxes):
        y = 0.70 - i * 0.085
        rbox(fig, 0.018, y, 0.098, 0.072, fc=BAND2, ec="#7A4A55", shadow=False)
        fig.text(0.025, y + 0.050, lab, fontsize=8, weight="semibold", color="#FBF4E6")
        fig.text(0.025, y + 0.018, val, fontsize=7.0, color="#E2CDBF")
        fig.text(0.108, y + 0.050, I["chevron"], family=ICON, fontsize=7, color="#B79A8F", ha="center")
    for i, (_, ic, _) in enumerate(PAGES):
        cx, cy = (0.041, 0.093)[i % 2], 0.392 - (i // 2) * 0.062
        on = i == page_no - 1
        rbox(fig, cx - 0.020, cy - 0.026, 0.040, 0.052, fc=GOLD if on else BAND2, ec=GOLD if on else "#7A4A55", r=0.03, shadow=False)
        fig.text(cx, cy + 0.004, I[ic], family=ICON, fontsize=12.5, color=BAND if on else "#D9C2B8", ha="center", va="center")
        fig.text(cx, cy - 0.019, str(i + 1), fontsize=6, color=BAND if on else "#B79A8F", ha="center")
    fig.text(0.067, 0.088, "Analysis and design by", fontsize=6.6, color="#E2CDBF", ha="center")
    fig.text(0.067, 0.068, "Osman Zakaria, PMP", fontsize=8.8, family="Georgia", weight="bold", color=GOLD, ha="center")
    fig.text(0.067, 0.050, "© 2026", fontsize=6.6, color="#E2CDBF", ha="center")
    x0, w, gap = 0.135, 0.1345, 0.0076
    for i, (ic, val, lab) in enumerate(kpis):
        x = x0 + i * (w + gap)
        rbox(fig, x, 0.875, w, 0.105, r=0.03)
        fig.text(x + 0.020, 0.938, I[ic], family=ICON, fontsize=18, color=CLARET, ha="center", va="center")
        fig.text(x + 0.039, 0.937, val, fontsize=18, family="Georgia", weight="bold", color=BAND, va="center")
        fig.text(x + w / 2, 0.893, lab, fontsize=7.4, weight="semibold", color=MUTED, ha="center", va="center")
    fig.text(0.135, 0.008, f"{source} {NOTE}", fontsize=6.7, color=MUTED)
    return fig


def chart(fig, x, y, w, h, title, pl=0.0, pb=0.0):
    rbox(fig, x, y + h + 0.010, w, 0.040, r=0.006)
    fig.text(x + w / 2, y + h + 0.030, title, fontsize=8.8, weight="bold", color=BAND, ha="center", va="center")
    rbox(fig, x, y, w, h, r=0.008)
    ax = fig.add_axes([x + 0.012 + pl, y + 0.045 + pb, w - 0.024 - pl, h - 0.075 - pb], zorder=2)
    ax.patch.set_alpha(0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0, labelsize=7.6, colors=INK)
    ax.set_yticks([])
    return ax


# ---------------------------------------------------------------------------------------- chart kinds
def chip(ax, x, y, text, dy=0, fs=7.2, ha="center", horizontal=False):
    off = (6, 0) if horizontal else (0, 6 + dy)
    ax.annotate(text, (x, y), xytext=off, textcoords="offset points", ha="left" if horizontal else ha,
                va="center" if horizontal else "bottom", fontsize=fs,
                bbox=dict(boxstyle="round,pad=0.28,rounding_size=0.5", fc=CHIP, ec="none"))


def short(labels, n=12):
    return ["\n".join(textwrap.wrap(str(l), n, break_long_words=False)) for l in labels]


def legend(ax, names, colors):
    h = [plt.Line2D([], [], marker="o", ls="", ms=6, color=c, label=n) for n, c in zip(names, colors)]
    ax.legend(handles=h, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=len(names), frameon=False,
              fontsize=7.4, handletextpad=0.3, columnspacing=1.0, borderaxespad=0.2)


def vbar(ax, labels, vals, fmt="{:,.0f}", colors=CLARET, wrap=11, fs=7.4):
    xs = range(len(vals))
    ax.bar(xs, vals, color=colors, width=0.62)
    for x, v in zip(xs, vals):
        chip(ax, x, v, fmt.format(v))
    ax.set_ylim(0, max(vals) * 1.25)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(short(labels, wrap), fontsize=fs)


def hbar(ax, labels, vals, fmt="{:,.0f}", colors=CLARET, ref=None, xmax=None):
    """Horizontal bars, largest at the top; ref draws a dashed reference line (odds ratio 1)."""
    ys = list(range(len(vals)))[::-1]
    ax.barh(ys, vals, color=colors, height=0.62)
    for y, v in zip(ys, vals):
        chip(ax, v, y, fmt.format(v), horizontal=True, fs=6.9)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=7.4)
    ax.set_xticks([])
    ax.set_xlim(0, (xmax or max(vals)) * 1.22)
    if ref is not None:
        ax.axvline(ref, color=MUTED, lw=0.9, ls=(0, (3, 3)))


def grouped(ax, cats, series, fmt="{:,.0f}", wrap=11):
    k = len(series)
    w = 0.8 / k
    allv = []
    for j, (_, vals, color) in enumerate(series):
        xs = [i - 0.4 + w * (j + 0.5) for i in range(len(cats))]
        ax.bar(xs, vals, width=w * 0.9, color=color)
        for x, v in zip(xs, vals):
            chip(ax, x, v, fmt.format(v), fs=6.6)
        allv += vals
    ax.set_ylim(0, max(allv) * 1.3)
    ax.set_xticks(range(len(cats)))
    ax.set_xticklabels(short(cats, wrap), fontsize=7.4)
    legend(ax, [s[0] for s in series], [s[2] for s in series])


def curve(ax, series, xlabel, ylim=(0, 105)):
    for name, xs, ys, color, style in series:
        ax.plot(xs, ys, color=color, lw=2.2, ls=style, solid_capstyle="round")
    ax.set_ylim(*ylim)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.grid(axis="y", color="#EEE4CE", lw=0.8)
    ax.set_axisbelow(True)
    ax.set_xlabel(xlabel, fontsize=7.6, color=MUTED)
    ax.tick_params(labelsize=7, colors=MUTED)
    legend(ax, [s[0] for s in series], [s[3] for s in series])


def money(v):
    return f"${v / 1e9:.1f}B" if abs(v) >= 1e9 else f"${v / 1e6:,.0f}M" if abs(v) >= 1e6 else f"${v / 1e3:,.0f}K"


def en(title):
    return str(title).split(" | ")[0]


def clip(s, n):
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


# ---------------------------------------------------------------------------------------- the pages
def build(D, out_dir=None):
    out_dir = out_dir or C.OUT / "dashboards"
    H, B, M = D["head"], {k: pd.DataFrame(v) for k, v in D["breakdowns"].items()}, D["metrics"]
    dept, big, watch = pd.DataFrame(D["department"]), pd.DataFrame(D["biggest"]), pd.DataFrame(D["watch"])
    F = pd.DataFrame(D["factors"])
    mat = f"{C.MATERIAL_GROWTH:.0%}+"
    src = "Source: open.canada.ca, Proactive Publication – Contracts over $10,000; awards April 2017 – March 2023 followed for 3 years."
    figs = []

    # 1 Overview ------------------------------------------------------------------------------------
    fig = frame(1, [("doc", f"{H['contracts']:,}", "Contracts followed"), ("edit", f"{H['amended']:.0%}", "Amended within 3 years"),
                    ("up", f"{H['material_growth']:.1%}", f"Grew {mat}"), ("history", f"{H['slipped']:.1%}", f"End date pushed {C.SCHEDULE_SLIP_DAYS}+ days"),
                    ("card", money(H["net_added"]), "Added after signing"), ("trend", f"{H['net_added'] / H['awarded']:+.0%}", "Growth on signed value")], src)
    vbar(chart(fig, *R1[0], "Value at signing vs after amendments ($B)"), ["Signed", "After amendments"],
         [H["awarded"] / 1e9, H["final"] / 1e9], fmt="${:.1f}B", colors=[GOLD, CLARET], wrap=12)
    conc = [c for c in H["concentration"] if c["top_pct"] <= 10]
    vbar(chart(fig, *R1[1], "Growth is concentrated: share of dollars added by the top contracts"),
         [f"Top {c['top_pct']:g}%" for c in conc], [100 * c["share_added"] for c in conc], fmt="{:.0f}%",
         colors=[CLARET if c["top_pct"] <= 1 else ROSE for c in conc], wrap=8)
    outcomes = [("Amended", H["amended"]), ("Grew at all", H["grew"]), (f"Grew {mat}", H["material_growth"]),
                ("At least doubled", H["doubled"]), (f"Pushed {C.SCHEDULE_SLIP_DAYS}+ days", H["slipped"]), ("Shrank", H["shrank"])]
    vbar(chart(fig, *R1[2], "What happens after signing (% of contracts)"), [o[0] for o in outcomes], [100 * o[1] for o in outcomes],
         fmt="{:.1f}%", colors=[ROSE, ROSE, CLARET, CLARET, GOLD, SAGE], wrap=9)
    fy = B["fiscal_year"]
    grouped(chart(fig, *R2[0], "By award year: share growing 25%+ and pushed 90+ days (%)"), [f"{int(y)}–{int(y) % 100 + 1:02d}" for y in fy.fiscal_year],
            [(f"Grew {mat}", list((100 * fy.material_growth).round(1)), CLARET), (f"Pushed {C.SCHEDULE_SLIP_DAYS}+ days", list((100 * fy.slipped).round(1)), GOLD)],
            fmt="{:.1f}")
    vbar(chart(fig, *R2[1], "Dollars added after signing, by award year ($B)"), [f"{int(y)}–{int(y) % 100 + 1:02d}" for y in fy.fiscal_year],
         fy.net_added / 1e9, fmt="${:.1f}B", colors=[CLARET if v == fy.net_added.max() else ROSE for v in fy.net_added])
    figs.append(fig)

    # 2 What drives growth (raw rates) --------------------------------------------------------------
    pr, cm, vb, du, en_, mo = (B[k] for k in ["procedure", "commodity", "value_band", "duration_band", "entity", "award_month"])
    sv, gd = cm.set_index("commodity").loc["Services"], cm.set_index("commodity").loc["Goods"]
    vorder = ["$10K–25K", "$25K–100K", "$100K–1M", "$1M–10M", "$10M+"]
    dorder = ["Under 3 months", "3–12 months", "1–3 years", "3+ years"]
    vb = vb.set_index("value_band").loc[vorder].reset_index()
    du = du.set_index("duration_band").loc[dorder].reset_index()
    fig = frame(2, [("layers", f"{sv.material_growth:.1%}", f"Services growing {mat}"), ("layers", f"{gd.material_growth:.1%}", f"Goods growing {mat}"),
                    ("flag", f"{pr.set_index('procedure').loc['Advance notice (ACAN)', 'material_growth']:.0%}", f"ACAN sole-source growing {mat}"),
                    ("history", f"{du.set_index('duration_band').loc['1–3 years', 'material_growth']:.0%}", f"1–3 year contracts growing {mat}"),
                    ("card", f"{vb.set_index('value_band').loc['$10M+', 'material_growth']:.0%}", f"$10M+ awards growing {mat}"),
                    ("calc", f"{mo.set_index('award_month').iloc[1].material_growth:.1%}", f"March awards growing {mat} (raw)")],
                src + f" Rates are raw shares of contracts growing {mat}; page 3 adjusts for everything else.")
    p = pr[pr.procedure != "Not reported"].sort_values("material_growth", ascending=False)
    vbar(chart(fig, *R1[0], f"How it was bought: share growing {mat} (%)"), p.procedure, 100 * p.material_growth, fmt="{:.1f}%",
         colors=[CLARET if r > 0.2 else ROSE for r in p.material_growth], wrap=12)
    c = cm[cm.commodity != "Not reported"].sort_values("material_growth", ascending=False)
    vbar(chart(fig, *R1[1], f"What was bought: share growing {mat} (%)"), c.commodity, 100 * c.material_growth, fmt="{:.1f}%",
         colors=[CLARET, ROSE, GOLD], wrap=12)
    e = en_[en_.entity != "Not reported"].sort_values("material_growth", ascending=False)
    vbar(chart(fig, *R1[2], f"Who awarded it: share growing {mat} (%)"), e.entity, 100 * e.material_growth, fmt="{:.1f}%",
         colors=[CLARET if r > 0.1 else ROSE for r in e.material_growth], wrap=10)
    grouped(chart(fig, *R3[0], "By award value (% of contracts)"), vb.value_band,
            [(f"Grew {mat}", list((100 * vb.material_growth).round(1)), CLARET), ("Amended", list((100 * vb.amended).round(1)), ROSE)], fmt="{:.0f}")
    grouped(chart(fig, *R3[1], "By planned length (% of contracts)"), du.duration_band,
            [(f"Grew {mat}", list((100 * du.material_growth).round(1)), CLARET), ("Amended", list((100 * du.amended).round(1)), ROSE)], fmt="{:.0f}")
    mor = float(F[(F.feature == "award_month") & (F.level == "March (fiscal year-end)")].odds_ratio.iloc[0])
    ax = chart(fig, *R3[2], f"Fiscal year-end: share growing {mat} (%)")
    vbar(ax, ["April–February", "March (year-end)"], list(100 * mo.material_growth), fmt="{:.1f}%", colors=[ROSE, ROSE], wrap=12)
    ax.text(0.5, 0.97, f"Holding other factors constant, March odds are {mor:.2f}:\nno year-end effect.", transform=ax.transAxes,
            ha="center", va="top", fontsize=7.4, color=MUTED)
    figs.append(fig)

    # 3 Risk factors (model odds ratios) ------------------------------------------------------------
    orr = lambda feat, lvl: float(F[(F.feature == feat) & (F.level == lvl)].odds_ratio.iloc[0])
    fig = frame(3, [("history", f"{orr('duration_band', '1–3 years'):.1f}x", "Odds, 1–3 yr vs under 3 months"),
                    ("card", f"{orr('value_band', '$10M+'):.1f}x", "Odds, $10M+ vs $10K–25K"),
                    ("bank", f"{orr('entity', 'PSPC'):.1f}x", "Odds, awarded by PSPC"),
                    ("flag", f"{orr('procedure', 'Advance notice (ACAN)'):.1f}x", "Odds, ACAN sole-source"),
                    ("layers", f"{orr('commodity', 'Goods'):.2f}x", "Odds, goods vs services"),
                    ("calc", f"{orr('award_month', 'March (fiscal year-end)'):.2f}x", "Odds, March awards")],
                f"Odds ratios of growing {mat} from an L2-regularised logistic regression on factors known at award, holding the others constant. "
                "1.0 = the reference level (dashed line).")
    def odds_panel(slot, feat, title, order=None, top=None):
        g = F[(F.feature == feat) & (F.level != "Not reported")]
        g = g.set_index("level").loc[order].reset_index() if order else g.sort_values("odds_ratio", ascending=False)
        if top:
            g = g.head(top)
        ax = chart(fig, *slot, title, pl=0.075)
        hbar(ax, [clip(l, 26) for l in g.level], list(g.odds_ratio), fmt="{:.2f}",
             colors=[CLARET if v >= 1.5 else ROSE if v >= 1 else SAGE for v in g.odds_ratio], ref=1.0)
    odds_panel(R1[0], "duration_band", "Planned length (vs under 3 months)", ["3+ years", "1–3 years", "3–12 months", "Under 3 months"][::-1])
    odds_panel(R1[1], "value_band", "Award value (vs $10K–25K)", vorder[::-1])
    odds_panel(R1[2], "procedure", "How it was bought (vs traditional competitive)")
    odds_panel(R3[0], "entity", "Who awarded it (vs standing-offer call-up)")
    odds_panel(R3[1], "commodity", "What was bought (vs services)")
    cat = F[(F.feature == "category") & (F.n >= 1000)].sort_values("odds_ratio", ascending=False).head(7)
    ax = chart(fig, *R3[2], "Highest-risk spending categories (1,000+ contracts)", pl=0.10)
    hbar(ax, [clip(l, 34) for l in cat.level], list(cat.odds_ratio), fmt="{:.2f}", colors=CLARET, ref=1.0)
    ax.text(1.0, -0.06, "Labels as published; the source spells some categories several ways.", transform=ax.transAxes, ha="right", fontsize=6.6, color=MUTED)
    figs.append(fig)

    # 4 Departments ---------------------------------------------------------------------------------
    dept = dept.assign(name=dept.owner_org_title.map(en))
    top_d = dept.sort_values("net_added", ascending=False).head(10)
    top_r = dept.sort_values("material_growth", ascending=False).head(10)
    fig = frame(4, [("bank", f"{len(dept)}", "Departments with 300+ contracts"),
                    ("card", money(top_d.iloc[0].net_added), clip(f"Added by {top_d.iloc[0]['name']}", 34)),
                    ("trend", f"{top_d.iloc[0].growth_pct:+.0%}", "Its growth on signed value"),
                    ("up", f"{top_r.iloc[0].material_growth:.0%}", f"Highest department share growing {mat}"),
                    ("pie", f"{top_d.head(3).net_added.sum() / dept.net_added.sum():.0%}", "Of dollars added, top 3 departments"),
                    ("doc", f"{dept.contracts.sum():,.0f}", "Contracts in these departments")],
                src + " Departments with fewer than 300 contracts are left out.")
    ax = chart(fig, *R2[0], "Dollars added after signing: the 10 largest ($M)", pl=0.13)
    hbar(ax, [clip(n, 40) for n in top_d.name], list(top_d.net_added / 1e6), fmt="${:,.0f}M",
         colors=[CLARET if i < 3 else ROSE for i in range(len(top_d))])
    ax = chart(fig, *R2[1], f"Highest share of contracts growing {mat} (%)", pl=0.13)
    hbar(ax, [clip(n, 40) for n in top_r.name], list(100 * top_r.material_growth), fmt="{:.0f}%",
         colors=[CLARET if i < 3 else ROSE for i in range(len(top_r))])
    big3 = dept.sort_values("contracts", ascending=False).head(8)
    grouped(chart(fig, *R1[0], "The 8 busiest departments: growing 25%+ vs amended (%)"), [clip(n, 22) for n in big3.name],
            [(f"Grew {mat}", list((100 * big3.material_growth).round(1)), CLARET), ("Amended", list((100 * big3.amended).round(1)), ROSE)],
            fmt="{:.0f}", wrap=10)
    gp = dept.sort_values("growth_pct", ascending=False).head(6)
    vbar(chart(fig, *R1[1], "Highest dollar growth on signed value (%)"), [clip(n, 24) for n in gp.name], list(100 * gp.growth_pct),
         fmt="{:.0f}%", colors=CLARET, wrap=11, fs=6.8)
    vol = dept.sort_values("awarded", ascending=False).head(6)
    vbar(chart(fig, *R1[2], "Largest signed value ($B)"), [clip(n, 24) for n in vol.name], list(vol.awarded / 1e9), fmt="${:.1f}B",
         colors=GOLD, wrap=11, fs=6.8)
    figs.append(fig)

    # 5 Risk model ----------------------------------------------------------------------------------
    lg, bo = M["logistic"], M["boosting"]
    fig = frame(5, [("check", f"{lg['auc']:.2f}", "AUC, out-of-time test"), ("chart", f"{bo['auc']:.2f}", "Gradient-boosting benchmark"),
                    ("up", f"{lg['lift_top10']:.1f}x", "Lift, riskiest 10%"), ("eye", f"{lg['recall_top10']:.0%}", f"Of {mat} growth caught in top 10%"),
                    ("doc", f"{M['train']['n']:,}", "Training contracts"), ("calc", f"{M['test']['n']:,}", "Test contracts, never seen")],
                f"Trained on awards {M['train']['from'][:7]} to {M['train']['to'][:7]}, tested on {M['test']['from'][:7]} to {M['test']['to'][:7]}. "
                "The calculator and watch list use the model refitted on all years.")
    ax = chart(fig, *R2[0], f"Gains: share of {mat} growth caught by reviewing the riskiest contracts (%)", pb=0.02)
    curve(ax, [("Logistic model", [g["pct"] for g in lg["gains"]], [100 * g["caught"] for g in lg["gains"]], CLARET, "-"),
               ("Gradient boosting", [g["pct"] for g in bo["gains"]], [100 * g["caught"] for g in bo["gains"]], GOLD, "-"),
               ("Random review", [0, 100], [0, 100], ROSE, "--")], "Contracts reviewed (%)")
    ax = chart(fig, *R2[1], "Calibration: predicted vs observed rate, by tenth of risk (%)", pb=0.02)
    cal = lg["calibration"]
    curve(ax, [("Logistic model", [100 * c["pred"] for c in cal], [100 * c["obs"] for c in cal], CLARET, "-"),
               ("Perfect calibration", [0, 50], [0, 50], ROSE, "--")], "Predicted (%)", ylim=(0, 52))
    ax.set_yticks([0, 10, 20, 30, 40, 50])
    ax.plot([100 * c["pred"] for c in cal], [100 * c["obs"] for c in cal], "o", color=CLARET, ms=4)
    ax.set_ylim(0, 52)
    ax.set_xlim(0, 52)
    ax.text(0.98, 0.04, f"Riskiest tenth: predicted {100 * cal[-1]['pred']:.0f}%, observed {100 * cal[-1]['obs']:.0f}%.\nRankings hold; top scores run high.",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7.2, color=MUTED)
    ms = [("AUC", "auc"), ("PR-AUC", "pr_auc"), ("Caught in top 10%", "recall_top10")]
    grouped(chart(fig, *R1[0], "Logistic model vs gradient-boosting benchmark (%)"), [m[0] for m in ms],
            [("Logistic", [round(100 * lg[k]) for _, k in ms], CLARET), ("Gradient boosting", [round(100 * bo[k]) for _, k in ms], GOLD)])
    vbar(chart(fig, *R1[1], "Contracts in each period"), ["Train 2017–21", "Test 2021–23"], [M["train"]["n"], M["test"]["n"]],
         colors=[ROSE, CLARET], wrap=12)
    vbar(chart(fig, *R1[2], f"Base rate vs riskiest tenth: share growing {mat} (%)"),
         ["All test contracts", "Riskiest 10%"], [100 * lg["base_rate"], 100 * lg["base_rate"] * lg["lift_top10"]], fmt="{:.1f}%",
         colors=[ROSE, CLARET], wrap=12)
    figs.append(fig)

    # 6 Largest increases and watch list ------------------------------------------------------------
    big = big.assign(added=big.final_value - big.v0, name=big.owner_org_title.map(en))
    tb = big.sort_values("added", ascending=False).head(10)
    watch = watch.assign(name=watch.owner_org_title.map(en))
    fig = frame(6, [("up", money(tb.iloc[0].added), "Largest single increase"), ("trend", f"{tb.iloc[0].final_value / tb.iloc[0].v0:.1f}x", "Its final vs signed value"),
                    ("card", money(big.added.sum()), f"Added by the {len(big)} largest"), ("eye", f"{len(watch)}", "Awards on the watch list"),
                    ("warn", f"{watch.risk.max():.0%}", "Highest predicted risk"), ("doc", f"{(watch.commodity == 'Services').mean():.0%}", "Of watch list that are services")],
                f"Watch list: the {len(watch)} highest-risk awards of $1M+ since April 2024, too recent to have an outcome. "
                "Suppliers are not named: the score describes the kind of contract, not the supplier.")
    ax = chart(fig, *R2[0], "The 10 largest increases after signing ($M added)", pl=0.16)
    hbar(ax, [clip(f"{d.strip()} · {n}", 52) for d, n in zip(tb.description_en, tb.name)], list(tb.added / 1e6), fmt="${:,.0f}M",
         colors=[CLARET if i < 3 else ROSE for i in range(len(tb))])
    wc = watch.groupby(watch.description_en.str.strip()).agg(n=("risk", "size"), risk=("risk", "mean")).sort_values(["n", "risk"], ascending=False).head(8)
    ax = chart(fig, *R2[1], f"Watch list by spending category: awards (average chance of growing {mat})", pl=0.16)
    hbar(ax, [clip(c, 52) for c in wc.index], list(wc.n), colors=[CLARET if i < 2 else ROSE for i in range(len(wc))])
    for y, (n, r) in zip(range(len(wc))[::-1], zip(wc.n, wc.risk)):
        ax.annotate(f"avg {r:.0%}", (n, y), xytext=(34, 0), textcoords="offset points", va="center", fontsize=6.8, color=MUTED)
    wp = watch.procedure.value_counts()
    vbar(chart(fig, *R1[0], "Watch list by how it was bought (awards)"), wp.index, list(wp.values), colors=CLARET, wrap=12)
    wd = watch.duration_band.value_counts().reindex(dorder).dropna()
    vbar(chart(fig, *R1[1], "Watch list by planned length (awards)"), wd.index, list(wd.values), colors=GOLD, wrap=12)
    wn = watch.name.value_counts().head(5)
    vbar(chart(fig, *R1[2], "Watch list by department (top 5, awards)"), [clip(n, 26) for n in wn.index], list(wn.values),
         colors=ROSE, wrap=12, fs=6.8)
    figs.append(fig)

    # 7 Cost and schedule control (earned-value measures at close) ----------------------------------
    PC = D["controls"]
    pf, qd = PC["performance"]["portfolio"], PC["performance"]["quadrants"]
    perf = {k: pd.DataFrame(PC["performance"][k]) for k in ["commodity", "procedure", "duration_band", "value_band", "fiscal_year"]}
    fig = frame(7, [("card", money(pf["bac"]), "BAC: signed baseline"), ("up", money(pf["eac"]), "EAC: cost at completion"),
                    ("warn", money(pf["cv"]).replace("$-", "−$"), "CV = BAC − EAC"), ("calc", f"{pf['cpi']:.2f}", "CPI at close = BAC ÷ EAC"),
                    ("trend", f"{pf['vac_pct']:.0%}".replace("-", "−"), "VAC % of baseline"), ("history", f"{pf['spi_t']:.2f}", "SPI(t) = planned ÷ actual time")],
                "Earned-value measures at close: each contract is a project, signed value = BAC, value after 3 years of amendments = EAC. "
                "No progress data is published, so in-flight CPI and SPI cannot be measured; 1.00 = on baseline.")
    pr7 = perf["procedure"].sort_values("cpi")
    ax = chart(fig, *R1[0], "CPI at close by procurement method (1.00 = on baseline)", pl=0.075)
    hbar(ax, list(pr7.procedure), list(pr7.cpi), fmt="{:.2f}", colors=[CLARET if v < 0.8 else ROSE for v in pr7.cpi], ref=1.0, xmax=1.0)
    du7 = perf["duration_band"].set_index("duration_band").loc[["Under 3 months", "3–12 months", "1–3 years", "3+ years"]].reset_index()
    grouped(chart(fig, *R1[1], "CPI and SPI(t) at close by planned length"), du7.duration_band,
            [("CPI", list(du7.cpi.round(2)), CLARET), ("SPI(t)", list(du7.spi_t.round(2)), GOLD)], fmt="{:.2f}")
    cm7 = perf["commodity"].sort_values("cpi")
    grouped(chart(fig, *R1[2], "CPI and SPI(t) at close by commodity"), cm7.commodity,
            [("CPI", list(cm7.cpi.round(2)), CLARET), ("SPI(t)", list(cm7.spi_t.round(2)), GOLD)], fmt="{:.2f}")
    tot = sum(qd.values())
    vbar(chart(fig, *R2[0], f"Off track: {100 - 100 * qd['on_track'] / tot:.1f}% of contracts (cost {mat} or {C.SCHEDULE_SLIP_DAYS}+ days late), by type (%)"),
         ["Over cost only", "Late only", "Over cost and late"], [100 * qd[k] / tot for k in ("cost_only", "schedule_only", "both")],
         fmt="{:.1f}%", colors=[ROSE, GOLD, CLARET], wrap=12)
    fy7 = perf["fiscal_year"]
    grouped(chart(fig, *R2[1], "Portfolio CPI and SPI(t) at close by award year"), [f"{int(y)}–{int(y) % 100 + 1:02d}" for y in fy7.fiscal_year],
            [("CPI", list(fy7.cpi.round(2)), CLARET), ("SPI(t)", list(fy7.spi_t.round(2)), GOLD)], fmt="{:.2f}")
    figs.append(fig)

    # 8 Estimating: reference-class forecasting and PERT --------------------------------------------
    rc = pd.DataFrame(PC["reference_classes"])
    rc["cls"] = rc.commodity.str[:5].str.replace("Const", "Constr.").str.replace("Servi", "Services") + " · " + rc.duration_band.str.replace(" months", " mo").str.replace(" years", " yr")
    svc = rc[(rc.commodity == "Services") & (rc.duration_band == "1–3 years")].iloc[0]
    ex_bac = 10e6
    ex_mean, ex_sd = ex_bac * svc.pert_mean, ex_bac * svc.pert_sd
    fig = frame(8, [("list", f"{len(rc)}", "Reference classes, $1M+ contracts"), ("up", f"+{svc.p80:.0%}", "P80 uplift, services 1–3 yrs"),
                    ("check", f"+{rc.p80.min():.0%}", "Lowest P80 uplift (goods)"), ("calc", f"{svc.pert_mean:.2f}", "PERT mean, services 1–3 yrs"),
                    ("chart", f"±{svc.pert_sd:.2f}", "PERT σ, services 1–3 yrs"), ("card", money(ex_mean), "PERT estimate, $10M award")],
                "Reference-class forecasting (Flyvbjerg): uplift on the signed baseline needed for 50/80/90% confidence of no overrun, from 2017–23 contracts of $1M+. "
                "PERT: O, M, P = P10, median, P90 of final ÷ signed value; mean = (O+4M+P)/6, σ = (P−O)/6.")
    grouped(chart(fig, *R2[0], "Reference-class uplift on the baseline for P50 / P80 / P90 confidence (%)"), list(rc.cls),
            [("P50", list((100 * rc.p50).round()), ROSE), ("P80", list((100 * rc.p80).round()), CLARET), ("P90", list((100 * rc.p90).round()), GOLD)],
            fmt="{:.0f}", wrap=10)
    ax = chart(fig, *R2[1], "PERT three-point estimate by class: final ÷ signed value (mean ± σ)", pl=0.075)
    order = rc.sort_values("pert_mean")
    ys = range(len(order))
    ax.barh(list(ys), list(order.pert_mean - 1), left=1, color=ROSE, height=0.5)
    ax.errorbar(list(order.pert_mean), list(ys), xerr=list(order.pert_sd), fmt="o", color=CLARET, ms=4, capsize=3, lw=1.2)
    for y, (m, sd) in zip(ys, zip(order.pert_mean, order.pert_sd)):
        ax.annotate(f"{m:.2f} ± {sd:.2f}", (m + sd, y), xytext=(6, 0), textcoords="offset points", va="center", fontsize=6.9)
    ax.set_yticks(list(ys)); ax.set_yticklabels(list(order.cls), fontsize=7.4)
    ax.set_xlim(0.95, 1.62); ax.set_xticks([1.0, 1.1, 1.2, 1.3, 1.4, 1.5]); ax.tick_params(axis="x", labelsize=7, colors=MUTED)
    ax.axvline(1.0, color=MUTED, lw=0.9, ls=(0, (3, 3)))
    vbar(chart(fig, *R1[0], f"Chance a major contract grows {mat}, by class (%)"), list(rc.cls), list((100 * rc.p_material).round(1)), fmt="{:.0f}%",
         colors=[CLARET if v > 0.2 else ROSE for v in rc.p_material], wrap=8, fs=6.6)
    ax = chart(fig, *R1[1], "Worked example: $10M services contract, planned 1–3 years")
    ax.set_xticks([]); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    lines_ = [("Optimistic (P10)", f"{svc.pert_o:.2f} × BAC", money(ex_bac * svc.pert_o)),
              ("Most likely (median)", f"{svc.pert_m:.2f} × BAC", money(ex_bac * svc.pert_m)),
              ("Pessimistic (P90)", f"{svc.pert_p:.2f} × BAC", money(ex_bac * svc.pert_p)),
              ("PERT mean (O+4M+P)/6", f"{svc.pert_mean:.3f} × BAC", money(ex_mean)),
              ("PERT σ (P−O)/6", f"{svc.pert_sd:.3f} × BAC", money(ex_sd)),
              ("Budget at P80, PERT normal", "mean + 0.84σ", money(ex_mean + 0.8416 * ex_sd)),
              ("Budget at P80, reference class", f"BAC × {1 + svc.p80:.2f}", money(ex_bac * (1 + svc.p80)))]
    for i, (a, b, c_) in enumerate(lines_):
        y = 0.93 - i * 0.135
        ax.text(0.02, y, a, fontsize=8, weight="semibold", va="center")
        ax.text(0.58, y, b, fontsize=8, color=MUTED, va="center")
        ax.text(0.98, y, c_, fontsize=8.6, weight="bold", color=BAND, va="center", ha="right")
        if i in (2, 4):
            ax.axhline(y - 0.0675, color=EDGE, lw=0.8)
    da = rc.sort_values("dollar_uplift", ascending=False)
    vbar(chart(fig, *R1[2], "Dollar-weighted growth on baseline by class (%)"), list(da.cls), list((100 * da.dollar_uplift).round(1)), fmt="{:.0f}%",
         colors=[CLARET if v > 0.2 else ROSE for v in da.dollar_uplift], wrap=8, fs=6.6)
    figs.append(fig)

    # 9 Risk and contingency: Monte Carlo, EMV, probability-impact ----------------------------------
    sm, bt, cc = PC["simulation"], PC["simulation"]["backtest"], PC["change_control"]
    fig = frame(9, [("doc", f"{sm['awards']:,}", "Recent $1M+ awards simulated"), ("card", money(sm["bac"]), "Their combined BAC"),
                    ("trend", f"{sm['expected'] / sm['bac']:.0%}", "Expected cost growth"),
                    ("warn", f"{sm['contingency_pct']:.0%}", f"P{C.CONTINGENCY_LEVEL} contingency reserve"),
                    ("check", f"{bt['percentile_of_actual']:.0f}th", "Backtest: actual's percentile"), ("pie", money(PC["emv"]["emv_total"]), "Total EMV of cost-growth risk")],
                f"Monte Carlo ({C.SIMULATIONS:,} runs), $1M+ awards since Apr 2024: each grows {mat} with its calibrated probability; change sizes drawn from past "
                "$1M+ contracts of the same kind. EMV = probability × typical impact.")
    h = sm["histogram"]
    ax = chart(fig, *R2[0], f"Simulated portfolio cost growth, % of BAC ({C.SIMULATIONS:,} runs)", pb=0.03)
    edges = [100 * e for e in h["edges"]]
    ax.bar(edges[:-1], h["counts"], width=[b - a for a, b in zip(edges[:-1], edges[1:])], align="edge", color=ROSE, edgecolor=SHEET, lw=0.5)
    for k, col, lab in [("p50", BAND, "P50"), (f"p{C.CONTINGENCY_LEVEL}", CLARET, f"P{C.CONTINGENCY_LEVEL}"), ("p90", GOLD, "P90")]:
        x = 100 * sm[k] / sm["bac"]
        ax.axvline(x, color=col, lw=1.6)
        ax.text(x, max(h["counts"]) * 0.97, f" {lab} {x:.0f}%", color=col, fontsize=7.6, weight="bold", va="top")
    ax.set_xlim(0, 100 * sm["p95"] / sm["bac"] * 1.15)
    ax.set_xlabel("Cost growth across the portfolio (% of BAC)", fontsize=7.6, color=MUTED)
    ax.tick_params(axis="x", labelsize=7, colors=MUTED)
    vbar(chart(fig, *R1[0], "Backtest: built on 2017–21, run on 2021–23 $1M+ awards (%)"), ["Simulated P10", "Simulated P50", "Actual", "Simulated P90"],
         [100 * bt["p10"], 100 * bt["p50"], 100 * bt["actual"], 100 * bt["p90"]], fmt="{:.1f}%", colors=[ROSE, ROSE, CLARET, ROSE], wrap=10)
    grid = pd.DataFrame(PC["pi_grid"])
    pv = grid.pivot(index="prob_band", columns="impact_band", values="awards").reindex(index=range(5), columns=range(5)).fillna(0)
    ev = grid.pivot(index="prob_band", columns="impact_band", values="emv").reindex(index=range(5), columns=range(5)).fillna(0)
    ax = chart(fig, *R1[1], "Probability-impact matrix: awards (shade = EMV)", pl=0.05, pb=0.02)
    from matplotlib.colors import LinearSegmentedColormap
    shade = (ev / ev.values.max()) ** 0.5
    ax.imshow(shade.values[::-1], cmap=LinearSegmentedColormap.from_list("c", [SHEET, ROSE, CLARET]), vmin=0, vmax=1, aspect="auto")
    for i in range(5):
        for j in range(5):
            v = int(pv.values[4 - i, j])
            ax.text(j, i, f"{v:,}", ha="center", va="center", fontsize=7.4, color="white" if shade.values[4 - i, j] > 0.55 else INK)
    pl_ = [f"{int(a * 100)}–{int(b * 100)}%" if b < 1 else f"{int(a * 100)}%+" for a, b in zip(C.PROB_BANDS[:-1], C.PROB_BANDS[1:])]
    il_ = [f"<${C.IMPACT_BANDS[1] / 1e6:.0f}M"] + [f"${a / 1e6:.0f}–{b / 1e6:.0f}M" for a, b in zip(C.IMPACT_BANDS[1:-2], C.IMPACT_BANDS[2:-1])] + [f"${C.IMPACT_BANDS[-2] / 1e6:.0f}M+"]
    ax.set_yticks(range(5)); ax.set_yticklabels(pl_[::-1], fontsize=7)
    ax.set_xticks(range(5)); ax.set_xticklabels(il_, fontsize=7)
    ax.set_xlabel("Typical impact if it grows", fontsize=7.4, color=MUTED); ax.set_ylabel("Probability", fontsize=7.4, color=MUTED)
    dist = pd.DataFrame(cc["distribution"])
    vbar(chart(fig, *R1[2], f"Change control: amendments per contract (median first change {cc['median_first_change_days']:.0f} days)"),
         [f"{a} change{'s' if a != '1' else ''}" for a in dist.amendments], list(dist.contracts), colors=[SAGE] + [CLARET] * 5, wrap=8)
    reg = pd.DataFrame(PC["register"]).head(10)
    ax = chart(fig, *R2[1], "Risk register: the 10 highest-EMV awards ($M; probability in brackets)", pl=0.17)
    hbar(ax, [f"{clip(f'{d.strip()} · {n}', 46)} ({pr_:.0%})" for d, n, pr_ in zip(reg.description_en, reg.department, reg.p)],
         list(reg.emv / 1e6), fmt="${:,.0f}M", colors=[CLARET if i < 3 else ROSE for i in range(len(reg))])
    figs.append(fig)

    out_dir.mkdir(parents=True, exist_ok=True)
    with PdfPages(out_dir / "change_orders_dashboards.pdf") as pdf:
        for f, name in zip(figs, FILES):
            f.savefig(out_dir / f"{name}.png", dpi=220, facecolor=BG)
            pdf.savefig(f, facecolor=BG)
            plt.close(f)
    return [out_dir / f"{n}.png" for n in FILES]


def from_cache():
    return build(json.loads((C.OUT / "app_data.json").read_text(encoding="utf-8")))


if __name__ == "__main__":
    print(from_cache())
