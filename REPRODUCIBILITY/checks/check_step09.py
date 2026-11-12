"""Acceptance checks for step 9 (plan/plan.md, Amendment 3): the final presentation polish of the three documents.

Every check prints PASS/FAIL with actual vs expected; exit code 1 if any check fails.

What is checked (plan step 9):
  Baseline    verify/baseline_step09/ is byte-identical to `git show 44d683d:<path>`; its dumps match the baseline files
  Workbook    diff against the step-8 workbook limited to the 8 reworded cells, the 3.2 flag move (A79 -> A61), the new 0.0 A20
              author cell and docProps; navigation; formulas = 0; numeric cells
  Author      exact AUTHOR_LINE on 0.0 A20, in the note directly after the title and on the guide cover; file properties
  Glyphs      "a grave" in all three documents, 0 U+FFFD, Gill Sans MT on the author cells
  Banned      the extended banned-phrase list over every text surface of the three documents (no exclusion)
  Guide       structure unchanged, "Reconciliation and checks" once in 1.1/2.1/3.1/4.2, section 5 table, section 3 explanations
              of final_review.md absent from sections 1-5, A.3 limitations and figures, section 6 sentence, token provenance
  Note        number tokens, paragraphs, structure, A4, two pages with page-2 fill <= 0.90
  Regression  two fresh rebuilds: identical PDF / JSON / docx / PNG / xlsx (but docProps/core.xml), 24 fingerprints equal
              verify/fp_step06.txt; check_step01-08 pass counts
  Visual      PNGs of the three documents go to verify/render/step09/
The rebuilds run first (before any DuckDB connection is opened) because they delete and recreate data/curiosity.duckdb.
"""
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "py"))
sys.stdout.reconfigure(encoding="utf-8")

PY = sys.executable
REPORT = ROOT / "report"
XLSX = REPORT / "DeLonghi_DCF_Valuation.xlsx"
DOCX = REPORT / "DeLonghi_DCF_Valuation_note.docx"
PNG = REPORT / "note_chart.png"
PDF = REPORT / "DeLonghi_DCF_process_guide.pdf"
GJSON = REPORT / "build" / "guide_numbers.json"
BASE = ROOT / "verify" / "baseline_step09"
BASE_AMEND2 = ROOT / "verify" / "baseline_amend2"
BASE_COMMIT = "44d683d"
BASE_PATHS = {"DeLonghi_DCF_Valuation.xlsx": "report/DeLonghi_DCF_Valuation.xlsx",
              "DeLonghi_DCF_Valuation_note.docx": "report/DeLonghi_DCF_Valuation_note.docx",
              "DeLonghi_DCF_process_guide.pdf": "report/DeLonghi_DCF_process_guide.pdf",
              "note_chart.png": "report/note_chart.png", "guide_numbers.json": "report/build/guide_numbers.json"}
RENDER_TAG = "step09"
EXPECTED_COUNTS = {"01": 128, "02": 78, "03": 148, "04": 66}
MIN_COUNTS = {"05": 93, "06": 25, "07": 74, "08": 66}
EXP_AUTHOR_NAME = "Mina Khella"
EXP_AUTHOR_EMAIL = "mina.khellas@gmail.com"
EXP_AUTHOR_AFFIL = "Undergraduate in Statistics and Economics, Università degli studi di Milano Bicocca"
EXP_AUTHOR_LINE = f"{EXP_AUTHOR_NAME} · {EXP_AUTHOR_EMAIL} · {EXP_AUTHOR_AFFIL}"
EXP_REWORDED_CELLS = ["2.2 Bridge Inputs!F13", "2.2 Bridge Inputs!F17", "2.2 Bridge Inputs!H17", "2.2 Bridge Inputs!H7",
                      "3.1 FCFF Forecast!F26", "3.1 FCFF Forecast!F27", "3.1 FCFF Forecast!G30", "3.2 Valuation!H46"]
EXP_NUMERIC = 1237
EXP_CHECK_ROWS = 65
AUTHOR_CELL = "0.0 Overview!A20"
NEW_S6 = ("Each figure in the note was matched by script, at the display precision of the cell, against a cell on the sheet "
          "named by its tag; dates and year labels are not figures and are exempt.")
OLD_S6 = "Every number in the note was checked by script"
LIMITATION_PHRASES = ["book value", "twice", "decides the sign", "narrowly", "no live formulas", "not an investment recommendation"]
A3_FIGURES = ["79.6", "24.6", "0.98", "0.52"]
RECON = "Reconciliation and checks"
S5_ROWS = ["Raw data", "Statements", "Rates and bridge", "Valuation", "Simulation", "Workbook", "Note", "Rebuild"]
NOTE_PAGES, NOTE_FILL_MAX = 2, 0.90
EMU_PER_PT = 12700
MAX_PAGES = 20
SMALL_PT_EXPECTED = 9
TAG = re.compile(r"\[(\d\.\d)\]")


