"""Number-token rules shared by py/07_process_guide.py (writes report/build/guide_numbers.json) and checks/check_step08.py.

Purpose
    One definition of "a number token" in the process guide, so that the builder's provenance list and the checker's
    extraction from the finished PDF use identical rules.
Inputs
    none (pure functions on text).
Outputs
    NUM, scrub(), tokens(), norm().
Brief definitions implemented
    none (presentation only). Plan Amendment 2, step 8 "Guide numbers": only section ids, "[x.y]" tags, folios, ISO dates,
    FY/H labels and the sheet ids inside a "WORKBOOK" line are excluded, by regex. There is no small-integer exemption.
"""
import re

NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
WORKBOOK_PREFIX = "WORKBOOK ▸"
_EXCLUDE = [
    re.compile(r"§[0-9A-Z][0-9A-Za-z.]*"),        # section ids: "§1.1", "§A.2"
    re.compile(r"\[\d\.\d\]"),                           # sheet tags: "[3.2]"
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),                # ISO dates
    re.compile(r"\b(?:FY|H)\d+E?\b"),                    # FY2025, FY2026E, H1
    re.compile(r"\bPage \d+\b"),                         # folio
]


def scrub(text):
    """Remove the excluded patterns; lines that start with the WORKBOOK marker are dropped whole."""
    lines = [ln for ln in text.split("\n") if not ln.strip().startswith(WORKBOOK_PREFIX)]
    out = "\n".join(lines)
    for rx in _EXCLUDE:
        out = rx.sub(" ", out)
    return out


def tokens(text):
    """Number tokens in reading order, thousands separators removed (a trailing comma is not part of a number)."""
    return [t.replace(",", "") for t in NUM.findall(scrub(text))]


def norm(text):
    """Whitespace-normalised text with typographic dashes and the minus sign folded to '-'."""
    t = text.replace("−", "-").replace("–", "-").replace("—", "-").replace("’", "'")
    return re.sub(r"\s+", " ", t).strip()
