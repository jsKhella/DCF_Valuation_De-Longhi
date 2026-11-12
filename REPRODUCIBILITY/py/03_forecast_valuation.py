"""Step 3: forecast FY2026E-30E FCFF and value the base case (Gordon growth, exit-multiple cross-check).

Purpose
    Derive every forecast driver from history, guidance and the approved decisions, write them with rule, source and
    note to forecast_assumptions, then run the shared DCF engine (py/dcf.py, value_per_share) once on the base
    parameters and store its outputs: forecast_fcff (one row per FY2026E-30E), valuation (ordered EV -> equity ->
    per-share walk) and multiples_check (Damodaran Furn/Home Furnishings EV/EBITDA exit cross-check).

Inputs (DuckDB, built by steps 0-2)
    hist_ratios (step 1), wacc and bridge_inputs (step 2), raw_report_lines (PR_H1_2026 guidance; AR2025 segment
    note 45 adjusted EBITDA and report-on-operations reclassified IS), raw_damodaran_vebitda_europe,
    raw_damodaran_vebitda_global.

Outputs (DuckDB tables, CREATE OR REPLACE, no timestamps)
    forecast_assumptions (driver, rule, value, value_by_year, source, note)
    forecast_fcff        (fy, revenue, growth, adj_ebit_margin, adj_ebit, tax_rate, nopat, da, capex, nwc, delta_nwc,
                          fcff, share_based_cost, adj_ebitda_mgmt, nopat_tv, fcff_tv)   fcff_tv/nopat_tv only FY2030
    valuation            (line_no, section, item, fy, value, unit, treatment, note)
    multiples_check      (region, industry, n_firms, ev_ebitda, fy2030_ebitda, tv_exit, pv_tv_exit, ev_exit,
                          equity_value_exit, value_per_share_exit, pct_vs_gordon, implied_gordon_ev_ebitda, source)

Brief definitions implemented (by term)
    "FCFF", "Tax rate" (Decision 8A), "Terminal value" (Gordon primary + EV/EBITDA exit cross-check), "Discounting"
    (year fractions to the price date, Decision 1A), "Equity bridge" (Decision 1A distributions, Decision 4A
    cash-like, minorities at book = simplification), "Net working capital" (% of revenue, FY2025), "Adjusted EBIT"
    (keeps share-based cost; management's adjusted EBITDA excludes it, hence the guidance bridge).
    Decision 7 drivers: growth 5.0% in FY2026E fading linearly towards g (/5); FY2026E margin from the adjusted
    EBITDA guidance midpoint; linear margin fade to the FY2024-25 average by FY2030E; D&A % and capex % = FY2021-25
    averages; NWC % = FY2025. Decision 9A: capex includes right-of-use additions (hist capex_pct is incl. ROU).

Decision constants (approved at Gate 1, plan/plan.md Decisions 7): see DECISION_* below. Every other number is
read from DuckDB tables.
"""
import re
import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "curiosity.duckdb"
sys.path.insert(0, str(ROOT / "py"))
import dcf  # noqa: E402

# ------------------------------------------------------------------ approved decision constants (plan Decision 7)
DECISION_GROWTH_FY2026 = 0.05     # midpoint of "mid-single digit" revenue-growth guidance
DECISION_TERMINAL_G = 0.02        # ECB inflation target; below rf
DECISION_GROWTH_FADE_YEARS = 5    # growth_t = 5.0% - (5.0% - g) x (t - 2026) / 5
DECISION_MARGIN_ANCHOR_FYS = (2024, 2025)   # like-for-like perimeter after La Marzocco
DECISION_AVG_FYS = (2021, 2022, 2023, 2024, 2025)  # D&A %, capex %, tax median window

con = duckdb.connect(str(DB))


def find_one(doc, pattern, pages=None):
    q = "SELECT page, line_no, text FROM raw_report_lines WHERE doc_id = ? AND regexp_matches(text, ?)"
    args = [doc, pattern]
    if pages:
        q += " AND page BETWEEN ? AND ?"
        args += list(pages)
    rows = con.execute(q + " ORDER BY page, line_no", args).fetchall()
    assert len(rows) == 1, f"{doc} /{pattern}/: expected exactly 1 line, got {rows}"
    return rows[0]


def line(doc, page, line_no):
    return con.execute("SELECT text FROM raw_report_lines WHERE doc_id=? AND page=? AND line_no=?",
                       [doc, page, line_no]).fetchall()[0][0]


