"""Steps 6 and 8: write the 2-page investment note report/DeLonghi_DCF_Valuation_note.docx and its chart report/note_chart.png.

Purpose
    Turn the verified workbook into a short note (Thesis, Main assumptions, Valuation range, Risks, Conclusion vs market
    price) with one chart, in the Ledger identity (A4, ivory paper, Garamond headings, Gill Sans MT body, one vermilion accent).
    Every number is read back from report/DeLonghi_DCF_Valuation.xlsx and printed at the workbook's own display precision (the
    cell's number format), so the note cannot disagree with the workbook. Every sentence that carries a number ends with the
    sheet tags "[x.y]" of the sheets its figures were read from; the headline paragraph is followed by a paragraph with its tag.

Inputs
    report/DeLonghi_DCF_Valuation.xlsx (numbers and the headline sentence in '3.2 Valuation'!A3), DuckDB tables report_headline
    (sentence is asserted identical to '3.2 Valuation'!A3) and mc_histogram (chart bars), py/ledger_style.py, py/doc_map.py.
Outputs
    report/DeLonghi_DCF_Valuation_note.docx, report/note_chart.png (Monte Carlo histogram with market price and base value lines).
    Both are byte-reproducible (fixed document dates, fixed zip member order and times).

Brief definitions implemented (by term)
    Section 6 "Investment note" (thesis, main assumptions, valuation range, risks, conclusion vs market price; one chart;
    every number in the verified workbook) and "Precision" (EUR m no decimals, EUR per share 2 decimals, % 1 decimal, WACC
    and g 2 decimals, multiples 1 decimal). The Amendment's stated simplifications (minorities at book value, Italy risk
    double counting, low Europe industry beta) are named in the Risks section.

Step 9 (Amendment 3): the author line sits under the title; the document author is doc_map.AUTHOR_NAME.

Rule: no analysis numbers are typed here. Only layout constants (font sizes, widths) appear as named constants.
"""
import io
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import openpyxl  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.text import WD_BREAK  # noqa: E402,F401
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Mm, Pt, RGBColor  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "py"))
import doc_map  # noqa: E402
import ledger_style as LS  # noqa: E402

DB = ROOT / "data" / "curiosity.duckdb"
XLSX = ROOT / "report" / "DeLonghi_DCF_Valuation.xlsx"
DOCX = ROOT / "report" / "DeLonghi_DCF_Valuation_note.docx"
PNG = ROOT / "report" / "note_chart.png"

PAGE_W_MM, PAGE_H_MM = 210, 297                      # A4
MARGIN_MM, MARGIN_TOP_MM = 18, 16
PIC_W_MM, PIC_H_MM, DPI = 150, 64, 150
TAG_PT, TITLE_PT, SPACE_AFTER_PT, LINE_SPACING = 8, 22, 3, 1.1
FIXED_DT = datetime(2026, 11, 9)
ZIP_TIME = (2026, 11, 9, 0, 0, 0)
FIG_W, FIG_H, BAR_FILL = 7.0, 3.0, 0.95
FMT_DECIMALS = {"0.00": 2, "0.000": 3, "0.0": 1, "0.0000": 4, "0": 0}
TAG_RX = re.compile(r"(\[\d\.\d\])")

wb = openpyxl.load_workbook(XLSX)
USED = []                                            # sheet ids of the figures read since the last sentence ended


def fmt(cell):
    """Display string of a numeric cell at its own number format (same rule as the workbook display); records the sheet."""
    v, nf = cell.value, cell.number_format
    USED.append(doc_map.SHEET_ID[cell.parent.title])
    if nf == "#,##0":
        return f"{v:,.0f}"
    if nf == "0.0%":
        return f"{v * 100:.1f}%"
    if nf == "0.00%":
        return f"{v * 100:.2f}%"
    if nf == '0.0"x"':
        return f"{v:.1f}x"
    if nf in FMT_DECIMALS:
        return f"{v:.{FMT_DECIMALS[nf]}f}"
    raise ValueError(f"unhandled number format {nf!r} at {cell.coordinate}")