def run(args, **kw):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, **kw)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def members(p):
    z = zipfile.ZipFile(p)
    return {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}


def counts(script):
    r = run([PY, str(HERE / script)])
    m = re.findall(r"(\d+)/(\d+) checks passed", r.stdout)
    return (int(m[-1][0]), int(m[-1][1]), r.returncode) if m else (0, 0, r.returncode)


# ------------------------------------------------------------------ 0. rebuilds and regression runs (before any DB connection)
fresh = []
for i in (1, 2):
    r = run([PY, str(ROOT / "run.py"), "--fresh", "--through", "7"])
    if r.returncode:
        print(r.stdout[-1500:], r.stderr[-1500:])
    fp_lines = [ln for ln in (ROOT / "verify" / "fp_step06.txt").read_text(encoding="utf-8").split("\n") if ln.strip()]
    fp = run([PY, str(HERE / "fingerprint.py"), "--compare", str(ROOT / "verify" / "fp_step06.txt")]
             + [ln.split("\t")[0] for ln in fp_lines])
    fresh.append({"rc": r.returncode, "fp": (fp.returncode, len(fp_lines)),
                  "pdf": sha(PDF) if PDF.exists() else None, "json": sha(GJSON) if GJSON.exists() else None,
                  "docx": members(DOCX) if DOCX.exists() else None, "png": sha(PNG) if PNG.exists() else None,
                  "xlsx": members(XLSX) if XLSX.exists() else None})
step_counts = {n: counts(f"check_step{n}.py") for n in ["01", "02", "03", "04", "07", "05", "06", "08"]}

from _lib import Checks  # noqa: E402
import banned  # noqa: E402
import doc_map as DM  # noqa: E402
import ledger_style as LS  # noqa: E402
from guide_tokens import NUM, WORKBOOK_PREFIX, norm, tokens  # noqa: E402
from note_tokens import note_tokens  # noqa: E402
from xlsx_dump import dump_lines  # noqa: E402

import openpyxl  # noqa: E402
import pdfplumber  # noqa: E402
from docx import Document  # noqa: E402
from openpyxl.cell.cell import MergedCell  # noqa: E402
from pdfminer.pdfdocument import PDFDocument  # noqa: E402
from pdfminer.pdfparser import PDFParser  # noqa: E402

c = Checks()

# ------------------------------------------------------------------ 1. baseline snapshot
for name, git_path in BASE_PATHS.items():
    g = subprocess.run(["git", "show", f"{BASE_COMMIT}:{git_path}"], cwd=ROOT, capture_output=True)
    c.equal(f"baseline {name} is byte-identical to git show {BASE_COMMIT}:{git_path}",
            g.returncode == 0 and (BASE / name).read_bytes() == g.stdout, True)
sums = dict(ln.split(" *")[::-1] for ln in (BASE / "SHA256SUMS.txt").read_text().splitlines() if ln.strip())
c.equal("SHA256SUMS.txt matches the 5 snapshot files",
        (len(sums), all(sha(BASE / k) == v for k, v in sums.items())), (5, True))
base_cells = (BASE / "xlsx_cells.txt").read_text(encoding="utf-8").splitlines()
c.equal("baseline xlsx_cells.txt equals a fresh dump of the baseline workbook", dump_lines(BASE / "DeLonghi_DCF_Valuation.xlsx") == base_cells, True)
base_doc = Document(str(BASE / "DeLonghi_DCF_Valuation_note.docx"))
base_paras = (BASE / "note_paras.txt").read_text(encoding="utf-8").split("\n")[:-1]
c.equal("baseline note_paras.txt equals the paragraphs of the baseline docx", base_paras, [p.text for p in base_doc.paragraphs])

# ------------------------------------------------------------------ 2. workbook diff against the step-8 workbook
new = openpyxl.load_workbook(XLSX)
old = openpyxl.load_workbook(BASE / "DeLonghi_DCF_Valuation.xlsx")


def sig(cell):
    f, fl, al, b = cell.font, cell.fill, cell.alignment, cell.border
    side = lambda s: (s.style, s.color.rgb if s.color else None) if s is not None else None  # noqa: E731
    return (cell.number_format, f.name, f.sz, f.b, f.i, f.u, f.color.rgb if f.color else None, fl.fill_type,
            fl.fgColor.rgb if fl.fgColor else None, al.horizontal, al.vertical, al.wrap_text, al.indent,
            side(b.top), side(b.bottom), side(b.left), side(b.right))


