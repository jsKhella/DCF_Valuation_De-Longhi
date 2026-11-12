"""Step 8: build the process guide report/DeLonghi_DCF_process_guide.pdf and its number provenance report/build/guide_numbers.json.

Purpose
    A formal-register guide to the valuation in the Ledger identity (ivory paper, Garamond headings, Gill Sans MT body, one
    vermilion accent for step numerals and key results, hairline rules). Sections follow py/doc_map.py (ids, titles); every
    section opens with a "WORKBOOK > <sheet names>" line that names the workbook sheets it describes.
Inputs
    data/curiosity.duckdb (read-only: result numbers), brief/research_brief.md, plan/plan.md, evidence/step0[1-7].md,
    evidence/data_quality_log.md, report/final_review.md, data/raw/SOURCES.md (prose and counts), report/*.xlsx (sheet names),
    py/ledger_style.py (palette, fonts), py/doc_map.py (sections), py/guide_tokens.py (number-token rules).
Outputs
    report/DeLonghi_DCF_process_guide.pdf (A4, outline, contents links, embedded fonts, byte-reproducible) and
    report/build/guide_numbers.json: every number token of the guide in reading order with its provenance: either a DuckDB
    query plus a format ("db", "db_text"), a file plus an anchor phrase ("file"), or a row count in a file ("file_rows").
Brief definitions implemented
    none (documentation). Rule: no analysis number is typed here. Each number is produced by D()/DS() from DuckDB, or sits
    inside FT()/FR() text that is verified at build time to occur verbatim on a line of the named file that contains the anchor.
    A bare number in the text raises an error, so an unsourced figure cannot reach the PDF.
"""
import json
import re
import sys
from pathlib import Path

import duckdb
import openpyxl
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, HRFlowable, KeepTogether, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "py"))
import doc_map  # noqa: E402
import ledger_style as LS  # noqa: E402
from guide_tokens import tokens  # noqa: E402

OUT = ROOT / "report" / "DeLonghi_DCF_process_guide.pdf"
OUT_JSON = ROOT / "report" / "build" / "guide_numbers.json"
XLSX = ROOT / "report" / "DeLonghi_DCF_Valuation.xlsx"
DB = ROOT / "data" / "curiosity.duckdb"
FINAL = "report/final_review.md"
SOURCES = "data/raw/SOURCES.md"
BRIEF = "brief/research_brief.md"
EV1, EV2, EV3, EV4, EV7 = ("evidence/step01.md", "evidence/step02.md", "evidence/step03.md", "evidence/step04.md",
                           "evidence/step07.md")
EV6 = "evidence/step06.md"

# ---- layout constants (points unless stated) ----
MARGIN_X, MARGIN_TOP, MARGIN_BOTTOM = 2.0 * cm, 1.8 * cm, 2.0 * cm
FOOT_Y = 1.1 * cm
SEC_PT, SUB_PT, LEAD_FACTOR = 24, 17, 1.35
KEY_PT = 28
RULE_W = 0.5
TBL_PAD = 3
COVER_TOP_SPACE = 5 * cm
CODE_FIRST_PAGE_ARROW_SIZE = LS.BODY_PT
WIDTH = A4[0] - 2 * MARGIN_X

LS.rl_register_fonts()
BODY_F = "GillSansMT"
INK, GREY, VERM, HAIR, TINT, PAPER = (LS.rl_color(x) for x in (LS.INK, LS.GREY, LS.VERMILION, LS.HAIRLINE, LS.TINT, LS.PAPER))
VERM_HEX = "#" + LS.VERMILION

# ================================================================ provenance machinery
con = duckdb.connect(str(DB), read_only=True)
SPECS, ENTRIES = [], []
_file_cache = {}
RS, RE_ = "\x01", "\x03"                      # region start (with spec id) / end
REGION = re.compile("\x01(\\d+)\x02(.*?)\x03", re.S)


def lines_of(rel):
    if rel not in _file_cache:
        _file_cache[rel] = (ROOT / rel).read_text(encoding="utf-8").split("\n")
    return _file_cache[rel]


def _region(spec, text):
    SPECS.append(spec)
    return f"\x01{len(SPECS) - 1}\x02{text}\x03"


def q(sql):
    return con.execute(sql).fetchone()[0]


def D(sql, fmt):
    """A number from DuckDB, formatted with a Python format spec. Returns the text and records the provenance."""
    return _region({"kind": "db", "sql": sql, "fmt": fmt}, format(q(sql), fmt))


def DS(sql):
    """A text from DuckDB (every number token in it is recorded with the query)."""
    return _region({"kind": "db_text", "sql": sql}, str(q(sql)))


def FT(rel, anchor, text):
    """Prose whose numbers all occur verbatim on a line of `rel` that contains `anchor` (verified now and by the check)."""
    if not any(anchor in ln for ln in lines_of(rel)):
        raise ValueError(f"anchor not found in {rel}: {anchor!r}")
    return _region({"kind": "file", "file": rel, "anchor": anchor}, text)


def FR(rel, heading):
    """Number of table rows under the heading that contains `heading` in `rel` (header and separator rows excluded)."""
    n, on = 0, False
    for ln in lines_of(rel):
        if ln.startswith("#"):
            on = heading in ln
            continue
        if on and ln.startswith("| ") and not ln.startswith("| File") and not ln.startswith("|--"):
            n += 1
    if n == 0:
        raise ValueError(f"no table rows under {heading!r} in {rel}")
    return _region({"kind": "file_rows", "file": rel, "heading": heading}, str(n))


def _plain(t):
    t = re.sub(r"<[^>]+>", "", t)
    return t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")


def _verify(spec, tok):
    if spec["kind"] == "file":
        hit = [ln for ln in lines_of(spec["file"]) if spec["anchor"] in ln]
        if not any(tok in tokens(ln.replace("−", "-")) or tok in [t.replace(",", "") for t in re.findall(r"\d[\d,]*(?:\.\d+)?", ln)]
                   for ln in hit):
            raise ValueError(f"token {tok!r} not on a line with anchor {spec['anchor']!r} in {spec['file']}")


