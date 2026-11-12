"""Step 0 (Planner): load the non-tabular raw sources into DuckDB raw_ tables.

Run from the project root (run.py does this). Inputs are read from data/raw/ only.

Creates / replaces:
  raw_documents            one row per PDF: doc_id, file, sha256, n_pages
  raw_report_lines         one row per text line of every PDF: doc_id, page (1-based PDF page), line_no, text
  raw_damodaran_<name>     one table per Damodaran sheet used (header row = row starting with 'Industry Name'
                           or 'Country'); all columns kept, names lower-snake-cased
  raw_damodaran_params     key/value scalars from the Damodaran files (mature-market ERP, update dates, ...)
  raw_damodaran_indname    company -> industry mapping (sheet 'By industry')

PDF text is extracted with `pdftotext -raw` (xpdf 4.06 ships with Git for Windows at
C:/Program Files/Git/ucrt64/bin). pdftotext separates pages with a form feed, so page numbers are exact
PDF page indices (not the printed page numbers). If pdftotext is missing we fall back to pdfplumber,
which is slower and splits words differently; the fallback is logged.

The .csv / .json sources (ECB yields, Yahoo prices) are loaded by sql/00_load_raw.sql.
"""
import hashlib
import re
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

import duckdb
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "curiosity.duckdb"

PDFS = {
    "AR2021": "reports/delonghi_FY2021_annual_report.pdf",
    "AR2022": "reports/delonghi_FY2022_annual_report.pdf",
    "AR2023": "reports/delonghi_FY2023_annual_report.pdf",
    "AR2024": "reports/delonghi_FY2024_annual_report.pdf",
    "AR2025": "reports/delonghi_FY2025_annual_report.pdf",
    "PRES_FY2025": "reports/delonghi_FY2025_results_presentation.pdf",
    "IR_H1_2026": "reports/delonghi_H1_2026_interim_report.pdf",
    "PR_H1_2026": "reports/delonghi_H1_2026_press_release.pdf",
    "PRES_H1_2026": "reports/delonghi_H1_2026_presentation.pdf",
}

