"""Acceptance checks for step 8 (plan/plan.md, Amendment 2): the process guide PDF and the investment note in the Ledger identity.

Purpose
    Guide structure (outline, contents links, A4, page count), tags and mapping to the workbook, guide numbers (PDF tokens
    against report/build/guide_numbers.json and every provenance entry), guide substance (final_review.md sections 3 and 4,
    the Gate 2 statement, the six limitations), note numbers against the step-6 baseline, note structure and page, banned
    phrases over guide, note and workbook, fonts and glyphs, determinism (two builds), table fingerprints, and the renders.
Inputs
    report/*.xlsx, *.docx, *.pdf, report/build/guide_numbers.json, report/final_review.md, data/raw/SOURCES.md, evidence packs,
    verify/baseline_amend2/note_tokens.txt, verify/fp_step06.txt, py/doc_map.py, py/ledger_style.py, py/guide_tokens.py.
Outputs
    PASS/FAIL lines on stdout (exit 1 on any FAIL); PNG pages in verify/render/step08/.
Brief definitions implemented
    none (presentation checks). Run after: python run.py --through 7
"""
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path

import duckdb
import openpyxl
import pdfplumber
from docx import Document
from fontTools.ttLib import TTFont as FTFont
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdftypes import resolve1

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "py"))
from _lib import Checks  # noqa: E402
import doc_map  # noqa: E402
import ledger_style as LS  # noqa: E402
from guide_tokens import NUM, WORKBOOK_PREFIX, norm, tokens  # noqa: E402
from note_tokens import note_tokens  # noqa: E402
import banned as BN  # noqa: E402

REPORT = ROOT / "report"
XLSX = REPORT / "DeLonghi_DCF_Valuation.xlsx"
DOCX = REPORT / "DeLonghi_DCF_Valuation_note.docx"
PNG = REPORT / "note_chart.png"
PDF = REPORT / "DeLonghi_DCF_process_guide.pdf"
GJSON = REPORT / "build" / "guide_numbers.json"
BASE = ROOT / "verify" / "baseline_amend2"
FINAL = REPORT / "final_review.md"
DB = ROOT / "data" / "curiosity.duckdb"

A4_W_PT, A4_H_PT, A4_TOL_PT = 595.3, 841.9, 0.5
MAX_PAGES = 20
NOTE_PAGES, NOTE_FILL_MAX = 2, 0.90
EMU_PER_PT = 12700
BANNED_RX, US_RX = BN.BANNED_RX, BN.US_RX            # E1: the extended list of checks/banned.py (step 9)
INTERVIEW_MAX = 0                                      # E1: "interview" no longer appears anywhere
ALLOWED_PDF_FONTS = {"Garamond", "Garamond-Bold", "Garamond-Italic", "GillSansMT", "GillSansMT-Bold", "GillSansMT-Italic",
                     "DejaVuSans"}
LIMITATION_PHRASES = ["book value", "twice", "decides the sign", "narrowly", "no live formulas", "not an investment recommendation"]
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
YEARS = {str(y) for y in range(2020, 2031)}
TAG = re.compile(r"\[(\d\.\d)\]")

c = Checks()


def run(args, **kw):
    return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True, **kw)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def docx_members(p):
    z = zipfile.ZipFile(p)
    return {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}


# ---------------------------------------------------------------- builds (and determinism)
b_note1 = run(["py/06_build_note.py"])
b_guide1 = run(["py/07_process_guide.py"])
c.equal("note builds (rc)", b_note1.returncode, 0)
c.equal("guide builds (rc)", b_guide1.returncode, 0)
if b_note1.returncode or b_guide1.returncode or not PDF.exists():
    print((b_note1.stderr + b_guide1.stderr)[-1500:])
    c.done()
