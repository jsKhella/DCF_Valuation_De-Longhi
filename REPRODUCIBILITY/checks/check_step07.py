"""Acceptance checks for step 7 (plan/plan.md, Amendment 2): the workbook rebuilt on the shared Ledger style.

Every check prints PASS/FAIL with actual vs expected; exit code 1 if any check fails.

What is checked (plan step 7):
  Baseline  the 4 snapshot files in verify/baseline_amend2/ equal `git show 59ecd69:<path>`; xlsx_cells.txt equals verify/xlsx_dump_run1.txt
  Sheets    the 11 names in R-A order
  Values    every non-empty baseline cell equals its mapped new cell (value, type, number format), with the stated exceptions;
            1,237 numeric cells on 1.1-5.1, none on 0.0; 5.1 rows identical to the baseline (65, all PASS)
  Labels    column-B rule on the 6 label sheets; no inserted column elsewhere
  Formulas  0
  Links     internal hyperlinks exist and resolve; every sheet links to 0.0; prev/next follow R-A order
  Bands     row 1 reads "GUIDE ▸ §<id>"; the headline on 0.0 and 3.2 equals report_headline
  Layout    freeze panes, fit to width, landscape when wide
  Fonts     Garamond / Gill Sans MT only; palette only in styles.xml and the chart; no hex literal outside py/ledger_style.py
  Chart     one native BarChart on 4.2 whose values equal mc_histogram.count
  Regression  check_step01-06 pass counts; fingerprint.py unchanged; two fresh runs give the 24 fingerprints and identical workbooks
  Banned phrases and visual render (PNG per page, band id on a page for every sheet)
Step 9 (Amendment 3), non-weakening edits: F1 the rows of 3.2 below the moved bridge block close up (old row r -> r + 2 - (r_end_old -
r_h_old), so old 77 -> 61); F2 the baseline text equals doc_map.reword(old) with exactly 8 reworded cells; F3 the banned list is
checks/banned.py; F4 layout assertions for 3.2 (max_row 61, row 60 empty, flag merge, style and height).
The determinism runs delete and rebuild data/curiosity.duckdb (run.py --fresh --through 5) before any DB connection is opened.
"""
import ast
import bisect
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "py"))
sys.stdout.reconfigure(encoding="utf-8")
from _lib import Checks  # noqa: E402
import doc_map as DM  # noqa: E402
import ledger_style as LS  # noqa: E402
from xlsx_dump import dump_lines  # noqa: E402
import banned as BN  # noqa: E402

import openpyxl  # noqa: E402
from openpyxl.cell.cell import MergedCell  # noqa: E402

PY = sys.executable
XLSX = ROOT / "report" / "DeLonghi_DCF_Valuation.xlsx"
BASE = ROOT / "verify" / "baseline_amend2"
BASE_FILES = ["DeLonghi_DCF_Valuation.xlsx", "DeLonghi_DCF_Valuation_note.docx", "DeLonghi_DCF_process_guide.pdf", "note_chart.png"]
BASELINE_COMMIT = "59ecd69"
RENDER_DIR = ROOT / "verify" / "render" / "step07"
SCRATCH = ROOT / "verify" / "scratch_step07"
EXPECTED_NUMERIC = 1237
EXPECTED_CHECK_ROWS = 65
MIN_PASS_STEP05 = 86
EXPECTED_STEP_COUNTS = {"01": 128, "02": 78, "03": 148, "04": 66}
MIN_PASS_STEP06 = 17          # step 8 added checks to check_step06.py (A4, tags); the floor stays at the step-7 count
HIST_BINS, HIST_RUNS = 54, 10000
WIDE_UNITS = 120
OVERVIEW = DM.SHEET_NAMES[0]
FIRST_HEADER = {"0.0 Overview": "Sheet", "1.1 Statements": "Statement", "1.2 Adjustments & Ratios": "FY", "2.1 WACC": "Input",
                "2.2 Bridge Inputs": "Bridge input", "3.1 FCFF Forecast": "Line item", "3.2 Valuation": "Headline numbers",
                "3.3 Multiples Check": "region", "4.1 Sensitivity": "WACC \\ g", "4.2 Monte Carlo": "Statistic", "5.1 Checks": "Check"}
