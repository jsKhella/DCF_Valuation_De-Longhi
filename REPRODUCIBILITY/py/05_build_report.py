"""Steps 5 and 7: build the Excel report report/DeLonghi_DCF_Valuation.xlsx (values only, no formulas) from DuckDB.

Purpose
    Step 5: lay out the tables of steps 1-4 as nine sheets, write the headline sentence at the top of the Valuation
    sheet, and add a Checks sheet with every reconciliation (BS balances, CF reconciles, FCFF tie-out, sensitivity
    centre = base, MC run 0 = base, histogram, the step 1-4 acceptance scripts, determinism).
    Step 7 (Amendment 2): the nine sheets are first built in their step-5 layout (an in-memory "old" workbook), then
    `relayout()` places every cell on the 11 numbered sheets of py/doc_map.py: two rows are inserted on top (row 1 band
    with links, row 2 numeral and title), the sheets whose column A holds DuckDB keys get a readable-label column B,
    the bridge_inputs block of Valuation moves to 2.2 Bridge Inputs, and 0.0 Overview is added. Cell values, types and
    number formats are unchanged. Styling comes from py/report_style.py, which imports every colour and font from
    py/ledger_style.py.
    Step 9 (Amendment 3): the rows below the moved bridge block close up (the simplification flag moves from 3.2 row 79 to
    row 61); source text cells go through doc_map.reword() (6 fixed rules, DuckDB untouched); 0.0 Overview gets the author
    line (doc_map.AUTHOR_LINE) in A20; the file creator and last-modified-by are doc_map.AUTHOR_NAME.

Inputs (DuckDB tables built by steps 1-4)
    hist_statements, hist_adjustments, hist_ratios, forecast_assumptions, forecast_fcff, wacc_inputs, wacc,
    bridge_inputs, valuation, multiples_check, sensitivity, beta_sensitivity, mc_params, mc_runs, mc_summary,
    mc_histogram. Also runs checks/check_step01..04.py and a determinism test (see below).

Outputs
    report/DeLonghi_DCF_Valuation.xlsx   the 11 sheets listed in py/doc_map.py (0.0 Overview ... 5.1 Checks)
    table report_headline (key, value, display, source): the sentence and each number in it

Brief definitions implemented (by term)
    Section 6 "Headline sentence", "Excel workbook" (eleven sheets, values only, Checks sheet) and "Precision" (EUR m with
    no decimals, EUR per share 2 decimals, % 1 decimal, WACC and g 2 decimals, multiples 1 decimal). The cell holds the
    unrounded source value; rounding is a number format only (round-trip to the table exact).
    "Minorities at book value, flagged as a simplification" (3.2 Valuation sheet) and "country risk double counting noted as
    a limitation" (2.1 WACC sheet), per the Amendment.

Determinism test (Checks sheet): a scratch copy of the pipeline (py/, sql/, run.py, data/raw) in a temp folder is rebuilt
    twice with `run.py --fresh --through 4`; the order-independent fingerprints (checks/fingerprint.py) of all step 1-4
    tables must be identical in both rebuilds and equal to the live database. This is the "two fresh runs" test, done
    without deleting the live database while this script runs.

Rule: no numbers are typed in this file other than named UPPER_CASE constants (tolerances, formatting). Every number in
    the workbook comes from a DuckDB query.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import duckdb
import openpyxl
import pandas as pd
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.chart.text import RichText, Text
from openpyxl.chart.title import Title
from openpyxl.drawing.text import (CharacterProperties, Font, Paragraph, ParagraphProperties,
                                   RegularTextRun)
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.styles import Border
from openpyxl.utils import get_column_letter
from openpyxl.utils.indexed_list import IndexedList
from openpyxl.worksheet.hyperlink import Hyperlink

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "curiosity.duckdb"
OUT = ROOT / "report" / "DeLonghi_DCF_Valuation.xlsx"
sys.path.insert(0, str(ROOT / "checks"))
sys.path.insert(0, str(ROOT / "py"))
from fingerprint import fingerprint  # noqa: E402
import doc_map as DM  # noqa: E402  (sheet registry, label sheets, LABELS)
import ledger_style as LS  # noqa: E402  (palette and fonts, defined once)
import report_style as RS  # noqa: E402  (presentation only: style_sheet)

# ---- named constants (tolerances, formatting) ----
C3, C4, C5, C6, C7, C8 = 3, 4, 5, 6, 7, 8     # column indices
ROW_HDR, ROW_HDR_VAL = 3, 4                    # first header row on a sheet
WIDTHS_1 = {"A": 12, "B": 52, "C": 52}
WIDTHS_2 = {"A": 30, "B": 52, "F": 60}
WIDTHS_3 = {"A": 34, "B": 70, "D": 40, "E": 50, "F": 70}
WIDTHS_4 = {"A": 44, "B": 18, "C": 18, "D": 110}
WIDTHS_5 = {"A": 34, "B": 18, "C": 14, "D": 22, "E": 40, "F": 40, "G": 80}
WIDTHS_6 = {"A": 30}
WIDTHS_7 = {"A": 26, "B": 16, "C": 16, "D": 60}
WIDTHS_8 = {"A": 14, "B": 26, "M": 90}
WIDTHS_9 = {"A": 100, "B": 28, "C": 22, "D": 22, "E": 12, "F": 10}
TOL_STMT = 0.002          # plan step 1 tie-out tolerance, EUR m
TOL_ID = 1e-9             # plan step 3/4 identity tolerance
TOL_EV = 1e-6             # plan step 3 EV / TV recomputation tolerance, EUR m
FMT_M, FMT_SH, FMT_P1, FMT_P2, FMT_X = "#,##0", "0.00", "0.0%", "0.00%", '0.0"x"'
FMT_BETA, FMT_YR, FMT_INT, FMT_SHARES, FMT_PCTILE, FMT_CORR = "0.000", "0.0000", "0", "0.0", "0.0", "0.00"
COL_WIDTHS = {"A": 46, "B": 22, "C": 16, "D": 16, "E": 16, "F": 16, "G": 16, "H": 16}
ORD_TEENS, ORD_HUNDRED, ORD_TEN = (10, 20), 100, 10   # ordinal suffix rule (11th, 12th, 13th)
ORD_SUFFIX = {1: "st", 2: "nd", 3: "rd"}
FIXED_DATETIME = datetime(2026, 11, 9)   # constant workbook properties (idempotent file content)
STEP_CHECKS = ["check_step01.py", "check_step02.py", "check_step03.py", "check_step04.py"]
FP_TABLES = ["hist_statements", "hist_adjustments", "hist_ratios", "wacc_inputs", "bridge_inputs", "wacc",
             "forecast_assumptions", "forecast_fcff", "valuation", "multiples_check", "sensitivity",
             "beta_sensitivity", "mc_params", "mc_runs", "mc_summary", "mc_histogram"]
STATEMENT_RANK = "CASE statement WHEN 'IS' THEN 1 WHEN 'BS' THEN 2 ELSE 3 END"
PCT1_RATIOS = {"growth", "adj_ebit_margin", "da_pct", "capex_pct", "capex_excl_rou_pct", "nwc_pct", "eff_tax_rate"}
PCT1_FORECAST = {"growth", "adj_ebit_margin", "tax_rate"}
ASSUMP_EURM = {"revenue_fy2025", "nwc_fy2025", "guidance_adj_ebitda_fy2026", "adj_ebitda_fy2025_mgmt",
               "share_based_cost_fy2025"}
ASSUMP_PCT2 = {"terminal_g", "wacc"}
ASSUMP_INT = {"growth_fade_years"}
PCT2_NAMES = {"wacc", "terminal_g", "rf", "erp_mature", "country_spread", "tax_marginal", "kd_pre", "kd_post", "ke",
              "terminal_g_reference", "wacc_mean", "wacc_sd", "wacc_lower", "wacc_upper", "g"}
WACC_ROW_BETA = {"beta_u", "beta_l"}
WACC_ROW_PCT1 = {"d_e", "w_e", "w_d"}
MC_SUMMARY_INT = {"n_runs", "n_wacc_redraws"}
CHART_ANCHOR = "D5"          # on 4.2, beside the percentile table (rows 5-20)
CHART_W, CHART_H, CHART_GAP = 17, 7.2, 15
ROW_SHIFT = 2                # rows inserted on top of every sheet (band, title)
CHART_PT_SCALE = 100         # DrawingML font size unit: hundredths of a point
HDR_ROW_22 = 4               # header row of the moved bridge block on 2.2 (row 3 holds the description)
LABEL_W = 36                 # width of the readable-label column B
OV_WIDTHS = {"A": 34, "B": 16, "C": 100}
OV_HEADER_ROW = 8            # header row of the step index on 0.0 Overview
OV_HEADLINE_ROW = 3
OV_NOTE_ROWS = (5, 6)
OV_AUTHOR_ROW = 20           # author line on 0.0 Overview, one blank row below the step index (rows 9-18)
OV_HEADERS = ["Sheet", "Guide section", "Content"]
LINK_COL_OVERVIEW, LINK_COL_PREV, LINK_COL_NEXT = 2, 3, 4   # row-1 link cells
VAL_COLS = 7                 # columns A-G of the old Valuation sheet
DEFAULT_COL_UNITS = 13       # width assumed for a column without an explicit width
HIST_TITLE = "Monte Carlo: value per share (EUR), runs per bin"
LIMITATION_NOTES = [
    "Limitation: Italy risk is double counted. The risk-free rate is the Italian 10-year BTP yield (already includes "
    "Italian sovereign risk) and the cost of equity adds the Italy default spread on top of the mature-market ERP "
    "(brief formula, kept as agreed in the Amendment, no memo lines). This lifts the cost of equity and lowers value.",
    "Limitation: the Europe Furniture/Home Furnishings industry beta is low (a small, highly leveraged sample, so its unlevering is suspect). The "
    "base case uses it as agreed; the beta sensitivity line shows the Global Furn/Home beta, which gives a much higher "
    "WACC and a much lower value per share. Beta is the dominant driver of the answer.",
    "Limitation: right-of-use and lease treatment, stale rf date (ECB monthly average, latest available) and "
    "balance-sheet date (31 Dec 2025) are described in the Valuation and bridge notes.",
]
SIMPLIFICATION_NOTE = ("SIMPLIFICATION FLAG: minorities at book value (not market value) are deducted in the equity "
                       "bridge, as agreed in the Amendment. Minorities at book likely understate their share of value.")
GUIDE_FILE, NOTE_FILE = "DeLonghi_DCF_process_guide.pdf", "DeLonghi_DCF_Valuation_note.docx"
OV_TEXT = {
    "1.1": "Condensed income statement, balance sheet and cash flow, FY2021-FY2025, with the document and page of every row.",
    "1.2": "Itemised non-recurring adjustments and the historical ratios (margins, D&A, capex, working capital, tax rate, FCFF).",
    "2.1": "Cost of equity, cost of debt and WACC with every input and its source; the beta sensitivity line; limitations.",
    "2.2": "Inputs of the bridge from enterprise value to equity value per share: debt, leases, cash, distributions, minorities, shares, price.",
    "3.1": "FCFF forecast FY2026E-FY2030E and the driver rules with their sources.",
    "3.2": "Discounting, terminal value, enterprise value, the equity bridge, value per share and the headline numbers.",
    "3.3": "Exit-multiple cross-check against the Damodaran Furniture/Home Furnishings EV/EBITDA.",
    "4.1": "Value per share over a grid of WACC and terminal growth, and the beta sensitivity line.",
    "4.2": "Monte Carlo distribution of value per share, percentile table, price percentile, parameters and histogram.",
    "5.1": "Every reconciliation and acceptance check, each with actual, expected and result.",
}
BRIDGE_DESC = ("Inputs of the equity bridge (enterprise value to equity value per share): debt, leases, cash and cash-like "
               "assets, 2026 distributions, minorities at book value, share count, price and price date. Used on 3.2 Valuation.")
BRIDGE_POINTER = "Equity bridge inputs: see sheet 2.2 Bridge Inputs."
REG = {"headers": {}, "sections": {}, "notes": {}, "ctx": {}}   # layout facts recorded while building, old coordinates


# ---------------------------------------------------------------- helpers
def unit_fmt(unit, name):
    """Number format for a row from its unit column and name (display precision only; the cell keeps the full value)."""
    if unit == "decimal":
        return FMT_P2 if name in PCT2_NAMES else FMT_P1
    if unit == "EUR m":
        return FMT_M
    if unit == "EUR per share":
        return FMT_SH
    if unit == "million shares":
        return FMT_SHARES
    if unit == "years":
        return FMT_YR
    if unit == "ratio":
        if name == "d_e":
            return FMT_P1
        return FMT_YR if name.startswith("discount_factor") else FMT_BETA
    if unit in ("yyyymmdd", "integer"):
        return FMT_INT
    if unit == "runs":
        return FMT_M
    if unit == "correlation":
        return FMT_CORR
    return "General"


def put(ws, row, col, value, fmt=None, bold=False):
    """Write a value (and its number format) in the step-5 layout. `bold` is kept for readability only: fonts are set later."""
    if isinstance(value, bool):
        value = "yes" if value else "no"
    cell = ws.cell(row=row, column=col, value=value)
    if fmt and isinstance(value, (int, float)):
        cell.number_format = fmt
    return cell


def header(ws, row, labels, start=1):
    REG["headers"].setdefault(ws.title, {})[row] = start + len(labels) - 1
    for i, lab in enumerate(labels):
        put(ws, row, start + i, lab, bold=True)


def reg_set(kind, sheet, row):
    REG[kind].setdefault(sheet, set()).add(row)


def widths(ws, extra=None):
    for col, w in COL_WIDTHS.items():
        ws.column_dimensions[col].width = w
    for col, w in (extra or {}).items():
        ws.column_dimensions[col].width = w


def rows_of(con, sql):
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def ordinal(n):
    n = int(n)
    if ORD_TEENS[0] <= n % ORD_HUNDRED <= ORD_TEENS[1]:
        return f"{n}th"
    return f"{n}" + ORD_SUFFIX.get(n % ORD_TEN, "th")


# ---------------------------------------------------------------- 1. pipeline checks and determinism (before opening the DB)
def run_step_checks():
    results = []
    for name in STEP_CHECKS:
        r = subprocess.run([sys.executable, str(ROOT / "checks" / name)], cwd=ROOT, capture_output=True, text=True)
        m = re.findall(r"(\d+)/(\d+) checks passed", r.stdout)
        passed, total = (int(m[-1][0]), int(m[-1][1])) if m else (0, 1)
        results.append((name, passed, total, r.returncode))
    return results


def fingerprints_of(db_path):
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        return {t: fingerprint(con, t).split("\t", 1)[1] for t in FP_TABLES}
    finally:
        con.close()


def determinism_runs():
    """Two fresh rebuilds in a scratch copy of the project; returns (live, run_a, run_b) fingerprint dicts."""
    live = fingerprints_of(DB)
    scratch = Path(tempfile.mkdtemp(prefix="curiosity_det_"))
    try:
        for d in ("py", "sql"):
            shutil.copytree(ROOT / d, scratch / d, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy2(ROOT / "run.py", scratch / "run.py")
        (scratch / "data").mkdir()
        shutil.copytree(ROOT / "data" / "raw", scratch / "data" / "raw")
        (scratch / "checks").mkdir()
        shutil.copy2(ROOT / "checks" / "fingerprint.py", scratch / "checks" / "fingerprint.py")
        outs = []
        for _ in range(2):
            subprocess.run([sys.executable, str(scratch / "run.py"), "--fresh", "--through", "4"], cwd=scratch,
                           check=True, capture_output=True, text=True)
            outs.append(fingerprints_of(scratch / "data" / "curiosity.duckdb"))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    return live, outs[0], outs[1]


# ---------------------------------------------------------------- 2. headline
def build_headline(con):
    V = {r["item"]: r["value"] for r in rows_of(con, "SELECT item, value FROM valuation")}
    W = rows_of(con, "SELECT * FROM wacc WHERE \"case\" = 'base'")[0]
    MC = rows_of(con, "SELECT * FROM mc_summary")[0]
    B = {r["item"]: r["value"] for r in rows_of(con, "SELECT item, value FROM bridge_inputs")}
    up = V["upside_pct"]
    word = "above" if up > 0 else "below"
    sentence = (f"De'Longhi is worth EUR {V['value_per_share']:.2f} per share (DCF base case, WACC {W['wacc']:.2%}, "
                f"g {V['terminal_g']:.2%}); the 80% Monte Carlo range is EUR {MC['p10']:.2f} to EUR {MC['p90']:.2f}; "
                f"the market price of EUR {B['price']:.2f} sits at the {ordinal(round(MC['price_percentile']))} "
                f"percentile, i.e. {abs(up):.1%} {word} the base-case value.")
    rows = [
        ("sentence", None, sentence, "assembled from the rows below"),
        ("value_per_share", V["value_per_share"], f"{V['value_per_share']:.2f}", "valuation.value_per_share"),
        ("wacc", W["wacc"], f"{W['wacc']:.2%}", "wacc.wacc where case = 'base'"),
        ("g", V["terminal_g"], f"{V['terminal_g']:.2%}", "valuation.terminal_g (= forecast_assumptions terminal_g)"),
        ("mc_p10", MC["p10"], f"{MC['p10']:.2f}", "mc_summary.p10"),
        ("mc_p90", MC["p90"], f"{MC['p90']:.2f}", "mc_summary.p90"),
        ("price", B["price"], f"{B['price']:.2f}", "bridge_inputs.price"),
        ("price_percentile", MC["price_percentile"], f"{MC['price_percentile']:.1f}", "mc_summary.price_percentile"),
        ("price_percentile_ordinal", float(round(MC["price_percentile"])), ordinal(round(MC["price_percentile"])),
         "mc_summary.price_percentile rounded to an integer"),
        ("pct_vs_base", up, f"{abs(up):.1%} {word}", "valuation.upside_pct = price / value - 1"),
    ]
    df = pd.DataFrame(rows, columns=["key", "value", "display", "source"])
    con.register("hl_df", df)
    con.execute("CREATE OR REPLACE TABLE report_headline AS SELECT * FROM hl_df")
    con.unregister("hl_df")
    return sentence, rows_of(con, "SELECT * FROM report_headline")


# ---------------------------------------------------------------- 3. sheets
def sheet_statements(wb, con):
    ws = wb.create_sheet("Statements_5Y")
    put(ws, 1, 1, "Condensed statements (the lines FCFF and the equity bridge need), EUR m. IS and CF FY2021-FY2025; "
                  "balance sheet YE2020-YE2025. Each year from the latest report that presents it.", bold=True)
    fys = [r[0] for r in con.execute("SELECT DISTINCT fy FROM hist_statements ORDER BY fy").fetchall()]
    hr = ROW_HDR
    header(ws, hr, ["Statement", "Line item"] + [f"FY{fy}" for fy in fys])
    lines = con.execute(f"SELECT statement, line_item FROM hist_statements GROUP BY statement, line_item "
                        f"ORDER BY {STATEMENT_RANK}, MIN(rowid)").fetchall()
    data = {(r["statement"], r["line_item"], r["fy"]): r["value_eur_m"] for r in rows_of(con, "SELECT * FROM hist_statements")}
    row = hr
    for st, li in lines:
        row += 1
        put(ws, row, 1, st)
        put(ws, row, 2, li)
        for j, fy in enumerate(fys):
            v = data.get((st, li, fy))
            if v is not None:
                put(ws, row, C3 + j, v, FMT_M)
    row += 2
    put(ws, row, 1, "Source of every row (document and PDF page)", bold=True)
    reg_set("sections", ws.title, row)
    row += 1
    header(ws, row, ["Source: FY", "Statement", "Line item", "Document", "PDF page"])
    for r in rows_of(con, f"SELECT * FROM hist_statements ORDER BY fy, {STATEMENT_RANK}, rowid"):
        row += 1
        put(ws, row, 1, r["fy"], FMT_INT)
        put(ws, row, 2, r["statement"])
        put(ws, row, C3, r["line_item"])
        put(ws, row, C4, r["doc_id"])
        put(ws, row, C5, r["pdf_page"], FMT_INT)
    widths(ws, WIDTHS_1)


def sheet_adjust_ratios(wb, con):
    ws = wb.create_sheet("Adjustments_Ratios")
    put(ws, 1, 1, "Non-recurring adjustments (largest items itemised, EUR m; sign as in the income statement "
                  "'of which non-recurring' reversed: amounts sum to minus that figure) and historical ratios.", bold=True)
    hr = ROW_HDR
    header(ws, hr, ["FY", "Item", "Amount (EUR m)", "Document", "PDF page", "Description", "Note document", "Note page"])
    row = hr
    for r in rows_of(con, "SELECT * FROM hist_adjustments ORDER BY fy, (item LIKE 'other non-recurring%'), item"):
        row += 1
        put(ws, row, 1, r["fy"], FMT_INT)
        put(ws, row, 2, r["item"])
        put(ws, row, C3, r["amount_eur_m"], "#,##0.0")
        put(ws, row, C4, r["doc_id"])
        put(ws, row, C5, r["pdf_page"], FMT_INT)
        put(ws, row, C6, r["description"])
        put(ws, row, C7, r["note_doc_id"])
        put(ws, row, C8, r["note_page"], FMT_INT)
    row += 2
    ratios = rows_of(con, "SELECT * FROM hist_ratios ORDER BY fy")
    header(ws, row, ["Ratio"] + [f"FY{r['fy']}" for r in ratios])
    for k in [k for k in ratios[0] if k != "fy"]:
        row += 1
        put(ws, row, 1, k)
        for j, r in enumerate(ratios):
            put(ws, row, 2 + j, r[k], FMT_P1 if k in PCT1_RATIOS else FMT_M)
    widths(ws, WIDTHS_2)


def sheet_forecast(wb, con):
    ws = wb.create_sheet("Forecast_FCFF")
    put(ws, 1, 1, "FCFF forecast FY2026E-FY2030E, EUR m and %. Drivers and their notes are listed below the table.", bold=True)
    fc = rows_of(con, "SELECT * FROM forecast_fcff ORDER BY fy")
    hr = ROW_HDR
    header(ws, hr, ["Line item"] + [f"FY{r['fy']}E" for r in fc])
    row = hr
    for k in [k for k in fc[0] if k != "fy"]:
        row += 1
        put(ws, row, 1, k)
        for j, r in enumerate(fc):
            if r[k] is not None:
                put(ws, row, 2 + j, r[k], FMT_P1 if k in PCT1_FORECAST else FMT_M)
    row += 2
    header(ws, row, ["Driver", "Rule", "Value", "Value by year", "Source", "Note"])
    for r in rows_of(con, "SELECT * FROM forecast_assumptions ORDER BY rowid"):
        row += 1
        name = r["driver"]
        fmt = FMT_M if name in ASSUMP_EURM else FMT_INT if name in ASSUMP_INT else FMT_P2 if name in ASSUMP_PCT2 else FMT_P1
        put(ws, row, 1, name)
        put(ws, row, 2, r["rule"])
        put(ws, row, C3, r["value"], fmt)
        put(ws, row, C4, r["value_by_year"])
        put(ws, row, C5, r["source"])
        put(ws, row, C6, r["note"])
    widths(ws, WIDTHS_3)


def sheet_wacc(wb, con):
    ws = wb.create_sheet("WACC")
    put(ws, 1, 1, "WACC: every input with its source, the two cases, and the beta sensitivity line. Rates in %.", bold=True)
    hr = ROW_HDR
    header(ws, hr, ["Input", "Value", "Unit", "Source"])
    row = hr
    for r in rows_of(con, "SELECT * FROM wacc_inputs ORDER BY rowid"):
        row += 1
        put(ws, row, 1, r["input"])
        put(ws, row, 2, r["value"], unit_fmt(r["unit"], r["input"]))
        put(ws, row, C3, r["unit"])
        put(ws, row, C4, r["source"])
    row += 2
    cases = rows_of(con, "SELECT * FROM wacc ORDER BY (\"case\" <> 'base')")
    header(ws, row, ["Item"] + [r["case"] for r in cases])
    for k in [k for k in cases[0] if k != "case"]:
        row += 1
        put(ws, row, 1, k)
        fmt = FMT_BETA if k in WACC_ROW_BETA else FMT_P1 if k in WACC_ROW_PCT1 else FMT_P2
        for j, r in enumerate(cases):
            put(ws, row, 2 + j, r[k], fmt)
    row += 2
    bs = rows_of(con, "SELECT * FROM beta_sensitivity")[0]
    header(ws, row, ["Beta sensitivity line", "Value"])
    for k, v in bs.items():
        row += 1
        put(ws, row, 1, k)
        fmt = FMT_BETA if k == "beta_u" else FMT_P2 if k == "wacc" else FMT_P1 if k == "pct_vs_base" else FMT_SH
        put(ws, row, 2, v, fmt)
    row += 2
    header(ws, row, ["Limitations"])
    for note in LIMITATION_NOTES:
        row += 1
        put(ws, row, 1, note)
        reg_set("notes", ws.title, row)
    widths(ws, WIDTHS_4)


def sheet_valuation(wb, con, sentence, hl):
    ws = wb.create_sheet("Valuation")
    put(ws, 1, 1, sentence, bold=True)
    put(ws, 2, 1, "EUR m unless stated; value per share in EUR. Discounted to the price date with year fractions.")
    hr = ROW_HDR_VAL
    header(ws, hr, ["Headline numbers", "Value", "Display", "Source"])
    row = hr
    for r in hl:
        if r["key"] == "sentence":
            continue
        row += 1
        k = r["key"]
        fmt = FMT_P2 if k in ("wacc", "g") else FMT_P1 if k == "pct_vs_base" else FMT_PCTILE if k == "price_percentile" \
            else FMT_INT if k == "price_percentile_ordinal" else FMT_SH
        put(ws, row, 1, k)
        put(ws, row, 2, r["value"], fmt)
        put(ws, row, C3, r["display"])
        put(ws, row, C4, r["source"])
    row += 2
    header(ws, row, ["Item", "Section", "FY", "Value", "Unit", "Treatment", "Note"])
    REG["ctx"].setdefault(ws.title, {})["val_table_hdr"] = row
    for r in rows_of(con, "SELECT * FROM valuation ORDER BY line_no"):
        row += 1
        put(ws, row, 1, r["item"])
        put(ws, row, 2, r["section"])
        if r["fy"] is not None:
            put(ws, row, C3, r["fy"], FMT_INT)
        put(ws, row, C4, r["value"], unit_fmt(r["unit"], r["item"]))
        put(ws, row, C5, r["unit"])
        put(ws, row, C6, r["treatment"])
        put(ws, row, C7, r["note"])
    row += 2
    put(ws, row, 1, "Exit-multiple cross-check (Damodaran Furn/Home Furnishings EV/EBITDA; Gordon growth is the primary method)", bold=True)
    reg_set("sections", ws.title, row)
    row += 1
    header(ws, row, ["Region", "industry", "ev_ebitda", "value_per_share_exit", "pct_vs_gordon", "implied_gordon_ev_ebitda"])
    for r in rows_of(con, "SELECT * FROM multiples_check ORDER BY rowid"):
        row += 1
        put(ws, row, 1, r["region"])
        put(ws, row, 2, r["industry"])
        put(ws, row, C3, r["ev_ebitda"], FMT_X)
        put(ws, row, C4, r["value_per_share_exit"], FMT_SH)
        put(ws, row, C5, r["pct_vs_gordon"], FMT_P1)
        put(ws, row, C6, r["implied_gordon_ev_ebitda"], FMT_X)
    row += 2
    header(ws, row, ["Bridge input", "Value", "Unit", "As of", "Source", "Treatment", "Note"])
    for r in rows_of(con, "SELECT * FROM bridge_inputs ORDER BY rowid"):
        row += 1
        put(ws, row, 1, r["item"])
        put(ws, row, 2, r["value"], unit_fmt(r["unit"], r["item"]))
        put(ws, row, C3, r["unit"])
        put(ws, row, C4, r["as_of"])
        put(ws, row, C5, r["source"])
        put(ws, row, C6, r["treatment"])
        put(ws, row, C7, r["note"])
    row += 2
    put(ws, row, 1, SIMPLIFICATION_NOTE, bold=True)
    reg_set("notes", ws.title, row)
    widths(ws, WIDTHS_5)


def sheet_sensitivity(wb, con):
    ws = wb.create_sheet("Sensitivity")
    put(ws, 1, 1, "Value per share (EUR): WACC (rows) x terminal growth g (columns). The centre cell is the base case.", bold=True)
    hr = ROW_HDR
    gs = [r[0] for r in con.execute("SELECT DISTINCT g FROM sensitivity ORDER BY g").fetchall()]
    ws_ = [r[0] for r in con.execute("SELECT DISTINCT wacc FROM sensitivity ORDER BY wacc").fetchall()]
    put(ws, hr, 1, "WACC \\ g", bold=True)
    REG["headers"].setdefault(ws.title, {})[hr] = 1 + len(gs)      # the grid header row is the first table on the sheet
    for j, g in enumerate(gs):
        put(ws, hr, 2 + j, g, FMT_P2, bold=True)
    grid = {(r["wacc"], r["g"]): r["value_per_share"] for r in rows_of(con, "SELECT * FROM sensitivity")}
    for i, w in enumerate(ws_):
        put(ws, hr + 1 + i, 1, w, FMT_P2, bold=True)
        for j, g in enumerate(gs):
            put(ws, hr + 1 + i, 2 + j, grid[(w, g)], FMT_SH)
    base_w = con.execute("SELECT wacc FROM wacc WHERE \"case\" = 'base'").fetchone()[0]
    base_g = con.execute("SELECT value FROM valuation WHERE item = 'terminal_g'").fetchone()[0]
    REG["ctx"].setdefault(ws.title, {})["sens_base"] = (hr + 1 + ws_.index(base_w), 2 + gs.index(base_g))
    REG["ctx"].setdefault(ws.title, {})["sens_grid"] = (hr + 1, 2, hr + len(ws_), 1 + len(gs))
    row = hr + len(ws_) + 2
    bs = rows_of(con, "SELECT * FROM beta_sensitivity")[0]
    header(ws, row, ["Beta sensitivity line", "Value"])
    for k, v in bs.items():
        row += 1
        put(ws, row, 1, k)
        fmt = FMT_BETA if k == "beta_u" else FMT_P2 if k == "wacc" else FMT_P1 if k == "pct_vs_base" else FMT_SH
        put(ws, row, 2, v, fmt)
    widths(ws, WIDTHS_6)


def sheet_montecarlo(wb, con):
    ws = wb.create_sheet("MonteCarlo")
    put(ws, 1, 1, "Monte Carlo: distribution of value per share (EUR) over the runs; percentile table, price percentile, "
                  "histogram and distribution parameters.", bold=True)
    hr = ROW_HDR
    header(ws, hr, ["Statistic", "Value"])
    row = hr
    mc = rows_of(con, "SELECT * FROM mc_summary")[0]
    for k, v in mc.items():
        row += 1
        fmt = FMT_PCTILE if k == "price_percentile" else FMT_M if k in MC_SUMMARY_INT else FMT_SH
        put(ws, row, 1, k)
        put(ws, row, 2, v, fmt)
    row += 2
    header(ws, row, ["Parameter", "Value", "Unit", "Note"])
    for r in rows_of(con, "SELECT * FROM mc_params ORDER BY rowid"):
        row += 1
        put(ws, row, 1, r["param"])
        put(ws, row, 2, r["value"], unit_fmt(r["unit"], r["param"]))
        put(ws, row, C3, r["unit"])
        put(ws, row, C4, r["note"])
    row += 2
    hh = row
    header(ws, hh, ["Bin low", "Bin high", "Count"])
    hist = rows_of(con, "SELECT * FROM mc_histogram ORDER BY bin_id")
    for i, r in enumerate(hist):
        put(ws, hh + 1 + i, 1, r["bin_lo"], FMT_SH)
        put(ws, hh + 1 + i, 2, r["bin_hi"], FMT_SH)
        put(ws, hh + 1 + i, C3, r["count"], FMT_M)
    REG["ctx"].setdefault(ws.title, {})["hist"] = (hh, len(hist))
    widths(ws, WIDTHS_7)


def sheet_multiples(wb, con):
    ws = wb.create_sheet("Multiples_Check")
    put(ws, 1, 1, "Exit-multiple cross-check: Damodaran Furn/Home Furnishings EV/EBITDA (x) applied to FY2030E EBITDA. "
                  "Replaces the Peers sheet. EUR m, EUR per share, x.", bold=True)
    hr = ROW_HDR
    rows = rows_of(con, "SELECT * FROM multiples_check ORDER BY rowid")
    cols = list(rows[0])
    header(ws, hr, cols)
    fmts = {"n_firms": FMT_M, "ev_ebitda": FMT_X, "implied_gordon_ev_ebitda": FMT_X, "value_per_share_exit": FMT_SH,
            "pct_vs_gordon": FMT_P1}
    for i, r in enumerate(rows):
        for j, k in enumerate(cols):
            put(ws, hr + 1 + i, 1 + j, r[k], fmts.get(k, FMT_M))
    widths(ws, WIDTHS_8)


def sheet_checks(wb, con, step_results, det):
    ws = wb.create_sheet("Checks")
    put(ws, 1, 1, "Reconciliations and acceptance checks (all must be PASS). Values are computed from the DuckDB tables.", bold=True)
    hr = ROW_HDR
    header(ws, hr, ["Check", "Source", "Actual", "Expected", "Tolerance", "Result"])
    checks = []

    def add(name, source, actual, expected, tol):
        ok = abs(actual - expected) <= tol
        checks.append((name, source, actual, expected, tol, "PASS" if ok else "FAIL"))

    def add_text(name, source, actual, expected):
        checks.append((name, source, actual, expected, None, "PASS" if actual == expected else "FAIL"))

    # balance sheet balances
    for fy, ta, tl in con.execute("""SELECT a.fy, a.value_eur_m, b.value_eur_m FROM hist_statements a
            JOIN hist_statements b ON a.fy = b.fy AND a.statement = 'BS' AND b.statement = 'BS'
            WHERE a.line_item = 'total assets' AND b.line_item = 'total net equity and liabilities' ORDER BY a.fy""").fetchall():
        add(f"Balance sheet balances YE{fy} (total assets = total net equity and liabilities)", "hist_statements", ta, tl, TOL_STMT)
    # cash flow reconciles
    for fy, o, cf, tr, cl, bs in con.execute("""SELECT o.fy, o.value_eur_m, p.value_eur_m, t.value_eur_m, c.value_eur_m, b.value_eur_m
            FROM hist_statements o
            JOIN hist_statements p ON o.fy = p.fy AND p.statement = 'CF' AND p.line_item = 'cash flow for the period'
            JOIN hist_statements t ON o.fy = t.fy AND t.statement = 'CF' AND t.line_item = 'translation difference on cash'
            JOIN hist_statements c ON o.fy = c.fy AND c.statement = 'CF' AND c.line_item = 'closing cash and cash equivalents'
            JOIN hist_statements b ON o.fy = b.fy AND b.statement = 'BS' AND b.line_item = 'cash and cash equivalents'
            WHERE o.statement = 'CF' AND o.line_item = 'opening cash and cash equivalents' ORDER BY o.fy""").fetchall():
        add(f"Cash flow reconciles to change in cash FY{fy} (opening + period + translation = closing)", "hist_statements", o + cf + tr, cl, TOL_STMT)
        add(f"CF closing cash equals balance-sheet cash FY{fy}", "hist_statements", cl, bs, TOL_STMT)
    # historical FCFF identity
    for r in rows_of(con, "SELECT * FROM hist_ratios ORDER BY fy"):
        add(f"Historical FCFF tie-out FY{r['fy']} (adj EBIT x (1 - t) + D&A - capex - dNWC)", "hist_ratios", r["fcff_hist"],
            r["adj_ebit"] * (1 - r["eff_tax_rate"]) + r["da"] - r["capex_total"] - r["delta_nwc"], TOL_ID)
    # forecast FCFF identity and NOPAT
    for r in rows_of(con, "SELECT * FROM forecast_fcff ORDER BY fy"):
        add(f"FCFF identity FY{r['fy']}E (NOPAT + D&A - capex - dNWC = FCFF)", "forecast_fcff", r["fcff"],
            r["nopat"] + r["da"] - r["capex"] - r["delta_nwc"], TOL_ID)
        add(f"NOPAT = adj EBIT x (1 - tax rate) FY{r['fy']}E", "forecast_fcff", r["nopat"], r["adj_ebit"] * (1 - r["tax_rate"]), TOL_ID)
    V = {r["item"]: r["value"] for r in rows_of(con, "SELECT item, value FROM valuation")}
    sum_pv_items = sum(v for k, v in V.items() if k.startswith("pv_fcff_"))
    add("Sum of yearly PV of FCFF = sum_pv_fcff", "valuation", sum_pv_items, V["sum_pv_fcff"], TOL_EV)
    add("Terminal value: TV = fcff_tv x (1 + g) / (WACC - g)", "valuation", V["tv_gordon"],
        V["fcff_tv"] * (1 + V["terminal_g"]) / (V["wacc"] - V["terminal_g"]), TOL_EV)
    add("PV of TV = TV x discount factor FY2030", "valuation", V["pv_tv"], V["tv_gordon"] * V["discount_factor_2030"], TOL_EV)
    add("EV = sum PV + PV TV", "valuation", V["ev"], V["sum_pv_fcff"] + V["pv_tv"], TOL_EV)
    eq = (V["ev"] + V["cash"] + V["cash_like_financial_assets"] - V["bank_debt"] - V["other_financial_payables"]
          - V["lease_liabilities"] - V["distributions_2026"] - V["minority_book"])
    add("Equity bridge: EV + cash + cash-like - debt - leases - distributions - minorities (book) = equity value", "valuation", V["equity_value"], eq, TOL_EV)
    add("Value per share = equity value / diluted shares", "valuation", V["value_per_share"], V["equity_value"] / V["diluted_shares"], TOL_ID)
    add("Upside_pct = price / value per share - 1", "valuation", V["upside_pct"], V["price"] / V["value_per_share"] - 1, TOL_ID)
    # sensitivity, MC
    centre = con.execute("""SELECT s.value_per_share FROM sensitivity s, wacc w, valuation v
        WHERE w.\"case\" = 'base' AND v.item = 'terminal_g' AND s.wacc = w.wacc AND s.g = v.value""").fetchall()
    add_text("Sensitivity centre cell found exactly once (base WACC, base g)", "sensitivity", len(centre), 1)
    add("Sensitivity centre = base value per share", "sensitivity, valuation", centre[0][0], V["value_per_share"], TOL_ID)
    mc = rows_of(con, "SELECT * FROM mc_summary")[0]
    add("MC run 0 (zero shifts, base WACC) = base value per share", "mc_summary, valuation", mc["run0_value_per_share"], V["value_per_share"], TOL_ID)
    add("Beta sensitivity WACC = wacc row 'beta_sensitivity'", "beta_sensitivity, wacc",
        con.execute("SELECT wacc FROM beta_sensitivity").fetchone()[0],
        con.execute("SELECT wacc FROM wacc WHERE \"case\" = 'beta_sensitivity'").fetchone()[0], 0)
    add("MC histogram counts sum to n_runs", "mc_histogram, mc_summary", con.execute("SELECT SUM(count) FROM mc_histogram").fetchone()[0], mc["n_runs"], 0)
    add("MC rows in mc_runs = n_runs", "mc_runs, mc_summary", con.execute("SELECT COUNT(*) FROM mc_runs").fetchone()[0], mc["n_runs"], 0)
    add("MC price percentile = 100 x share of runs below price", "mc_runs, mc_summary",
        con.execute("SELECT 100.0 * AVG(CASE WHEN value_per_share < (SELECT price FROM mc_summary) THEN 1.0 ELSE 0.0 END) FROM mc_runs").fetchone()[0],
        mc["price_percentile"], TOL_ID)
    # step acceptance scripts
    for name, passed, total, rc in step_results:
        add(f"{name}: all acceptance checks pass ({passed}/{total}, exit code {rc})", name, passed, total, 0)
    # determinism
    live, a, b = det
    for t in FP_TABLES:
        add_text(f"Determinism: {t} fingerprint identical in two fresh rebuilds and the live database", "checks/fingerprint.py",
                 "equal" if (a[t] == b[t] == live[t]) else f"differ: {live[t]} / {a[t]} / {b[t]}", "equal")
    row = hr
    for name, source, actual, expected, tol, result in checks:
        row += 1
        put(ws, row, 1, name)
        put(ws, row, 2, source)
        put(ws, row, C3, actual, "General")
        put(ws, row, C4, expected, "General")
        if tol is not None:
            put(ws, row, C5, tol, "General")
        put(ws, row, C6, result, bold=True)
    widths(ws, WIDTHS_9)
    return [c for c in checks if c[-1] != "PASS"]