h1 = (sha(PDF), docx_members(DOCX), sha(PNG), sha(GJSON))
b_note2 = run(["py/06_build_note.py"])
b_guide2 = run(["py/07_process_guide.py"])
h2 = (sha(PDF), docx_members(DOCX), sha(PNG), sha(GJSON))
c.equal("second builds succeed", (b_note2.returncode, b_guide2.returncode), (0, 0))
c.equal("two builds: byte-identical PDF", h1[0], h2[0])
c.equal("two builds: identical docx members (all package members)", (h1[1] == h2[1], len(h1[1])), (True, len(h2[1])))
c.equal("two builds: identical chart PNG", h1[2], h2[2])
c.equal("two builds: identical guide_numbers.json", h1[3], h2[3])

# ---------------------------------------------------------------- guide: structure
wb = openpyxl.load_workbook(XLSX)
sheet_names = wb.sheetnames
pdf = pdfplumber.open(str(PDF))
npages = len(pdf.pages)
page_text = [(p.extract_text() or "") for p in pdf.pages]
full_text = "\n".join(page_text)
c.between("guide has at most 20 pages", npages, 1, MAX_PAGES)
bad_size = [(i + 1, round(float(p.width), 1), round(float(p.height), 1)) for i, p in enumerate(pdf.pages)
            if abs(float(p.width) - A4_W_PT) > A4_TOL_PT or abs(float(p.height) - A4_H_PT) > A4_TOL_PT]
c.equal("every guide page is A4 (595.3 x 841.9 pt, 0.5)", bad_size, [])

fh = open(PDF, "rb")
pdoc = PDFDocument(PDFParser(fh))
outline = [(lvl, title) for (lvl, title, _d, _a, _se) in pdoc.get_outlines()]
ids_outline = [re.match(r"§(\S+)", t).group(1) if re.match(r"§(\S+)", t) else t for _l, t in outline]
ids_expected = [s[0] for s in doc_map.SECTIONS]
c.equal("PDF outline ids, in order", ids_outline, ids_expected)

# contents-page links: one per id, landing on the page where the heading appears
pdf_pages = list(PDFPage.create_pages(pdoc))
objid_to_index = {pg.pageid: i for i, pg in enumerate(pdf_pages)}
link_pages = {}
for i, pg in enumerate(pdf_pages):
    n_links = 0
    for a in (resolve1(pg.annots) or []):
        a = resolve1(a)
        if a.get("Subtype") is not None and getattr(a.get("Subtype"), "name", "") == "Link":
            n_links += 1
    if n_links:
        link_pages[i] = n_links
contents_pages = [i for i, n in link_pages.items() if n >= len(ids_expected) - 1]
c.equal("one contents page holds the links", len(contents_pages), 1)
heading_page = {}
for sid, title in doc_map.SECTIONS:
    rx = re.compile(r"^§" + re.escape(sid) + r"\s+" + re.escape(title) + r"\s*$", re.M)
    hits = [i for i, t in enumerate(page_text) if rx.search(t) and i not in contents_pages]
    heading_page[sid] = hits
c.equal("every section heading appears exactly once outside the contents page",
        [k for k, v in heading_page.items() if len(v) != 1], [])
link_targets = []
if contents_pages:
    cp = pdf_pages[contents_pages[0]]
    for a in (resolve1(cp.annots) or []):
        a = resolve1(a)
        dest = a.get("Dest")
        if dest is None and a.get("A") is not None:
            dest = resolve1(a["A"]).get("D")
        dest = resolve1(dest)
        if isinstance(dest, (bytes, str)) or hasattr(dest, "name"):
            name = dest if isinstance(dest, bytes) else (dest.name if hasattr(dest, "name") else dest.encode())
            dest = pdoc.get_dest(name)
        dest = resolve1(dest)
        if isinstance(dest, dict):
            dest = resolve1(dest.get("D"))
        pref = dest[0]
        link_targets.append(objid_to_index.get(getattr(pref, "objid", None)))
    c.equal("contents page: one link annotation per id", len(link_targets), len(ids_expected))
    want = sorted(heading_page[s][0] for s in ids_expected if len(heading_page[s]) == 1)
    c.equal("contents links land on the pages of the headings", sorted(link_targets), want)