BASE9 = ROOT / "verify" / "baseline_step09"
NAVY = ["1F3864", "2F5597", "EEF2F8"]
STEP8_FILES = {"06_build_note.py", "07_process_guide.py", "07_verify_guide.py"}   # restyled in step 8
KEY_RE = re.compile(r"^[a-z][A-Za-z0-9]*(_[A-Za-z0-9]+)*$")


def run(cmd, timeout=1500):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)


def counts(script):
    r = run([PY, str(HERE / script)])
    m = re.findall(r"(\d+)/(\d+) checks passed", r.stdout)
    return (int(m[-1][0]), int(m[-1][1]), r.returncode) if m else (0, 0, r.returncode)


def signature(path):
    """Values, number formats, styles, merges, links, sizes, freeze panes, chart anchors of a workbook (determinism)."""
    wb = openpyxl.load_workbook(path)
    out = []
    for ws in wb.worksheets:
        out.append((ws.title, "meta", ws.freeze_panes, sorted(str(r) for r in ws.merged_cells.ranges),
                    sorted((k, round(v.width or 0, 3), v.hidden) for k, v in ws.column_dimensions.items()),
                    sorted((k, v.height) for k, v in ws.row_dimensions.items() if v.height),
                    ws.page_setup.orientation, ws.page_setup.fitToWidth, ws.page_setup.fitToHeight,
                    [(ch.anchor._from.col, ch.anchor._from.row, ch.width, ch.height) for ch in ws._charts]))
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c, MergedCell):
                    continue
                hl = (c.hyperlink.location, c.hyperlink.ref) if c.hyperlink else None
                out.append((ws.title, c.coordinate, repr(c.value), c.number_format, c.font.name, c.font.sz, c.font.b, c.font.i,
                            c.font.color.rgb if c.font.color else None, c.fill.fgColor.rgb, c.alignment.horizontal,
                            c.alignment.wrap_text, c.border.bottom.style if c.border.bottom else None,
                            c.border.top.style if c.border.top else None, hl))
    return out


# ------------------------------------------------------------------ 0. runs that rebuild the database (before any connection)
runs_ok, sigs, fps_ok = [], [], []
for i in (1, 2):
    r = run([PY, str(ROOT / "run.py"), "--fresh", "--through", "5"])
    runs_ok.append(r.returncode)
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-2000:])
    fp = run([PY, str(HERE / "fingerprint.py"), "--compare", str(ROOT / "verify" / "fp_step06.txt")]
             + [ln.split("\t")[0] for ln in (ROOT / "verify" / "fp_step06.txt").read_text(encoding="utf-8").split("\n") if ln])
    fps_ok.append((fp.returncode, fp.stdout.strip().splitlines()[-1] if fp.stdout.strip() else fp.stderr[-300:]))
    sigs.append(signature(XLSX) if XLSX.exists() else None)

step_counts = {n: counts(f"check_step{n}.py") for n in ["01", "02", "03", "04", "05", "06"]}   # 05 and 06 rebuild their files
render = run([PY, str(HERE / "render_png.py"), str(XLSX), "step07"])

# ------------------------------------------------------------------ 1. baseline
c = Checks()
for f in BASE_FILES:
    g = subprocess.run(["git", "show", f"{BASELINE_COMMIT}:report/{f}"], cwd=ROOT, capture_output=True)
    c.equal(f"baseline snapshot {f} is byte-identical to git show {BASELINE_COMMIT}:report/{f}",
            (BASE / f).read_bytes() == g.stdout and g.returncode == 0, True)