# ---------------------------------------------------------------- 4. relayout onto the 11 numbered sheets (Amendment 2)
def lcol(is_label, c):
    """Old column -> new column: on label sheets column B is the readable label, so every column after A moves right by one."""
    if not is_label:
        return c
    return 1 if c == 1 else c + 1


def new_workbook():
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    wb._fonts = IndexedList([LS.xl_font("body")])            # default font = Gill Sans MT
    wb._named_styles["Normal"].font = LS.xl_font("body")
    wb._colors = []                                           # no indexed-colour table in styles.xml (palette only)
    return wb


def link(ws, row, col, text, target_sheet):
    cell = ws.cell(row=row, column=col, value=text)
    cell.hyperlink = Hyperlink(ref=cell.coordinate, location=f"'{target_sheet}'!A1", display=text)
    return cell


def band_and_title(ws):
    sid = DM.SHEET_ID[ws.title]
    ws.cell(row=1, column=1, value=f"GUIDE {LS.ARROW} §{sid}")
    prev, nxt = DM.prev_next(ws.title)
    if ws.title != DM.SHEET_NAMES[0]:
        link(ws, 1, LINK_COL_OVERVIEW, DM.SHEET_NAMES[0], DM.SHEET_NAMES[0])
    if prev:
        link(ws, 1, LINK_COL_PREV, f"Prev {DM.SHEET_ID[prev]}", prev)
    if nxt:
        link(ws, 1, LINK_COL_NEXT, f"Next {DM.SHEET_ID[nxt]}", nxt)
    ws.cell(row=2, column=1).value = CellRichText(
        TextBlock(InlineFont(rFont=LS.HEAD_FONT, sz=LS.NUMERAL_PT, b=True, color=LS.VERMILION), sid),
        TextBlock(InlineFont(rFont=LS.HEAD_FONT, sz=LS.TITLE_PT, color=LS.INK), "  " + DM.TITLE_OF_ID[sid]))


