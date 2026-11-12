# Reproducibility

Everything needed to rebuild the De'Longhi DCF valuation from raw data and check that you get the same numbers. This folder is self-contained: run every command from **inside this folder**.

**Headline result to reproduce:** De'Longhi is worth **€56.47 per share** (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is **€44.34 to €74.08**; the market price of **€45.32** (close of 6 Nov 2026) sits at the 12th percentile, 19.7% below the base-case value.

## What is in this folder

| Path | Purpose |
|------|---------|
| `run.py` | Pipeline runner: `python run.py --fresh` rebuilds every output from `data/raw/` |
| `py/`, `sql/` | The analysis code (the only place the logic lives) |
| `checks/` | Acceptance checks per step (`check_step01`–`04` run inside the pipeline) and helpers |
| `fetch_data.py` | Downloads the company PDFs and Damodaran datasets into `data/raw/` and checks every SHA-256 |
| `data/raw/SOURCES.md` | Every input file: URL, size, SHA-256, licence |
| `data/raw/market/` | Frozen snapshot of the ECB and Yahoo Finance files (these feeds change daily, so the snapshot *is* the input) |
| `requirements-lock.txt` | Exact package versions the results were produced with |
| `reference/xlsx_cells.txt` | Every cell of the published workbook, for comparison |
| `verify_reproduction.py` | Compares your rebuilt workbook with the reference |
| `brief/`, `plan/`, `evidence/`, `report/final_review.md` | Research brief, approved plan with amendments, per-step evidence packs, data quality log and final review. They explain *why* each assumption was chosen, and the process guide quotes from them |

Created when you run the steps below (not stored): `data/raw/reports/`, `data/raw/damodaran/`, `data/curiosity.duckdb`, and the outputs in `report/`.

## Requirements

- Python 3.14 (tested; 3.11+ should work). Windows 11 was the test platform.
- Internet access, once, to download the company PDFs and Damodaran datasets (about 100 MB).
- Recommended: `pdftotext` 4.06 (xpdf) on your PATH. It ships with Git for Windows in `C:\Program Files\Git\ucrt64\bin`. Without it the loader falls back to `pdfplumber`, which spaces words differently and can change the parsed text.
- For the process guide PDF and the note's styling: the Garamond and Gill Sans MT fonts in `C:\Windows\Fonts` (installed with Microsoft Office). The numbers do not depend on them.

## Steps

From inside this folder:

```bash
# 1. Environment
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-lock.txt   # Linux/macOS: .venv/bin/python

# 2. Inputs: downloads the PDFs/datasets, checks the market snapshot, verifies every SHA-256
.venv\Scripts\python.exe fetch_data.py

# 3. Rebuild everything (about 3 minutes): database, WACC, DCF, Monte Carlo, workbook, note, guide
.venv\Scripts\python.exe run.py --fresh

# 4. Compare with the published results
.venv\Scripts\python.exe verify_reproduction.py
```

Step 3 prints the headline sentence near the end and `failed checks on Checks sheet: 0`. Step 4 should print two `PASS` lines. The outputs land in `report/`: `DeLonghi_DCF_Valuation.xlsx`, `DeLonghi_DCF_Valuation_note.docx` and `DeLonghi_DCF_process_guide.pdf` are the files published in `../Deliverables/` as `WorkBook.xlsx`, `Valuation note.docx` and `Process guide.pdf`.

## What the pipeline does

| Step | Files | Result |
|------|-------|--------|
| 0 | `py/00_load_raw.py`, `sql/00_*.sql` | Loads PDFs, Damodaran and market files into `data/curiosity.duckdb` (`raw_` tables) |
| 1 | `py/01_statements.py`, `sql/01_ratios.sql` | Historical statements FY2021 to FY2025 and ratios |
| 2 | `py/02_wacc_bridge.py` | Cost of capital (CAPM, Damodaran beta, country premium) and bridge inputs |
| 3 | `py/03_forecast_valuation.py`, `py/dcf.py` | FCFF forecast, discounting, terminal value, equity bridge, value per share |
| 4 | `py/04_sensitivity_mc.py` | WACC × g grid, beta sensitivity, 10,000-run Monte Carlo (seed 20261109) |
| 5 | `py/05_build_report.py` | Excel workbook; also reruns checks 1–4 and a two-run determinism test (written to the `Checks` sheet) |
| 6 | `py/06_build_note.py` | Investment note (.docx) and chart, numbers read back from the workbook |
| 7 | `py/07_process_guide.py` | Process guide (.pdf), numbers read from the database and the documents listed above |

`checks/check_step05.py` to `check_step09.py` were regression checks used while the project was built. They compare against internal baselines that are not shipped here, so they are kept for transparency but are not part of the reproduction.

## What "reproduced" means

- **Numbers:** every workbook cell matches `reference/xlsx_cells.txt` (the author line `Overview!A20` is excluded). The Monte Carlo is seeded, so it is exact.
- **Not byte-identical files:** `.xlsx`, `.docx` and `.pdf` files embed timestamps, so their file hashes differ between runs even when contents are identical. Compare cells (step 4), not hashes.
- Tested on 2026-11-12 from a clean copy of this folder: all 2,985 cells identical, and the rebuilt note and guide have the same text as the published deliverables.

## Known limitations

1. **Market data is a snapshot.** The ECB yields and Yahoo prices were downloaded on 2026-11-09 (the 9 Nov Yahoo bar is intraday, the valuation uses the 6 Nov close). Downloading them again returns a different window and different values; use the files in `data/raw/market/`.
2. **Source URLs can change.** `fetch_data.py` reports `MISMATCH` or `MISSING` if a publisher moves or edits a file. The hashes in `data/raw/SOURCES.md` are the integrity record. Results are only guaranteed for files that match them. (All 25 files matched on 2026-11-12.)
3. **Licences.** The De'Longhi reports are copyrighted and Yahoo Finance data is for personal, non-commercial use. This is why the PDFs and Damodaran files are downloaded rather than stored here, and why the Yahoo snapshot is kept only for reproducibility.