base_cells = (BASE / "xlsx_cells.txt").read_text(encoding="utf-8").splitlines()
run1 = (ROOT / "verify" / "xlsx_dump_run1.txt").read_text(encoding="utf-8").splitlines()
c.equal("baseline xlsx_cells.txt equals verify/xlsx_dump_run1.txt line for line", base_cells == run1, True)
c.equal("baseline xlsx_cells.txt line count (non-empty cells; the plan's 2,698 counts newline characters)", len(base_cells), 2699)
c.equal("baseline xlsx_cells.txt equals a fresh dump of the baseline workbook", dump_lines(BASE / BASE_FILES[0]) == base_cells, True)
sums = dict(ln.split(" *") [::-1] for ln in (BASE / "SHA256SUMS.txt").read_text().splitlines())
import hashlib  # noqa: E402
c.equal("SHA256SUMS.txt matches the 4 snapshot files",
        all(hashlib.sha256((BASE / k).read_bytes()).hexdigest() == v for k, v in sums.items()) and len(sums) == 4, True)
c.equal("baseline note_tokens.txt exists and is not empty", (BASE / "note_tokens.txt").stat().st_size > 0, True)

# ------------------------------------------------------------------ 2. sheets
new = openpyxl.load_workbook(XLSX)
old = openpyxl.load_workbook(BASE / BASE_FILES[0])
c.equal("workbook builds (last fresh run exit codes)", runs_ok, [0, 0])
c.equal("sheet names and order (R-A)", new.sheetnames, DM.SHEET_NAMES)
c.equal("sheet names are the 11 expected names", new.sheetnames, ["0.0 Overview", "1.1 Statements", "1.2 Adjustments & Ratios",
        "2.1 WACC", "2.2 Bridge Inputs", "3.1 FCFF Forecast", "3.2 Valuation", "3.3 Multiples Check", "4.1 Sensitivity",
        "4.2 Monte Carlo", "5.1 Checks"])

# ------------------------------------------------------------------ 3. values
ov = old["Valuation"]
r_h_old = next(r for r in range(1, ov.max_row + 1) if ov.cell(r, 1).value == DM.BRIDGE_HEADER)
r_end_old = r_h_old
while ov.cell(r_end_old + 1, 1).value not in (None, ""):
    r_end_old += 1
nb = new[DM.BRIDGE_SHEET]
r_h_new = next((r for r in range(1, nb.max_row + 1) if nb.cell(r, 1).value == DM.BRIDGE_HEADER), None)
c.equal("2.2 Bridge Inputs holds the bridge block header", r_h_new is not None, True)
print(f"INFO  old bridge block rows {r_h_old}-{r_end_old}; new header row {r_h_new}")


def mapped(sheet, r, col):
    """(new sheet, row, col) for an old cell, per the Design cell mapping."""
    label = lambda cc: 1 if cc == 1 else cc + 1  # noqa: E731
    if sheet == "Valuation" and r_h_old <= r <= r_end_old:
        return DM.BRIDGE_SHEET, r - r_h_old + r_h_new, label(col)
    if sheet == "Valuation" and r > r_end_old:      # F1: rows below the moved block close up behind the pointer (old 77 -> 61)
        return "3.2 Valuation", r + 2 - (r_end_old - r_h_old), label(col)
    ns = DM.OLD_TO_NEW[sheet]
    return ns, r + 2, (label(col) if ns in DM.LABEL_SHEETS else col)


