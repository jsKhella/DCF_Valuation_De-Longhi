"""Ledger presentation for the workbook built by py/05_build_report.py (formatting only, openpyxl styles).

Purpose
    `style_sheet(ws, info)` restyles a finished sheet in the Ledger identity: paper background, hairline rules, no boxed
    grids, a small band in row 1 ("GUIDE ▸ §x.y" plus links), a large numeral and title in row 2, bold table headers with an
    ink rule, vermilion on key results only, freeze panes below the first table header and print setup.
    All colours, fonts and sizes come from py/ledger_style.py; sheet ids and names come from py/doc_map.py.
Inputs
    a sheet whose cells are already in their final positions, and `info`: {"headers": {row: last col}, "sections": {rows},
    "notes": {rows}, "ctx": {...}} registered by 05 while it laid the sheet out.
Rule
    Never changes a cell value, a cell position, a sheet name/order or a number format. Only fonts, fills, borders,
    alignment, merges of empty cells, column/row sizes and page setup.
"""
from openpyxl.styles import Alignment, Border
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.properties import PageSetupProperties

import doc_map as DM
import ledger_style as LS

# ---- layout constants ----
PAD_COLS = 8                  # blank columns to the right that also carry the paper colour
A4_PAPER = 9                  # openpyxl/Excel paper size code for A4
WIDE_UNITS = 120              # landscape when the used width exceeds this many character units
DEFAULT_COL_W = 9
BAND_H, TITLE_H, SECTION_H = 18, 40, 22
DESC_ROW, DESC_ROW_VAL = 3, 4     # description / headline row; 3.2 Valuation also has a note in row 4
CHARS_PER_UNIT = 1.05         # characters of Gill Sans MT 10 pt that fit in one column-width unit
WRAP_MIN_LEN = 40             # text longer than this wraps
LINK_COLS = (2, 3, 4)         # row-1 columns holding the Overview / previous / next links
KEY_NAMES = {"value_per_share", "wacc", "price", "price_percentile"}
MC_KEY_NAMES = {"price_percentile"}
KEY_SHEETS = {"3.2 Valuation": KEY_NAMES, "2.1 WACC": KEY_NAMES, "4.2 Monte Carlo": MC_KEY_NAMES}
HEADLINE_SHEETS = {"0.0 Overview", "3.2 Valuation"}
HEADLINE_LINE_H = 22
DESC_LINE_H = 15

AL_NUM = Alignment(horizontal="right", vertical="top")
AL_TXT = Alignment(horizontal="left", vertical="top")
AL_WRAP = Alignment(horizontal="left", vertical="top", wrap_text=True)
AL_HDR = Alignment(horizontal="center", vertical="center", wrap_text=True)
AL_HDR_LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
AL_CENTER = Alignment(horizontal="center", vertical="top")
AL_TXT_IND = Alignment(horizontal="left", vertical="top", indent=1)    # text after a number column keeps a gap
AL_WRAP_IND = Alignment(horizontal="left", vertical="top", wrap_text=True, indent=1)
AL_TITLE = Alignment(horizontal="left", vertical="center")


def col_w(ws, col):
    return ws.column_dimensions[get_column_letter(col)].width or DEFAULT_COL_W


def used_width(ws):
    return sum(col_w(ws, c) for c in range(1, ws.max_column + 1))