def build_overview(ws, sentence):
    ws.cell(row=OV_HEADLINE_ROW, column=1, value=sentence)
    ws.cell(row=OV_NOTE_ROWS[0], column=1, value=f"Process guide: report/{GUIDE_FILE}. Guide sections carry the same ids as the "
            "sheets below; the band in row 1 of every sheet names its section.")
    ws.cell(row=OV_NOTE_ROWS[1], column=1, value=f"Investment note: report/{NOTE_FILE}. Each figure in the note carries the id of "
            "the sheet it comes from, for example [3.2].")
    for i, lab in enumerate(OV_HEADERS):
        ws.cell(row=OV_HEADER_ROW, column=1 + i, value=lab)
    row = OV_HEADER_ROW
    for sid, name, _title in DM.SHEETS[1:]:
        row += 1
        link(ws, row, 1, name, name)
        ws.cell(row=row, column=2, value=f"§{sid}")
        ws.cell(row=row, column=C3, value=OV_TEXT[sid])
    ws.cell(row=OV_AUTHOR_ROW, column=1, value=DM.AUTHOR_LINE)
    for letter, w in OV_WIDTHS.items():
        ws.column_dimensions[letter].width = w


def _rich(text, kind, size, bold=False):
    """Rich text title with the Ledger font (headings Garamond, body Gill Sans MT)."""
    face = LS.HEAD_FONT if kind == "head" else LS.BODY_FONT
    cp = CharacterProperties(latin=Font(typeface=face), sz=int(size * CHART_PT_SCALE), b=bold, solidFill=LS.INK)
    run = RegularTextRun(rPr=cp, t=text)
    return Title(tx=Text(rich=RichText(p=[Paragraph(pPr=ParagraphProperties(defRPr=cp), r=[run])])), overlay=False)