bad, first_bad, n_cmp, n_title = [], None, 0, 0
changed_text, rule_used, digit_bad = [], {}, []
for ws in old.worksheets:
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell, MergedCell) or cell.value is None:
                continue
            ns, nr, nc = mapped(ws.title, cell.row, cell.column)
            tgt = new[ns].cell(nr, nc)
            if cell.row == 1 and ws.title != "Valuation":
                n_title += 1
                continue                                   # old row-1 title texts are the only exception
            n_cmp += 1
            exp = DM.reword(cell.value) if isinstance(cell.value, str) else cell.value        # F2: the only allowed text difference
            if not (tgt.value == exp and type(tgt.value) is type(cell.value) and tgt.number_format == cell.number_format):
                bad.append((ws.title, cell.coordinate, ns, tgt.coordinate, cell.value, tgt.value))
            if isinstance(cell.value, str) and tgt.value != cell.value:
                changed_text.append(f"{ns}!{tgt.coordinate}")
                for a_, _b in DM.TEXT_REWORDS:
                    if a_ in cell.value:
                        rule_used[a_] = rule_used.get(a_, 0) + 1
                if re.findall(r"\d+", cell.value) != re.findall(r"\d+", tgt.value):
                    digit_bad.append(f"{ns}!{tgt.coordinate}")
c.equal(f"every baseline cell ({n_cmp} compared, {n_title} old title texts exempt) equals its mapped new cell in value, type and number format",
        (len(bad), bad[:2]), (0, []))
c.equal("F2: exactly 8 text cells differ from their baseline text (2.2 H7, F13, F17, H17; 3.1 F26, F27, G30; 3.2 H46)",
        sorted(changed_text), ["2.2 Bridge Inputs!F13", "2.2 Bridge Inputs!F17", "2.2 Bridge Inputs!H17", "2.2 Bridge Inputs!H7",
                               "3.1 FCFF Forecast!F26", "3.1 FCFF Forecast!F27", "3.1 FCFF Forecast!G30", "3.2 Valuation!H46"])
c.equal("F2: each of the 6 reword rules is used at least once", sorted(a_ for a_, _b in DM.TEXT_REWORDS if not rule_used.get(a_)), [])
c.equal("F2: in each reworded cell the sequence of digit runs equals the old text", digit_bad, [])
c.equal("3.2 Valuation!A3 equals the baseline Valuation!A1 headline", new["3.2 Valuation"]["A3"].value, ov["A1"].value)

# F4: layout of 3.2 after the gap is closed (compared with the step-8 workbook in verify/baseline_step09)
v32, v32_prev = new["3.2 Valuation"], openpyxl.load_workbook(BASE9 / "DeLonghi_DCF_Valuation.xlsx")["3.2 Valuation"]
c.equal("F4: 3.2 max_row is 61 and nothing exists below row 61", (v32.max_row, [x.coordinate for r_ in v32.iter_rows(min_row=62) for x in r_ if x.value is not None]), (61, []))
c.equal("F4: 3.2 row 60 is empty", [x.value for x in v32[60]], [None] * v32.max_column)
c.equal("F4: 3.2 pointer stays at A59 with its link to 2.2 Bridge Inputs", (v32["A59"].hyperlink.location if v32["A59"].hyperlink else None),
        "'2.2 Bridge Inputs'!A1")
flag_new, flag_prev = v32["A61"], v32_prev["A79"]
c.equal("F4: the flag A61 equals the previous A79 in value, font, fill and alignment",
        (flag_new.value, flag_new.font.name, flag_new.font.sz, flag_new.font.i, flag_new.fill.fgColor.rgb, flag_new.alignment.wrap_text),
        (flag_prev.value, flag_prev.font.name, flag_prev.font.sz, flag_prev.font.i, flag_prev.fill.fgColor.rgb, flag_prev.alignment.wrap_text))
c.equal("F4: the flag merge is A61:H61 (was A79:H79) and the row height is unchanged",
        ("A61:H61" in {str(m_) for m_ in v32.merged_cells.ranges}, v32.row_dimensions[61].height), (True, v32_prev.row_dimensions[79].height))
num_by_sheet = {ws.title: sum(1 for row in ws.iter_rows() for x in row if isinstance(x.value, (int, float)) and not isinstance(x.value, bool))
                for ws in new.worksheets}