def thousands(tok: str) -> float:
    neg = tok.startswith("(")
    v = float(tok.strip("()").replace(",", "")) / 1000
    return -v if neg else v


# ------------------------------------------------------------------ history (step 1)
H = con.execute("SELECT * FROM hist_ratios ORDER BY fy").df().set_index("fy")
assert list(H.index) == list(DECISION_AVG_FYS)
rev25 = float(H.loc[2025, "revenue"])
nwc25 = float(H.loc[2025, "nwc"])
da_pct = float(H.loc[list(DECISION_AVG_FYS), "da_pct"].mean())
capex_pct = float(H.loc[list(DECISION_AVG_FYS), "capex_pct"].mean())
nwc_pct = float(H.loc[2025, "nwc_pct"])
tax_incl = H.loc[H["tax_included"], "eff_tax_rate"]
tax_forecast = float(tax_incl.median())
margin_target = float(H.loc[list(DECISION_MARGIN_ANCHOR_FYS), "adj_ebit_margin"].mean())
tax_terminal = con.execute("SELECT tax_marginal FROM wacc WHERE \"case\"='base'").fetchall()[0][0]
wacc_base = con.execute("SELECT wacc FROM wacc WHERE \"case\"='base'").fetchall()[0][0]

# ------------------------------------------------------------------ guidance (PR_H1_2026, "Foreseeable business development and guidance")
gp, gl, _ = find_one("PR_H1_2026", r"^Foreseeable business development and guidance$")
gtext = " ".join(line("PR_H1_2026", gp, gl + k) for k in range(1, 5))
assert "mid-single digit" in gtext, gtext
m = re.search(r"€\s*([\d,.]+)\s*-\s*€\s*([\d,.]+)\s*million", gtext)
assert m, gtext
guid_lo, guid_hi = float(m.group(1).replace(",", "")), float(m.group(2).replace(",", ""))
guid_mid = (guid_lo + guid_hi) / 2
guid_src = f"PR_H1_2026 PDF p.{gp} lines {gl + 1}-{gl + 4} (guidance paragraph)"

# ------------------------------------------------------------------ FY2025 share-based cost (management adjusted EBITDA definition)
# AR2025 note 45 (segments): "EBITDA adjusted (***) ... 625,077", the line after "Total revenues (*) ... 3,801,458"
seg = [r for r in con.execute("SELECT page, line_no, text FROM raw_report_lines WHERE doc_id='AR2025' AND "
                              "regexp_matches(text, '^EBITDA adjusted \\(\\*\\*\\*\\) ')").fetchall()
       if abs(thousands(line("AR2025", r[0], r[1] - 1).split()[-1]) - rev25) < 5e-4
       and line("AR2025", r[0], r[1] - 1).startswith("Total revenues")]
assert len(seg) == 1, seg
sp, sl, stext = seg[0]
adj_ebitda25 = thousands(stext.split()[-1])
ebit25, da25, nonrec25 = float(H.loc[2025, "ebit_reported"]), float(H.loc[2025, "da"]), float(H.loc[2025, "nonrec"])
sbc25 = adj_ebitda25 - (ebit25 + da25) + nonrec25          # nonrec25 is negative (a cost) -> subtract the add-back
# cross-check with the reclassified IS bucket "Non-recurring expenses/share-based plan" (EUR m, 1 decimal)
bp, bl, btext = find_one("AR2025", r"^Non-recurring expenses/share-based plan \(", pages=(20, 30))
bucket = -float(re.search(r"^Non-recurring expenses/share-based plan \(([\d.]+)\)", btext).group(1))
assert abs(-bucket - (-nonrec25) - sbc25) < 0.05 + 1e-9, (bucket, nonrec25, sbc25)
sbc_pct = sbc25 / rev25

# FY2026E margin from the guidance midpoint: adj EBIT = guidance - D&A - share-based cost
rev26 = rev25 * (1 + DECISION_GROWTH_FY2026)
margin26 = guid_mid / rev26 - da_pct - sbc_pct


def fmt_years(years, vals):
    return "; ".join(f"{y}={v:.10g}" for y, v in zip(years, vals))


