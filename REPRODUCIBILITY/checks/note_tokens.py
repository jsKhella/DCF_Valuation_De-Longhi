"""Number tokens of the investment note (reading order), with the same scrub as checks/check_step06.py
(dates, '80% Monte Carlo' and FY/H labels removed; thousands separators kept as written).
Usage: python checks/note_tokens.py <note.docx> > note_tokens.txt   (also importable: note_tokens(path))
"""
import re
import sys

from docx import Document

NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"


def note_text(path):
    doc = Document(str(path))
    paras = [p.text for p in doc.paragraphs]
    for t in doc.tables:
        for row in t.rows:
            paras += [cell.text for cell in row.cells]
    return "\n".join(paras)


def note_tokens(path, strip_tags=False):
    text = note_text(path)
    if strip_tags:
        text = re.sub(r"\[\d\.\d\]", " ", text)
    scrub = re.sub(rf"\b\d{{1,2}} (?:{MONTHS}) \d{{4}}", " ", text)
    scrub = re.sub(r"80% Monte Carlo", " ", scrub)
    scrub = re.sub(r"\b(?:FY|H)\d+E?\b", " ", scrub)
    return NUM.findall(scrub)


if __name__ == "__main__":
    print("\n".join(note_tokens(sys.argv[1])))