c.equal("numeric cells on 1.1-5.1 total exactly 1,237", sum(v for k, v in num_by_sheet.items() if k != OVERVIEW), EXPECTED_NUMERIC)
c.equal("0.0 Overview has 0 numeric cells", num_by_sheet[OVERVIEW], 0)
ck_old, ck_new = old["Checks"], new["5.1 Checks"]
rows_old = [[ck_old.cell(r, k).value for k in range(1, 7)] for r in range(4, ck_old.max_row + 1) if ck_old.cell(r, 1).value]
rows_new = [[ck_new.cell(r, k).value for k in range(1, 7)] for r in range(6, ck_new.max_row + 1) if ck_new.cell(r, 1).value]
c.equal("5.1 Checks rows identical to the baseline", rows_new == rows_old, True)
c.equal("5.1 Checks has 65 rows, all PASS", (len(rows_new), all(x[5] == "PASS" for x in rows_new)), (EXPECTED_CHECK_ROWS, True))

# ------------------------------------------------------------------ 4. labels
viol, unlabelled, used = [], [], set()
for name in DM.LABEL_SHEETS:
    ws = new[name]
    for r in range(1, ws.max_row + 1):
        a, b = ws.cell(r, 1).value, ws.cell(r, 2).value
        if b is not None and not isinstance(b, str):
            viol.append((name, r, "B not text", b))
        if isinstance(a, str) and a in DM.LABEL_KEY_HEADERS:
            if b != DM.LABEL_HEADER:
                viol.append((name, r, "header B", b))
            continue
        if isinstance(a, str) and a in DM.LABELS:
            used.add(a)
            if b != DM.label_for(name, a):
                viol.append((name, r, a, b))
        elif b is not None and r > 2 and not (name == "3.2 Valuation" and r > 2 and False):
            viol.append((name, r, "B filled but A has no label", (a, b)))
        if isinstance(a, str) and r > 3 and KEY_RE.match(a) and a not in DM.LABELS and a not in DM.LABEL_KEY_HEADERS:
            unlabelled.append((name, r, a))
c.equal("label sheets: column B is empty or equals LABELS[A] on every row (headers read 'Label')", viol[:3], [])
c.equal("label sheets: every key-like text in column A has a label", unlabelled[:5], [])
c.equal("label sheets: no label in LABELS is unused", sorted(set(DM.LABELS) - used), [])
others = [n for n in DM.SHEET_NAMES if n not in DM.LABEL_SHEETS]
c.equal("non-label sheets have no 'Label' header cell", [n for n in others if any(x.value == DM.LABEL_HEADER for row in new[n].iter_rows() for x in row)], [])

# ------------------------------------------------------------------ 5. formulas
formula_cells = sum(1 for ws in new.worksheets for row in ws.iter_rows() for x in row
                    if x.data_type == "f" or (isinstance(x.value, str) and x.value.startswith("=")))
c.equal("formulas: 0 (no data_type f, no string starting with '=')", formula_cells, 0)

# ------------------------------------------------------------------ 6. hyperlinks
def target(cell):
    loc = cell.hyperlink.location if cell.hyperlink else None
    if not loc:
        return None
    m = re.match(r"^'(.+)'!([A-Z]+[0-9]+)$", loc)
    return (m.group(1), m.group(2)) if m else ("?", loc)


bad_links, row1, allt = [], {}, {}
for ws in new.worksheets:
    row1[ws.title], allt[ws.title] = set(), set()
    for row in ws.iter_rows():
        for x in row:
            if x.hyperlink is None:
                continue
            t = target(x)
            if t is None or t[0] not in new.sheetnames:
                bad_links.append((ws.title, x.coordinate, t))
                continue
            tw = new[t[0]]
            from openpyxl.utils.cell import coordinate_from_string, column_index_from_string  # noqa: E402
            col_l, r_ = coordinate_from_string(t[1])
            if r_ > tw.max_row or column_index_from_string(col_l) > tw.max_column:
                bad_links.append((ws.title, x.coordinate, t, "outside used range"))
            allt[ws.title].add(t[0])
            if x.row == 1:
                row1[ws.title].add(t[0])