A = [
    ("revenue_fy2025", "FY2025 actual total consolidated revenues (growth base)", rev25, None,
     "hist_ratios FY2025 revenue (AR2025 PDF p.144)", "EUR m."),
    ("nwc_fy2025", "FY2025 actual NWC = trade receivables + inventories - trade payables", nwc25, None,
     "hist_ratios FY2025 nwc (AR2025 PDF p.146-147)", "EUR m. Base for the FY2026E increase in NWC."),
    ("growth_fy2026", "Midpoint of 'mid-single digit' revenue-growth guidance (Decision 7)", DECISION_GROWTH_FY2026,
     None, guid_src, "H1 2026 revenue growth was +5.8% (PR_H1_2026 p.1); 5.0% is the midpoint of 4-6%."),
    ("terminal_g", "Gordon perpetual growth after FY2030E (Decision 7)", DECISION_TERMINAL_G, None,
     "Decision 7 (ECB 2% inflation target), plan/plan.md", "Below rf 4.362% (step 2 check). Grid 1.0-3.0% in step 4."),
    ("growth_fade_years", "Denominator of the linear growth fade: growth_t = g26 - (g26 - g) x (t - 2026) / 5",
     float(DECISION_GROWTH_FADE_YEARS), None, "Decision 7, plan/plan.md",
     "With /5 the FY2030E growth is 2.6%, not yet g; the remaining step to g happens in the terminal value."),
    ("guidance_adj_ebitda_fy2026", "Midpoint of the FY2026 adjusted EBITDA guidance range", guid_mid, None,
     guid_src, f"Range EUR {guid_lo:.0f}-{guid_hi:.0f} m (raised from 640-660 m). Management 'adjusted' excludes "
     "non-recurring items and share-based incentive cost."),
    ("adj_ebitda_fy2025_mgmt", "FY2025 management adjusted EBITDA (segment note 45 total)", adj_ebitda25, None,
     f"AR2025 PDF p.{sp} line {sl}", "EUR m. Used only to measure FY2025 share-based cost."),
    ("share_based_cost_fy2025",
     "Management adjusted EBITDA - (reported EBIT + amortization) - IS non-recurring add-back", sbc25, None,
     f"AR2025 PDF p.{sp} line {sl}; hist_ratios FY2025 ebit_reported, da, nonrec; cross-check AR2025 PDF p.{bp} "
     f"line {bl} bucket {bucket:.1f}",
     "EUR m. Kept inside adjusted EBIT (brief definition); payroll note 4 (AR2025 p.163) shows 30.271 m stock-option "
     "notional cost, the rest of management's bucket is other incentive plans."),
    ("share_based_pct", "FY2025 share-based cost / FY2025 revenue, held flat", sbc_pct, None,
     "share_based_cost_fy2025 / revenue_fy2025", "Only used to bridge guidance EBITDA to adjusted EBIT (Decision 7)."),
    ("da_pct", "Average of FY2021-25 D&A / revenue (simple mean of the 5 yearly ratios)", da_pct, None,
     "hist_ratios da_pct FY2021-25", "D&A = IS 'Amortization' incl. right-of-use depreciation (leases as debt)."),
    ("capex_pct", "Average of FY2021-25 capex / revenue incl. right-of-use additions (Decision 9A)", capex_pct, None,
     "hist_ratios capex_pct FY2021-25", "Capex = intangibles + PP&E + ROU additions, so leased assets are not free."),
    ("nwc_pct", "FY2025 NWC / revenue, held flat", nwc_pct, None, "hist_ratios nwc_pct FY2025",
     "FY2025 used (post La Marzocco perimeter); FY2021-25 range 2.0-9.1%."),
    ("adj_ebit_margin_fy2026", "guidance midpoint / FY2026E revenue - da_pct - share_based_pct", margin26, None,
     f"{guid_src}; derived", "Adjusted EBIT keeps share-based cost (brief definition)."),
    ("adj_ebit_margin_target_fy2030", "Average adjusted EBIT margin FY2024-25", margin_target, None,
     "hist_ratios adj_ebit_margin FY2024, FY2025", "Like-for-like perimeter after La Marzocco (Decision 7)."),
    ("tax_rate_forecast", "Median effective tax rate of included FY2021-25 years (Decision 8A)", tax_forecast, None,
     "hist_ratios eff_tax_rate, tax_included", "Applied to FY2026E-30E FCFF; all 5 years included (22.1-24.5%)."),
    ("tax_rate_terminal", "Italian marginal rate for the terminal FCFF (Decision 8A)", tax_terminal, None,
     "wacc.tax_marginal (Damodaran countrytaxrates.xls Italy)", "Steady-state assumption: tax credits fade out."),
]

for d in A:
    assert d[2] is not None and d[4] and d[5]


