"""Acceptance checks for step 6 (plan/plan.md): the investment note report/DeLonghi_DCF_Valuation_note.docx.

Checks: every number in the note matches a value displayed in the workbook (formatted with the cell's own number format,
i.e. at brief precision), except years/dates on an allowlist; exactly 1 picture; <= 900 words; the 5 section headings;
headline sentence identical to report_headline; the risks section names the 3 simplifications.
Step 8 additions (non-weakening): "[x.y]" tags are dropped before the number match only when x.y is a py/doc_map.py sheet
id; the page is A4; every sentence with a number carries at least one tag, every tag is a sheet id, and every number is
displayed (at its own number format) on a sheet tagged in the same sentence.
The note is rebuilt by running py/06_build_note.py first.
"""
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import duckdb
import openpyxl
from docx import Document

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "py"))
from _lib import Checks  # noqa: E402
from doc_map import SHEETS  # noqa: E402

SHEET_IDS = [s_[0] for s_ in SHEETS]
TAG = re.compile(r"\[(\d\.\d)\]")
A4_W_EMU, A4_H_EMU, A4_TOL = 7_560_000, 10_692_000, 0.01

XLSX = ROOT / "report" / "DeLonghi_DCF_Valuation.xlsx"
DOCX = ROOT / "report" / "DeLonghi_DCF_Valuation_note.docx"
PNG = ROOT / "report" / "note_chart.png"
SCRIPT = ROOT / "py" / "06_build_note.py"
MAX_WORDS = 900
HEADINGS = ["Thesis", "Main assumptions", "Valuation range", "Risks", "Conclusion vs market price"]
RISK_PHRASES = ["minorities at book", "Italy risk double counting", "low Europe industry beta"]
YEARS = {str(y) for y in range(2020, 2031)}
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"

built = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
print(f"build py/06_build_note.py rc={built.returncode} {built.stderr[-300:] if built.returncode else ''}")


def fmt(v, nf):
    if nf == "#,##0":
        return f"{v:,.0f}"
    if nf == "0.0%":
        return f"{v * 100:.1f}%"
    if nf == "0.00%":
        return f"{v * 100:.2f}%"
    if nf in ("0.00", "0.000", "0.0", "0.0000", "0"):
        return f"{v:.{len(nf.split('.')[1]) if '.' in nf else 0}f}"
    if nf == '0.0"x"':
        return f"{v:.1f}x"
    return None


def tokens(text):
    return {t.replace(",", "") for t in NUM.findall(text)}


c = Checks()
c.equal("note builds", built.returncode, 0)
c.equal("docx and chart png exist", (DOCX.exists(), PNG.exists()), (True, True))
if built.returncode or not DOCX.exists():
    c.done()

# displayed values of the workbook (numeric cells at their own format; plus the headline sentence and display column)
wb = openpyxl.load_workbook(XLSX)
shown = set()
for ws in wb.worksheets:
    for row in ws.iter_rows():
        for cell in row:
            v = cell.value
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                s = fmt(v, cell.number_format)
                if s:
                    shown |= tokens(s)
val = wb["3.2 Valuation"]       # Amendment 2: headline in A3; the display column of the headline block is D (B is the label)
shown |= tokens(val["A3"].value)
for r in range(7, 16):
    shown |= tokens(str(val.cell(row=r, column=4).value))

doc = Document(str(DOCX))
paras = [p.text for p in doc.paragraphs]
for t in doc.tables:
    for row in t.rows:
        paras += [cell.text for cell in row.cells]
text = "\n".join(paras)

# allowlist: dates, years, H1/FY labels, the "80%" in "80% Monte Carlo range", "5-year" style counts
tags_found = TAG.findall(text)
text_notags = TAG.sub(lambda m: " " if m.group(1) in SHEET_IDS else m.group(0), text)
scrub = re.sub(rf"\b\d{{1,2}} (?:{MONTHS}) \d{{4}}", " ", text_notags)
scrub = re.sub(r"80% Monte Carlo", " ", scrub)
scrub = re.sub(r"\b(?:FY|H)\d+E?\b", " ", scrub)
found = NUM.findall(scrub)
unmatched = []
for t in found:
    k = t.replace(",", "")
    if k in YEARS or k in shown:
        continue
    unmatched.append(t)
c.equal("numbers in note: count found > 20", len(found) > 20, True)
c.equal("zero unmatched numbers (vs workbook displayed values)", unmatched, [])