# ---------------------------------------------------------------- guide: tags and mapping
sec_ids = ids_expected
sheet_of_sec = {}
for sid in sec_ids:
    if sid in doc_map.NAME_OF_ID and sid != "0.0":
        sheet_of_sec[sid] = [doc_map.NAME_OF_ID[sid]]
    elif sid in ("0.0", "0", "6"):
        sheet_of_sec[sid] = [doc_map.NAME_OF_ID["0.0"]]
    elif sid.startswith("A"):
        sheet_of_sec[sid] = [doc_map.NAME_OF_ID["5.1"]]
    else:
        sheet_of_sec[sid] = [n for k, n in doc_map.NAME_OF_ID.items() if k.startswith(sid + ".")]
bad_wb_line, bad_names = [], []
for sid, title in doc_map.SECTIONS:
    if len(heading_page.get(sid, [])) != 1:
        continue
    lines = page_text[heading_page[sid][0]].split("\n")
    idx = [i for i, ln in enumerate(lines) if re.match(r"^§" + re.escape(sid) + r"\s", ln)]
    nxt = lines[idx[0] + 1].strip() if idx and idx[0] + 1 < len(lines) else ""
    if not nxt.startswith(WORKBOOK_PREFIX):
        bad_wb_line.append((sid, nxt[:40]))
        continue
    names = [x.strip() for x in nxt[len(WORKBOOK_PREFIX):].split(" · ")]
    if names != sheet_of_sec[sid] or any(n not in sheet_names for n in names):
        bad_names.append((sid, names))
c.equal("every section opens with a WORKBOOK line", bad_wb_line, [])
c.equal("WORKBOOK names are existing sheets and match the section", bad_names, [])
bands = {n: str(wb[n]["A1"].value) for n in sheet_names}
band_ids = {n: re.sub(r"^GUIDE ▸ §", "", v) for n, v in bands.items()}
c.equal("every sheet band section id exists as a guide heading", [n for n, i in band_ids.items() if i not in ids_expected], [])
two_part = [i for i in ids_expected if re.fullmatch(r"\d\.\d", i)]
c.equal("two-part numeric ids correspond one-to-one to the 11 sheets", sorted(two_part), sorted(band_ids.values()))

# ---------------------------------------------------------------- guide: numbers
g = json.loads(GJSON.read_text(encoding="utf-8"))
entries = g["entries"]
pdf_tokens = tokens(full_text)
json_tokens = [e["token"].replace(",", "") for e in entries]
first_diff = next((i for i, (a, b) in enumerate(zip(pdf_tokens, json_tokens)) if a != b), None)
c.equal("PDF number tokens equal guide_numbers.json tokens in order (count)", len(pdf_tokens), len(json_tokens))
c.equal("PDF number tokens equal guide_numbers.json tokens in order (first difference)",
        None if first_diff is None else (first_diff, pdf_tokens[first_diff - 2:first_diff + 3], json_tokens[first_diff - 2:first_diff + 3]), None)
c.equal("guide lists at least 100 number tokens", len(entries) >= 100, True)

con = duckdb.connect(str(DB), read_only=True)
unmatched = []
file_cache = {}
for k, e in enumerate(entries):
    tok = e["token"]
    kind = e["kind"]
    ok = False
    if kind == "db":
        v = con.execute(e["sql"]).fetchone()[0]
        ok = [t.replace(",", "") for t in NUM.findall(format(v, e["fmt"]))] == [tok.replace(",", "")]
    elif kind == "db_text":
        v = str(con.execute(e["sql"]).fetchone()[0])
        ok = tok.replace(",", "") in [t.replace(",", "") for t in NUM.findall(v)]
    elif kind == "file":
        lines = file_cache.setdefault(e["file"], (ROOT / e["file"]).read_text(encoding="utf-8").split("\n"))
        hit = [ln for ln in lines if e["anchor"] in ln]
        ok = any(tok.replace(",", "") in [t.replace(",", "") for t in NUM.findall(ln)] and tok in ln.replace("−", "-") for ln in hit) \
            or any(tok.replace(",", "") in [t.replace(",", "") for t in NUM.findall(ln)] for ln in hit)
    elif kind == "file_rows":
        lines = (ROOT / e["file"]).read_text(encoding="utf-8").split("\n")
        n, on = 0, False
        for ln in lines:
            if ln.startswith("#"):
                on = e["heading"] in ln
                continue
            if on and ln.startswith("| ") and not ln.startswith("| File") and not ln.startswith("|--"):
                n += 1
        ok = str(n) == tok
    if not ok:
        unmatched.append((k, kind, tok, e.get("sql") or e.get("anchor") or e.get("heading")))
