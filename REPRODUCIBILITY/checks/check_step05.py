"""Acceptance checks for step 5 (plan/plan.md): the Excel report report/DeLonghi_DCF_Valuation.xlsx.

Every check prints PASS/FAIL with actual vs expected; exit code 1 if any check fails.

What is checked (plan step 5):
  - sheets exactly and in order; headline sentence at the top of Valuation, equal to report_headline and to a sentence
    rebuilt here from valuation / wacc / mc_summary / bridge_inputs at the stated precision
  - no formulas; py/05_build_report.py reads only DuckDB (AST scan: no numeric literals outside named constants)
  - round-trip: every numeric cell (all sheets except Checks) equals a source-table value (|diff| < 1e-9), and the key
    source values are found at the expected label/column; number formats per the brief's precision rules
  - WACC sheet: inputs with sources, beta sensitivity line, Italy double-counting note; Valuation: minorities at book flag
  - Checks sheet: all PASS and all required reconciliations present; MonteCarlo sheet: percentile table, price percentile,
    one native bar chart, distribution parameters
The workbook is rebuilt by running py/05_build_report.py first (it needs the DuckDB tables of steps 1-4).

Amendment 2 (step 7): the workbook has 11 numbered sheets (py/doc_map.py). Every `wb["<old name>"]` goes through the fixed map
NEW; the sheets whose column A holds DuckDB keys carry a readable-label column B, so value columns are found by header name
instead of position; the bridge_inputs block is on 2.2 Bridge Inputs; the headline sits in '3.2 Valuation'!A3 and on 0.0 Overview.
No tolerance, expected value or check was removed.
"""
import ast
import bisect
import subprocess
import sys
from pathlib import Path

import duckdb
import openpyxl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from _lib import Checks  # noqa: E402

XLSX = ROOT / "report" / "DeLonghi_DCF_Valuation.xlsx"
SCRIPT = ROOT / "py" / "05_build_report.py"
STYLE_SCRIPTS = [ROOT / "py" / "report_style.py", ROOT / "py" / "ledger_style.py", ROOT / "py" / "doc_map.py"]
SHEETS = ["0.0 Overview", "1.1 Statements", "1.2 Adjustments & Ratios", "2.1 WACC", "2.2 Bridge Inputs", "3.1 FCFF Forecast",
          "3.2 Valuation", "3.3 Multiples Check", "4.1 Sensitivity", "4.2 Monte Carlo", "5.1 Checks"]
NEW = {"Statements_5Y": "1.1 Statements", "Adjustments_Ratios": "1.2 Adjustments & Ratios", "Forecast_FCFF": "3.1 FCFF Forecast",
       "WACC": "2.1 WACC", "Valuation": "3.2 Valuation", "Bridge": "2.2 Bridge Inputs", "Sensitivity": "4.1 Sensitivity",
       "MonteCarlo": "4.2 Monte Carlo", "Multiples_Check": "3.3 Multiples Check", "Checks": "5.1 Checks"}
TOL = 1e-9
FMT_M, FMT_SH, FMT_P1, FMT_P2, FMT_X = "#,##0", "0.00", "0.0%", "0.00%", '0.0"x"'

# ------------------------------------------------------------------ 0. build the workbook (no DB connection open here)
built_ok = False
try:
    r = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
    built_ok = r.returncode == 0
    if not built_ok:
        print(r.stdout[-3000:], r.stderr[-3000:])
except Exception as e:
    print(f"ERROR running {SCRIPT}: {e!r}")

c = Checks()
c.equal("py/05_build_report.py runs without error", built_ok, True)
if not (built_ok and XLSX.exists()):
    c.equal("workbook exists", XLSX.exists(), True)
    c.done()

wb = openpyxl.load_workbook(XLSX)  # formulas visible (not data_only)
con = duckdb.connect(str(ROOT / "data" / "curiosity.duckdb"), read_only=True)


def q(sql):
    return con.execute(sql).fetchall()


def qd(sql):
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