def emit(text):
    """Return markup for reportlab; record one provenance entry per number token, in reading order."""
    out, pos = [], 0
    for m in REGION.finditer(text):
        seg = text[pos:m.start()]
        bare = tokens(_plain(seg))
        if bare:
            raise ValueError(f"unsourced number {bare} in: {_plain(seg)[:90]!r}")
        out.append(seg)
        spec, inner = SPECS[int(m.group(1))], m.group(2)
        for tok in tokens(_plain(inner)):
            _verify(spec, tok)
            ENTRIES.append({**spec, "token": tok})
        out.append(inner)
        pos = m.end()
    seg = text[pos:]
    bare = tokens(_plain(seg))
    if bare:
        raise ValueError(f"unsourced number {bare} in: {_plain(seg)[:90]!r}")
    out.append(seg)
    res = "".join(out)
    res = re.sub(r"&(?!amp;|lt;|gt;|#)", "&amp;", res)
    return res


# ================================================================ shortcuts to the result tables
def val(item, fmt):
    return D(f"SELECT value FROM valuation WHERE item = '{item}'", fmt)


def bri(item, fmt):
    return D(f"SELECT value FROM bridge_inputs WHERE item = '{item}'", fmt)


def wac(case, col, fmt):
    return D(f'SELECT {col} FROM wacc WHERE "case" = \'{case}\'', fmt)


def msu(col, fmt):
    return D(f"SELECT {col} FROM mc_summary", fmt)


def hr(fy, col, fmt):
    return D(f"SELECT {col} FROM hist_ratios WHERE fy = {fy}", fmt)


def fas(driver, fmt, scale=""):
    return D(f"SELECT value{scale} FROM forecast_assumptions WHERE driver = '{driver}'", fmt)


def mcp(param, fmt, scale=""):
    return D(f"SELECT value{scale} FROM mc_params WHERE param = '{param}'", fmt)


def bsl(col, fmt, neg=False):
    return D(f"SELECT {'-' if neg else ''}{col} FROM beta_sensitivity", fmt)


def fcf(fy, col, fmt):
    return D(f"SELECT {col} FROM forecast_fcff WHERE fy = {fy}", fmt)


WACC_LOW = int(re.search(r"WACC outside (\d+)-", next(ln for ln in lines_of(BRIEF) if "WACC outside 6-10%" in ln)).group(1)) / 100   # lower WACC bound in the brief
FY_HIST = [r[0] for r in con.execute("SELECT fy FROM hist_ratios ORDER BY fy").fetchall()]
Y26 = FT(FINAL, "Valuation date and bridge (Decision 1A)", "2026")
FY_FC = [r[0] for r in con.execute("SELECT fy FROM forecast_fcff ORDER BY fy").fetchall()]

# ================================================================ styles
def PS(name, **kw):
    base = dict(fontName=BODY_F, bulletFontName=BODY_F, fontSize=LS.BODY_PT, leading=LS.BODY_PT * LEAD_FACTOR, textColor=INK, spaceAfter=4,
                alignment=TA_LEFT)
    base.update(kw)
    return ParagraphStyle(name, **base)


BODY = PS("body")
SMALL = PS("small", fontSize=LS.SMALL_PT, leading=LS.SMALL_PT * LEAD_FACTOR, textColor=GREY)
CELL = PS("cell", fontSize=LS.SMALL_PT, leading=LS.SMALL_PT * LEAD_FACTOR, spaceAfter=0)
CELLB = PS("cellb", fontName="GillSansMT-Bold", fontSize=LS.SMALL_PT, leading=LS.SMALL_PT * LEAD_FACTOR, spaceAfter=0)
QUOTE = PS("quote", fontName="Garamond-Italic", fontSize=LS.HEAD_PT, leading=LS.HEAD_PT * LEAD_FACTOR, leftIndent=10, spaceAfter=6)
BUL = PS("bul", leftIndent=14, bulletIndent=3, spaceAfter=3, bulletFontName=BODY_F)
WBLINE = PS("wb", fontSize=LS.SMALL_PT, leading=LS.SMALL_PT * LEAD_FACTOR, textColor=GREY, spaceAfter=6)
SUBH = PS("subh", fontName="Garamond-Bold", fontSize=LS.HEAD_PT, leading=LS.HEAD_PT * LEAD_FACTOR, spaceBefore=6, spaceAfter=2)
KEY = PS("key", fontName="Garamond-Bold", fontSize=KEY_PT, leading=KEY_PT * LEAD_FACTOR, textColor=VERM, spaceAfter=2)
TITLE = PS("title", fontName="Garamond-Bold", fontSize=LS.NUMERAL_PT * 2, leading=LS.NUMERAL_PT * 2 * LEAD_FACTOR, spaceAfter=8)
SUBTITLE = PS("subtitle", fontName="Garamond-Italic", fontSize=LS.SUBTITLE_PT, leading=LS.SUBTITLE_PT * LEAD_FACTOR, textColor=GREY)
AUTHOR = PS("author", fontSize=LS.SMALL_PT, leading=LS.SMALL_PT * LEAD_FACTOR, textColor=GREY, spaceAfter=0)
CONTENT = PS("content", fontName="Garamond", fontSize=LS.HEAD_PT, leading=LS.HEAD_PT * 1.6, spaceAfter=0)


def ARROW_MARKUP():
    return f'<font name="{LS.SYMBOL_FONT}">{LS.ARROW}</font>'


class Sec(Paragraph):
    """Section heading: a vermilion numeral plus a title (same size, so one text line), with outline data."""

    def __init__(self, sid, title, level):
        size = SEC_PT if level == 0 else SUB_PT
        st = PS(f"sec{level}{sid}", fontName="Garamond-Bold", fontSize=size, leading=size * LEAD_FACTOR, spaceBefore=10 if level else 14,
                spaceAfter=2)
        txt = f'<font color="{VERM_HEX}">§{sid}</font>  {emit(title)}'
        super().__init__(txt, st)
        self.sid, self.level = sid, level
        self.key = "sec_" + sid.replace(".", "_")
        self.outline = f"§{sid} {title}"


S = []                                                  # story


def SECTION(sid, workbook_sheets, newpage=False, keep=5):
    title = dict(doc_map.SECTIONS)[sid]
    level = 0 if ("." not in sid or sid == "0.0") else 1
    if newpage:
        S.append(PageBreak())
    else:
        S.append(CondPageBreak(keep * cm))
    S.append(Sec(sid, title, level))
    S.append(Paragraph(f"WORKBOOK {ARROW_MARKUP()} " + " · ".join(n.replace("&", "&amp;") for n in workbook_sheets), WBLINE))
    S.append(HRFlowable(width="100%", thickness=RULE_W, color=HAIR, spaceBefore=0, spaceAfter=6))