c.equal("guide numbers: 0 unmatched provenance entries", unmatched[:5], [])
# allowed file sources: plan Design limits, plus evidence/step07.md (recorded deviation, human-accepted; see evidence/step08.md)
ALLOWED_SRC = {"brief/research_brief.md", "plan/plan.md", "evidence/data_quality_log.md", "report/final_review.md", "data/raw/SOURCES.md", "evidence/step07.md"}     | {f"evidence/step0{i}.md" for i in range(1, 7)}
c.equal("guide numbers: file entries only from the allowed source files",
        sorted({e["file"] for e in entries if "file" in e} - ALLOWED_SRC), [])
c.equal("guide numbers: entry kinds are db, db_text, file or file_rows",
        sorted({e["kind"] for e in entries} - {"db", "db_text", "file", "file_rows"}), [])

# ---------------------------------------------------------------- guide: substance
final_txt = FINAL.read_text(encoding="utf-8")
sec3 = final_txt.split("## 3.")[1].split("## 4.")[0]
sec4 = final_txt.split("## 4.")[1].split("## 5.")[0]
rows3 = [ln for ln in sec3.split("\n") if ln.startswith("| ") and not ln.startswith("| Step") and not ln.startswith("|---")]
gnorm = norm(full_text.replace("*", ""))
missing_rows = []
for ln in rows3:
    cells = [x.strip() for x in ln.strip().strip("|").split("|")]
    expl = norm(cells[2].replace("*", "").replace("`", ""))
    first = re.split(r"(?<=[.])\s", expl)[0][:60]
    pos = gnorm.find(first)
    if pos < 0:
        missing_rows.append(("first sentence not found", first))
        continue
    window = gnorm[pos:pos + len(expl) + 400]
    need = tokens(expl)
    have = tokens(window)
    if [t for t in need if t not in have]:
        missing_rows.append(("tokens missing", first, [t for t in need if t not in have]))
c.equal("final_review section 3 has 12 rows", len(rows3), 12)
# E2: the check "every row of final_review section 3 is present in the guide" is replaced by its inverse (see below)

body_pages = [t for i, t in enumerate(page_text) if i not in contents_pages]
body_text = "\n".join(body_pages)
sec_pos = {}
for sid, title in doc_map.SECTIONS:
    m = re.search(r"^§" + re.escape(sid) + r"\s+" + re.escape(title) + r"\s*$", body_text, re.M)
    sec_pos[sid] = m.start() if m else -1


def sec_text(sid):
    k = ids_expected.index(sid)
    end = sec_pos[ids_expected[k + 1]] if k + 1 < len(ids_expected) else len(body_text)
    return body_text[sec_pos[sid]:end]


a1_text = sec_text("A.1")
a1_tokens = set(tokens(a1_text))
cases = [re.sub(r"^\d+\.\s+", "", ln) for ln in sec4.split("\n") if re.match(r"^\d+\.\s", ln)]
c.equal("final_review section 4 has 5 cases", len(cases), 5)
missing_case = []
for i, cs in enumerate(cases, 1):
    need = set(tokens(re.sub(r"`[^`]*`", " ", cs.replace("*", ""))))
    miss = sorted(need - a1_tokens)
    if miss:
        missing_case.append((i, miss))
c.equal("the 5 spot-check cases are in the audit trail with all their numbers", missing_case, [])

s12n = norm(sec_text("1.2"))
c.equal("E3: section 1.2 states the 1-decimal display as accepted on 2026-11-09",
        all(x in s12n for x in ("1 decimal", "accepted", "2026-11-09")), True)