def write_assumptions(rows):
    df = pd.DataFrame(rows, columns=["driver", "rule", "value", "value_by_year", "source", "note"])
    con.register("fa_df", df)
    con.execute("CREATE OR REPLACE TABLE forecast_assumptions AS SELECT driver::VARCHAR AS driver, rule::VARCHAR AS rule, "
                "value::DOUBLE AS value, value_by_year::VARCHAR AS value_by_year, source::VARCHAR AS source, "
                "note::VARCHAR AS note FROM fa_df")
    con.unregister("fa_df")


write_assumptions(A)

# ------------------------------------------------------------------ run the shared engine on the base case
P = dcf.load_base_params(con)
assert P["wacc"] == wacc_base
R = dcf.value_per_share(P)
yrs = R["years"]

# path drivers (computed by the engine, stored for the Forecast_FCFF sheet)
A += [
    ("revenue_growth", "growth_t = growth_fy2026 - (growth_fy2026 - terminal_g) x (t - 2026) / growth_fade_years",
     None, fmt_years(yrs, R["growth"]), "Decision 7", "Linear fade from guidance towards g."),
    ("adj_ebit_margin", "margin_t = m2026 + (m_target - m2026) x (t - 2026) / 4", None,
     fmt_years(yrs, R["adj_ebit_margin"]), "Decision 7",
     "Linear fade from the guidance-implied FY2026E margin to the FY2024-25 average by FY2030E."),
    ("wacc", "Base-case WACC from step 2", wacc_base, None, "wacc case='base'",
     "Discount rate for every FCFF and the terminal value."),
]
write_assumptions(A)

# ------------------------------------------------------------------ forecast_fcff
ff = pd.DataFrame({"fy": yrs, **{k: R[k] for k in ("revenue", "growth", "adj_ebit_margin", "adj_ebit", "tax_rate",
                                                   "nopat", "da", "capex", "nwc", "delta_nwc", "fcff",
                                                   "share_based_cost", "adj_ebitda_mgmt")}})
ff["nopat_tv"] = [R["nopat_tv"] if y == yrs[-1] else None for y in yrs]
ff["fcff_tv"] = [R["fcff_tv"] if y == yrs[-1] else None for y in yrs]
con.register("ff_df", ff)
con.execute("CREATE OR REPLACE TABLE forecast_fcff AS SELECT fy::INTEGER AS fy, * EXCLUDE (fy, nopat_tv, fcff_tv), "
            "nopat_tv::DOUBLE AS nopat_tv, fcff_tv::DOUBLE AS fcff_tv FROM ff_df ORDER BY fy")
con.unregister("ff_df")

# ------------------------------------------------------------------ valuation (ordered walk)
BI = {r[0]: (r[1], r[2], r[3]) for r in con.execute("SELECT item, source, treatment, note FROM bridge_inputs").fetchall()}
V = []


def add(section, item, fy, value, unit, treatment, note):
    V.append((len(V) + 1, section, item, fy, float(value), unit, treatment, note))


add("rates", "wacc", None, R["wacc"], "decimal", "discount rate", "Base case, step 2 (wacc case='base').")
add("rates", "terminal_g", None, R["terminal_g"], "decimal", "Gordon growth", "Decision 7.")
for i, y in enumerate(yrs):
    add("discounting", f"tau_{y}", y, R["tau"][i], "years", "year fraction",
        f"(31 Dec {y} - {P['valuation_date'].isoformat()}) / 365.25, year-end convention.")
for i, y in enumerate(yrs):
    add("discounting", f"discount_factor_{y}", y, R["discount_factor"][i], "ratio", "1 / (1 + wacc)^tau", "")
for i, y in enumerate(yrs):
    add("discounting", f"pv_fcff_{y}", y, R["pv_fcff"][i], "EUR m", "fcff x discount factor",
        "FY2026E counted in full (Decision 1A: net debt at 31 Dec 2025)." if y == yrs[0] else "")
add("ev", "sum_pv_fcff", None, R["sum_pv_fcff"], "EUR m", "sum", "")
add("ev", "fcff_tv", yrs[-1], R["fcff_tv"], "EUR m", "terminal FCFF",
    "FY2030E FCFF with tax at the marginal 27.81% (Decision 8A).")