def P(text, style=BODY):
    S.append(Paragraph(emit(text), style))


def H(text):
    S.append(Paragraph(emit(text), SUBH))


def B(items):
    for it in items:
        S.append(Paragraph(emit(it), BUL, bulletText="•"))


def TABLE(rows, widths, header=True, align_right_from=None):
    data = []
    for r, row in enumerate(rows):
        data.append([Paragraph(emit(str(c)), CELLB if (header and r == 0) else CELL) for c in row])
    t = Table(data, colWidths=[w * WIDTH for w in widths], repeatRows=1 if header else 0)
    st = [("FONTNAME", (0, 0), (-1, -1), BODY_F), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), TBL_PAD), ("BOTTOMPADDING", (0, 0), (-1, -1), TBL_PAD),
          ("LEFTPADDING", (0, 0), (-1, -1), 0), ("LINEBELOW", (0, 0), (-1, -1), RULE_W, HAIR)]
    if header:
        st += [("LINEBELOW", (0, 0), (-1, 0), RULE_W * 2, INK), ("BACKGROUND", (0, 0), (-1, 0), TINT)]
    t.setStyle(TableStyle(st))
    S.append(KeepTogether([t, Spacer(1, 6)]))


W2, W3, W4, W6 = [0.55, 0.45], [0.46, 0.27, 0.27], [0.34, 0.22, 0.22, 0.22], [0.25, 0.15, 0.15, 0.15, 0.15, 0.15]
FYS = lambda ys: [f"FY{y}" for y in ys]                  # noqa: E731

# ================================================================ content
SHEET = {sid: name for sid, name, _ in doc_map.SHEETS}

# ---- cover and contents (cover has no numbers)
S.append(Spacer(1, COVER_TOP_SPACE))
S.append(Paragraph("What is De'Longhi worth?", TITLE))
S.append(Paragraph("Process guide to a discounted-cash-flow valuation", SUBTITLE))
S.append(Spacer(1, 0.6 * cm))
for _line in (doc_map.AUTHOR_NAME, doc_map.AUTHOR_EMAIL, doc_map.AUTHOR_AFFILIATION):   # plain text, no link, no digits
    S.append(Paragraph(_line, AUTHOR))
S.append(Spacer(1, 1.2 * cm))
S.append(HRFlowable(width="100%", thickness=RULE_W, color=HAIR, spaceBefore=0, spaceAfter=10))
P("The guide documents the question, the method, the data, each workbook sheet and the checks behind it. It accompanies "
  "report/DeLonghi_DCF_Valuation.xlsx and report/DeLonghi_DCF_Valuation_note.docx. Every section opens with the workbook sheets it "
  "describes, and every sheet opens with a band that names its guide section.")
S.append(PageBreak())
S.append(Paragraph("Contents", PS("contents_h", fontName="Garamond-Bold", fontSize=SEC_PT, leading=SEC_PT * LEAD_FACTOR, spaceAfter=10)))
for sid, title in doc_map.SECTIONS:
    indent = 0 if (len(sid) == 1 and (sid.isdigit() or sid == "A")) or sid in ("0.0",) else 16
    key = "sec_" + sid.replace(".", "_")
    S.append(Paragraph(f'<a href="#{key}" color="#{LS.INK}">§{sid}   {title}</a>', PS(f"toc{sid}", parent=CONTENT, leftIndent=indent,
                                                                                         fontName="Garamond", fontSize=LS.HEAD_PT,
                                                                                         leading=LS.HEAD_PT * 1.6, spaceAfter=0)))

# ---- 0.0
SECTION("0.0", [SHEET["0.0"]], newpage=True)
H("Question")
P("What is De'Longhi S.p.A. worth per share on a free-cash-flow DCF basis, which assumptions drive that value, and is the current "
  "market price reasonable?")
H("Answer")
S.append(Paragraph(emit(f"EUR {val('value_per_share', '.2f')} per share"), KEY))
S.append(Paragraph(emit(DS("SELECT display FROM report_headline WHERE key = 'sentence'")), QUOTE))
P(f"The conclusion depends mainly on beta. With the Global Furniture/Home Furnishings unlevered beta of {bsl('beta_u', '.3f')}, the WACC "
  f"becomes {bsl('wacc', '.2%')} and the same forecast gives EUR {bsl('value_per_share', '.2f')} per share, {bsl('pct_vs_base', '.1%', neg=True)} "
  f"below the base case and below the market price of EUR {val('price', '.2f')}. The sign of the result therefore depends on the beta choice, "
  "and the investment note says so.")
H("Method")
P("The project followed a fixed routine so that nothing was assumed and every number could be re-checked.")
TABLE([["Stage", "What was done", "Output"],
       ["Definition", "Objectives, terms and assumptions were fixed in advance, before any analysis.", "Approved research brief"],
       ["Checks first", "The acceptance checks of each step were written as code before the analysis they test, and were never loosened to obtain a pass.",
        "Check script for each step"],
       ["Analysis", "Each step was written as small pieces of SQL and Python, run one at a time, and documented as it was built.",
        "Code, tables, evidence pack"],
       ["Independent recomputation", "Every figure was recomputed by a second, independent method that did not reuse the first reading.",
        "Recomputation recorded in each evidence pack"],
       ["Rebuild", "Two clean rebuilds from the raw files were compared by table fingerprints; nothing was edited by hand.",
        "Identical fingerprints"],
       ["Approval", "The headline, the assumptions, the weak points and five cases to trace were collected and approved on 2026-11-09.",
        "Approved report"]], [0.2, 0.55, 0.25])