def link_of(cell):
    return (cell.hyperlink.location, cell.hyperlink.display) if cell.hyperlink else None


c.equal("workbook: same 11 sheets in the same order as the step-8 workbook", new.sheetnames, old.sheetnames)
val_diff, style_diff, link_diff, other = [], [], [], []
ROW_FLAG_NEW, ROW_FLAG_OLD = 61, 79
for ws_old in old.worksheets:
    ws_new = new[ws_old.title]
    is_val = ws_old.title == "3.2 Valuation"
    is_ov = ws_old.title == "0.0 Overview"
    for row in ws_old.iter_rows():
        for co in row:
            if isinstance(co, MergedCell):
                continue
            r_old = co.row
            if is_val and r_old >= 60:
                if r_old != ROW_FLAG_OLD:
                    if co.value is not None:
                        val_diff.append((ws_old.title, co.coordinate, "unexpected old content"))
                    continue
                cn = ws_new.cell(row=ROW_FLAG_NEW, column=co.column)
            else:
                cn = ws_new.cell(row=r_old, column=co.column)
            key = f"{ws_old.title}!{co.coordinate}"
            if co.value != cn.value or type(co.value) is not type(cn.value):
                val_diff.append(key)
            if sig(co) != sig(cn):
                style_diff.append(key)
            if link_of(co) != link_of(cn):
                link_diff.append(key)
    # cells present only in the new sheet must be empty (or the author cell)
    for row in ws_new.iter_rows():
        for cn in row:
            if isinstance(cn, MergedCell) or cn.value is None:
                continue
            if f"{ws_new.title}!{cn.coordinate}" == AUTHOR_CELL:
                continue
            if cn.row > ws_old.max_row and not (is_val and cn.row == ROW_FLAG_NEW):
                other.append(f"{ws_new.title}!{cn.coordinate} has content below the old used range")
c.equal("workbook diff: the only value differences are the 8 reworded cells", sorted(val_diff, key=str), sorted(EXP_REWORDED_CELLS))
c.equal("workbook diff: no style difference on any baseline cell (3.2 A79 compared with A61)", style_diff, [])
c.equal("workbook diff: no hyperlink difference", link_diff, [])
c.equal("workbook diff: no content below the old used range other than the moved flag and the author cell", other, [])
ms = lambda ws: sorted(str(m) for m in ws.merged_cells.ranges)  # noqa: E731
merge_diff = {}
for n in old.sheetnames:
    a, b = ms(old[n]), ms(new[n])
    if n == "3.2 Valuation":
        a = sorted([x for x in a if x != f"A{ROW_FLAG_OLD}:H{ROW_FLAG_OLD}"] + [f"A{ROW_FLAG_NEW}:H{ROW_FLAG_NEW}"])
    if a != b:
        merge_diff[n] = (a[-2:], b[-2:])
c.equal("workbook diff: merges equal, the flag merge A79:H79 became A61:H61", merge_diff, {})
dim_diff = []
for n in old.sheetnames:
    ho = {k: v.height for k, v in old[n].row_dimensions.items() if v.height}
    hn = {k: v.height for k, v in new[n].row_dimensions.items() if v.height}
    if n == "3.2 Valuation":
        flag_h = ho.pop(ROW_FLAG_OLD, None)
        ho = {k: v for k, v in ho.items() if k < 60}
        if hn.pop(ROW_FLAG_NEW, None) != flag_h:
            dim_diff.append((n, "flag row height"))
    if ho != hn:
        dim_diff.append((n, "row heights"))
    wo = {k: v.width for k, v in old[n].column_dimensions.items()}
    wn = {k: v.width for k, v in new[n].column_dimensions.items()}
    if wo != wn:
        dim_diff.append((n, "column widths"))
    if old[n].freeze_panes != new[n].freeze_panes:
        dim_diff.append((n, "freeze panes"))
c.equal("workbook diff: row heights (flag row moved), column widths and freeze panes equal", dim_diff, [])
v32 = new["3.2 Valuation"]
c.equal("3.2: max_row 61, row 60 empty, pointer at A59 linking to 2.2, flag text in A61",
        (v32.max_row, [x.value for x in v32[60]], v32["A59"].hyperlink.location, str(v32["A61"].value).startswith("SIMPLIFICATION FLAG")),
        (61, [None] * v32.max_column, "'2.2 Bridge Inputs'!A1", True))