def sent(text):
    """Close a sentence: put the tags of the sheets used since the last sentence in front of its final full stop."""
    tags = sorted(set(USED))
    USED.clear()
    if not tags:
        return text
    assert text.endswith("."), text
    return text[:-1] + "".join(f" [{t}]" for t in tags) + "."


def find(ws, label, col=1, start=1):
    for r in range(start, ws.max_row + 1):
        if ws.cell(row=r, column=col).value == label:
            return r
    raise KeyError(label)


def numcell(ws, label, start=1, last_col=5):
    """Numeric cell on the row labelled `label` (column A): the right-most numeric value in columns B..last_col."""
    r = find(ws, label, 1, start)
    cells = [ws.cell(row=r, column=k) for k in range(2, last_col + 1)]
    nums = [x for x in cells if isinstance(x.value, (int, float)) and not isinstance(x.value, bool)]
    return nums[-1]


# Amendment 2: sheet names are the numbered ones; on these four label sheets column B holds the readable label,
# so every value column is one to the right of its step-5 position.
V, W, F, M = (wb[doc_map.NAME_OF_ID[k]] for k in ("3.2", "2.1", "3.1", "4.2"))
r_val = find(V, "Item")                                   # start of the valuation line items
r_tab = find(W, "Item")                                   # start of the base / beta_sensitivity table
r_bs = find(W, "Beta sensitivity line")
r_reg = find(V, "Region")


def val(label):
    return numcell(V, label, r_val)


def top(label):                                           # headline block, value in column B
    return numcell(V, label, 1, 3)


def wacc_in(label):
    return numcell(W, label, 1, 3)


def wacc_tab(label, col):
    return W.cell(row=find(W, label, 1, r_tab), column=col)


def bsens(label):
    return numcell(W, label, r_bs, 3)


def f_first(label):
    return F.cell(row=find(F, label), column=3)


def assump(label):
    return numcell(F, label, find(F, "Driver"), 4)


def mc(label):
    return numcell(M, label, 1, 3)


def disp(label):                                          # text display in column D of the headline block (sheet 3.2)
    USED.append(doc_map.SHEET_ID[V.title])
    return V.cell(row=find(V, label), column=4).value


sentence = V["A3"].value
con = duckdb.connect(str(DB), read_only=True)
db_sentence = con.execute("SELECT display FROM report_headline WHERE key = 'sentence'").fetchone()[0]
assert sentence == db_sentence, "3.2 Valuation!A3 differs from report_headline"
bins = con.execute("SELECT bin_lo, bin_hi, count FROM mc_histogram ORDER BY bin_lo").fetchall()
con.close()

r_eu, r_gl = find(V, "Europe", 1, r_reg), find(V, "Global", 1, r_reg)
exit_eu_x, exit_eu_v = V.cell(row=r_eu, column=4), V.cell(row=r_eu, column=5)
exit_gl_x, exit_gl_v = V.cell(row=r_gl, column=4), V.cell(row=r_gl, column=5)

# ---------------------------------------------------------------- chart (palette only)
price, base = top("price").value, top("value_per_share").value
width = (bins[0][1] - bins[0][0]) * BAR_FILL
plt.rcParams.update(LS.mpl_rc())
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.bar([(lo + hi) / 2 for lo, hi, _ in bins], [n for _, _, n in bins], width=width, color=LS.mpl_hex(LS.GREY),
       edgecolor=LS.mpl_hex(LS.PAPER), linewidth=0, antialiased=False)
ax.axvline(price, color=LS.mpl_hex(LS.VERMILION), lw=2, label=f"Market price EUR {fmt(top('price'))}")
ax.axvline(base, color=LS.mpl_hex(LS.INK), lw=2, ls="--", label=f"Base case EUR {fmt(top('value_per_share'))}")
USED.clear()
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
ax.set_xlabel("Value per share (EUR)")
ax.set_ylabel("Number of runs")
ax.set_title("Monte Carlo distribution of value per share", loc="left", fontweight="bold")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(PNG, dpi=DPI, facecolor=LS.mpl_hex(LS.PAPER), metadata={"Software": None})
plt.close(fig)