B(["<b>Checks are written first</b> and are never loosened to obtain a pass.",
   "<b>Definitions are fixed in advance.</b> If the data forces a change, work stops and the project owner decides.",
   "<b>One source of truth.</b> Every number comes from code that rebuilds the results from the raw files; nothing is typed by hand into the workbook.",
   "<b>Plausibility bounds fixed in advance.</b> A result is re-examined if the DCF value is more than "
   + FT(BRIEF, "DCF value more than 30% from the market price", "30%") + " from the market price, the terminal value exceeds "
   + FT(BRIEF, "Terminal value above 80% of EV", "80%") + " of enterprise value, the WACC is outside "
   + FT(BRIEF, "WACC outside 6-10%", "6 to 10%") + ", g is " + FT(BRIEF, "g of 2.5% or more", "2.5%")
   + " or more, or the market price lies outside the Monte Carlo "
   + FT(BRIEF, "Market price outside the Monte Carlo 10th-90th percentile range", "10th to 90th") + " percentile range."])
H("Idea of a DCF")
P("A company is worth the cash it will hand to its investors in the future, converted into today's money. Five years of free cash flow are "
  "forecast, a terminal value covers everything after that, and all of it is discounted at a rate that reflects risk (the WACC). Debt and "
  "other claims are then subtracted to obtain the value that belongs to shareholders, which is divided by the number of shares. "
  "History runs from FY2021 to FY2025 and the forecast from FY2026E to FY2030E, in EUR.")

# ---- 0
SECTION("0", [SHEET["0.0"]])
P(f"All inputs were downloaded on 2026-11-09 and are loaded unchanged by the first pipeline step. data/raw/SOURCES.md lists every file "
  f"with URL, size and " + FT(SOURCES, "| File | URL | Bytes | SHA-256 |", "SHA-256") + ". The market price is the close of 2026-11-06; the bar of 2026-11-09 is intraday and excluded.")
TABLE([["Group", "Files", "Retrieved", "Licence"],
       ["Company documents: annual reports, interim report, results presentations and press release", FR(SOURCES, "company documents"),
        "2026-11-09", "Company public-disclosure documents; private research use with source citation"],
       ["Damodaran datasets (update of " + FT(SOURCES, "Damodaran Online datasets, January 2026", "January 2026") + "): betas, multiples, country premia",
        FR(SOURCES, "Damodaran Online datasets"), "2026-11-09", "Freely downloadable public data; attribution requested"],
       ["ECB Data Portal: ten-year government bond yields, Italy and Germany", FR(SOURCES, "ECB Data Portal"), "2026-11-09",
        "ECB statistics reuse policy; source acknowledgement"],
       ["Yahoo Finance chart API: daily prices", FR(SOURCES, "Yahoo Finance chart API"), "2026-11-09",
        "Yahoo terms of service; personal, non-commercial use"]], [0.40, 0.08, 0.14, 0.38])

# ---- 1
SECTION("1", [SHEET["1.1"], SHEET["1.2"]])
P("Five annual reports are condensed to the lines that the cash flow calculation and the equity bridge need, with totals kept for tie-out. "
  "Ratios are then derived from those lines.")

SECTION("1.1", [SHEET["1.1"]])
B(["The income statement, balance sheet and cash flow statement of each annual report are read; the document and page of every value are kept.",
   f"The condensed statements hold {D('SELECT count(*) FROM hist_statements', 'd')} lines in total (income statement, balance sheet and cash flow, "
   "five years).",
   "Tie-outs hold: each balance sheet balances and each cash flow statement agrees with the change in cash.",
   "Later reports replace earlier values only where the company restated. The only restatement on the condensed lines is a presentation change "
   "in the FY2023 cash flow."])
TABLE([["EUR m"] + FYS(FY_HIST)]
      + [["Revenue"] + [hr(y, "revenue", ",.1f") for y in FY_HIST],
         ["Reported EBIT"] + [hr(y, "ebit_reported", ",.1f") for y in FY_HIST],
         ["Net working capital"] + [hr(y, "nwc", ",.1f") for y in FY_HIST],
         ["Capex incl. right-of-use"] + [hr(y, "capex_total", ",.1f") for y in FY_HIST]], W6)
H("Reconciliation and checks")
P(FT(EV1, "105 of 105 values", "All 105 ratio values were recomputed independently by a different method and were identical.")
  + " " + FT(EV1, "Checks: 128/128 pass", "All 128 acceptance checks pass.")
  + " The report lines were read with a separate tokenizer, while the main build used a fixed page map and SQL, so the two readings are independent.")

ADJ_SQL = "SELECT count(*) FROM hist_adjustments WHERE item NOT LIKE 'other non-recurring%'"
SECTION("1.2", [SHEET["1.2"]])
B(["Adjusted EBIT is reported EBIT with non-recurring items removed: restructuring, impairments and gains or losses on asset sales.",
   f"The largest one-off items are itemised with their source page ({D(ADJ_SQL, 'd')} items); "
   "the rest of each year's non-recurring total is one residual line, so adjusted EBIT uses the full total.",
   "Net working capital is trade receivables plus inventories minus trade payables. The effective tax rate is income tax divided by profit before tax.",
   "Adjustment amounts are displayed with " + FT(FINAL, "adjustment amounts show 1 decimal", "1 decimal")
   + " instead of the brief's whole-number rule, because whole numbers would show small items as zero. This display was accepted on 2026-11-09."])
TABLE([["Ratio"] + FYS(FY_HIST)]
      + [["Adjusted EBIT margin"] + [hr(y, "adj_ebit_margin", ".2%") for y in FY_HIST],
         ["Revenue growth"] + ["n/a"] + [hr(y, "growth", ".1%") for y in FY_HIST[1:]],
         ["Effective tax rate"] + [hr(y, "eff_tax_rate", ".2%") for y in FY_HIST],
         ["D&amp;A, % of revenue"] + [hr(y, "da_pct", ".2%") for y in FY_HIST],
         ["Capex, % of revenue"] + [hr(y, "capex_pct", ".2%") for y in FY_HIST],
         ["NWC, % of revenue"] + [hr(y, "nwc_pct", ".2%") for y in FY_HIST]], W6)
P(f"The adjusted margin troughs in FY2022. The average of FY2024 and FY2025 is {D('SELECT avg(adj_ebit_margin) FROM hist_ratios WHERE fy >= 2024', '.2%')}, "
  f"which anchors the margin fade in the forecast. The median effective tax rate over the included years is "
  f"{D('SELECT median(eff_tax_rate) FROM hist_ratios WHERE tax_included', '.2%')}.")