add("ev", "tv_gordon", yrs[-1], R["tv_gordon"], "EUR m", "fcff_tv x (1 + g) / (wacc - g)", "Value at 31 Dec 2030.")
add("ev", "pv_tv", yrs[-1], R["pv_tv"], "EUR m", "tv x discount factor 2030", "")
add("ev", "ev", None, R["ev"], "EUR m", "sum_pv_fcff + pv_tv", "Enterprise value at the price date.")
add("ev", "tv_share_of_ev", None, R["tv_share_of_ev"], "decimal", "pv_tv / ev", "")
for it, sign in [("cash", "add"), ("cash_like_financial_assets", "add"), ("bank_debt", "deduct"),
                 ("other_financial_payables", "deduct"), ("lease_liabilities", "deduct"),
                 ("distributions_2026", "deduct"), ("minority_book", "deduct")]:
    src, _treat, bnote = BI[it]
    note = f"Source: {src}."
    if it == "minority_book":
        note = "SIMPLIFICATION: minorities at book value, not market value; likely understates their claim. " + note
    if it == "distributions_2026":
        note = "Decision 1A: H1 2026 dividends + buybacks paid after the balance-sheet date. " + note
    add("bridge", it, None, P[it], "EUR m", sign, note)
add("bridge", "equity_value", None, R["equity_value"], "EUR m",
    "ev + cash + cash-like - debt - other fin. payables - leases - distributions - minorities", "")
add("per_share", "diluted_shares", None, P["diluted_shares"], "million shares", "divisor",
    f"Source: {BI['diluted_shares'][0]}.")
add("per_share", "value_per_share", None, R["value_per_share"], "EUR per share", "equity_value / diluted_shares",
    "DCF base case.")
add("per_share", "price", None, P["price"], "EUR per share", "market price", f"Source: {BI['price'][0]}.")
add("per_share", "upside_pct", None, R["upside_pct"], "decimal", "price / value_per_share - 1",
    "Negative = market price below the base-case value.")

vdf = pd.DataFrame(V, columns=["line_no", "section", "item", "fy", "value", "unit", "treatment", "note"])
con.register("v_df", vdf)
con.execute("CREATE OR REPLACE TABLE valuation AS SELECT line_no::INTEGER AS line_no, section, item, fy::INTEGER AS fy, "
            "value::DOUBLE AS value, unit, treatment, note FROM v_df ORDER BY line_no")
con.unregister("v_df")

# ------------------------------------------------------------------ multiples_check (Damodaran Furn/Home Furnishings, ev_ebitda)
M = []
for region, table, fname in [("Europe", "raw_damodaran_vebitda_europe", "vebitdaEurope.xls"),
                             ("Global", "raw_damodaran_vebitda_global", "vebitdaGlobal.xls")]:
    rows = con.execute(f"SELECT industry_name, number_of_firms, ev_ebitda FROM {table} "
                       "WHERE industry_name = 'Furn/Home Furnishings'").fetchall()
    assert len(rows) == 1, rows
    ind, n, mult = rows[0]
    x = dcf.exit_multiple_value(R, P, mult)
    M.append((region, ind, n, mult, R["ebitda_2030"], x["tv_exit"], x["pv_tv_exit"], x["ev_exit"],
              x["equity_value_exit"], x["value_per_share_exit"], x["pct_vs_gordon"], R["implied_gordon_ev_ebitda"],
              f"Damodaran {fname} (Jan 2026), column 'EV/EBITDA' (positive-EBITDA firms); FY2030E EBITDA = "
              "adjusted EBIT + D&A (share-based cost kept, like reported EBITDA)"))
mdf = pd.DataFrame(M, columns=["region", "industry", "n_firms", "ev_ebitda", "fy2030_ebitda", "tv_exit", "pv_tv_exit",
                               "ev_exit", "equity_value_exit", "value_per_share_exit", "pct_vs_gordon",
                               "implied_gordon_ev_ebitda", "source"])
con.register("m_df", mdf)
con.execute("CREATE OR REPLACE TABLE multiples_check AS SELECT region, industry, n_firms::INTEGER AS n_firms, "
            "* EXCLUDE (region, industry, n_firms) FROM m_df ORDER BY region")
con.unregister("m_df")

for t in ("forecast_assumptions", "forecast_fcff", "valuation", "multiples_check"):
    print(f"  {t}: {con.execute(f'SELECT COUNT(*) FROM {t}').fetchall()[0][0]} rows")
print(f"  EV {R['ev']:.3f} m, equity {R['equity_value']:.3f} m, value/share {R['value_per_share']:.4f}, "
      f"TV share {R['tv_share_of_ev']:.4f}, upside_pct {R['upside_pct']:.4f}")
con.close()