# ---------------------------------------------------------------- note
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Mm(PAGE_W_MM), Mm(PAGE_H_MM)
sec.left_margin = sec.right_margin = sec.bottom_margin = Mm(MARGIN_MM)
sec.top_margin = Mm(MARGIN_TOP_MM)

st = doc.styles
st["Normal"].font.name, st["Normal"].font.size = LS.BODY_FONT, Pt(LS.BODY_PT)
st["Normal"].paragraph_format.space_after = Pt(SPACE_AFTER_PT)
st["Normal"].paragraph_format.line_spacing = LINE_SPACING
st["List Bullet"].font.name, st["List Bullet"].font.size = LS.BODY_FONT, Pt(LS.BODY_PT)
st["Title"].font.name, st["Title"].font.size = LS.HEAD_FONT, Pt(TITLE_PT)
st["Heading 1"].font.name, st["Heading 1"].font.size = LS.HEAD_FONT, Pt(LS.HEAD_PT + 1)
for name in ("Title", "Heading 1"):
    st[name].font.bold = True
    st[name].font.color.rgb = RGBColor.from_string(LS.INK)
st["Heading 1"].paragraph_format.space_before = Pt(8)
st["Heading 1"].paragraph_format.space_after = Pt(2)
st["Title"].paragraph_format.space_after = Pt(4)


def hairline_below(paragraph):
    ppr = paragraph._p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for k, v in (("w:val", "single"), ("w:sz", "4"), ("w:space", "1"), ("w:color", LS.HAIRLINE)):
        bottom.set(qn(k), v)
    bdr.append(bottom)
    ppr.append(bdr)


def runs(paragraph, text, kind="body", size=LS.BODY_PT, bold=False, italic=False):
    """Add `text` as runs; the sheet tags are set smaller and grey."""
    for piece in TAG_RX.split(text):
        if not piece:
            continue
        run = paragraph.add_run(piece)
        if TAG_RX.fullmatch(piece):
            LS.docx_run_font(run, "body", TAG_PT, False, False, LS.GREY)
        else:
            LS.docx_run_font(run, kind, size, bold, italic, LS.INK)


def body(text, style=None):
    p = doc.add_paragraph(style=style)
    runs(p, text)
    return p


def heading(text, level):
    p = doc.add_heading(level=level)
    if level == 0:
        runs(p, text, "head", TITLE_PT, True)
        hairline_below(p)
    else:
        runs(p, text, "head", LS.HEAD_PT + 1, True)
    return p


def bullets(items):
    for t in items:
        body(t, "List Bullet")


heading("De'Longhi: DCF investment note", 0)

# author line (step 9, Amendment 3): one Normal-style paragraph directly under the title, small grey plain text
author_p = doc.add_paragraph()
LS.docx_run_font(author_p.add_run(doc_map.AUTHOR_LINE), "body", LS.SMALL_PT, False, False, LS.GREY)

# headline paragraph (equal to report_headline); the key result is set in the accent colour; the tag follows in the next paragraph
p = doc.add_paragraph()
key = f"EUR {fmt(top('value_per_share'))}"
USED.clear()
head, _, tail = sentence.partition(key)
assert _ == key
for txt, accent in ((head, False), (key, True), (tail, False)):
    if txt:
        run = p.add_run(txt)
        LS.docx_run_font(run, "head", LS.HEADLINE_PT, accent, not accent, LS.VERMILION if accent else LS.INK)
body("Figures above: [" + doc_map.SHEET_ID[V.title] + "].")