def _txpr(kind, size):
    face = LS.HEAD_FONT if kind == "head" else LS.BODY_FONT
    cp = CharacterProperties(latin=Font(typeface=face), sz=int(size * CHART_PT_SCALE), solidFill=LS.INK)
    return RichText(p=[Paragraph(pPr=ParagraphProperties(defRPr=cp), endParaRPr=cp)])


def chart_fonts(chart):
    """Chart title Garamond, axis titles and tick labels Gill Sans MT (same ink as the series)."""
    chart.title = _rich(HIST_TITLE, "head", LS.SUBTITLE_PT)
    chart.y_axis.title = _rich("Runs", "body", LS.SMALL_PT)
    chart.x_axis.title = _rich("Value per share, bin lower edge (EUR)", "body", LS.SMALL_PT)
    chart.x_axis.txPr = _txpr("body", LS.SMALL_PT)
    chart.y_axis.txPr = _txpr("body", LS.SMALL_PT)


def add_chart(ws, hh, nh):
    chart = BarChart()
    chart.type = "col"
    chart.title = HIST_TITLE
    chart.y_axis.title = "Runs"
    chart.x_axis.title = "Value per share, bin lower edge (EUR)"
    chart.x_axis.delete = False
    chart.y_axis.delete = False
    chart.legend = None
    chart.width, chart.height = CHART_W, CHART_H
    chart.gapWidth = CHART_GAP
    count_col = lcol(True, C3)
    data = Reference(ws, min_col=count_col, min_row=hh, max_row=hh + nh)
    cats = Reference(ws, min_col=1, min_row=hh + 1, max_row=hh + nh)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.series[0].graphicalProperties = GraphicalProperties(solidFill=LS.INK)
    chart.series[0].graphicalProperties.line.solidFill = LS.INK
    chart.y_axis.majorGridlines = None
    chart_fonts(chart)
    ws.add_chart(chart, CHART_ANCHOR)