# ---- 2
SECTION("2", [SHEET["2.1"], SHEET["2.2"]])
P("The discount rate is estimated from market inputs, and the balance-sheet items needed to move from enterprise value to equity value per "
  "share are collected.")

SECTION("2.1", [SHEET["2.1"]])
B(["The risk-free rate is the ECB monthly average of the ten-year Italian government yield for "
   + FT(FINAL, "ECB monthly average for Sep 2026", "September 2026") + ". The mature-market premium and the Italy default spread come from Damodaran.",
   "Cost of equity (CAPM) is the risk-free rate plus the relevered beta times the sum of the mature premium and the Italy default spread. "
   "The industry beta is relevered at De'Longhi's own debt-to-equity ratio.",
   "Debt for the weights is gross financial debt plus lease liabilities; equity is market capitalisation. After-tax cost of debt uses the marginal Italian tax rate."])
cols = [("Risk-free rate", "rf", ".3%"), ("Unlevered beta", "beta_u", ".3f"), ("Relevered beta", "beta_l", ".3f"),
        ("Mature equity risk premium", "erp_mature", ".2%"), ("Italy default spread", "country_spread", ".2%"),
        ("Cost of equity", "ke", ".2%"), ("Pre-tax cost of debt", "kd_pre", ".2%"), ("After-tax cost of debt", "kd_post", ".2%"),
        ("Debt weight", "w_d", ".1%"), ("WACC", "wacc", ".2%")]
TABLE([["Parameter", "Base case", "Global-beta line"]]
      + [[lab, wac("base", col, fm), wac("beta_sensitivity", col, fm)] for lab, col, fm in cols], W3)
H("Reconciliation and checks")
P(FT(EV2, "42/42 exact", "Every bridge value and every WACC column (42 of 42 values) was rebuilt independently from the raw lines with 0 mismatches.")
  + " " + FT(EV2, "Checks: 78/78 pass", "All 78 acceptance checks pass."))

SECTION("2.2", [SHEET["2.2"]])
B([f"Net debt is taken at the balance-sheet date (2025-12-31). The reported net financial position is net cash of EUR {bri('nfp_reported', '.1f')} m.",
   "Cash-like financial assets (deposits, securities, derivative fair values) count as cash; guarantee deposits and operating receivables do not.",
   "Distributions already paid in " + Y26 + " (dividends and buybacks) are deducted, and minorities are deducted at book value, which is a simplification."])
rows = [("Cash and cash equivalents", "cash"), ("Cash-like financial assets", "cash_like_financial_assets"), ("Bank debt", "bank_debt"),
        ("Other financial payables", "other_financial_payables"), ("Lease liabilities", "lease_liabilities"),
        ("Distributions paid in " + Y26, "distributions_2026"), ("Minorities at book value", "minority_book")]
TABLE([["Bridge input", "EUR m"]] + [[lab, bri(k, ",.3f")] for lab, k in rows]
      + [["Diluted shares (m)", bri("diluted_shares", ".6f")], ["Share price (EUR)", bri("price", ".2f")],
         ["Market capitalisation", bri("market_cap", ",.1f")]], W2)

# ---- 3
SECTION("3", [SHEET["3.1"], SHEET["3.2"], SHEET["3.3"]])
P("Free cash flow to the firm (FCFF) is adjusted EBIT times one minus the tax rate, plus depreciation and amortisation, minus capex, minus the "
  "increase in net working capital. It is forecast for five years, a terminal value is added, and everything is discounted to the price date.")

SECTION("3.1", [SHEET["3.1"]])
B([f"Revenue grows {fas('growth_fy2026', '.1%')} in FY2026E (the midpoint of the mid-single-digit guidance) and fades linearly towards g of {fas('terminal_g', '.1%')}.",
   f"The FY2026E margin is derived from the adjusted EBITDA guidance midpoint of EUR {fas('guidance_adj_ebitda_fy2026', '.0f')} m and fades to "
   f"{fas('adj_ebit_margin_target_fy2030', '.2%')}, the average of FY2024 and FY2025.",
   f"Depreciation, capex and net working capital are held at {fas('da_pct', '.2%')}, {fas('capex_pct', '.2%')} and {fas('nwc_pct', '.2%')} of revenue. "
   f"The explicit-year tax rate is {fas('tax_rate_forecast', '.1%')}; the terminal value uses the Italian marginal rate of {fas('tax_rate_terminal', '.2%')}."])
TABLE([["EUR m", "Revenue", "Growth", "Adjusted EBIT margin", "FCFF"]]
      + [[f"FY{y}E", fcf(y, "revenue", ",.1f"), fcf(y, "growth", ".1%"), fcf(y, "adj_ebit_margin", ".1%"), fcf(y, "fcff", ",.1f")] for y in FY_FC],
      [0.16, 0.2, 0.18, 0.26, 0.2])
H("Reconciliation and checks")
P(FT(EV3, "Checks: 148/148 pass", "All 148 acceptance checks pass.")
  + " " + FT(EV3, "All 20 compared numbers", "20 compared numbers (FCFF and margin per year, terminal value, enterprise value, equity value and exit values) were rebuilt with one independent SQL chain and agreed to rounding precision."))

SECTION("3.2", [SHEET["3.2"]])
rows = [("Sum of discounted FCFF", "sum_pv_fcff", 1), ("Discounted terminal value", "pv_tv", 1), ("Enterprise value", "ev", 1),
        ("Equity value", "equity_value", 1)]
TABLE([["Valuation line", "EUR m"]] + [[lab, val(k, ",.1f")] for lab, k, _ in rows]
      + [["Value per share (EUR)", val("value_per_share", ".2f")], ["Market price (EUR)", val("price", ".2f")],
         ["Terminal value, share of enterprise value", val("tv_share_of_ev", ".1%")],
         ["Base-case value above market price", D("SELECT value / (SELECT value FROM valuation WHERE item = 'price') - 1 FROM valuation WHERE item = 'value_per_share'", ".1%")]], W2)
P(f"Equity value is enterprise value plus cash and cash-like assets, minus bank debt, other financial payables, leases, distributions and minorities, "
  f"divided by {val('diluted_shares', '.6f')} m diluted shares.")