c.equal("3.2: no cell below row 61", [x.coordinate for row in v32.iter_rows(min_row=62) for x in row if x.value is not None], [])
numeric = {ws.title: sum(1 for row in ws.iter_rows() for x in row if isinstance(x.value, (int, float)) and not isinstance(x.value, bool))
           for ws in new.worksheets}
c.equal("numeric cells: 1,237 on 1.1-5.1, 0 on 0.0", (sum(v for k, v in numeric.items() if k != "0.0 Overview"), numeric["0.0 Overview"]),
        (EXP_NUMERIC, 0))
c.equal("formulas: 0", sum(1 for ws in new.worksheets for row in ws.iter_rows() for x in row
                           if x.data_type == "f" or (isinstance(x.value, str) and x.value.startswith("="))), 0)
ck = new["5.1 Checks"]
ck_old = old["5.1 Checks"]
rows_new = [[ck.cell(r, k).value for k in range(1, 7)] for r in range(6, ck.max_row + 1) if ck.cell(r, 1).value]
rows_old = [[ck_old.cell(r, k).value for k in range(1, 7)] for r in range(6, ck_old.max_row + 1) if ck_old.cell(r, 1).value]
c.equal("5.1 Checks: 65 rows, all PASS, identical to the step-8 workbook", (len(rows_new), all(x[5] == "PASS" for x in rows_new), rows_new == rows_old),
        (EXP_CHECK_ROWS, True, True))
# navigation
bad_links, tgt = [], {}
for ws in new.worksheets:
    tgt[ws.title] = set()
    for row in ws.iter_rows():
        for x in row:
            if x.hyperlink is None:
                continue
            m = re.match(r"^'(.+)'!([A-Z]+)(\d+)$", x.hyperlink.location or "")
            if not m or m.group(1) not in new.sheetnames:
                bad_links.append((ws.title, x.coordinate, x.hyperlink.location))
                continue
            tw = new[m.group(1)]
            if int(m.group(3)) > tw.max_row or openpyxl.utils.column_index_from_string(m.group(2)) > tw.max_column:
                bad_links.append((ws.title, x.coordinate, "outside the used range"))
            tgt[ws.title].add(m.group(1))
c.equal("navigation: every hyperlink resolves to an existing sheet and a cell in its used range", bad_links[:3], [])
c.equal("navigation: 0.0 links to the 10 other sheets", sorted(tgt["0.0 Overview"]), sorted(set(DM.SHEET_NAMES) - {"0.0 Overview"}))
# docProps
zx = zipfile.ZipFile(XLSX)
zo = zipfile.ZipFile(BASE / "DeLonghi_DCF_Valuation.xlsx")
changed_members = sorted(n for n in zx.namelist() if n not in zo.namelist() or zx.read(n) != zo.read(n))
print(f"INFO  package members that differ from the step-8 workbook: {changed_members}")

# ------------------------------------------------------------------ 3. reword rules
old_text = {f"{ws.title}!{x.coordinate}": x.value for ws in old.worksheets for row in ws.iter_rows() for x in row if isinstance(x.value, str)}
rules = getattr(DM, "TEXT_REWORDS", [])
c.equal("doc_map.TEXT_REWORDS holds exactly the 5 plan rules plus the human-approved sixth", rules, [
    ("The plan's 'NFP table", "The figure quoted as 'NFP table"), ("(The plan cites", "(An earlier reference cites"),
    ("Performance Shares Plan rights", "performance-share rights"), ("the plan's estimate", "an assumption fixed in advance"),
    (", plan/plan.md", ", fixed in advance"), ("incentive plans", "incentive schemes")])
used = Counter()
bad_digits, bad_new = [], []
for key in EXP_REWORDED_CELLS:
    o, nn = old_text[key], new[key.split("!")[0]][key.split("!")[1]].value
    exp = o
    for a, b in rules:
        if a in exp:
            used[a] += 1
        exp = exp.replace(a, b)
    if nn != exp or hasattr(DM, "reword") and DM.reword(o) != nn:
        bad_new.append(key)
    if re.findall(r"\d+", o) != re.findall(r"\d+", nn):
        bad_digits.append(key)
c.equal("reworded cells: new text = old text with the ordered rules applied (8 cells)", bad_new, [])
c.equal("reworded cells: the sequence of digit runs is identical to the old text", bad_digits, [])
c.equal("each of the 6 rules is used at least once", sorted(a for a, _ in rules if used[a] == 0), [])
c.equal("reword rules contain no digit and no banned word",
        [r for r in rules if re.search(r"\d", r[0] + r[1]) or banned.hits(r[1])], [])

