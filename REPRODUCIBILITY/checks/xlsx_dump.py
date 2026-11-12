"""Cell dump of a workbook in the format of verify/xlsx_dump_run1.txt: one line per non-empty cell,
`Sheet!A1=<repr(value)>|<number format>`, sheets in workbook order, cells row by row.
Usage: python checks/xlsx_dump.py <workbook.xlsx> > out.txt   (also importable: dump_lines(path))
"""
import sys

import openpyxl
from openpyxl.cell.cell import MergedCell


def dump_lines(path):
    wb = openpyxl.load_workbook(path)
    out = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c, MergedCell) or c.value is None:
                    continue
                out.append(f"{ws.title}!{c.coordinate}={c.value!r}|{c.number_format}")
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(dump_lines(sys.argv[1])))