P("Plausibility bounds fixed in advance:")
TABLE([["Test", "Limit", "Result"],
       ["DCF value versus market price", FT(BRIEF, "DCF value more than 30% from the market price", "30%"),
        D("SELECT value / (SELECT value FROM valuation WHERE item = 'price') - 1 FROM valuation WHERE item = 'value_per_share'", ".1%")],
       ["Terminal value, share of enterprise value", FT(BRIEF, "Terminal value above 80% of EV", "80%"), val("tv_share_of_ev", ".1%")],
       ["WACC", FT(BRIEF, "WACC outside 6-10%", "6 to 10%"), val("wacc", ".2%")],
       ["Terminal growth g", FT(BRIEF, "g of 2.5% or more", "below 2.5%"), val("terminal_g", ".2%")]], W3)

SECTION("3.3", [SHEET["3.3"]])
P("The terminal value is cross-checked against an exit multiple: the Damodaran EV/EBITDA for Furniture/Home Furnishings is applied to FY2030E EBITDA.")
TABLE([["Region", "Firms", "EV/EBITDA", "Value per share (EUR)"]]
      + [[r, D(f"SELECT n_firms FROM multiples_check WHERE region = '{r}'", "d"), D(f"SELECT ev_ebitda FROM multiples_check WHERE region = '{r}'", ".2f") + "x",
          D(f"SELECT value_per_share_exit FROM multiples_check WHERE region = '{r}'", ".2f")] for r in ("Europe", "Global")], W4)
P(f"The multiple implied by the Gordon-growth terminal value is {D('SELECT implied_gordon_ev_ebitda FROM multiples_check LIMIT 1', '.1f')}x EBITDA, "
  "above both Damodaran multiples, so the base case is somewhat more optimistic than market multiples.")

# ---- 4
SECTION("4", [SHEET["4.1"], SHEET["4.2"]])
P("A single number hides uncertainty. The sensitivity grid shows the effect of two assumptions, and the Monte Carlo varies growth, margin and WACC together.")

SECTION("4.1", [SHEET["4.1"]])
GRID = "SELECT value_per_share FROM (SELECT *, dense_rank() OVER (ORDER BY wacc) AS r, dense_rank() OVER (ORDER BY g) AS c FROM sensitivity) WHERE r = {r} AND c = {c}"
GRIDW = "SELECT wacc FROM (SELECT *, dense_rank() OVER (ORDER BY wacc) AS r FROM sensitivity) WHERE r = {r} LIMIT 1"
GRIDG = "SELECT g FROM (SELECT *, dense_rank() OVER (ORDER BY g) AS c FROM sensitivity) WHERE c = {c} LIMIT 1"
IDX = range(1, q("SELECT count(DISTINCT g) FROM sensitivity") + 1)
TABLE([["WACC / g"] + [D(GRIDG.format(c=c), ".1%") for c in IDX]]
      + [[D(GRIDW.format(r=r), ".2%")] + [D(GRID.format(r=r, c=c), ".2f") for c in IDX] for r in IDX], [0.2, 0.16, 0.16, 0.16, 0.16, 0.16])
P("Value per share in EUR for five WACC levels (rows) and five terminal growth rates (columns). The centre cell equals the base case. "
  f"The beta line replaces the base beta with the Global beta: WACC {bsl('wacc', '.2%')}, value EUR {bsl('value_per_share', '.2f')} per share.")

SECTION("4.2", [SHEET["4.2"]])
B(["Each run draws a growth shift, a margin shift and a WACC. The growth and margin shifts are correlated through operating leverage; the WACC is "
   "independent and truncated at both ends; g is held at the base case.",
   f"{mcp('n_runs', ',.0f')} runs with the fixed seed {mcp('seed', '.0f')} make the result repeatable."])
TABLE([["Parameter", "Value"],
       ["Growth shift, standard deviation (pp)", mcp("sd_growth_shift", ".1f", " * 100")],
       ["Margin shift, standard deviation (pp)", mcp("sd_margin_shift", ".1f", " * 100")],
       ["Correlation of growth and margin shifts", mcp("rho_growth_margin", ".1f")],
       ["WACC, standard deviation (pp)", mcp("wacc_sd", ".2f", " * 100")],
       ["WACC truncation, lower and upper bound", mcp("wacc_lower", ".1%") + " and " + mcp("wacc_upper", ".1%")]], W2)
TABLE([["Statistic (EUR per share)", "Value"]]
      + [[lab, msu(col, ".2f")] for lab, col in [(FT(EV4, "p5/p25/p50/p75/p95", "5th") + " percentile", "p5"),
                                                 (FT(EV4, "MC p10 EUR", "10th") + " percentile", "p10"), ("Median", "p50"), ("Mean", "mean"),
                                                 (FT(EV4, "MC p90 EUR", "90th") + " percentile", "p90"),
                                                 (FT(EV4, "p5/p25/p50/p75/p95", "95th") + " percentile", "p95")]]
      + [["Market price percentile", msu("price_percentile", ".1f")]], W2)
P(f"The mean exceeds the median because value is a convex function of the WACC. The histogram on the sheet has "
  f"{D('SELECT count(*) FROM mc_histogram', 'd')} bins that sum to {D('SELECT sum(count) FROM mc_histogram', ',.0f')} runs.")
H("Reconciliation and checks")
P(FT(EV4, "all 25 grid cells", "All 25 grid cells and all 10,000 run values were recomputed with independent vectorised code and agreed to rounding precision.")
  + " " + FT(EV4, "reproduced bit-for-bit", "The random draws were reproduced bit-for-bit from the documented generator, with 0 mismatching runs.")
  + " " + FT(EV4, "Checks: 66/66 pass", "All 66 acceptance checks pass."))

# ---- 5
SECTION("5", [SHEET["5.1"]])
P("The workbook ends with a sheet of reconciliations. Each is recomputed from the database and reported with its result. "
  "The table below lists, for each stage, what was reconciled and which figures were recomputed.")