a3_text = norm(sec_text("A.3"))
c.equal("six limitation items are kept", [p for p in LIMITATION_PHRASES if p not in a3_text], [])
c.equal("E2: A.3 states the figures 79.6%, 24.6%, 0.98 and 0.52", [f for f in ("79.6%", "24.6%", "0.98", "0.52") if f not in a3_text], [])
sec15 = norm(" ".join(sec_text(s_) for s_ in ["1", "1.1", "1.2", "2", "2.1", "2.2", "3", "3.1", "3.2", "3.3", "4", "4.1", "4.2", "5", "5.1"]))
absent_rows = []
for ln in rows3:
    expl = norm([x.strip() for x in ln.strip().strip("|").split("|")][2].replace("*", "").replace("`", ""))
    first = re.split(r"(?<=[.])\s", expl)[0][:60]
    if first in sec15:
        absent_rows.append(first)
c.equal("E2 (requirement 6): none of the 12 final_review section-3 explanations appears in guide sections 1-5", absent_rows, [])
s6_n = norm(sec_text("6"))
c.equal("E5: section 6 holds the new figure-matching sentence and not the old one",
        ("Each figure in the note was matched by script, at the display precision of the cell, against a cell on the sheet named by its tag; "
         "dates and year labels are not figures and are exempt." in s6_n, "Every number in the note was checked by script" in s6_n), (True, False))

# ---------------------------------------------------------------- note: numbers and structure
doc = Document(str(DOCX))
base_tokens = Counter(t.replace(",", "") for t in (BASE / "note_tokens.txt").read_text(encoding="utf-8").split())
new_tokens = Counter(t.replace(",", "") for t in note_tokens(DOCX, strip_tags=True))
# Baseline: 55 tokens. Three tokens carried no workbook cell of their own ("25" from "FY2024-25", "5" and "95" from "5th to 95th"
# matched other cells only by coincidence), so the sentences were reworded in words; listed in evidence/step08.md.
REWORDED = Counter({"25": 1, "5": 1, "95": 1})
c.equal("baseline file lists the tokens of the verified step-6 note (61; evidence packs say 55)", sum(base_tokens.values()), 61)
c.equal("note tokens: baseline minus new equals the 3 listed rewordings", base_tokens - new_tokens, REWORDED)
c.equal("note tokens: nothing added to the baseline", new_tokens - base_tokens, Counter())
head_texts = [p.text.strip() for p in doc.paragraphs if p.style.name.startswith("Heading")]
c.equal("note: the 5 headings unchanged, in order", head_texts,
        ["Thesis", "Main assumptions", "Valuation range", "Risks", "Conclusion vs market price"])
n_media = len([n for n in zipfile.ZipFile(DOCX).namelist() if n.startswith("word/media/")])
c.equal("note: 1 picture and 1 media file", (len(doc.inline_shapes), n_media), (1, 1))
text_note = "\n".join(p.text for p in doc.paragraphs)
c.between("note: at most 900 words", len(re.findall(r"\S+", text_note)), 1, 900)
sentence = con.execute("SELECT display FROM report_headline WHERE key = 'sentence'").fetchone()[0]
paras = [p.text for p in doc.paragraphs]
c.equal("note: headline paragraph equals report_headline", sentence in paras, True)
hi = paras.index(sentence) if sentence in paras else -1
c.equal("note: tags of the headline sit in the next paragraph", bool(TAG.search(paras[hi + 1])) if hi >= 0 else False, True)
risk, on = [], False
for p in doc.paragraphs:
    if p.style.name.startswith("Heading"):
        on = p.text.strip() == "Risks"
        continue
    if on:
        risk.append(p.text.lower())
risk = " ".join(risk)
for ph in ["minorities at book", "italy risk double counting", "low europe industry beta"]:
    c.equal(f"note: Risks names {ph}", ph in risk, True)

sect = doc.sections[0]
c.near("note page width (EMU, 1%)", sect.page_width, 7_560_000, rel=0.01)
c.near("note page height (EMU, 1%)", sect.page_height, 10_692_000, rel=0.01)