# ------------------------------------------------------------------ helpers to navigate by label
def header_row(ws, label, col=1):
    for row in range(1, ws.max_row + 1):
        if ws.cell(row, col).value == label:
            return row
    return None


def header_map(ws, hr):
    return {ws.cell(hr, col).value: col for col in range(1, ws.max_column + 1) if ws.cell(hr, col).value is not None}


def row_of(ws, hr, label, col=1):
    for row in range(hr + 1, ws.max_row + 1):
        if ws.cell(row, col).value == label:
            return row
    return None


def get(ws, hlabel, rlabel, clabel):
    """cell at (row labelled rlabel under header row hlabel, column whose header is clabel)"""
    hr = header_row(ws, hlabel)
    if hr is None:
        return None
    cm = header_map(ws, hr)
    rr = row_of(ws, hr, rlabel)
    if rr is None or clabel not in cm:
        return None
    return ws.cell(rr, cm[clabel])


def val_close(cell, expected):
    if cell is None or cell.value is None or expected is None:
        return False
    return isinstance(cell.value, (int, float)) and abs(cell.value - expected) < TOL


# ------------------------------------------------------------------ 1. sheets, order
c.equal("sheet names and order", wb.sheetnames, SHEETS)

# ------------------------------------------------------------------ 2. no formulas
formula_cells = 0
for ws in wb.worksheets:
    for row in ws.iter_rows():
        for cell in row:
            if cell.data_type == "f" or (isinstance(cell.value, str) and cell.value.startswith("=")):
                formula_cells += 1
c.equal("no formulas (cells with data_type f or text starting with '=')", formula_cells, 0)

# ------------------------------------------------------------------ 3. script reads only DuckDB: AST literal scan
src = SCRIPT.read_text(encoding="utf-8")
ALLOWED_INTS = {0, 1, 2}


