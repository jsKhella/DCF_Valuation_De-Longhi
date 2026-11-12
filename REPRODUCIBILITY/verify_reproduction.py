"""Compare a fresh rebuild with the reference results shipped in reference/.

    python verify_reproduction.py

Checks (run after `python run.py --fresh`):
  1. Every cell of report/DeLonghi_DCF_Valuation.xlsx equals the reference cell dump
     (the author line Overview!A20 is excluded).
  2. The headline numbers of the report are the published ones.
Workbook/docx/pdf byte hashes are NOT compared: zip/PDF containers embed timestamps.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "checks"))
from xlsx_dump import dump_lines  # noqa: E402

HEADLINE = ["56.47", "44.34", "74.08", "45.32", "6.52%", "2.00%"]


def main():
    ref = (Path(__file__).parent / "reference" / "xlsx_cells.txt").read_text(encoding="utf-8").splitlines()
    new = [l for l in dump_lines(ROOT / "report" / "DeLonghi_DCF_Valuation.xlsx") if not l.startswith("0.0 Overview!A20=")]
    ok = True
    diff = [(a, b) for a, b in zip(ref, new) if a != b]
    if len(ref) != len(new) or diff:
        ok = False
        print(f"FAIL  workbook differs from reference: {len(ref)} vs {len(new)} cells, {len(diff)} changed")
        for a, b in diff[:5]:
            print("  ref:", a[:160], "\n  new:", b[:160])
    else:
        print(f"PASS  all {len(new)} workbook cells identical to the reference")
    text = "\n".join(new)
    missing = [h for h in HEADLINE if h not in text]
    if missing:
        ok = False
        print("FAIL  headline figures not found in workbook:", missing)
    else:
        print("PASS  headline figures present:", ", ".join(HEADLINE))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