# ---------------------------------------------------------------- banned phrases
wb_strings = [str(cell.value) for ws in wb.worksheets for row in ws.iter_rows() for cell in row
              if isinstance(cell.value, str)]
note_extra = [cell.text for t_ in doc.tables for row_ in t_.rows for cell in row_.cells]
for s_ in doc.sections:
    for part_ in (s_.header, s_.footer, s_.first_page_header, s_.first_page_footer, s_.even_page_header, s_.even_page_footer):
        note_extra += [p_.text for p_ in part_.paragraphs]
docs_text = {"guide": full_text, "note": "\n".join(paras + note_extra), "workbook": "\n".join(wb_strings)}
for name, t in docs_text.items():
    hits = sorted({m.group(0).lower() for m in BANNED_RX.finditer(t)} | {m.group(0) for m in US_RX.finditer(t)})
    c.equal(f"banned phrases in {name}: 0 hits", hits, [])
iv_pages = [i for i, t in enumerate(page_text) if re.search(r"interview", t, re.I)]
iv_n = len(re.findall(r"interview", full_text, re.I))
s0_page = heading_page.get("0", [npages])[0] if heading_page.get("0") else npages
c.between("'interview' appears at most 3 times", iv_n, 0, INTERVIEW_MAX)
c.equal("'interview' appears only on the section 0.0 pages", [p for p in iv_pages if p > s0_page], [])

# ---------------------------------------------------------------- fonts and glyphs
def base_name(bf):
    n = bf.name if hasattr(bf, "name") else str(bf)
    return n.split("+")[-1]


pdf_fonts, no_embed = set(), []
for i, pg in enumerate(pdf_pages):
    res = resolve1(pg.resources) or {}
    for key, ref in (resolve1(res.get("Font")) or {}).items():
        f = resolve1(ref)
        nm = base_name(resolve1(f.get("BaseFont")))
        pdf_fonts.add(nm)
        d = f
        if getattr(resolve1(f.get("Subtype")), "name", "") == "Type0":
            d = resolve1(resolve1(f["DescendantFonts"])[0])
        fd = resolve1(d.get("FontDescriptor"))
        if fd is None or fd.get("FontFile2") is None:
            no_embed.append(nm)
c.equal("PDF fonts all embedded (FontFile2)", sorted(set(no_embed)), [])
c.equal("PDF font set within the allowed set", sorted(pdf_fonts - ALLOWED_PDF_FONTS), [])
cmaps = {}
def cmap_for(name):
    if name not in cmaps:
        path = LS.dejavu_path() if name == "DejaVuSans" else LS.TTF[name]
        cmaps[name] = set(FTFont(str(path)).getBestCmap().keys())
    return cmaps[name]
bad_glyph, dejavu_chars, fffd = [], set(), 0
for pg in pdf.pages:
    for ch in pg.chars:
        nm = ch["fontname"].split("+")[-1]
        t = ch["text"]
        if "�" in t:
            fffd += 1
        if nm == "DejaVuSans":
            dejavu_chars.add(t)
        if nm in ALLOWED_PDF_FONTS and t.strip() and ord(t[0]) not in cmap_for(nm):
            bad_glyph.append((nm, t))
c.equal("PDF: every character is in its font's cmap", bad_glyph[:5], [])
c.equal("PDF: DejaVuSans used only for the arrow", sorted(dejavu_chars - {LS.ARROW}), [])
c.equal("PDF: no U+FFFD", fffd, 0)

zf = zipfile.ZipFile(DOCX)
xml_all = {n: zf.read(n).decode("utf-8") for n in ("word/document.xml", "word/styles.xml") if n in zf.namelist()}
fonts_docx = set()
for x in xml_all.values():
    for m in re.finditer(r"<w:rFonts\b([^>]*)/?>", x):
        for a in re.finditer(r'w:(ascii|hAnsi|cs|eastAsia)="([^"]*)"', m.group(1)):
            fonts_docx.add(a.group(2))
        if "Theme" in m.group(1):
            fonts_docx.add("THEME:" + m.group(1)[:30])