TABLE([["Stage", "What was reconciled", "Checks and figures recomputed"],
       ["§0 Raw data", "Files loaded unchanged, with source, retrieval date and licence recorded.",
        "Every file hashed with " + FT(SOURCES, "| File | URL | Bytes | SHA-256 |", "SHA-256") + "; hashes listed in data/raw/SOURCES.md."],
       ["§1 Statements", "Balance sheets balance; the cash flow agrees with the change in cash.",
        FT(EV1, "105 of 105 values", "105 values") + " recomputed; " + FT(EV1, "Checks: 128/128 pass", "128 checks") + "."],
       ["§2 Rates and bridge", "Bridge and WACC rebuilt from the raw report lines.",
        FT(EV2, "42/42 exact", "42 of 42 values") + " identical; " + FT(EV2, "Checks: 78/78 pass", "78 checks") + "."],
       ["§3 Valuation", "FCFF identity, terminal value, enterprise value and the equity bridge recomputed.",
        FT(EV3, "All 20 compared numbers", "20 numbers") + "; " + FT(EV3, "Checks: 148/148 pass", "148 checks") + "."],
       ["§4 Simulation", "Grid cells and Monte Carlo runs recomputed with vectorised code; the random draws reproduced.",
        FT(EV4, "all 25 grid cells", "25 grid cells") + "; " + FT(EV4, "all 25 grid cells", "10,000 runs") + " reproduced bit-for-bit under the fixed seed; "
        + FT(EV4, "Checks: 66/66 pass", "66 checks") + "."],
       ["Workbook", "Every reconciliation recomputed from the database; the cells read back against the database.",
        FT(EV7, "5.1 Checks has 65 rows", "65 reconciliation rows") + ", all PASS; "
        + FT(EV7, "Baseline cells: 2,691 compared, 0 mismatches", "2,691 cells compared with the earlier build, 0 mismatches") + "; "
        + FT(EV7, "Numeric cells: 1,237", "1,237 numeric cells") + "; " + FT(EV7, "formulas: 0 (no data_type f", "0 formulas") + "."],
       ["Note", "Each figure matched to the cell of the sheet named by its tag.", "Figures compared at the display precision of the cell."],
       ["Rebuild", "Two clean rebuilds from the raw files.",
        "Identical fingerprints for " + FT(EV7, "identical fingerprints for all 24 tables", "24") + " tables."]], [0.2, 0.4, 0.4])

SECTION("5.1", [SHEET["5.1"]])
B([FT(EV7, "5.1 Checks has 65 rows", "The sheet holds 65 rows, all PASS. They cover the balance sheets, the cash flow tie-outs, the FCFF identity, the bridge and the determinism of the tables."),
   FT(EV7, "Steps 01 to 04 still pass (128, 78, 148, 66)", "The acceptance checks of the four analysis steps pass with 128, 78, 148 and 66 checks.")
   + " " + FT(EV7, "identical fingerprints for all 24 tables", "Two clean rebuilds gave identical fingerprints for all 24 tables."),
   "The workbook holds values only; its cells were read back against the database."])
# ---- 6
SECTION("6", [SHEET["0.0"]])
B(["The investment note is two " + FT(EV6, "Page size is US Letter", "A4") + " pages with five headings (Thesis, Main assumptions, Valuation range, Risks, Conclusion vs market price) and one chart: the Monte Carlo histogram with the market price and the base case marked.",
   "Every figure in the note is read back from the workbook at the workbook's own display precision and carries a sheet tag such as [3.2], so the note cannot disagree with the workbook.",
   f"The base case gives EUR {val('value_per_share', '.2f')} per share against EUR {val('price', '.2f')}; the Monte Carlo " + FT(FINAL, "the 80% Monte Carlo range", "80%") + f" range is EUR {msu('p10', '.2f')} to EUR {msu('p90', '.2f')}.",
   "The Risks section names the three simplifications: minorities at book value, Italy risk double counting, and the low Europe industry beta."])
B(["Each figure in the note was matched by script, at the display precision of the cell, against a cell on the sheet named by its tag; dates and year labels are not figures and are exempt. Three number tokens that matched a cell only by coincidence were reworded in words. The headline paragraph equals the workbook headline character for character."])

# ---- A
SECTION("A", [SHEET["5.1"]])
P("The appendix holds the audit trail of five cases, the glossary and the limitations.")

SECTION("A.1", [SHEET["5.1"]])
P("The five cases below can be traced in the workbook in about ten minutes.")
CASES = [
 ("Step 1, source tie-out (check against the PDF).",
  "AR2025 p.144: total consolidated revenues 3,801,458 and EBIT 458,145, with non-recurring (1,637). Adjusted EBIT = 458.145 + 1.637 = 459.782, margin 12.09%. "
  "The same figures appear on sheets [1.1] and [1.2].", "**Step 1, source tie-out"),
 ("Step 2, net financial position.",
  "Bank debt 227.043 + other financial payables 212.180 + leases 94.370 - cash 998.448 - financial assets 305.138 (of which 304.744 is the cash-like amount used in the bridge, and 0.394 is lease prepayments) = -769.993, "
  "i.e. net cash of EUR 770.0 m, which matches AR2025 PDF p.177 (769,993). Cash-like assets are the sum of derivatives, fair-value financial assets and other current financial assets from note 24 (AR2025 p.171) "
  "plus 60.343 from the net financial position line (p.177). Sheet [2.2].", "**Step 2, net financial position"),
 ("Step 3, the FY2026E FCFF row.",
  "Revenue 3,991.531; adjusted EBIT 511.627; NOPAT 388.172 at 24.13% tax; D&A 132.410; capex 160.387; change in NWC 5.041; FCFF = 355.154. "
  "The guidance check: 511.627 + 132.410 + 35.963 = 680.000, the midpoint of the EUR 670-690 m guidance (H1 2026 press release, p.6). Sheet [3.1].", "**Step 3, the FY2026E FCFF row"),
 ("Step 3, the bridge to value per share.",
  "EV 8,032.898 + cash 998.448 + cash-like 304.744 - bank debt 227.043 - other financial payables 212.180 - leases 94.370 - distributions 156.400 - minorities 197.801 = 8,448.296, "
  "divided by 149.600349 m diluted shares = EUR 56.47. The check is that net cash is added, treasury shares are excluded and minorities are deducted. Sheet [3.2].", "**Step 3, the bridge to value per share"),
 ("Step 4, Monte Carlo.",
  "Run 2057 (growth shift -3.67 pp, margin shift -1.75 pp, WACC 6.13%) gives EUR 45.30, which is just below the price. In total 1,203 of 10,000 runs fall below EUR 45.32, so the percentile is 12.0, "
  "and the headline on sheet [3.2] says \"12th\". The Global-beta line gives EUR 35.60, 37.0% below the base case. Sheet [4.2].", "**Step 4, Monte Carlo"),
]
for lead, body, anchor in CASES:
    S.append(Paragraph(emit(FT(FINAL, anchor, f"<b>{lead}</b> " + body)), BUL, bulletText="•"))