c.equal("internal hyperlinks name an existing sheet and a cell in its used range", bad_links[:3], [])
exp_row1 = {}
for n in DM.SHEET_NAMES:
    p, nx = DM.prev_next(n)
    exp_row1[n] = ({OVERVIEW} if n != OVERVIEW else set()) | ({p} if p else set()) | ({nx} if nx else set())
c.equal("row 1 links: every sheet except 0.0 links to 0.0; prev/next follow R-A order (0.0 next only, 5.1 prev only)",
        {k: sorted(v) for k, v in row1.items()}, {k: sorted(v) for k, v in exp_row1.items()})
c.equal("0.0 Overview links to all 10 other sheets", sorted(allt[OVERVIEW]), sorted(set(DM.SHEET_NAMES) - {OVERVIEW}))

# ------------------------------------------------------------------ 7. bands and headline
band_bad = [(n, new[n]["A1"].value) for n in DM.SHEET_NAMES if new[n]["A1"].value != f"GUIDE {LS.ARROW} §{DM.SHEET_ID[n]}"]
c.equal("each band reads exactly 'GUIDE ▸ §<own id>'", band_bad, [])
c.equal("each band id is in doc_map SECTIONS", [n for n in DM.SHEET_NAMES if DM.SHEET_ID[n] not in {s[0] for s in DM.SECTIONS}], [])
sentence = c.scalar("SELECT display FROM report_headline WHERE key = 'sentence'")
c.equal("0.0 Overview headline cell equals the report_headline sentence", new[OVERVIEW]["A3"].value, sentence)
c.equal("3.2 Valuation A3 equals the report_headline sentence", new["3.2 Valuation"]["A3"].value, sentence)
c.equal("row 2 of every sheet reads '<id>  <title>' (numeral and title as text)",
        [n for n in DM.SHEET_NAMES if str(new[n]["A2"].value) != f"{DM.SHEET_ID[n]}  {DM.TITLE_OF_ID[DM.SHEET_ID[n]]}"], [])
ov_text = " ".join(str(x.value) for row in new[OVERVIEW].iter_rows() for x in row if x.value is not None)
c.equal("0.0 names the guide and the note", all(s in ov_text for s in ["DeLonghi_DCF_process_guide.pdf", "DeLonghi_DCF_Valuation_note.docx"]), True)

# ------------------------------------------------------------------ 8. layout
fr_bad, ps_bad = [], []
for n in DM.SHEET_NAMES:
    ws = new[n]
    hr = next((r for r in range(1, ws.max_row + 1) if ws.cell(r, 1).value == FIRST_HEADER[n]), None)
    exp = f"{'C' if n == '1.1 Statements' else 'A'}{hr + 1}" if hr else None
    if ws.freeze_panes != exp:
        fr_bad.append((n, ws.freeze_panes, exp))
    width = sum((ws.column_dimensions[openpyxl.utils.get_column_letter(k)].width or 8.43) for k in range(1, ws.max_column + 1))
    want = "landscape" if width > WIDE_UNITS else "portrait"
    if (ws.page_setup.fitToWidth, ws.page_setup.fitToHeight, ws.sheet_properties.pageSetUpPr.fitToPage) != (1, 0, True) \
            or (ws.page_setup.orientation or "portrait") != want:
        ps_bad.append((n, ws.page_setup.fitToWidth, ws.page_setup.fitToHeight, ws.page_setup.orientation, round(width), want))
c.equal("freeze panes directly below the first table header (1.1 also freezes A:B)", fr_bad, [])
c.equal("fitToWidth 1, fitToHeight 0, landscape when the used width exceeds 120 units", ps_bad, [])