def relayout(old, sentence):
    wb = new_workbook()
    sheets = {n: wb.create_sheet(n) for n in DM.SHEET_NAMES}
    info = {n: {"headers": {}, "sections": set(), "notes": set(), "ctx": {}} for n in DM.SHEET_NAMES}
    val = old["Valuation"]
    r_h = next(r for r in range(1, val.max_row + 1) if val.cell(row=r, column=1).value == DM.BRIDGE_HEADER)
    r_end = r_h
    while val.cell(row=r_end + 1, column=1).value not in (None, ""):
        r_end += 1

    def target(oname, r):
        if oname == "Valuation" and r_h <= r <= r_end:
            return DM.BRIDGE_SHEET, r - r_h + HDR_ROW_22
        if oname == "Valuation" and r > r_end:
            # step 9 (Amendment 3): the rows below the moved block close up behind the pointer (old 77 -> 3.2 row 61)
            return DM.OLD_TO_NEW[oname], r + ROW_SHIFT - (r_end - r_h)
        return DM.OLD_TO_NEW[oname], r + ROW_SHIFT

    for oname, nname in DM.OLD_TO_NEW.items():
        ows = old[oname]
        for row in ows.iter_rows():
            for cell in row:
                if cell.value is None:
                    continue
                tname, tr = target(oname, cell.row)
                dst = sheets[tname].cell(row=tr, column=lcol(tname in DM.LABEL_SHEETS, cell.column))
                dst.value = DM.reword(cell.value) if isinstance(cell.value, str) else cell.value
                dst.number_format = cell.number_format
        for c in range(1, ows.max_column + 1):
            w = ows.column_dimensions[get_column_letter(c)].width
            for tname in [nname] + ([DM.BRIDGE_SHEET] if oname == "Valuation" else []):
                sheets[tname].column_dimensions[get_column_letter(lcol(tname in DM.LABEL_SHEETS, c))].width = w
        for r, last in REG["headers"].get(oname, {}).items():
            tname, tr = target(oname, r)
            info[tname]["headers"][tr] = lcol(tname in DM.LABEL_SHEETS, last)
        for kind in ("sections", "notes"):
            for r in REG[kind].get(oname, set()):
                tname, tr = target(oname, r)
                info[tname][kind].add(tr)
    sens = REG["ctx"]["Sensitivity"]
    r0, c0, r1, c1 = sens["sens_grid"]
    info["4.1 Sensitivity"]["ctx"]["sens_grid"] = (r0 + ROW_SHIFT, c0, r1 + ROW_SHIFT, c1)
    info["4.1 Sensitivity"]["ctx"]["sens_base"] = (sens["sens_base"][0] + ROW_SHIFT, sens["sens_base"][1])

    # readable-label column B on the label sheets
    for tname in DM.LABEL_SHEETS:
        ws = sheets[tname]
        ws.column_dimensions["B"].width = LABEL_W
        for r in range(1, ws.max_row + 1):
            a = ws.cell(row=r, column=1).value
            if isinstance(a, str):
                if a in DM.LABEL_KEY_HEADERS:
                    ws.cell(row=r, column=2, value=DM.LABEL_HEADER)
                elif a in DM.LABELS:
                    ws.cell(row=r, column=2, value=DM.label_for(tname, a))

    # 2.2 Bridge Inputs: description in row 3; 3.2 Valuation: pointer where the block used to be
    sheets[DM.BRIDGE_SHEET].cell(row=ROW_SHIFT + 1, column=1, value=BRIDGE_DESC)
    pr = r_h + ROW_SHIFT
    link(sheets["3.2 Valuation"], pr, 1, BRIDGE_POINTER, DM.BRIDGE_SHEET)
    info["3.2 Valuation"]["notes"].add(pr)

    # equity bridge range on 3.2 (ev down to value per share, searched below the valuation table header)
    ws = sheets["3.2 Valuation"]
    first = last = None
    for r in range(REG["ctx"]["Valuation"]["val_table_hdr"] + ROW_SHIFT + 1, ws.max_row + 1):
        v = ws.cell(row=r, column=1).value
        if v == "ev" and first is None:
            first = r
        if v == "value_per_share" and first is not None:
            last = r
            break
    info["3.2 Valuation"]["ctx"]["bridge"] = (first, last)
    info["3.2 Valuation"]["ctx"]["bridge_cols"] = lcol(True, VAL_COLS)

    # overview, bands, titles, links
    build_overview(sheets[DM.SHEET_NAMES[0]], sentence)
    info[DM.SHEET_NAMES[0]]["headers"][OV_HEADER_ROW] = len(OV_HEADERS)
    info[DM.SHEET_NAMES[0]]["notes"].update(OV_NOTE_ROWS)
    for name in DM.SHEET_NAMES:
        band_and_title(sheets[name])

    # chart on 4.2 Monte Carlo
    hh, nh = REG["ctx"]["MonteCarlo"]["hist"]
    add_chart(sheets["4.2 Monte Carlo"], hh + ROW_SHIFT, nh)

    for name in DM.SHEET_NAMES:
        RS.style_sheet(sheets[name], info[name])
    # author line on 0.0: small grey body text on one line (overflows to the right), no rule, no link
    ov_ws = sheets[DM.SHEET_NAMES[0]]
    for col in range(1, ov_ws.max_column + 1):
        ov_ws.cell(row=OV_AUTHOR_ROW, column=col).border = Border()
    author = ov_ws.cell(row=OV_AUTHOR_ROW, column=1)
    author.font = LS.xl_font("body", LS.SMALL_PT, color=LS.GREY)
    author.alignment = RS.AL_TXT
    return wb