SECTION("A.2", [SHEET["5.1"]], keep=16)  # keep the heading with its (unsplittable) table
GL = [("Adjusted EBIT", "Operating profit before interest and tax, with one-off items (restructuring, impairments, gains and losses on asset sales) removed."),
      ("Beta", "Sensitivity of a share's return to the market. The industry beta is relevered to the company's own debt-to-equity ratio."),
      ("CAPM", "Cost of equity = risk-free rate + beta x (equity risk premium + Italy default spread). The BTP yield already reflects Italy risk, which is why adding the default spread counts that risk twice."),
      ("Diluted shares", "Shares issued, minus treasury shares, plus shares that options and rights could create."),
      ("Enterprise value", "Value of the operations of the whole business, before debt and other claims."),
      ("Equity bridge", "The steps from enterprise value to equity value: add cash, subtract debt, leases, distributions and minorities."),
      ("FCFF", "Free cash flow to the firm: adjusted EBIT times one minus the tax rate, plus D&amp;A, minus capex, minus the increase in NWC."),
      ("Gordon growth", "Terminal value = next year's cash flow / (WACC - g), for a cash flow that grows forever at g."),
      (FT(FINAL, "IFRS 16 leases", "IFRS 16"), "Accounting rule that puts leases on the balance sheet as an asset and a debt-like liability. Leases are treated as debt here."),
      ("Minority interests", "The part of subsidiaries owned by outside shareholders. Deducted at book value, which is a simplification."),
      ("Monte Carlo", "Repeating a calculation many times with random draws of the uncertain inputs to see the spread of outcomes."),
      ("NWC", "Net working capital: trade receivables + inventories - trade payables."),
      ("Percentile", "The p-th percentile is the value below which p% of the outcomes lie."),
      ("Plausibility bound", "A limit fixed in advance; a result outside it is re-examined, for example a terminal value above " + FT(BRIEF, "Terminal value above 80% of EV", "80%") + " of enterprise value."),
      ("pp", "Percentage points."),
      ("Terminal value", "Value of all cash flows after the explicit forecast, lumped into one number at the end of the forecast."),
      ("WACC", "Weighted average cost of capital: the blended required return of shareholders and lenders, used as the discount rate."),
      ("g", "Long-run growth rate of the cash flow after the forecast; it must stay below the risk-free rate.")]
TABLE([["Term", "Meaning"]] + [[a, b] for a, b in GL], [0.2, 0.8])

SECTION("A.3", [SHEET["5.1"]])
B([f"Minorities are deducted at book value (EUR {val('minority_book', '.1f')} m), not market value.",
   "Italy's country risk is counted twice in the cost of equity (via the BTP yield and the default spread), as the brief specified.",
   f"The beta is low and decides the sign of the conclusion: EUR {val('value_per_share', '.2f')} with the Europe beta and EUR {bsl('value_per_share', '.2f')} with the Global beta.",
   "The conclusion is sensitive to the assumptions and holds only narrowly: the terminal value is " + val("tv_share_of_ev", ".1%")
   + " of enterprise value against a bound of " + FT(BRIEF, "Terminal value above 80% of EV", "80%") + "; the base-case value is "
   + D("SELECT value / (SELECT value FROM valuation WHERE item = 'price') - 1 FROM valuation WHERE item = 'value_per_share'", ".1%")
   + " above the price against a bound of " + FT(BRIEF, "DCF value more than 30% from the market price", "30%")
   + "; the market price is EUR " + D("SELECT (SELECT value FROM valuation WHERE item = 'price') - p10 FROM mc_summary", ".2f")
   + " above the Monte Carlo " + FT(EV4, "MC p10 EUR", "10th") + " percentile; and the base WACC is "
   + D(f"SELECT (wacc - {WACC_LOW}) * 100 FROM wacc WHERE \"case\" = 'base'", ".2f") + " pp above the lower bound of "
   + FT(BRIEF, "WACC outside 6-10%", "6%") + ".",
   "The workbook holds values only, with no live formulas.",
   "This is a valuation comparison, not an investment recommendation.",
   "Rendering of the three documents was verified in LibreOffice only; Excel and Word may differ slightly in spacing."])


# ================================================================ build
def on_page(canv, d):
    canv.saveState()
    canv.setFillColor(PAPER)
    canv.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
    if d.page > 1:
        canv.setStrokeColor(HAIR)
        canv.setLineWidth(RULE_W)
        canv.line(MARGIN_X, FOOT_Y + 10, A4[0] - MARGIN_X, FOOT_Y + 10)
        canv.setFillColor(GREY)
        canv.setFont(BODY_F, LS.SMALL_PT)
        canv.drawString(MARGIN_X, FOOT_Y, "De'Longhi DCF valuation: process guide")
        canv.drawRightString(A4[0] - MARGIN_X, FOOT_Y, f"Page {d.page}")
    canv.restoreState()


class Doc(BaseDocTemplate):
    def afterFlowable(self, f):
        if isinstance(f, Sec):
            self.canv.bookmarkPage(f.key)
            self.canv.addOutlineEntry(f.outline, f.key, f.level, 0)


doc = Doc(str(OUT), pagesize=A4, leftMargin=MARGIN_X, rightMargin=MARGIN_X, topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
          title="De'Longhi DCF valuation: process guide", author=doc_map.AUTHOR_NAME, subject="Process guide", invariant=1,
          initialFontName=BODY_F, initialFontSize=LS.BODY_PT, initialLeading=LS.BODY_PT * LEAD_FACTOR)
doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(MARGIN_X, MARGIN_BOTTOM, WIDTH, A4[1] - MARGIN_TOP - MARGIN_BOTTOM, id="f",
                                                         leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=on_page)])
OUT.parent.mkdir(parents=True, exist_ok=True)
doc.build(S)
OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps({"entries": ENTRIES}, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {OUT.relative_to(ROOT)} ({len(ENTRIES)} number tokens) and {OUT_JSON.relative_to(ROOT)}")