heading("Thesis", 1)
body(" ".join([
    sent(f"The discounted cash flow values De'Longhi at EUR {fmt(top('value_per_share'))} per share, against a market price of "
         f"EUR {fmt(top('price'))} on 6 November 2026."),
    sent(f"Enterprise value is EUR {fmt(val('ev'))} m, of which the terminal value is {fmt(val('tv_share_of_ev'))}."),
    sent(f"The company holds net cash: cash of EUR {fmt(val('cash'))} m and cash-like financial assets of "
         f"EUR {fmt(val('cash_like_financial_assets'))} m exceed bank debt, other financial payables and leases."),
    sent(f"After deducting those liabilities, the 2026 distributions of EUR {fmt(val('distributions_2026'))} m and minorities, equity "
         f"value is EUR {fmt(val('equity_value'))} m on {fmt(val('diluted_shares'))} m diluted shares."),
    "The shares therefore look moderately cheap, and the size of the gap depends mainly on the discount rate."]))

heading("Main assumptions", 1)
bullets([
    " ".join([sent(f"Revenue grows {fmt(f_first('growth'))} in FY2026E (midpoint of the mid-single-digit guidance) and fades linearly "
                   f"towards the terminal growth rate g of {fmt(val('terminal_g'))}.")]),
    " ".join([sent(f"The adjusted EBIT margin starts at {fmt(f_first('adj_ebit_margin'))} in FY2026E (derived from the adjusted EBITDA "
                   f"guidance of EUR {fmt(assump('guidance_adj_ebitda_fy2026'))} m) and fades to "
                   f"{fmt(assump('adj_ebit_margin_target_fy2030'))} by FY2030E, the average of FY2024 and FY2025."),
              sent(f"The forecast tax rate is {fmt(assump('tax_rate_forecast'))}.")]),
    " ".join([sent(f"Cost of equity is {fmt(wacc_tab('ke', 3))}: risk-free rate {fmt(wacc_in('rf'))}, relevered beta "
                   f"{fmt(wacc_tab('beta_l', 3))} (unlevered Damodaran Europe Furniture/Home Furnishings beta "
                   f"{fmt(wacc_in('beta_u_base'))}), mature equity risk premium {fmt(wacc_in('erp_mature'))} plus an Italy default "
                   f"spread of {fmt(wacc_in('country_spread'))}."),
              sent(f"After-tax cost of debt is {fmt(wacc_in('kd_post'))} at a debt weight of {fmt(wacc_in('w_d'))}."),
              sent(f"The resulting WACC is {fmt(val('wacc'))}.")]),
])

heading("Valuation range", 1)
body(" ".join([
    sent(f"A Monte Carlo of growth, margin and WACC gives an 80% range of EUR {fmt(top('mc_p10'))} to EUR {fmt(top('mc_p90'))} "
         f"per share, with a median of EUR {fmt(mc('p50'))} and a band from the fifth to the ninety-fifth percentile of EUR {fmt(mc('p5'))} to "
         f"EUR {fmt(mc('p95'))}."),
    sent(f"The market price sits at the {disp('price_percentile_ordinal')} percentile of the simulated values."),
    sent(f"An exit-multiple cross-check gives EUR {fmt(exit_eu_v)} per share at the Damodaran Europe multiple of "
         f"{fmt(exit_eu_x)} and EUR {fmt(exit_gl_v)} at the Global multiple of {fmt(exit_gl_x)}, both below the Gordon-growth value.")]))
pic = doc.add_paragraph()
pic.paragraph_format.space_after = Pt(0)
pic.add_run().add_picture(str(PNG), width=Mm(PIC_W_MM), height=Mm(PIC_H_MM))

heading("Risks", 1).paragraph_format.page_break_before = True
bullets([
    " ".join([sent(f"Beta dominates. The base case uses the low Europe industry beta of {fmt(wacc_in('beta_u_base'))}."),
              sent(f"With the Global Furniture/Home Furnishings beta of {fmt(bsens('beta_u'))} the WACC is {fmt(bsens('wacc'))} and value "
                   f"falls to EUR {fmt(bsens('value_per_share'))} per share ({fmt(bsens('pct_vs_base'))}), below the market price.")]),
    " ".join(["Minorities at book value are deducted in the equity bridge. This is a simplification that likely understates the "
              "minorities' share of value",
              sent(f"(book value EUR {fmt(val('minority_book'))} m).")]),
    "Italy risk double counting: the risk-free rate is an Italian government yield and the cost of equity also adds an "
    "Italy default spread, which raises the discount rate and lowers value. This is a stated limitation.",
    " ".join([sent(f"Terminal value is {fmt(val('tv_share_of_ev'))} of enterprise value, so small changes in WACC or g move the answer "
                   f"materially."),
              sent(f"The FY2026E margin of {fmt(f_first('adj_ebit_margin'))} sits above the five-year average, and the forecast fades it.")]),
])