def lines_for(text, width_units):
    return max(1, -(-int(len(str(text)) / CHARS_PER_UNIT) // max(1, int(width_units))))


def style_sheet(ws, info):
    name = ws.title
    sid = DM.SHEET_ID[name]
    maxr, maxc = ws.max_row, ws.max_column
    total_w = used_width(ws)
    hdrs = info["headers"]
    sections = info["sections"]
    notes = info["notes"]
    key_names = KEY_SHEETS.get(name, set())
    rule_ink = LS.xl_side(LS.INK, "thin")
    rule_hair = LS.xl_side(LS.HAIRLINE, "thin")
    body = LS.xl_font("body")

    ws.sheet_view.showGridLines = False
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_setup.paperSize = A4_PAPER
    ws.page_setup.orientation = "landscape" if total_w > WIDE_UNITS else "portrait"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0

    # paper everywhere: every cell of the used rectangle, plus the blank columns to the right through column styles
    paper = LS.xl_fill(LS.PAPER)
    for r in range(1, maxr + 1):
        for c in range(1, maxc + 1):
            cell = ws.cell(row=r, column=c)
            cell.fill = paper
            cell.font = body
            cell.alignment = AL_TXT
    for c in range(1, maxc + PAD_COLS + 1):
        dim = ws.column_dimensions[get_column_letter(c)]
        if dim.width is None:
            dim.width = DEFAULT_COL_W
        dim.fill = paper
        dim.font = body

    # row 1: band and links
    for c in range(1, maxc + 1):
        ws.cell(row=1, column=c).border = Border(bottom=rule_hair)
    band = ws.cell(row=1, column=1)
    band.font = LS.xl_font("body", LS.SMALL_PT, color=LS.GREY)
    band.alignment = AL_TITLE
    for c in LINK_COLS:
        cell = ws.cell(row=1, column=c)
        if cell.value is not None:
            cell.font = LS.xl_font("body", LS.SMALL_PT, color=LS.INK, underline="single")
            cell.alignment = AL_TITLE
    ws.row_dimensions[1].height = BAND_H

    # row 2: oversized numeral (vermilion) + title; rule under it
    for c in range(1, maxc + 1):
        ws.cell(row=2, column=c).border = Border(bottom=rule_ink)
    ws.cell(row=2, column=1).font = LS.xl_font("head", LS.TITLE_PT, color=LS.INK)
    ws.cell(row=2, column=1).alignment = AL_TITLE
    ws.row_dimensions[2].height = TITLE_H

    # rows 3 (and 4 on 3.2): description or headline, merged across the sheet width
    desc_rows = [DESC_ROW] + ([DESC_ROW_VAL] if name == "3.2 Valuation" else [])
    for r in desc_rows:
        cell = ws.cell(row=r, column=1)
        if cell.value is None:
            continue
        headline = name in HEADLINE_SHEETS and r == DESC_ROW
        if maxc > 1:
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=maxc)
        cell.alignment = AL_WRAP
        if headline:
            cell.font = LS.xl_font("head", LS.HEADLINE_PT, color=LS.INK)
            ws.row_dimensions[r].height = lines_for(cell.value, total_w) * HEADLINE_LINE_H + LS.PAD_PT
        else:
            cell.font = LS.xl_font("head", LS.BODY_PT + 1, italic=True, color=LS.GREY)
            ws.row_dimensions[r].height = lines_for(cell.value, total_w) * DESC_LINE_H + LS.PAD_PT

    label_sheet = name in DM.LABEL_SHEETS
    width = 1
    for r in range(DESC_ROW, maxr + 1):
        if r in desc_rows:
            continue
        cells = [ws.cell(row=r, column=c) for c in range(1, maxc + 1)]
        filled = [c for c in cells if c.value is not None]
        if r in hdrs:
            width = hdrs[r]
            for i, c in enumerate(cells[:width]):
                c.font = LS.xl_font("body", LS.SMALL_PT, bold=True, color=LS.INK)
                c.alignment = AL_HDR_LEFT if i == 0 else AL_HDR
                c.border = Border(bottom=rule_ink)
            continue
        if not filled:
            continue
        if r in notes:
            if maxc > 1:
                ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=maxc)
            top = ws.cell(row=r, column=1)
            top.font = LS.xl_font("body", LS.NOTE_PT, italic=True, color=LS.GREY)
            top.alignment = AL_WRAP
            ws.row_dimensions[r].height = lines_for(top.value, total_w) * DESC_LINE_H + LS.PAD_PT
            continue
        if r in sections:
            for c in filled:
                c.font = LS.xl_font("head", LS.HEAD_PT, bold=True, color=LS.INK)
                c.alignment = AL_TXT
            ws.row_dimensions[r].height = SECTION_H
            continue
        span = max(width, max(c.column for c in filled))
        is_key = ws.cell(row=r, column=1).value in key_names
        for c in cells[:span]:
            c.border = Border(bottom=rule_hair)
            v = c.value
            if label_sheet and c.column == 2 and isinstance(v, str):
                c.font = LS.xl_font("body", color=LS.GREY)
                c.alignment = AL_TXT
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                c.alignment = AL_NUM
                if is_key:
                    c.font = LS.xl_font("body", bold=True, color=LS.VERMILION)
            elif isinstance(v, str) and len(v) > WRAP_MIN_LEN:
                c.alignment = AL_WRAP if c.column == 1 else AL_WRAP_IND
            elif isinstance(v, str) and c.column > 1:
                c.alignment = AL_TXT_IND
            if is_key and c.column == 1:
                c.font = LS.xl_font("body", bold=True)

    ctx = info["ctx"]
    # equity bridge block on 3.2: from ev down to value per share
    if name == "3.2 Valuation" and "bridge" in ctx:
        first, last = ctx["bridge"]
        tint = LS.xl_fill(LS.TINT)
        for r in range(first, last + 1):
            for c in range(1, ctx["bridge_cols"] + 1):
                cell = ws.cell(row=r, column=c)
                cell.fill = tint
                cell.font = LS.xl_font("body", bold=True,
                                       color=LS.VERMILION if (r == last and isinstance(cell.value, (int, float))) else LS.INK)
                cell.border = Border(top=rule_ink if r == first else rule_hair, bottom=rule_ink if r == last else rule_hair)
    # sensitivity grid: axes tinted, base cell outlined in ink with a vermilion value
    if name == "4.1 Sensitivity" and "sens_grid" in ctx:
        r0, c0, r1, c1 = ctx["sens_grid"]
        tint = LS.xl_fill(LS.TINT)
        for r in range(r0 - 1, r1 + 1):
            for c in range(1, c1 + 1):
                if r == r0 - 1 or c == 1:
                    cell = ws.cell(row=r, column=c)
                    cell.fill = tint
                    cell.font = LS.xl_font("body", bold=True)
                    cell.alignment = AL_NUM
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                ws.cell(row=r, column=c).alignment = AL_NUM
        br, bc = ctx["sens_base"]
        base = ws.cell(row=br, column=bc)
        base.font = LS.xl_font("body", bold=True, color=LS.VERMILION)
        edge = LS.xl_side(LS.INK, "medium")
        base.border = Border(left=edge, right=edge, top=edge, bottom=edge)
    # checks: PASS in ink, FAIL in vermilion
    if name == "5.1 Checks":
        res_col = hdrs[max(hdrs)]
        for r in range(max(hdrs) + 1, maxr + 1):
            cell = ws.cell(row=r, column=res_col)
            cell.font = LS.xl_font("body", bold=True, color=LS.INK if cell.value == "PASS" else LS.VERMILION)
            cell.alignment = AL_CENTER

    # freeze panes directly below the first table header (1.1 also freezes columns A:B)
    first_hdr = min(hdrs) if hdrs else 1
    ws.freeze_panes = f"{'C' if name == '1.1 Statements' else 'A'}{first_hdr + 1}"
