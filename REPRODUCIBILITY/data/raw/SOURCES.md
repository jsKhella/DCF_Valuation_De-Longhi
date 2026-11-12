# Raw data sources

All files downloaded by the Planner on **2026-11-09** (between 15:20 and 15:55 UTC) with `curl`, no login.
Total size about 101 MB. Files are git-ignored; this file is the record needed to re-download them and check
integrity (`sha256sum`). Loaded by step 0 (`py/00_load_raw.py`, `sql/00_load_raw.sql`).

## De'Longhi S.p.A. company documents (`reports/`)
Licence: company public-disclosure documents (Italian listed-issuer obligations, CONSOB / Borsa Italiana).
Copyright De'Longhi S.p.A.; no open licence. Used here for private research with source citation. The English
annual reports are "courtesy copy" translations of the Italian legal originals (the ESEF filing is the legal version).

| File | URL | Bytes | SHA-256 |
|------|-----|-------|---------|
| delonghi_FY2021_annual_report.pdf | https://www.delonghigroup.com/sites/default/files/Financial%20Annual%20Report%20at%2031%20December%202021_0.pdf | 7047728 | 9f617154c938bb51da1bc537f84e1d81dcca290488f08128051865dbe873d190 |
| delonghi_FY2022_annual_report.pdf | https://www.delonghigroup.com/sites/default/files/Annual%20Report%20at%2031.12.2022_courtesy%20copy.pdf | 6585623 | 2e1eddc66a7e748d9e1899288f440a451956549085a6a84f7901d1296374daa2 |
| delonghi_FY2023_annual_report.pdf | https://www.delonghigroup.com/sites/default/files/Annual%20financial%20report%2031.12.2023-courtesy%20copy.pdf | 8843576 | cc7e0d6ed91f2e0a81de3ea448a4ddad71c7faa3ab19ba76fbbae150ac5de78a |
| delonghi_FY2024_annual_report.pdf | https://www.delonghigroup.com/sites/default/files/2025-04/Financial%20Report%202024_2.pdf | 22151147 | 8ea98b9c3f74c9e5c879d4e3b2c5a491c8186084c72d7f3e7903e36235ff1190 |
| delonghi_FY2025_annual_report.pdf | https://www.delonghigroup.com/sites/default/files/Financial%20Annual%20Report%202025_coutesy%20copy.pdf | 24656608 | 6ffcb39b0527e753f6e7cabf3bbc0f5c6c0eac8a6100235a636a5b80e50f1aab |
| delonghi_FY2025_results_presentation.pdf | https://www.delonghigroup.com/sites/default/files/De%27%20Longhi%20Group%20-%20FY%20%26%20Q4%202025%20Results.pdf | 2979386 | 950e2f6268274e172e76d33cdb5ab2f6bf6b045142a2e49abc5e5064e72e9061 |
| delonghi_H1_2026_interim_report.pdf | https://www.delonghigroup.com/sites/default/files/Interim%20financial%20report%20at%2030%20June%202026_PER%20PUBBLICAZIONE.pdf | 3992337 | 539544e0ef2d32f13a34b84fc1d09e9d5d6811a8a21686ace8149a1a68aff331 |
| delonghi_H1_2026_press_release.pdf | https://www.delonghigroup.com/sites/default/files/DeLonghi%20-%20press%20release%20Q2-26%20results_E.pdf | 1555034 | 0ca2b4586d2127ef85adc989dbc5cd2c226c66c12c5f956b51db41331c991d20 |
| delonghi_H1_2026_presentation.pdf | https://www.delonghigroup.com/sites/default/files/De%27%20Longhi%20Group%20-%20Q2%202026%20Results.pdf | 2469203 | 8e513bc026b296ca2fa7d041c3e0f093c4e3295f8a0fb96f5a90726c422ad340 |

The 9M / Q3 2026 report was not yet published on the download date (results archive for 2026 lists Q1 and H1 only).

## Damodaran Online datasets, January 2026 update (`damodaran/`)
Source: Aswath Damodaran, NYU Stern, https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datacurrent.html
Licence: freely downloadable public data; no formal licence; the author asks for attribution. Update dates read from
the files: industry files 2026-01-05, ctryprem 2026-01-01 (file saved 2026-01-27).

| File | URL | Bytes | SHA-256 |
|------|-----|-------|---------|
| betaEurope.xls | https://pages.stern.nyu.edu/~adamodar/pc/datasets/betaEurope.xls | 81408 | bbbb860ddb252c3b881105c6f69df378a6facff7af1987b9413dfa98405a710a |
| betaGlobal.xls | https://pages.stern.nyu.edu/~adamodar/pc/datasets/betaGlobal.xls | 82944 | 10c33f46df2a35fa7e4e8c4386c01f9da636fc2ab3e1e98307a52a947c9ab52b |
| waccEurope.xls | https://pages.stern.nyu.edu/~adamodar/pc/datasets/waccEurope.xls | 78848 | ed2454dba81c471fadb7eb97f12deffb115d126611b4a7ad155c38cd17e73235 |
| vebitdaEurope.xls | https://pages.stern.nyu.edu/~adamodar/pc/datasets/vebitdaEurope.xls | 58368 | c0561e72707d522d8612b5523f02f4bab3fb7fc5182858eb82fa77242aa48fd1 |
| vebitdaGlobal.xls | https://pages.stern.nyu.edu/~adamodar/pc/datasets/vebitdaGlobal.xls | 58368 | 7c54331b5461e0a1df6b0b3e4225bcd7a8d45efd189f74b2bbdfc229f8e00c27 |
| peEurope.xls | https://pages.stern.nyu.edu/~adamodar/pc/datasets/peEurope.xls | 61952 | 547de2d52bf3606734bca8bce34e3d26380461699c80173efca6904a650f955e |
| peGlobal.xls | https://pages.stern.nyu.edu/~adamodar/pc/datasets/peGlobal.xls | 63488 | 762439484f797df8571cce9f5d529a6ab60e40d873cd91801aecdca0bd8276b3 |
| ctryprem.xls | https://pages.stern.nyu.edu/~adamodar/pc/datasets/ctryprem.xls | 994304 | 66135df68bc4c8830830a29f9017f848968d85712ff7ba2627c8355d04fae784 |
| countrytaxrates.xls | https://pages.stern.nyu.edu/~adamodar/pc/datasets/countrytaxrates.xls | 49152 | acaf535aa974c9f77898c26fb0333ee26ad1ef3ce1db0412f817fa7ec60b5582 |
| indname.xls | https://pages.stern.nyu.edu/~adamodar/pc/datasets/indname.xls | 22255104 | a1f4d70aa2cff728d846ca0b2fbdf7ea94030d2df6e140418920d3addb22c363 |