# ------------------------------------------------------------------ 9. fonts and palette
font_bad = sorted({(ws.title, x.font.name) for ws in new.worksheets for row in ws.iter_rows() for x in row
                   if x.font.name not in LS.FONT_NAMES})[:4]
c.equal("every cell font is Garamond or Gill Sans MT", font_bad, [])
zf = zipfile.ZipFile(XLSX)
pal = {p.upper() for p in LS.PALETTE}
rgbs = {m[-6:].upper() for m in re.findall(r'rgb="([0-9A-Fa-f]{6,8})"', zf.read("xl/styles.xml").decode("utf-8"))}
c.equal("every rgb colour in xl/styles.xml is in the ledger palette", sorted(rgbs - pal), [])
chart_xml = "".join(zf.read(n).decode("utf-8") for n in zf.namelist() if n.startswith("xl/charts/"))
crgb = {m.upper() for m in re.findall(r'srgbClr val="([0-9A-Fa-f]{6})"', chart_xml)}
c.equal("every rgb colour in the chart XML is in the ledger palette", sorted(crgb - pal), [])
hexre = re.compile(r"""["'#]([0-9A-Fa-f]{6})["']""")
lit_bad, step8_hex = [], []
for p in sorted((ROOT / "py").glob("*.py")):
    hits = [h for h in hexre.findall(p.read_text(encoding="utf-8")) if re.search(r"[A-Fa-f]", h) and re.search(r"[0-9]", h)]
    if p.name == "ledger_style.py":
        continue
    (step8_hex if p.name in STEP8_FILES else lit_bad).extend((p.name, h) for h in hits)
c.equal("no hex colour literal in py/*.py outside ledger_style.py (step-8 files 06/07 are scoped out, see INFO)", lit_bad, [])
print(f"INFO  hex literals still present in step-8 files (restyled in step 8): {step8_hex}")
navy = [(p.name, n) for p in (ROOT / "py").glob("*.py") for n in NAVY if n.lower() in p.read_text(encoding="utf-8").lower()]
c.equal("navy hexes 1F3864, 2F5597, EEF2F8 appear nowhere in py/", navy, [])

# ------------------------------------------------------------------ 10. chart
mc = new["4.2 Monte Carlo"]
c.equal("4.2 Monte Carlo: exactly 1 native BarChart", [type(ch).__name__ for ch in mc._charts], ["BarChart"])
for n in DM.SHEET_NAMES:
    if n != "4.2 Monte Carlo":
        c.equal(f"{n}: no chart", len(new[n]._charts), 0)