# ------------------------------------------------------------------ 4. author line
ov = new["0.0 Overview"]
a20 = ov["A20"]
c.equal("author: '0.0 Overview'!A20 equals AUTHOR_LINE exactly", a20.value, EXP_AUTHOR_LINE)
c.equal("author: A20 is Gill Sans MT, small, grey, with no hyperlink",
        (a20.font.name, a20.font.sz, a20.font.color.rgb[-6:], a20.hyperlink), (LS.BODY_FONT, SMALL_PT_EXPECTED, LS.GREY, None))
c.equal("author: doc_map constants hold the exact strings",
        (getattr(DM, "AUTHOR_NAME", None), getattr(DM, "AUTHOR_EMAIL", None), getattr(DM, "AUTHOR_AFFILIATION", None),
         getattr(DM, "AUTHOR_LINE", None)), (EXP_AUTHOR_NAME, EXP_AUTHOR_EMAIL, EXP_AUTHOR_AFFIL, EXP_AUTHOR_LINE))
doc = Document(str(DOCX))
paras = [p.text for p in doc.paragraphs]
title_i = next(i for i, p in enumerate(doc.paragraphs) if p.style.name == "Title")
ap = doc.paragraphs[title_i + 1]
c.equal("author: the note paragraph directly after the title is AUTHOR_LINE (Normal style)", (ap.text, ap.style.name), (EXP_AUTHOR_LINE, "Normal"))
c.equal("author: note runs are Gill Sans MT, small, grey, no hyperlink",
        ({r.font.name for r in ap.runs}, {r.font.size.pt for r in ap.runs}, {str(r.font.color.rgb) for r in ap.runs},
         len(ap._p.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hyperlink"))),
        ({LS.BODY_FONT}, {float(SMALL_PT_EXPECTED)}, {LS.GREY}, 0))
pdf = pdfplumber.open(str(PDF))
page_text = [(p.extract_text() or "") for p in pdf.pages]
full_text = "\n".join(page_text)
p1 = norm(page_text[0])
c.equal("author: guide page 1 holds the name, the e-mail and the affiliation ('Università' intact)",
        [x for x in (EXP_AUTHOR_NAME, EXP_AUTHOR_EMAIL, EXP_AUTHOR_AFFIL) if x not in p1], [])
fh = open(PDF, "rb")
pdoc = PDFDocument(PDFParser(fh))
info = {k: (v.decode("utf-8", "ignore") if isinstance(v, bytes) else str(v)) for k, v in (pdoc.info[0] if pdoc.info else {}).items()}
c.equal("author: PDF /Author, xlsx creator and docx core author equal AUTHOR_NAME",
        (info.get("Author"), new.properties.creator, doc.core_properties.author), (EXP_AUTHOR_NAME,) * 3)
zd = zipfile.ZipFile(DOCX)
props = {"xlsx core": zx.read("docProps/core.xml").decode(), "xlsx app": zx.read("docProps/app.xml").decode(),
         "docx core": zd.read("docProps/core.xml").decode(), "docx app": zd.read("docProps/app.xml").decode(),
         "pdf info": " ".join(info.values())}
c.equal("author: no document property equals or contains CURIOSITY",
        [k for k, v in props.items() if re.search(r"curiosity", v, re.I)], [])
c.equal("author: docx comments property is empty", doc.core_properties.comments, "")

# ------------------------------------------------------------------ 5. glyphs
fffd = {"xlsx": sum(str(x.value).count("�") for ws in new.worksheets for row in ws.iter_rows() for x in row if x.value is not None),
        "docx": "\n".join(paras).count("�"), "pdf": full_text.count("�")}
c.equal("glyphs: 0 U+FFFD in the workbook, the note and the guide", fffd, {"xlsx": 0, "docx": 0, "pdf": 0})
c.equal("glyphs: 'Università' present in the three documents", ("Università" in ov["A20"].value, "Università" in "\n".join(paras), "Università" in page_text[0]),
        (True, True, True))

# ------------------------------------------------------------------ 6. banned phrases (every text surface, no exclusion)


def xml_text(x):
    return " ".join(re.findall(r">([^<]+)<", x))


surf = {}
surf["guide pages"] = full_text
surf["guide metadata"] = " ".join(info.values())
surf["guide outline"] = " ".join(t for (_l, t, _d, _a, _s) in pdoc.get_outlines())
tbl = []
for t in doc.tables:
    for row in t.rows:
        tbl += [cell.text for cell in row.cells]
hf = []
for s in doc.sections:
    for part in (s.header, s.footer, s.first_page_header, s.first_page_footer, s.even_page_header, s.even_page_footer):
        hf += [p.text for p in part.paragraphs]
cp = doc.core_properties
surf["note body"] = "\n".join(paras + tbl)
surf["note header/footer"] = "\n".join(hf)
surf["note properties"] = " ".join(str(getattr(cp, a) or "") for a in ("author", "last_modified_by", "title", "subject", "keywords",
                                                                     "comments", "category")) + " " + xml_text(props["docx app"])
surf["xlsx cells"] = "\n".join(str(x.value) for ws in new.worksheets for row in ws.iter_rows() for x in row if isinstance(x.value, str))
surf["xlsx comments"] = "\n".join(x.comment.text for ws in new.worksheets for row in ws.iter_rows() for x in row if x.comment)
surf["xlsx header/footer"] = "\n".join(str(getattr(getattr(ws, h), part).text or "") for ws in new.worksheets
                                       for h in ("oddHeader", "oddFooter", "evenHeader", "evenFooter", "firstHeader", "firstFooter")
                                       for part in ("left", "center", "right"))
surf["xlsx sheet names"] = " ".join(new.sheetnames)
surf["xlsx properties"] = xml_text(props["xlsx core"]) + " " + xml_text(props["xlsx app"])
surf["xlsx charts"] = " ".join(xml_text(zx.read(n).decode()) for n in zx.namelist() if n.startswith("xl/charts/"))
for name, text in surf.items():
    c.equal(f"banned phrases in {name}: 0 hits", banned.hits(text), [])

# ------------------------------------------------------------------ 7. guide structure
npages = len(pdf.pages)
c.between("guide: at most 20 pages", npages, 1, MAX_PAGES)
c.equal("guide: every page is A4", [i for i, p in enumerate(pdf.pages) if abs(float(p.width) - 595.3) > 0.5 or abs(float(p.height) - 841.9) > 0.5], [])
ids_expected = [s[0] for s in DM.SECTIONS]
outline = [(lvl, t) for (lvl, t, _d, _a, _s) in pdoc.get_outlines()]
base_pdoc = PDFDocument(PDFParser(open(BASE / "DeLonghi_DCF_process_guide.pdf", "rb")))
base_outline = [(lvl, t) for (lvl, t, _d, _a, _s) in base_pdoc.get_outlines()]
c.equal("guide: outline identical to the step-8 PDF (22 ids, same titles, same order)", (outline == base_outline, len(outline)), (True, 22))
c.equal("guide: outline ids equal doc_map SECTIONS", [re.match(r"§(\S+)", t).group(1) for _l, t in outline], ids_expected)

contents_idx = next(i for i, t in enumerate(page_text) if t.strip().startswith("Contents"))
body_text = "\n".join(t for i, t in enumerate(page_text) if i != contents_idx)
sec_pos = {}
for sid, title in DM.SECTIONS:
    m = re.search(r"^§" + re.escape(sid) + r"\s+" + re.escape(title) + r"\s*$", body_text, re.M)
    sec_pos[sid] = m.start() if m else -1
c.equal("guide: every section heading found once in the body", [k for k, v in sec_pos.items() if v < 0], [])


def sec_text(sid):
    k = ids_expected.index(sid)
    end = sec_pos[ids_expected[k + 1]] if k + 1 < len(ids_expected) else len(body_text)
    return body_text[sec_pos[sid]:end]


bad_wb = []
for sid in ids_expected:
    lines = sec_text(sid).split("\n")
    if len(lines) < 2 or not lines[1].strip().startswith(WORKBOOK_PREFIX) or any(
            n.strip() not in new.sheetnames for n in lines[1].strip()[len(WORKBOOK_PREFIX):].split(" · ")):
        bad_wb.append(sid)
c.equal("guide: every section opens with a WORKBOOK line naming existing sheets", bad_wb, [])
bands = {n: re.sub(r"^GUIDE ▸ §", "", str(new[n]["A1"].value)) for n in new.sheetnames}
c.equal("guide: every sheet band id is a guide heading", [n for n, i in bands.items() if i not in ids_expected], [])

# ------------------------------------------------------------------ 8. guide content
reco = {sid: len(re.findall(RECON, norm(sec_text(sid)))) for sid in ids_expected if sid.split(".")[0] in "1234" and sid != "0.0"}
c.equal("guide: 'Reconciliation and checks' occurs exactly once in 1.1, 2.1, 3.1, 4.2 and in no other section 1-4",
        {k: v for k, v in reco.items() if v != (1 if k in ("1.1", "2.1", "3.1", "4.2") else 0)}, {})
s5 = norm(sec_text("5"))
c.equal("guide: section 5 has a row for stages 0-4, workbook, note and rebuild", [r for r in S5_ROWS if r not in s5], [])
s15 = norm(" ".join(sec_text(s) for s in ["1", "1.1", "1.2", "2", "2.1", "2.2", "3", "3.1", "3.2", "3.3", "4", "4.1", "4.2", "5", "5.1"]))
final_txt = (REPORT / "final_review.md").read_text(encoding="utf-8")
sec3 = final_txt.split("## 3.")[1].split("## 4.")[0]
rows3 = [ln for ln in sec3.split("\n") if ln.startswith("| ") and not ln.startswith("| Step") and not ln.startswith("|---")]
present = []
for ln in rows3:
    expl = norm([x.strip() for x in ln.strip().strip("|").split("|")][2].replace("*", "").replace("`", ""))
    first = re.split(r"(?<=[.])\s", expl)[0][:60]
    if first in s15:
        present.append(first)
c.equal("guide: none of the 12 final_review section-3 explanations appears in sections 1-5 (12 rows read)", (len(rows3), present), (12, []))
a3 = norm(sec_text("A.3"))
c.equal("guide: A.3 still contains all 6 limitation phrases", [p for p in LIMITATION_PHRASES if p not in a3], [])
c.equal("guide: A.3 contains the figures 79.6%, 24.6%, 0.98 and 0.52", [f for f in A3_FIGURES if f not in tokens(a3)], [])
g = json.loads(GJSON.read_text(encoding="utf-8"))
entries = g["entries"]
pdf_tokens = tokens(full_text)
json_tokens = [e["token"].replace(",", "") for e in entries]
a3_start = len(tokens("\n".join(page_text[:contents_idx + 1]))) + len(tokens(body_text[:sec_pos["A.3"]]))
a3_n = len(tokens(sec_text("A.3")))
slice_ = entries[a3_start:a3_start + a3_n]
c.equal("guide: the four A.3 figures each have a provenance entry (db or file) inside the A.3 token range",
        sorted(f for f in A3_FIGURES if not any(e["token"] == f and e["kind"] in ("db", "db_text", "file", "file_rows") for e in slice_)), [])
s6 = norm(sec_text("6"))
c.equal("guide: section 6 holds the new sentence verbatim and not the old one", (norm(NEW_S6) in s6, OLD_S6 in s6), (True, False))
c.equal("guide: PDF number tokens equal guide_numbers.json tokens in order", (pdf_tokens == json_tokens, len(pdf_tokens), len(json_tokens)),
        (True, len(pdf_tokens), len(pdf_tokens)))
print(f"INFO  guide number tokens: {len(json_tokens)} (step-8 baseline: {len(json.loads((BASE / 'guide_numbers.json').read_text(encoding='utf-8'))['entries'])})")
meth = norm(sec_text("0.0"))
c.equal("guide 0.0: method stages Definition, Checks first, Analysis, Independent recomputation (the label wraps in its table cell), Rebuild, Approval; 'Plausibility bounds fixed in advance'",
        [x for x in ("Definition", "Checks first", "Analysis", "Independent", "recomputation", "Rebuild", "Approval",
                     "Plausibility bounds fixed in advance") if x not in meth], [])
c.equal("guide A.2: glossary entry 'Plausibility bound' replaces 'Smell test'", ("Plausibility bound" in norm(sec_text("A.2")), "Smell" in norm(sec_text("A.2"))), (True, False))
s12 = norm(sec_text("1.2"))
c.equal("guide 1.2: states '1 decimal', 'accepted' and '2026-11-09'", [x for x in ("1 decimal", "accepted", "2026-11-09") if x not in s12], [])

# ------------------------------------------------------------------ 9. note
doc_tokens = Counter(t.replace(",", "") for t in note_tokens(DOCX, strip_tags=True))
base_note_tokens = Counter(t.replace(",", "") for t in note_tokens(BASE / "DeLonghi_DCF_Valuation_note.docx", strip_tags=True))
a2_tokens = Counter(t.replace(",", "") for t in (BASE_AMEND2 / "note_tokens.txt").read_text(encoding="utf-8").split())
c.equal("note tokens: multiset equals the step-8 note's tokens (58 = the 61 of baseline_amend2 less the 3 step-8 rewordings)",
        (doc_tokens == base_note_tokens, sum(doc_tokens.values()), sorted((a2_tokens - doc_tokens).elements())),
        (True, 58, sorted(["25", "5", "95"])))
without_author = [p for i, p in enumerate(paras) if i != title_i + 1]
c.equal("note paragraphs equal note_paras.txt except the one inserted author paragraph", without_author, base_paras)
heads = [p.text.strip() for p in doc.paragraphs if p.style.name.startswith("Heading")]
c.equal("note: 5 headings", heads, ["Thesis", "Main assumptions", "Valuation range", "Risks", "Conclusion vs market price"])
c.equal("note: 1 picture, at most 900 words", (len(doc.inline_shapes), len(re.findall(r"\S+", "\n".join(paras))) <= 900), (1, True))
sentence = c.scalar("SELECT display FROM report_headline WHERE key = 'sentence'")
hi = paras.index(sentence) if sentence in paras else -1
c.equal("note: headline paragraph equals report_headline and its tags are in the next paragraph",
        (hi >= 0, bool(TAG.search(paras[hi + 1])) if hi >= 0 else False), (True, True))
sect = doc.sections[0]
c.near("note: A4 width (EMU, 1%)", sect.page_width, 7_560_000, rel=0.01)
c.near("note: A4 height (EMU, 1%)", sect.page_height, 10_692_000, rel=0.01)

# ------------------------------------------------------------------ 10. determinism and regression
a, b = fresh
c.equal("two fresh rebuilds (run.py --fresh --through 7) succeed", (a["rc"], b["rc"]), (0, 0))
c.equal("two fresh rebuilds: the 24 fingerprints equal verify/fp_step06.txt", (a["fp"], b["fp"]), ((0, 24), (0, 24)))
c.equal("two fresh rebuilds: byte-identical guide PDF", a["pdf"] == b["pdf"] and a["pdf"] is not None, True)
c.equal("two fresh rebuilds: byte-identical guide_numbers.json", a["json"] == b["json"] and a["json"] is not None, True)
c.equal("two fresh rebuilds: identical note docx members", a["docx"] == b["docx"] and a["docx"] is not None, True)
c.equal("two fresh rebuilds: identical note_chart.png", a["png"] == b["png"] and a["png"] is not None, True)
diff_x = sorted(k for k in set(a["xlsx"]) | set(b["xlsx"]) if a["xlsx"].get(k) != b["xlsx"].get(k))
c.equal("two fresh rebuilds: the workbook differs only in docProps/core.xml (or not at all)", [k for k in diff_x if k != "docProps/core.xml"], [])
for n, exp in EXPECTED_COUNTS.items():
    c.equal(f"check_step{n}.py passes {exp}/{exp}", step_counts[n], (exp, exp, 0))
for n, floor in MIN_COUNTS.items():
    p_, t_, rc_ = step_counts[n]
    c.equal(f"check_step{n}.py passes with at least {floor} checks and none failing", (p_ >= floor, p_ == t_, rc_), (True, True, 0))
print(f"INFO  pass counts: {step_counts}")

# ------------------------------------------------------------------ 11. visual renders
sys.path.insert(0, str(HERE))
import render_png  # noqa: E402
g_png = render_png.render(PDF, RENDER_TAG)
n_png = render_png.render(DOCX, RENDER_TAG)
x_png = render_png.render(XLSX, RENDER_TAG)
c.equal("renders: guide pages, note pages (exactly 2) and workbook pages written to verify/render/step09",
        (len(g_png) == npages, len(n_png), len(x_png) >= len(DM.SHEET_NAMES)), (True, NOTE_PAGES, True))
note_pdf = ROOT / "verify" / "render" / RENDER_TAG / (DOCX.stem + ".pdf")
with pdfplumber.open(str(note_pdf)) as npdf:
    last = npdf.pages[-1]
    bottom = max((w["bottom"] for w in last.extract_words()), default=0.0)
    top_m = sect.top_margin / EMU_PER_PT
    printable = float(last.height) - top_m - sect.bottom_margin / EMU_PER_PT
    c.between("note: page 2 of the render ends above 90 % of the printable height", (bottom - top_m) / printable, 0.0, NOTE_FILL_MAX)
    c.equal("note render: 'Università' extracted from page 1 and no U+FFFD", ("Università" in (npdf.pages[0].extract_text() or ""),
            "�" in "".join(p.extract_text() or "" for p in npdf.pages)), (True, False))
xl_pdf = ROOT / "verify" / "render" / RENDER_TAG / (XLSX.stem + ".pdf")
with pdfplumber.open(str(xl_pdf)) as xpdf:
    c.equal("workbook render: the author line is extracted on the 0.0 page", "Università" in (xpdf.pages[0].extract_text() or ""), True)

c.done()