## Market data (`market/`)

### ECB Data Portal: long-term interest rate for convergence purposes (10-year government bond yield, monthly average)
Licence: ECB statistics reuse policy, free reuse including commercial with source acknowledgement
("Source: ECB Data Portal"). Last observation in file: 2026-09.

| File | URL | Bytes | SHA-256 |
|------|-----|-------|---------|
| ecb_irs_italy_10y_monthly.csv | https://data-api.ecb.europa.eu/service/data/IRS/M.IT.L.L40.CI.0000.EUR.N.Z?format=csvdata&startPeriod=2021-01 | 25111 | 4e33b1d25a2dfbe9a7c63cc01467dffdabe14b4f53b35068b8c4200df42c6a58 |
| ecb_irs_germany_10y_monthly.csv | https://data-api.ecb.europa.eu/service/data/IRS/M.DE.L.L40.CI.0000.EUR.N.Z?format=csvdata&startPeriod=2021-01 | 25257 | bf2de1e06b610b8cc6cee024ea70b34e819e945fc3d7c9d25efc10326d69d378 |

### Yahoo Finance chart API (v8), 5 years of daily prices, downloaded 2026-11-09 ~15:50 UTC
Licence: Yahoo terms of service (personal, non-commercial use; no redistribution). Unauthenticated public endpoint.
The 2026-11-09 bar is an **intraday** value (Milan was still trading at download time), not a close.
The fundamentals endpoints (quoteSummary, v7 quote) require a session crumb and were NOT used.

| File | URL | Bytes | SHA-256 |
|------|-----|-------|---------|
| yahoo_chart_DLG.MI.json | https://query1.finance.yahoo.com/v8/finance/chart/DLG.MI?range=5y&interval=1d&events=div%2Csplit | 137655 | 95e229a00916b685ad62be235ddf0ffa19bfc0aefcdb64d335e08cc75563dc2a |
| yahoo_chart_FTSEMIB.MI.json | https://query1.finance.yahoo.com/v8/finance/chart/FTSEMIB.MI?range=5y&interval=1d&events=div%2Csplit | 78751 | 1cfa26771311444d67c6ccda501c99b04755db9be7d5621900d6c0014e2f41e8 |
| yahoo_chart_SK.PA.json | https://query1.finance.yahoo.com/v8/finance/chart/SK.PA?range=5y&interval=1d&events=div%2Csplit | 125554 | a382ef4d046b9e3f96e053d98e6aac23a8e824740a455fc6edc4f27c45947d6d |
| yahoo_chart_ELUX-B.ST.json | https://query1.finance.yahoo.com/v8/finance/chart/ELUX-B.ST?range=5y&interval=1d&events=div%2Csplit | 129958 | 0b049e18b96cb9947b7fdf95561634a954431a53d5ca35d74db077a298603ef9 |
| yahoo_chart_BRG.AX.json | https://query1.finance.yahoo.com/v8/finance/chart/BRG.AX?range=5y&interval=1d&events=div%2Csplit | 136930 | fe4f551026d4bbe5c7c00550d2bf6948bd549976fa47072c9c5481bf1361ba6b |
| yahoo_chart_SN.json | https://query1.finance.yahoo.com/v8/finance/chart/SN?range=5y&interval=1d&events=div%2Csplit | 88499 | f23130747bbfe204f009025f80fb3889bdce65bf37e71d3b1cdcda1a011d872e |
| yahoo_chart_WHR.json | https://query1.finance.yahoo.com/v8/finance/chart/WHR?range=5y&interval=1d&events=div%2Csplit | 134899 | 596e56e9770961e39b89aff5947808fc0a30653963006b540d6dd63d15954034 |

Peer price files (SK.PA, ELUX-B.ST, BRG.AX, SN, WHR) are only used if the human picks peer option B in the plan.

## Tooling needed to rebuild
- Python packages (in `.venv`, added to requirements.txt): duckdb, pandas, openpyxl, xlrd (reads Damodaran .xls),
  pdfplumber (fallback PDF reader), python-docx (investment note), matplotlib (note chart).
- `pdftotext` 4.06 (xpdf), shipped with Git for Windows at `C:\Program Files\Git\ucrt64\bin\pdftotext.exe`; used with
  `-raw -enc UTF-8`. If absent, py/00_load_raw.py falls back to pdfplumber (slower, different word spacing).