n_media = len([n for n in zipfile.ZipFile(DOCX).namelist() if n.startswith("word/media/")])
c.equal("exactly 1 picture (inline shapes)", len(doc.inline_shapes), 1)
c.equal("exactly 1 media file in package", n_media, 1)
words = len(re.findall(r"\S+", text))
c.between("word count <= 900", words, 1, MAX_WORDS)

head_texts = [p.text.strip() for p in doc.paragraphs if p.style.name.startswith("Heading")]
for h in HEADINGS:
    c.equal(f"heading present: {h}", h in head_texts, True)

con = duckdb.connect(str(ROOT / "data" / "curiosity.duckdb"), read_only=True)
sentence = con.execute("SELECT display FROM report_headline WHERE key = 'sentence'").fetchone()[0]
c.equal("headline sentence in note identical to report_headline", sentence in paras, True)
c.equal("headline sentence identical to '3.2 Valuation'!A3", val["A3"].value, sentence)

# risks section text
idx = head_texts.index("Risks") if "Risks" in head_texts else -1
body = [p for p in doc.paragraphs]
risk_txt, on = [], False
for p in body:
    if p.style.name.startswith("Heading"):
        on = p.text.strip() == "Risks"
        continue
    if on:
        risk_txt.append(p.text)
risk_all = " ".join(risk_txt).lower()
for ph in RISK_PHRASES:
    c.equal(f"risks section names: {ph}", ph.lower() in risk_all, True)

# ---- step 8 additions: A4 page, tags and the tag-sheet match ----
sect = doc.sections[0]
c.near("page width is A4 (7,560,000 EMU, 1%)", sect.page_width, A4_W_EMU, rel=A4_TOL)
c.near("page height is A4 (10,692,000 EMU, 1%)", sect.page_height, A4_H_EMU, rel=A4_TOL)
c.equal("every tag is one of the 11 sheet ids", sorted(set(tags_found) - set(SHEET_IDS)), [])
c.equal("note carries at least one tag", len(tags_found) > 0, True)

shown_by_sheet = {}
for sid, name, _ in SHEETS:
    sh = set()
    for row in wb[name].iter_rows():
        for cell in row:
            v = cell.value
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                s_ = fmt(v, cell.number_format)
                if s_:
                    sh |= tokens(s_)
    shown_by_sheet[sid] = sh
shown_by_sheet["3.2"] |= tokens(val["A3"].value)
for r in range(7, 16):
    shown_by_sheet["3.2"] |= tokens(str(val.cell(row=r, column=4).value))
shown_by_sheet["0.0"] |= tokens(wb[SHEETS[0][1]]["A3"].value or "")

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def scrub_note(t):
    t = re.sub(rf"\b\d{{1,2}} (?:{MONTHS}) \d{{4}}", " ", t)
    t = re.sub(r"80% Monte Carlo", " ", t)
    return re.sub(r"\b(?:FY|H)\d+E?\b", " ", t)


body_paras = [p for p in doc.paragraphs if not p.style.name.startswith(("Heading", "Title"))]
bad_untagged, bad_tokens = [], []
for i, p in enumerate(body_paras):
    if p.text.strip() == sentence:                       # headline paragraph: its tags sit in the next paragraph
        nxt_tags = set(TAG.findall(body_paras[i + 1].text)) if i + 1 < len(body_paras) else set()
        c.equal("headline paragraph is followed by a tags paragraph", len(nxt_tags) > 0, True)
        miss = [t for t in tokens(scrub_note(p.text)) if t not in YEARS and not any(t in shown_by_sheet.get(x, set()) for x in nxt_tags)]
        c.equal("headline numbers are displayed on the sheets tagged in the next paragraph", miss, [])
        continue
    for sent in SENT_SPLIT.split(p.text):
        tg = set(TAG.findall(sent))
        toks = [t for t in tokens(scrub_note(TAG.sub(" ", sent))) if t not in YEARS]
        if not toks:
            continue
        if not tg:
            bad_untagged.append(sent[:60])
            continue
        for t in toks:
            if not any(t in shown_by_sheet.get(x, set()) for x in tg):
                bad_tokens.append((t, sorted(tg), sent[:50]))
c.equal("every sentence with a number carries a tag", bad_untagged, [])
c.equal("every number is displayed on a sheet tagged in the same sentence", bad_tokens, [])
c.done()