heading("Conclusion vs market price", 1)
body(" ".join([
    sent(f"At EUR {fmt(top('price'))} the market price is {disp('pct_vs_base')} the base-case value of "
         f"EUR {fmt(top('value_per_share'))}, but it lies inside the 80% range (EUR {fmt(top('mc_p10'))} to "
         f"EUR {fmt(top('mc_p90'))}) and only just above its lower end."),
    "The base case is therefore a moderately positive signal, not a clear mispricing, and it relies on a low-beta discount rate.",
    "With the higher Global beta the value is below the price.",
    "The shares can be read as fairly valued to moderately undervalued."]))

cp = doc.core_properties
cp.author, cp.last_modified_by, cp.created, cp.modified = doc_map.AUTHOR_NAME, doc_map.AUTHOR_NAME, FIXED_DT, FIXED_DT
cp.comments = ""
cp.title = "De'Longhi DCF note"

# ivory page background (w:background + displayBackgroundShape)
bg = OxmlElement("w:background")
bg.set(qn("w:color"), LS.PAPER)
doc.element.insert(0, bg)
settings = doc.settings.element
dbs = OxmlElement("w:displayBackgroundShape")
settings.insert(0, dbs)

buf = io.BytesIO()
doc.save(buf)


# ---------------------------------------------------------------- post-process: palette and fonts everywhere, fixed zip
def fix_rfonts(m):
    tag = m.group(0)
    attrs = dict(re.findall(r'(w:\w+)="([^"]*)"', tag))
    ascii_ = attrs.get("w:ascii", "")
    name = ascii_ if ascii_ in LS.FONT_NAMES else (LS.HEAD_FONT if "major" in tag else LS.BODY_FONT)
    return f'<w:rFonts w:ascii="{name}" w:hAnsi="{name}" w:cs="{name}" w:eastAsia="{name}"/>'


def fix_color(m):
    tag = m.group(0)
    tag = re.sub(r'\s+w:theme\w+="[^"]*"', "", tag)
    v = re.search(r'w:val="([^"]*)"', tag)
    if v and v.group(1) != "auto" and v.group(1).upper() not in LS.PALETTE:
        tag = tag.replace(v.group(0), f'w:val="{LS.INK}"')
    return tag


def clean(name, data):
    if not name.endswith(".xml") or not name.startswith("word/") or "theme" in name or name.endswith("fontTable.xml"):
        return data
    x = data.decode("utf-8")
    x = re.sub(r"<w:rFonts\b[^>]*/>", fix_rfonts, x)
    x = re.sub(r"<w:color\b[^>]*/>", fix_color, x)
    x = re.sub(r'\s+w:theme(?:Color|Shade|Tint|Fill|FillShade|FillTint)="[^"]*"', "", x)
    if name == "word/numbering.xml":
        x = re.sub(r'(<w:lvlText w:val=")[\uf000-\uf0ff](")', "\\g<1>\u2022\\2", x)
    return x.encode("utf-8")


zin = zipfile.ZipFile(io.BytesIO(buf.getvalue()))
with zipfile.ZipFile(DOCX, "w", zipfile.ZIP_DEFLATED) as zout:
    for name in zin.namelist():
        zi = zipfile.ZipInfo(name, ZIP_TIME)
        zi.compress_type = zipfile.ZIP_DEFLATED
        zout.writestr(zi, clean(name, zin.read(name)))
print(f"wrote {DOCX.relative_to(ROOT)} and {PNG.relative_to(ROOT)}")