ch = mc._charts[0]
ref = ch.series[0].val.numRef.f
m = re.match(r"^'4\.2 Monte Carlo'!\$([A-Z]+)\$(\d+):\$[A-Z]+\$(\d+)$", ref)
c.equal("chart value reference points at 4.2 Monte Carlo", bool(m), True)
col_c, r0, r1 = (openpyxl.utils.column_index_from_string(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (0, 0, 0)
plotted = [mc.cell(r, col_c).value for r in range(r0, r1 + 1)]    # the series title cell is referenced separately (tx)
hist = [r[0] for r in c.con.execute("SELECT count FROM mc_histogram ORDER BY bin_id").fetchall()]
c.equal("chart values equal mc_histogram.count (54 bins, sum 10,000)", (plotted == hist, len(plotted), sum(plotted)), (True, HIST_BINS, HIST_RUNS))

# ------------------------------------------------------------------ 11. check_step05 edits (non-weakening)
cs5 = (HERE / "check_step05.py").read_text(encoding="utf-8")
head = subprocess.run(["git", "show", "HEAD:checks/check_step05.py"], cwd=ROOT, capture_output=True, text=True).stdout
call = re.compile(r"\bc\.(equal|between|near|zero)\(")
c.equal("check_step05.py: number of c.* check calls not reduced vs HEAD", len(call.findall(cs5)) >= len(call.findall(head)), True)
for tolname in ["TOL = 1e-9", "rel=1e-12", "< 1e-9"]:
    c.equal(f"check_step05.py keeps tolerance '{tolname}' ({head.count(tolname)} at HEAD)", cs5.count(tolname) >= head.count(tolname), True)
c.equal("check_step05.py: SHEETS is the 11 names", all(f'"{n}"' in cs5 for n in DM.SHEET_NAMES), True)
c.equal("check_step05.py: AST scan covers report_style.py, ledger_style.py and doc_map.py",
        all(s in cs5 for s in ["report_style.py", "ledger_style.py", "doc_map.py"]), True)

# ------------------------------------------------------------------ 12. regression and determinism
for n, exp in EXPECTED_STEP_COUNTS.items():
    p, t, rc = step_counts[n]
    c.equal(f"check_step{n}.py passes {exp}/{exp}", (p, t, rc), (exp, exp, 0))
p6, t6, rc6 = step_counts["06"]
c.equal(f"check_step06.py passes with >= {MIN_PASS_STEP06} checks, none failing", (p6 >= MIN_PASS_STEP06, p6 == t6, rc6), (True, True, 0))
p5, t5, rc5 = step_counts["05"]
c.equal(f"check_step05.py passes with >= {MIN_PASS_STEP05} checks, none failing", (p5 >= MIN_PASS_STEP05, p5 == t5, rc5), (True, True, 0))
g = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "checks/fingerprint.py"], cwd=ROOT)
c.equal("checks/fingerprint.py unchanged (git diff empty)", g.returncode, 0)
c.equal("fresh run 1: the 24 fingerprints equal verify/fp_step06.txt", fps_ok[0], (0, "PASS  fingerprints identical"))
c.equal("fresh run 2: the 24 fingerprints equal verify/fp_step06.txt", fps_ok[1], (0, "PASS  fingerprints identical"))
c.equal("two fresh runs give identical workbooks (values, formats, styles, links, sizes, anchors)",
        sigs[0] is not None and sigs[0] == sigs[1], True)

# ------------------------------------------------------------------ 13. banned phrases
texts = [(ws.title, x.value) for ws in new.worksheets for row in ws.iter_rows() for x in row if isinstance(x.value, str)]
hits = [(sheet, BN.hits(t), t[:60]) for sheet, t in texts if BN.hits(t)]
c.equal("banned phrases (extended list of checks/banned.py, step 9) in all workbook strings: 0 hits", hits[:4], [])
iv = [(s, t[:40]) for s, t in texts if re.search(r"interview", t, re.I)]
c.equal("'interview' appears only on 0.0 Overview, at most 3 times", (len(iv) <= 3, [s for s, _ in iv if s != OVERVIEW]), (True, []))

# ------------------------------------------------------------------ 14. visual render
pngs = sorted(RENDER_DIR.glob("DeLonghi_DCF_Valuation_p*.png")) if RENDER_DIR.exists() else []
c.equal("render_png.py ran without error", render.returncode, 0)
c.between("PNG pages written to verify/render/step07 (one per workbook page, at least one per sheet)", len(pngs), len(DM.SHEET_NAMES), 200)
pdf = RENDER_DIR / "DeLonghi_DCF_Valuation.pdf"
first_pages = {}
if pdf.exists():
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(pdf))
    for i in range(len(doc)):
        txt = doc[i].get_textpage().get_text_range()
        for sid in [s[0] for s in DM.SHEETS]:
            if f"§{sid}" in txt and "GUIDE" in txt and sid not in first_pages:
                first_pages[sid] = i + 1
    doc.close()
c.equal("the rendered PDF shows the band 'GUIDE … §<id>' for every sheet, in sheet order",
        (sorted(first_pages) == sorted(s[0] for s in DM.SHEETS), list(first_pages.values()) == sorted(first_pages.values())), (True, True))
print(f"INFO  first page per sheet in the render: {first_pages}")

c.done()