def literal_scan(path):
    """Numeric literals outside module-level assignments to UPPER_CASE names (0, 1, 2 allowed as offsets)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    const_nodes = set()
    for node in tree.body:  # module-level assignments to UPPER_CASE names are the named constants
        if isinstance(node, ast.Assign) and all(
                all(isinstance(n, ast.Name) and n.id.isupper() for n in (t.elts if isinstance(t, ast.Tuple) else [t]))
                for t in node.targets):
            for sub in ast.walk(node):
                const_nodes.add(id(sub))
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            if id(node) in const_nodes:
                continue
            if isinstance(node.value, int) and node.value in ALLOWED_INTS:
                continue
            bad.append((node.lineno, node.value))
    return tree, bad


tree, bad = literal_scan(SCRIPT)
c.equal("py/05_build_report.py: no numeric literals outside named UPPER_CASE constants (0, 1, 2 allowed as offsets)", bad, [])
for sp in STYLE_SCRIPTS:
    c.equal(f"py/{sp.name}: no numeric literals outside named UPPER_CASE constants (0, 1, 2 allowed as offsets)", literal_scan(sp)[1], [])
c.equal("py/05_build_report.py reads DuckDB only (no pandas read_csv/read_excel, no open() of data files)",
        [w for w in ("read_csv", "read_excel", "read_parquet", "csv.reader") if w in src], [])
c.equal("py/05_build_report.py writes no formulas (no '=' string literal start)",
        [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
         and n.value.startswith("=")], [])

# ------------------------------------------------------------------ 4. headline sentence
V = {r["item"]: r["value"] for r in qd("SELECT item, value FROM valuation")}
W = qd("SELECT * FROM wacc WHERE \"case\" = 'base'")[0]
MC = qd("SELECT * FROM mc_summary")[0]
B = {r["item"]: r["value"] for r in qd("SELECT item, value FROM bridge_inputs")}


def ordinal(n):
    n = int(n)
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}" + {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


up = V["upside_pct"]
expected_sentence = (f"De'Longhi is worth EUR {V['value_per_share']:.2f} per share (DCF base case, WACC {W['wacc']:.2%}, "
                     f"g {V['terminal_g']:.2%}); the 80% Monte Carlo range is EUR {MC['p10']:.2f} to EUR {MC['p90']:.2f}; "
                     f"the market price of EUR {B['price']:.2f} sits at the {ordinal(round(MC['price_percentile']))} "
                     f"percentile, i.e. {abs(up):.1%} {'above' if up > 0 else 'below'} the base-case value.")
print("INFO  expected sentence:", expected_sentence)
hl = qd("SELECT * FROM report_headline")
hl_sentence = [r for r in hl if r["key"] == "sentence"]
c.equal("report_headline has exactly one 'sentence' row", len(hl_sentence), 1)
c.equal("report_headline sentence = sentence rebuilt from valuation, wacc, mc_summary, bridge_inputs",
        hl_sentence[0]["display"] if hl_sentence else None, expected_sentence)
ws = wb[NEW["Valuation"]]
c.equal("'3.2 Valuation'!A3 = headline sentence (top of sheet)", ws["A3"].value, expected_sentence)
c.equal("'0.0 Overview'!A3 = headline sentence", wb[SHEETS[0]]["A3"].value, expected_sentence)
HK = {r["key"]: r for r in hl}
for key, expect in [("value_per_share", V["value_per_share"]), ("wacc", W["wacc"]), ("g", V["terminal_g"]),
                    ("mc_p10", MC["p10"]), ("mc_p90", MC["p90"]), ("price", B["price"]),
                    ("price_percentile", MC["price_percentile"]), ("pct_vs_base", up)]:
    c.near(f"report_headline.{key} = source value", HK[key]["value"] if key in HK else None, expect, rel=1e-12)

# ------------------------------------------------------------------ 5. round-trip: every numeric cell is a source value
SOURCE_TABLES = ["hist_statements", "hist_adjustments", "hist_ratios", "forecast_assumptions", "forecast_fcff",
                 "wacc_inputs", "wacc", "bridge_inputs", "valuation", "multiples_check", "sensitivity",
                 "beta_sensitivity", "mc_params", "mc_summary", "mc_histogram", "report_headline"]
pool = []
for t in SOURCE_TABLES:
    for row in q(f"SELECT * FROM {t}"):
        for v in row:
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                pool.append(float(v))
pool.sort()


def in_pool(x):
    i = bisect.bisect_left(pool, x - TOL)
    return i < len(pool) and abs(pool[i] - x) < TOL


for name in SHEETS[1:-1]:      # 1.1 to 4.2 (Overview has no numbers, Checks holds the tolerances)
    ws = wb[name]
    n_num = unmatched = 0
    first_bad = None
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool):
                n_num += 1
                if not in_pool(float(cell.value)):
                    unmatched += 1
                    first_bad = first_bad or (cell.coordinate, cell.value)
    print(f"INFO  {name}: {n_num} numeric cells")
    c.equal(f"round-trip {name}: numeric cells not equal to any source-table value (|diff| < 1e-9)", (unmatched, first_bad), (0, None))
    c.between(f"{name} has numeric cells", n_num, 1, 10**6)

# --- targeted lookups: value at label/column equals source and number format is right
ws = wb[NEW["Statements_5Y"]]
bad = fmt_bad = 0
n = 0
for r in qd("SELECT fy, statement, line_item, value_eur_m FROM hist_statements"):
    cell = None
    hr = header_row(ws, "Statement")
    cm = header_map(ws, hr)
    for row in range(hr + 1, ws.max_row + 1):
        if ws.cell(row, 1).value == r["statement"] and ws.cell(row, 2).value == r["line_item"]:
            cell = ws.cell(row, cm[f"FY{r['fy']}"])
            break
    n += 1
    if not val_close(cell, r["value_eur_m"]):
        bad += 1
    elif cell.number_format != FMT_M:
        fmt_bad += 1
c.equal(f"1.1 Statements: all {n} hist_statements values at (statement, line item, FY) equal source", bad, 0)
c.equal("1.1 Statements: number format '#,##0' on all of them", fmt_bad, 0)
c.equal("1.1 Statements: BS has a FY2020 column, header FY2020..FY2025",
        [ws.cell(header_row(ws, "Statement"), col).value for col in range(3, 9)],
        ["FY2020", "FY2021", "FY2022", "FY2023", "FY2024", "FY2025"])

ws = wb[NEW["Adjustments_Ratios"]]
hr = header_row(ws, "Ratio")
cm = header_map(ws, hr)
bad = fmt_bad = n = 0
PCT_COLS = {"growth", "adj_ebit_margin", "da_pct", "capex_pct", "capex_excl_rou_pct", "nwc_pct", "eff_tax_rate"}
for r in qd("SELECT * FROM hist_ratios"):
    for k, v in r.items():
        if k in ("fy", "tax_included"):
            continue
        cell = None
        rr = row_of(ws, hr, k)
        if rr:
            cell = ws.cell(rr, cm[f"FY{r['fy']}"])
        n += 1
        if not val_close(cell, v):
            bad += 1
        elif cell.number_format != (FMT_P1 if k in PCT_COLS else FMT_M):
            fmt_bad += 1
c.equal(f"1.2 Adjustments & Ratios: all {n} hist_ratios values equal source", bad, 0)
c.equal("1.2 Adjustments & Ratios: ratio formats (% to 1 decimal, EUR m no decimals)", fmt_bad, 0)
ah = header_row(ws, "FY")
acm = header_map(ws, ah)          # value columns are found by header name (column B is the label column on this sheet)
adj_rows = [ws.cell(rr, acm["Amount (EUR m)"]).value for rr in range(ah + 1, hr)
            if isinstance(ws.cell(rr, acm["Amount (EUR m)"]).value, (int, float))]
c.equal("1.2 Adjustments & Ratios: adjustment amounts = hist_adjustments (sorted)",
        sorted(round(x, 9) for x in adj_rows),
        sorted(round(r[0], 9) for r in q("SELECT amount_eur_m FROM hist_adjustments")))
c.equal("1.2 Adjustments & Ratios: adjustments carry doc and page (no empty source cells)",
        sum(1 for rr in range(ah + 1, ah + 1 + q("SELECT COUNT(*) FROM hist_adjustments")[0][0])
            if ws.cell(rr, acm["Document"]).value is None or ws.cell(rr, acm["PDF page"]).value is None), 0)

ws = wb[NEW["Forecast_FCFF"]]
hr = header_row(ws, "Line item")
cm = header_map(ws, hr)
bad = fmt_bad = n = 0
for r in qd("SELECT * FROM forecast_fcff"):
    for k, v in r.items():
        if k == "fy" or v is None:
            continue
        rr = row_of(ws, hr, k)
        cell = ws.cell(rr, cm[f"FY{r['fy']}E"]) if rr else None
        n += 1
        if not val_close(cell, v):
            bad += 1
        elif cell.number_format != (FMT_P1 if k in ("growth", "adj_ebit_margin", "tax_rate") else FMT_M):
            fmt_bad += 1
c.equal(f"3.1 FCFF Forecast: all {n} forecast_fcff values equal source", bad, 0)
c.equal("3.1 FCFF Forecast: formats (% 1 decimal, EUR m 0 decimals)", fmt_bad, 0)
ah = header_row(ws, "Driver")
fcm = header_map(ws, ah)
nA = q("SELECT COUNT(*) FROM forecast_assumptions")[0][0]
c.equal("3.1 FCFF Forecast: assumptions block lists every driver with non-empty rule, source and note",
        sum(1 for rr in range(ah + 1, ah + 1 + nA)
            if not (ws.cell(rr, 1).value and ws.cell(rr, fcm["Rule"]).value and ws.cell(rr, fcm["Source"]).value
                    and ws.cell(rr, fcm["Note"]).value)), 0)
c.equal("3.1 FCFF Forecast: driver names equal forecast_assumptions",
        [ws.cell(rr, 1).value for rr in range(ah + 1, ah + 1 + nA)],
        [r[0] for r in q("SELECT driver FROM forecast_assumptions")])

# --- WACC
ws = wb[NEW["WACC"]]
ih = header_row(ws, "Input")
icm = header_map(ws, ih)
nI = q("SELECT COUNT(*) FROM wacc_inputs")[0][0]
bad = 0
for i, r in enumerate(qd("SELECT * FROM wacc_inputs")):
    rr = ih + 1 + i
    if ws.cell(rr, 1).value != r["input"] or not val_close(ws.cell(rr, icm["Value"]), r["value"]) or not ws.cell(rr, icm["Source"]).value:
        bad += 1
c.equal(f"2.1 WACC: all {nI} inputs shown with value and a source", bad, 0)
rfc = get(ws, "Input", "rf", "Value")
c.equal("2.1 WACC: rf displayed as 0.00%", rfc.number_format if rfc else None, FMT_P2)
wh = header_row(ws, "Item")
cm = header_map(ws, wh)
bad = 0
for r in qd("SELECT * FROM wacc"):
    for k, v in r.items():
        if k == "case":
            continue
        rr = row_of(ws, wh, k)
        if not (rr and val_close(ws.cell(rr, cm[r["case"]]), v)):
            bad += 1
c.equal("2.1 WACC: both wacc rows (base, beta_sensitivity) equal source for every column", bad, 0)
wc = get(ws, "Item", "wacc", "base")
c.equal("2.1 WACC: base wacc number format 0.00%", wc.number_format if wc else None, FMT_P2)
bs = qd("SELECT * FROM beta_sensitivity")[0]
c.equal("2.1 WACC: beta sensitivity line present with value per share = source",
        val_close(get(ws, "Beta sensitivity line", "value_per_share", "Value"), bs["value_per_share"]), True)
alltext = " ".join(str(cell.value) for row in ws.iter_rows() for cell in row if isinstance(cell.value, str)).lower()
c.equal("2.1 WACC: limitation note on Italy risk double counting", "double count" in alltext and "italy" in alltext, True)
c.equal("2.1 WACC: note on low Europe industry beta", "low" in alltext and "beta" in alltext and "europe" in alltext, True)

# --- Valuation
ws = wb[NEW["Valuation"]]
vh = header_row(ws, "Item")
cm = header_map(ws, vh)
bad = n = 0
FMT_BY_ITEM = {"wacc": FMT_P2, "terminal_g": FMT_P2, "tv_share_of_ev": FMT_P1, "upside_pct": FMT_P1,
               "value_per_share": FMT_SH, "price": FMT_SH, "ev": FMT_M, "equity_value": FMT_M, "sum_pv_fcff": FMT_M,
               "pv_tv": FMT_M, "minority_book": FMT_M, "cash": FMT_M, "tv_gordon": FMT_M}
fmt_bad = []
for r in qd("SELECT * FROM valuation"):
    rr = row_of(ws, vh, r["item"])
    cell = ws.cell(rr, cm["Value"]) if rr else None
    n += 1
    if not val_close(cell, r["value"]):
        bad += 1
    elif r["item"] in FMT_BY_ITEM and cell.number_format != FMT_BY_ITEM[r["item"]]:
        fmt_bad.append((r["item"], cell.number_format))
c.equal(f"3.2 Valuation: all {n} valuation lines equal source", bad, 0)
c.equal("3.2 Valuation: number formats on key lines (WACC/g 0.00%, EUR/share 0.00, % 0.0%, EUR m #,##0)", fmt_bad, [])
mrow = row_of(ws, vh, "minority_book")
c.equal("3.2 Valuation: minorities at book line carries the SIMPLIFICATION flag",
        bool(mrow) and "SIMPLIFICATION" in str(ws.cell(mrow, cm["Note"]).value).upper(), True)
vtext = " ".join(str(cell.value) for row in ws.iter_rows() for cell in row if isinstance(cell.value, str)).upper()
c.equal("3.2 Valuation: explicit simplification flag text for minorities at book", "MINORITIES AT BOOK" in vtext, True)
mh = header_row(ws, "Region")
cmm = header_map(ws, mh)
c.equal("3.2 Valuation: exit-multiple cross-check block shows Gordon vs exit % difference",
        all(val_close(ws.cell(mh + 1 + i, cmm["pct_vs_gordon"]), r[0])
            for i, r in enumerate(q("SELECT pct_vs_gordon FROM multiples_check"))), True)
wsb = wb[NEW["Bridge"]]
bh = header_row(wsb, "Bridge input")
bcm = header_map(wsb, bh)
nb = q("SELECT COUNT(*) FROM bridge_inputs")[0][0]
c.equal("2.2 Bridge Inputs: block lists all items with a source (and the items equal bridge_inputs)",
        (sum(1 for i in range(nb) if not wsb.cell(bh + 1 + i, bcm["Source"]).value),
         [wsb.cell(bh + 1 + i, 1).value for i in range(nb)]),
        (0, [r[0] for r in q("SELECT item FROM bridge_inputs ORDER BY rowid")]))
c.equal("3.2 Valuation: bridge block is no longer on 3.2", header_row(ws, "Bridge input"), None)
hh = header_row(ws, "Headline numbers")
hcm = header_map(ws, hh)
c.equal("3.2 Valuation: headline numbers block equals report_headline (excl. sentence)",
        all(val_close(ws.cell(row_of(ws, hh, k), hcm["Value"]), v["value"]) for k, v in HK.items() if k != "sentence"), True)

# --- Sensitivity
ws = wb[NEW["Sensitivity"]]
sh = header_row(ws, "WACC \\ g")
cm = {ws.cell(sh, col).value: col for col in range(2, 7)}
bad = fmt_bad = n = 0
for r in qd("SELECT * FROM sensitivity"):
    cc = next((col for gv, col in cm.items() if abs(gv - r["g"]) < TOL), None)
    rr = next((row for row in range(sh + 1, sh + 6) if abs(ws.cell(row, 1).value - r["wacc"]) < TOL), None)
    n += 1
    if cc is None or rr is None or not val_close(ws.cell(rr, cc), r["value_per_share"]):
        bad += 1
    elif ws.cell(rr, cc).number_format != FMT_SH or ws.cell(rr, 1).number_format != FMT_P2 or ws.cell(sh, cc).number_format != FMT_P2:
        fmt_bad += 1
c.equal(f"4.1 Sensitivity: all {n} grid cells at (WACC row, g column) equal source", bad, 0)
c.equal("4.1 Sensitivity: formats (axes 0.00%, cells 0.00)", fmt_bad, 0)
c.equal("4.1 Sensitivity: beta sensitivity line shown",
        val_close(get(ws, "Beta sensitivity line", "value_per_share", "Value"), bs["value_per_share"]), True)

# --- MonteCarlo
ws = wb[NEW["MonteCarlo"]]
th = header_row(ws, "Statistic")
tcm = header_map(ws, th)
bad = 0
for k, v in MC.items():
    rr = row_of(ws, th, k)
    if not (rr and val_close(ws.cell(rr, tcm["Value"]), v)):
        bad += 1
c.equal("4.2 Monte Carlo: percentile table (p5..p95), mean, sd, price, price percentile, base, run 0 equal mc_summary", bad, 0)
c.equal("4.2 Monte Carlo: p10 format 0.00 and price percentile format 0.0",
        (ws.cell(row_of(ws, th, "p10"), tcm["Value"]).number_format,
         ws.cell(row_of(ws, th, "price_percentile"), tcm["Value"]).number_format),
        (FMT_SH, "0.0"))
ph = header_row(ws, "Parameter")
pcm = header_map(ws, ph)
c.equal("4.2 Monte Carlo: distribution parameters equal mc_params",
        all(val_close(ws.cell(ph + 1 + i, pcm["Value"]), r[0]) for i, r in enumerate(q("SELECT value FROM mc_params"))), True)
hh = header_row(ws, "Bin low")
hcm = header_map(ws, hh)
nh = q("SELECT COUNT(*) FROM mc_histogram")[0][0]
c.equal("4.2 Monte Carlo: histogram rows equal mc_histogram (bin_lo, bin_hi, count)",
        [(ws.cell(hh + 1 + i, hcm["Bin low"]).value, ws.cell(hh + 1 + i, hcm["Bin high"]).value,
          ws.cell(hh + 1 + i, hcm["Count"]).value) for i in range(nh)],
        [tuple(r) for r in q("SELECT bin_lo, bin_hi, count FROM mc_histogram ORDER BY bin_id")])
charts = ws._charts
c.equal("4.2 Monte Carlo: exactly 1 native chart, a bar chart", [type(ch).__name__ for ch in charts], ["BarChart"])
c.equal("4.2 Monte Carlo: histogram counts sum to 10,000",
        sum(ws.cell(hh + 1 + i, hcm["Count"]).value for i in range(nh)), q("SELECT n_runs FROM mc_summary")[0][0])

# --- Multiples_Check
ws = wb[NEW["Multiples_Check"]]
mh = header_row(ws, "region")
cm = header_map(ws, mh)
bad = fmt_bad = n = 0
for i, r in enumerate(qd("SELECT * FROM multiples_check")):
    for k, v in r.items():
        if isinstance(v, (int, float)):
            n += 1
            cell = ws.cell(mh + 1 + i, cm[k])
            if not val_close(cell, v):
                bad += 1
            elif k in ("ev_ebitda", "implied_gordon_ev_ebitda") and cell.number_format != FMT_X:
                fmt_bad += 1
c.equal(f"3.3 Multiples Check: all {n} numeric values equal multiples_check", bad, 0)
c.equal("3.3 Multiples Check: multiples formatted 0.0\"x\"", fmt_bad, 0)
c.equal("3.3 Multiples Check: Europe ev_ebitda = 9.452668 exactly",
        round(ws.cell(mh + 1, cm["ev_ebitda"]).value, 6), 9.452668)

# --- Checks sheet
ws = wb[NEW["Checks"]]
ch = header_row(ws, "Check")
rows = []
for row in range(ch + 1, ws.max_row + 1):
    if ws.cell(row, 1).value:
        rows.append((ws.cell(row, 1).value, ws.cell(row, 6).value))
print(f"INFO  Checks sheet has {len(rows)} rows")
c.equal("Checks sheet: every row is PASS", [r for r in rows if r[1] != "PASS"], [])
names = " | ".join(r[0] for r in rows).lower()
for needle in ["balance sheet balances", "cash flow reconciles", "fcff identity", "ev = sum pv", "sensitivity centre",
               "mc run 0", "determinism", "check_step01", "check_step04"]:
    c.equal(f"Checks sheet lists '{needle}'", needle in names, True)
c.between("Checks sheet: 6 BS year-ends + 5 CF years + forecast + others", len(rows), 25, 200)
for needle, n_expect in [("balance sheet balances", 6), ("cash flow reconciles", 5), ("fcff identity", 5)]:
    c.equal(f"Checks sheet: '{needle}' appears once per year", sum(1 for r in rows if needle in r[0].lower()), n_expect)

# independent recomputation of two of them
c.near("independent: max |total assets - total net equity and liabilities| over 6 year-ends <= 0.002",
       min(q("""SELECT MAX(ABS(a.value_eur_m - b.value_eur_m)) FROM hist_statements a JOIN hist_statements b USING (fy)
                WHERE a.line_item = 'total assets' AND b.line_item = 'total net equity and liabilities'""")[0][0], 0.002),
       q("""SELECT MAX(ABS(a.value_eur_m - b.value_eur_m)) FROM hist_statements a JOIN hist_statements b USING (fy)
            WHERE a.line_item = 'total assets' AND b.line_item = 'total net equity and liabilities'""")[0][0], rel=1e-12)

# document properties are constant (idempotence)
c.equal("workbook creator set", wb.properties.creator is not None, True)

con.close()
c.done()