c.equal("docx fonts within {Garamond, Gill Sans MT}", sorted(fonts_docx - {"Garamond", "Gill Sans MT"}), [])
colors = set()
for x in xml_all.values():
    colors |= set(re.findall(r'<w:color\b[^>]*w:val="([^"]*)"', x))
c.equal("docx w:color values within the palette or auto", sorted(v for v in colors if v.upper() not in LS.PALETTE and v != "auto"), [])
c.equal("docx: no themeColor attribute in the styles", len(re.findall(r"w:themeColor", xml_all.get("word/styles.xml", ""))), 0)

# chart colours: every colour carried by more than 0.5 % of the pixels is close to a palette colour
from PIL import Image  # noqa: E402
im = Image.open(PNG).convert("RGB")
cnt = Counter(im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata())
tot = sum(cnt.values())
pal = [tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for h in LS.PALETTE]
far = [(col, round(n / tot, 4)) for col, n in cnt.items() if n / tot > 0.005 and min(sum((a - b) ** 2 for a, b in zip(col, p)) for p in pal) > 3]
c.equal("chart: dominant colours are palette colours", far, [])

# ---------------------------------------------------------------- fingerprints and regression
fp_lines = [ln for ln in (ROOT / "verify" / "fp_step06.txt").read_text(encoding="utf-8").split("\n") if ln.strip()]
tables = [ln.split("\t")[0] for ln in fp_lines]
fp = run(["checks/fingerprint.py", "--compare", "verify/fp_step06.txt", *tables])
c.equal("the 24 table fingerprints equal verify/fp_step06.txt", (len(tables), fp.returncode), (24, 0))
c.equal("checks/fingerprint.py is unchanged against HEAD",
        subprocess.run(["git", "diff", "--stat", "HEAD", "--", "checks/fingerprint.py"], cwd=ROOT, capture_output=True, text=True).stdout.strip(), "")

# ---------------------------------------------------------------- code hygiene, registration
HEX_RX = re.compile(r"#[0-9A-Fa-f]{6}|[\"'][0-9A-Fa-f]{6}[\"']")
hex_hits = {}
for f in sorted((ROOT / "py").glob("*.py")):
    if f.name == "ledger_style.py":
        continue
    txt = f.read_text(encoding="utf-8")
    found = HEX_RX.findall(txt) + [h for h in ("1F3864", "2F5597", "EEF2F8") if h in txt]
    if found:
        hex_hits[f.name] = found
c.equal("no hex colour literal in py/*.py outside ledger_style.py (no exemption)", hex_hits, {})
c.equal("py/07_verify_guide.py is deleted (superseded)", (ROOT / "py" / "07_verify_guide.py").exists(), False)
run_py = (ROOT / "run.py").read_text(encoding="utf-8")
c.equal("run.py registers step 7 with the process guide", 'py/07_process_guide.py' in run_py, True)
c.equal("run.py keeps step 6 on the note builder", 'py/06_build_note.py' in run_py, True)

# ---------------------------------------------------------------- renders (visual check material)
sys.path.insert(0, str(HERE))
import render_png  # noqa: E402
g_png = render_png.render(PDF, "step08")
n_png = render_png.render(DOCX, "step08")
c.equal("guide PNG pages rendered (one per page)", len(g_png), npages)
c.equal("note renders to exactly 2 pages", len(n_png), NOTE_PAGES)
note_pdf = ROOT / "verify" / "render" / "step08" / (DOCX.stem + ".pdf")
with pdfplumber.open(str(note_pdf)) as npdf:
    last = npdf.pages[-1]
    words = last.extract_words()
    bottom = max((w["bottom"] for w in words), default=0.0)
    top_m = sect.top_margin / EMU_PER_PT
    printable = float(last.height) - top_m - sect.bottom_margin / EMU_PER_PT
    c.between("note page 2: last text line ends above 90 % of the printable height",
              (bottom - top_m) / printable, 0.0, NOTE_FILL_MAX)
c.done()
