"""Ledger identity, defined once: palette, fonts, sizes and adapters for openpyxl, reportlab, python-docx and matplotlib.

Purpose
    The single place where a colour, a font name, a font file or a type size is written down (Amendment 2, R-D). The
    workbook (py/report_style.py, py/05_build_report.py), the investment note (py/06_build_note.py) and the process
    guide (py/07_process_guide.py) import from here. No other file under py/ holds a hex colour literal.
Inputs
    none (constants only). Font files: Windows fonts folder (Garamond, Gill Sans MT) and matplotlib's bundled DejaVu Sans.
Outputs
    constants and small adapter functions; nothing is written to disk.
Brief definitions implemented
    none (presentation only). Palette: paper, ink, one accent (vermilion, key results and step numerals only), grey,
    hairline and one neutral tint. Type: headings Garamond, body and tables Gill Sans MT.
"""
from pathlib import Path

# ---- palette (hex without '#') ----
PAPER, INK, VERMILION, GREY, HAIRLINE, TINT = "F6F1E7", "1A1A1A", "C8361D", "6B6B6B", "BDB6A8", "ECE4D2"
PALETTE = {PAPER, INK, VERMILION, GREY, HAIRLINE, TINT}

# ---- fonts ----
HEAD_FONT, BODY_FONT = "Garamond", "Gill Sans MT"
SYMBOL_FONT = "DejaVuSans"            # only used for the "▸" glyph in the PDF
FONT_NAMES = {HEAD_FONT, BODY_FONT}
FONTS_DIR = Path("C:/Windows/Fonts")
TTF = {
    "Garamond": FONTS_DIR / "GARA.TTF", "Garamond-Bold": FONTS_DIR / "GARABD.TTF",
    "Garamond-Italic": FONTS_DIR / "GARAIT.TTF",
    "GillSansMT": FONTS_DIR / "GIL_____.TTF", "GillSansMT-Bold": FONTS_DIR / "GILB____.TTF",
    "GillSansMT-Italic": FONTS_DIR / "GILI____.TTF",
}

# ---- sizes (points) ----
BODY_PT, SMALL_PT, NOTE_PT, HEAD_PT, SUBTITLE_PT, TITLE_PT, NUMERAL_PT, HEADLINE_PT = 10, 9, 9, 12, 14, 22, 28, 14
LINE_PT, PAD_PT = 14, 6               # row height model for wrapped text in the workbook
ARROW = "\u25b8"                      # "▸"


def dejavu_path():
    import matplotlib
    return Path(matplotlib.__file__).resolve().parent / "mpl-data" / "fonts" / "ttf" / "DejaVuSans.ttf"


# ---- openpyxl adapter ----
def xl_font(kind="body", size=BODY_PT, bold=False, italic=False, color=INK, underline=None):
    from openpyxl.styles import Font
    return Font(name=HEAD_FONT if kind == "head" else BODY_FONT, size=size, bold=bold, italic=italic, color=color,
                underline=underline)


def xl_fill(color):
    from openpyxl.styles import PatternFill
    return PatternFill("solid", fgColor=color)


def xl_side(color=HAIRLINE, style="thin"):
    from openpyxl.styles import Side
    return Side(style=style, color=color)


# ---- reportlab adapter (used by py/07_process_guide.py in step 8) ----
def rl_register_fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    for name, path in TTF.items():
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFont(TTFont(SYMBOL_FONT, str(dejavu_path())))
    from reportlab.lib.fonts import addMapping
    addMapping("Garamond", 0, 0, "Garamond")
    addMapping("Garamond", 1, 0, "Garamond-Bold")
    addMapping("Garamond", 0, 1, "Garamond-Italic")
    addMapping("GillSansMT", 0, 0, "GillSansMT")
    addMapping("GillSansMT", 1, 0, "GillSansMT-Bold")
    addMapping("GillSansMT", 0, 1, "GillSansMT-Italic")


def rl_color(hex6):
    from reportlab.lib import colors
    return colors.HexColor("#" + hex6)


# ---- python-docx adapter (used by py/06_build_note.py in step 8) ----
def docx_run_font(run, kind="body", size=BODY_PT, bold=False, italic=False, color=INK):
    from docx.shared import Pt, RGBColor
    name = HEAD_FONT if kind == "head" else BODY_FONT
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts")
    if rfonts is not None:
        for att in ("ascii", "hAnsi", "cs", "eastAsia"):
            rfonts.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}" + att, name)


# ---- matplotlib adapter (used by py/06_build_note.py in step 8) ----
def mpl_hex(hex6):
    return "#" + hex6


def mpl_rc():
    return {"font.family": "serif", "font.serif": [HEAD_FONT, "DejaVu Serif"], "text.color": mpl_hex(INK),
            "axes.edgecolor": mpl_hex(GREY), "axes.labelcolor": mpl_hex(INK), "xtick.color": mpl_hex(INK),
            "ytick.color": mpl_hex(INK), "figure.facecolor": mpl_hex(PAPER), "axes.facecolor": mpl_hex(PAPER)}