# ---------------------------------------------------------------- main
def main():
    step_results = run_step_checks()
    det = determinism_runs()
    con = duckdb.connect(str(DB))
    try:
        sentence, hl = build_headline(con)
        old = openpyxl.Workbook()
        old.remove(old.active)
        sheet_statements(old, con)
        sheet_adjust_ratios(old, con)
        sheet_forecast(old, con)
        sheet_wacc(old, con)
        sheet_valuation(old, con, sentence, hl)
        sheet_sensitivity(old, con)
        sheet_montecarlo(old, con)
        sheet_multiples(old, con)
        failed = sheet_checks(old, con, step_results, det)
        wb = relayout(old, sentence)
        wb.properties.creator = DM.AUTHOR_NAME
        wb.properties.lastModifiedBy = DM.AUTHOR_NAME
        wb.properties.created = FIXED_DATETIME
        wb.properties.modified = FIXED_DATETIME
        OUT.parent.mkdir(parents=True, exist_ok=True)
        wb.save(OUT)
    finally:
        con.close()
    print(f"Headline: {sentence}")
    print(f"Workbook written: {OUT.relative_to(ROOT)} ({len(wb.sheetnames)} sheets); failed checks on Checks sheet: {len(failed)}")
    for f in failed:
        print("  FAIL:", f)
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
