"""Acceptance checks for step 1 (plan/plan.md): condensed statements, adjustments, historical ratios.

Every check prints PASS/FAIL with actual vs expected; exit code 1 if any check fails.
Anchor values below are the acceptance values written in plan/plan.md (step 1), not computed here.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import Checks, ROOT  # noqa: E402

c = Checks()
TOL = 0.0005   # "exact to 0.001 m": values are stored as EUR thousand / 1000
TIE = 0.002    # tie-out tolerance from the plan


def v(fy, st, item):
    return c.scalar(f"SELECT value_eur_m FROM hist_statements WHERE fy={fy} AND statement='{st}' AND line_item='{item}'")


def absnear(name, actual, expected, tol):
    c.between(name, actual, expected - tol, expected + tol)


# ---------------- Coverage
for st, fys in [("IS", list(range(2021, 2026))), ("CF", list(range(2021, 2026))), ("BS", list(range(2020, 2026)))]:
    got = [r[0] for r in c.con.execute(
        f"SELECT DISTINCT fy FROM hist_statements WHERE statement='{st}' ORDER BY fy").fetchall()]
    c.equal(f"coverage {st} fiscal years", got, fys)
c.zero("statement only in IS/BS/CF", "SELECT COUNT(*) FROM hist_statements WHERE statement NOT IN ('IS','BS','CF')")
c.zero("(fy, statement, line_item) unique",
       "SELECT COUNT(*) FROM (SELECT fy, statement, line_item FROM hist_statements GROUP BY ALL HAVING COUNT(*) > 1)")
c.zero("no null values / keys / sources in hist_statements",
       "SELECT COUNT(*) FROM hist_statements WHERE value_eur_m IS NULL OR fy IS NULL OR line_item IS NULL "
       "OR doc_id IS NULL OR doc_id = '' OR pdf_page IS NULL")
c.zero("every (statement, line_item) present in every year of its statement",
       "SELECT COUNT(*) FROM (SELECT statement, line_item, COUNT(*) n FROM hist_statements GROUP BY ALL) "
       "WHERE n <> CASE WHEN statement='BS' THEN 6 ELSE 5 END")

# ---------------- Anchors (EUR m, FY2021..FY2025)
anchors = {
    ("IS", "total consolidated revenues"): [3221.587, 3158.433, 3075.904, 3497.555, 3801.458],
    ("IS", "ebit"): [386.930, 263.538, 329.628, 430.801, 458.145],
    ("IS", "ebit of which non-recurring"): [-30.762, 8.250, -5.502, -0.390, -1.637],
    ("BS", "total assets"): [3930.901, 3553.706, 3812.428, 4336.126, 4160.508],
    ("CF", "closing cash and cash equivalents"): [1026.081, 770.247, 1250.198, 1019.711, 998.448],
}
for (st, item), vals in anchors.items():
    for fy, val in zip(range(2021, 2026), vals):
        absnear(f"anchor {st} {item} FY{fy}", v(fy, st, item), val, TOL)

# ---------------- Tie-outs
for fy in range(2020, 2026):
    absnear(f"BS balances YE{fy}", v(fy, "BS", "total assets"), v(fy, "BS", "total net equity and liabilities"), TIE)
for fy in range(2021, 2026):
    lhs = (v(fy, "CF", "opening cash and cash equivalents") + v(fy, "CF", "cash flow for the period")
           + v(fy, "CF", "translation difference on cash"))
    absnear(f"CF opening + flow + translation = closing FY{fy}", lhs, v(fy, "CF", "closing cash and cash equivalents"), TIE)
    absnear(f"CF closing cash = BS cash FY{fy}", v(fy, "CF", "closing cash and cash equivalents"),
            v(fy, "BS", "cash and cash equivalents"), TIE)
    prev_close = (v(fy - 1, "CF", "closing cash and cash equivalents") if fy > 2021
                  else v(2020, "BS", "cash and cash equivalents"))
    absnear(f"opening cash FY{fy} = closing cash FY{fy - 1}", v(fy, "CF", "opening cash and cash equivalents"),
            prev_close, TIE)
    absnear(f"EBIT + net financial = PBT FY{fy}",
            v(fy, "IS", "ebit") + v(fy, "IS", "net financial income (expenses)"), v(fy, "IS", "profit before taxes"), TIE)
    absnear(f"PBT + taxes = profit FY{fy}", v(fy, "IS", "profit before taxes") + v(fy, "IS", "taxes"),
            v(fy, "IS", "consolidated profit"), TIE)

# ---------------- Adjustments
for fy in range(2021, 2026):
    s = c.scalar(f"SELECT SUM(amount_eur_m) FROM hist_adjustments WHERE fy={fy}")
    absnear(f"adjustments sum = -(IS non-recurring) FY{fy}", s, -v(fy, "IS", "ebit of which non-recurring"), 0.01)
    c.equal(f"exactly one residual row FY{fy}",
            c.scalar(f"SELECT COUNT(*) FROM hist_adjustments WHERE fy={fy} AND item='other non-recurring (not itemised)'"), 1)
n_items = c.scalar("SELECT COUNT(DISTINCT item) FROM hist_adjustments WHERE item <> 'other non-recurring (not itemised)'")
c.between("itemised (non-residual) item names in total", n_items, 3, 5)
c.zero("every adjustment has doc_id and pdf_page",
       "SELECT COUNT(*) FROM hist_adjustments WHERE doc_id IS NULL OR doc_id='' OR pdf_page IS NULL OR amount_eur_m IS NULL")

# ---------------- Ratios
c.equal("hist_ratios one row per fy 2021-2025",
        [r[0] for r in c.con.execute("SELECT fy FROM hist_ratios ORDER BY fy").fetchall()], list(range(2021, 2026)))
c.zero("adj_ebit = ebit_reported - nonrec", "SELECT COUNT(*) FROM hist_ratios WHERE abs(adj_ebit - (ebit_reported - nonrec)) > 1e-9")
absnear("adj_ebit FY2021", c.scalar("SELECT adj_ebit FROM hist_ratios WHERE fy=2021"), 417.692, TOL)
absnear("adj_ebit FY2025", c.scalar("SELECT adj_ebit FROM hist_ratios WHERE fy=2025"), 459.782, TOL)
absnear("FY2020 revenue used for FY2021 growth",
        c.scalar("SELECT value_eur_m FROM hist_other_inputs WHERE fy=2020 AND item='total consolidated revenues'"),
        2351.257, TOL)
absnear("FY2021 growth 37.0% +/- 0.1 pp", c.scalar("SELECT growth FROM hist_ratios WHERE fy=2021"), 0.370, 0.001)
c.zero("FY2021 growth = revenue / FY2020 revenue - 1",
       "SELECT COUNT(*) FROM hist_ratios r, hist_other_inputs o WHERE r.fy=2021 AND o.fy=2020 "
       "AND o.item='total consolidated revenues' AND abs(r.growth - (r.revenue / o.value_eur_m - 1)) > 1e-12")
c.zero("nwc = trade receivables + inventories - trade payables",
       "SELECT COUNT(*) FROM hist_ratios WHERE abs(nwc - (trade_receivables + inventories - trade_payables)) > 1e-9")
c.zero("ratio NWC items equal hist_statements BS lines",
       "SELECT COUNT(*) FROM hist_ratios r WHERE abs(r.trade_receivables - (SELECT value_eur_m FROM hist_statements "
       "WHERE fy=r.fy AND statement='BS' AND line_item='trade receivables')) > 1e-12 "
       "OR abs(r.inventories - (SELECT value_eur_m FROM hist_statements WHERE fy=r.fy AND statement='BS' AND line_item='inventories')) > 1e-12 "
       "OR abs(r.trade_payables - (SELECT value_eur_m FROM hist_statements WHERE fy=r.fy AND statement='BS' AND line_item='trade payables')) > 1e-12")
c.zero("delta_nwc = nwc - prior year-end nwc (FY2021 uses YE2020)",
       "SELECT COUNT(*) FROM hist_ratios r WHERE abs(r.delta_nwc - (r.nwc - (SELECT SUM(CASE line_item "
       "WHEN 'trade receivables' THEN value_eur_m WHEN 'inventories' THEN value_eur_m "
       "WHEN 'trade payables' THEN -value_eur_m END) FROM hist_statements WHERE statement='BS' AND fy=r.fy-1))) > 1e-9")
c.zero("capex_total = intangible + ppe + rou",
       "SELECT COUNT(*) FROM hist_ratios WHERE abs(capex_total - (capex_intangible + capex_ppe + capex_rou)) > 1e-9")
c.zero("capex_rou (Decision 9) = note 15 right-of-use additions, positive",
       "SELECT COUNT(*) FROM hist_ratios r LEFT JOIN hist_other_inputs o ON o.fy=r.fy AND o.item='right-of-use additions' "
       "WHERE o.value_eur_m IS NULL OR r.capex_rou <= 0 OR abs(r.capex_rou - o.value_eur_m) > 1e-12")
c.zero("FCFF identity fcff_hist = adj_ebit*(1-t) + da - capex_total - delta_nwc",
       "SELECT COUNT(*) FROM hist_ratios WHERE abs(fcff_hist - (adj_ebit*(1-eff_tax_rate) + da - capex_total - delta_nwc)) >= 1e-9")
c.zero("no nulls in hist_ratios",
       "SELECT COUNT(*) FROM hist_ratios WHERE " + " OR ".join(
           f"{col} IS NULL" for col in ["revenue", "growth", "ebit_reported", "nonrec", "adj_ebit", "adj_ebit_margin",
                                        "da", "da_pct", "capex_intangible", "capex_ppe", "capex_rou", "capex_total",
                                        "capex_pct", "capex_excl_rou_pct", "trade_receivables", "inventories",
                                        "trade_payables", "nwc", "nwc_pct", "delta_nwc", "pbt", "taxes",
                                        "eff_tax_rate", "tax_included", "fcff_hist"]))

# ---------------- Expected ranges
for fy in range(2021, 2026):
    r = c.con.execute(f"SELECT adj_ebit_margin, da_pct, capex_excl_rou_pct, nwc_pct, eff_tax_rate, tax_included "
                      f"FROM hist_ratios WHERE fy={fy}").fetchone()
    c.between(f"adj EBIT margin 7-15% FY{fy}", r[0], 0.07, 0.15)
    c.between(f"D&A 2.5-4.5% of revenue FY{fy}", r[1], 0.025, 0.045)
    c.between(f"capex excl. ROU 1.5-5% of revenue FY{fy}", r[2], 0.015, 0.05)
    c.between(f"NWC -5% to +15% of revenue FY{fy}", r[3], -0.05, 0.15)
    c.between(f"effective tax 18-30% FY{fy}", r[4], 0.18, 0.30)
    c.equal(f"tax_included consistent with 0-40% rule FY{fy}", r[5], 0 <= r[4] <= 0.40)
absnear("FY2025 effective tax 24.1%", c.scalar("SELECT eff_tax_rate FROM hist_ratios WHERE fy=2025"), 0.241, 0.0005)

# ---------------- Data quality log
log = (ROOT / "evidence" / "data_quality_log.md")
text = log.read_text(encoding="utf-8").lower() if log.exists() else ""
for kw, why in [("restatement", "restatements on condensed lines"), ("0.684", "FY2021 minority 0.684"),
                ("0.651", "FY2021 minority 0.651"), ("la marzocco", "La Marzocco consolidation 2024"),
                ("capital brands", "Capital Brands 2021"), ("reclassif", "FY2025 cost reclassification"),
                ("u+fffd", "euro-sign encoding"), ("intraday", "intraday Yahoo bar")]:
    c.equal(f"data quality log mentions {why}", kw in text, True)

c.done()