# (table suffix, file, sheet, first-column label of the header row)
DAMODARAN_SHEETS = [
    ("beta_europe", "betaEurope.xls", "Industry Averages", "Industry Name"),
    ("beta_global", "betaGlobal.xls", "Industry Averages", "Industry Name"),
    ("wacc_europe", "waccEurope.xls", "Industry Averages", "Industry Name"),
    ("vebitda_europe", "vebitdaEurope.xls", "Industry Averages", "Industry Name"),
    ("vebitda_global", "vebitdaGlobal.xls", "Industry Averages", "Industry Name"),
    ("pe_europe", "peEurope.xls", "Industry Averages", "Industry Name"),
    ("pe_global", "peGlobal.xls", "Industry Averages", "Industry Name"),
    ("ctryprem", "ctryprem.xls", "ERPs by country", "Country"),
    ("taxrates", "countrytaxrates.xls", "Sheet1", "Country"),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pdf_pages(p: Path):
    exe = shutil.which("pdftotext") or r"C:\Program Files\Git\ucrt64\bin\pdftotext.exe"
    if Path(exe).exists():
        out = subprocess.run([exe, "-raw", "-enc", "UTF-8", str(p), "-"], capture_output=True, check=True)
        pages = out.stdout.decode("utf-8", errors="replace").split("\f")
        if pages and pages[-1].strip() == "":
            pages = pages[:-1]
        return pages, "pdftotext-raw"
    print("  WARNING: pdftotext not found, falling back to pdfplumber", file=sys.stderr)
    import pdfplumber
    with pdfplumber.open(p) as pdf:
        return [(pg.extract_text() or "") for pg in pdf.pages], "pdfplumber"


def snake(s) -> str:
    s = re.sub(r"[^0-9a-zA-Z]+", "_", str(s)).strip("_").lower()
    return s or "col"


def read_sheet(file, sheet, header_label):
    df = pd.read_excel(RAW / "damodaran" / file, sheet_name=sheet, header=None)
    hdr_idx = df.index[df[0].astype(str).str.strip() == header_label][0]
    cols, seen = [], {}
    for c in df.iloc[hdr_idx]:
        n = snake(c) if pd.notna(c) else "unnamed"
        seen[n] = seen.get(n, 0) + 1
        cols.append(n if seen[n] == 1 else f"{n}_{seen[n]}")
    body = df.iloc[hdr_idx + 1:].copy()
    body.columns = cols
    body = body[body[cols[0]].notna()]
    body = body.loc[:, [c for c in cols if not c.startswith("unnamed")]]
    for c in body.columns[1:]:
        conv = pd.to_numeric(body[c], errors="coerce")
        if conv.notna().sum() >= 0.8 * body[c].notna().sum():
            body[c] = conv
        else:
            body[c] = body[c].astype("string")
    body[cols[0]] = body[cols[0]].astype(str).str.strip()
    body.insert(0, "source_file", file)
    return body.reset_index(drop=True)


def main():
    con = duckdb.connect(str(DB))

    # ---- PDFs -> raw_documents, raw_report_lines
    docs, lines = [], []
    for doc_id, rel in PDFS.items():
        p = RAW / rel
        pages, method = pdf_pages(p)
        docs.append({"doc_id": doc_id, "file": rel, "sha256": sha256(p), "n_pages": len(pages), "method": method})
        for i, txt in enumerate(pages, start=1):
            for j, ln in enumerate(txt.splitlines(), start=1):
                if ln.strip():
                    lines.append({"doc_id": doc_id, "page": i, "line_no": j, "text": ln.rstrip()})
        print(f"  {doc_id}: {len(pages)} pages ({method})")
    docs_df, lines_df = pd.DataFrame(docs), pd.DataFrame(lines)
    con.execute("CREATE OR REPLACE TABLE raw_documents AS SELECT * FROM docs_df")
    con.execute("CREATE OR REPLACE TABLE raw_report_lines AS SELECT * FROM lines_df")

    # ---- Damodaran industry / country sheets
    for suffix, file, sheet, label in DAMODARAN_SHEETS:
        df = read_sheet(file, sheet, label)
        con.execute(f"CREATE OR REPLACE TABLE raw_damodaran_{suffix} AS SELECT * FROM df")
        print(f"  raw_damodaran_{suffix}: {len(df)} rows")

    # ---- Damodaran scalar parameters (kept verbatim with their cell location)
    params = []
    erp = pd.read_excel(RAW / "damodaran" / "ctryprem.xls", sheet_name="ERPs by country", header=None)
    params.append(("ctryprem.xls", "ERPs by country", "B2", "date_of_update", str(erp.iat[1, 1])))
    params.append(("ctryprem.xls", "ERPs by country", "E3", "mature_market_erp", str(erp.iat[2, 4])))
    params.append(("ctryprem.xls", "ERPs by country", "E4", "us_erp", str(erp.iat[3, 4])))
    params.append(("ctryprem.xls", "ERPs by country", "E6", "crp_volatility_multiplier", str(erp.iat[5, 4])))
    for f in ["betaEurope.xls", "betaGlobal.xls", "waccEurope.xls", "vebitdaEurope.xls", "peEurope.xls",
              "countrytaxrates.xls"]:
        d = pd.read_excel(RAW / "damodaran" / f, sheet_name=0 if f == "countrytaxrates.xls" else "Industry Averages",
                          header=None)
        params.append((f, "Industry Averages" if f != "countrytaxrates.xls" else "Sheet1", "B1",
                       "date_updated", str(d.iat[0, 1])))
    b = pd.read_excel(RAW / "damodaran" / "betaEurope.xls", sheet_name="Industry Averages", header=None)
    params.append(("betaEurope.xls", "Industry Averages", "F9", "marginal_tax_used_for_unlevering", str(b.iat[8, 5])))
    w = pd.read_excel(RAW / "damodaran" / "waccEurope.xls", sheet_name="Industry Averages", header=None)
    params.append(("waccEurope.xls", "Industry Averages", "D9", "long_term_treasury_rate", str(w.iat[8, 3])))
    pdf = pd.DataFrame(params, columns=["source_file", "sheet", "cell", "param", "value"])
    con.execute("CREATE OR REPLACE TABLE raw_damodaran_params AS SELECT * FROM pdf")

    ind = pd.read_excel(RAW / "damodaran" / "indname.xls", sheet_name="By industry", header=None)
    hdr = ind.index[ind[0].astype(str).str.contains("Company Name", case=False)][0]
    ind.columns = [snake(c) for c in ind.iloc[hdr]]
    ind = ind.iloc[hdr + 1:].astype("string").reset_index(drop=True)
    con.execute("CREATE OR REPLACE TABLE raw_damodaran_indname AS SELECT * FROM ind")
    print(f"  raw_damodaran_indname: {len(ind)} rows")
    con.close()


if __name__ == "__main__":
    main()
