# Data feasibility: De'Longhi DCF valuation
Checked: 2026-11-09 by Planner. Database: `data/curiosity.duckdb` (rebuild with `python run.py --fresh`, step 0).

Revised 2026-11-09 for the brief's Amendment (resized scope, 6 steps). No new downloads: the data on disk and the
step-0 loader are reused unchanged. The resize removed the need for peer-by-peer data and for the minorities and
country-risk choices, because the human has now stated those.

## Verdict: GO WITH CHANGES

Every definition in brief section 2 and every workbook sheet in the amended section 6 can be computed from data that
is on disk, loaded and profiled. Four points are covered only if a definition is applied in a specific way. None is
adopted silently; each is a decision for the human in `plan/plan.md`:

1. **Risk-free rate "on the price date" (section 2):** no free daily 10-year BTP series could be downloaded without a
   login. The ECB Data Portal publishes the monthly average 10-year Italian yield. The latest month is **2026-09:
   4.362%**. Proposed change: use the latest available monthly average (plan Decision 2).
2. **Net debt and WACC weights (section 2):** De'Longhi has **net cash**. Net financial position at 31 Dec 2025 is
   +770.0 m (AR2025 / IR_H1_2026 p.18). So "net debt plus leases" is a negative debt weight. The brief's net-debt
   definition (debt + leases - cash) also leaves out about 305 m of current financial receivables and non-current
   financial assets that the company counts in its net financial position. Plan Decisions 4 and 5.
3. **Beta (section 2, amended: Damodaran Europe beta relevered plus one sensitivity line):** De'Longhi's Damodaran
   industry is Europe Furn/Home Furnishings (BIT:DLG in `raw_damodaran_indname`). Its unlevered beta is 0.345 (raw)
   or 0.397 (corrected for cash), and the sample's average D/E is 130%, so the unlevered figure is low. The Global
   figure for the same industry is 0.938 (cash-corrected). Which Europe variant to use, and which beta to show on the
   sensitivity line, is plan Decision 3.
4. **Valuation-date mismatch (section 8, open question):** the price date is 6 Nov 2026. The latest audited balance
   sheet is 31 Dec 2025 and the latest interim balance sheet is 30 Jun 2026; the Q3 2026 report was not yet published.
   Plan Decision 1.

Resolved by the Amendment (no longer decisions): the Peers sheet is replaced by Multiples_Check, which uses only the
Damodaran Furn/Home Furnishings EV/EBITDA (Europe 9.45x, Global 10.63x, positive-EBITDA firms); minorities are taken
at book value (197.8 m at YE2025); the brief's cost-of-equity formula (BTP + beta x (ERP + Italy default spread)) is
kept and the double counting of Italy risk is noted as a limitation. The 7 Yahoo price files for peers and the
FTSE MIB stay on disk and loaded, but no step uses them.

Time window: FY2021-FY2025 are all published (FY2025 annual report approved April 2026), so the brief's fallback to
FY2020-FY2024 is **not** needed. Population: De'Longhi S.p.A. consolidated group. Present in every annual report.

## Sources on disk
Full URLs, byte sizes, SHA-256 hashes and licences are in `data/raw/SOURCES.md`. About 101 MB in total, downloaded 2026-11-09.

| Group | Files | What it gives |
|-------|-------|---------------|
| De'Longhi annual reports FY2021-FY2025 (English courtesy copies) | 5 PDFs | Consolidated IS, BS, CF, notes (non-recurring items note 8, leases note 15, financial payables notes 32-33, shares notes 28/31) |
| De'Longhi H1 2026 interim report, press release, presentation; FY2025 results presentation | 4 PDFs | Latest NFP (30 Jun 2026), treasury shares, 2026 guidance, H1 2026 distributions |
| Damodaran Jan 2026 | 10 .xls | Industry betas (Europe, Global), WACC Europe, EV/EBITDA and P/E (Europe, Global), country ERP/default spread, marginal tax, company-to-industry map |
| ECB Data Portal | 2 CSV | Monthly 10-year yield, Italy and Germany, 2021-01 to 2026-09 |
| Yahoo Finance chart API | 7 JSON | Daily prices for 5 years: DLG.MI (market price), plus FTSE MIB and 5 peers (loaded but unused after the Amendment) |

Tooling added: `xlrd`, `pdfplumber`, `python-docx`, `matplotlib` installed in `.venv` and appended to
`requirements.txt`. PDF text comes from `pdftotext -raw` (xpdf 4.06, bundled with Git for Windows). The step-0 loader
falls back to pdfplumber if pdftotext is missing.

## Load (step 0, registered in run.py)
`run.py` STEPS[0] = `py/00_load_raw.py` (PDFs and .xls; DuckDB cannot read them natively) -> `sql/00_load_raw.sql`
(CSV and JSON) -> `sql/00_profile.sql` (writes `profile_columns`, `profile_tables`, `profile_keys`,
`profile_coverage`). A full `--fresh` rebuild takes about 15 s.

## Profile

| Table | Rows | Key | Key unique? | Notes |
|-------|------|-----|-------------|-------|
| raw_documents | 9 | doc_id | yes (9/9) | n_pages 13-289; all extracted with pdftotext-raw |
| raw_report_lines | 79,876 | doc_id, page, line_no | yes | 0% nulls. `page` = PDF page index (1-based), **not** the printed page number. The euro sign becomes U+FFFD |
| raw_ecb_yield_10y | 138 | country, period | yes | IT and DE, 2021-01 to 2026-09 (69 months each), 0% nulls, yield -0.583 to 4.885 |
| raw_yahoo_prices | 8,425 | ticker, trade_date | **no, 1 duplicate** | BRG.AX 2026-11-09 appears twice (one row has a null close). DLG.MI: 1,271 rows, 2021-11-09 to 2026-11-09. Close nulls 0.01%. The 2026-11-09 bars are intraday |
| raw_damodaran_beta_europe / _global | 96 / 96 | industry_name | yes | Europe "average_2021_2026" and Global "average_2020_24" history columns differ in name |
| raw_damodaran_wacc_europe | 96 | industry_name | n/a | Damodaran's own rf = 3.95% (Jan 2026) |
| raw_damodaran_vebitda_europe / _global | 96 / 96 | industry_name | yes | ev_ebitda null 2-3% (industries with negative EBITDA) |
| raw_damodaran_pe_europe / _global | 96 / 96 | industry_name | yes | |
| raw_damodaran_ctryprem | 180 | country | yes | Columns 2-3 hold region / rating text for some rows (sheet layout); Italy row is clean |
| raw_damodaran_taxrates | 251 | country | **no, 22 duplicates** | Duplicates are footnote rows below the table. Italy appears once: 27.81% |
| raw_damodaran_params | 12 | param+file | n/a | Mature-market ERP 4.23%, CRP volatility multiplier 1.5234, update dates |
| raw_damodaran_indname | 48,156 | exchange_ticker | **no, 12 duplicates** | Only '-' tickers repeat. BIT:DLG -> "Furn/Home Furnishings", Developed Europe |

### Key facts found in the profile (anchors for acceptance checks; EUR thousand as printed)
| FY | Total consolidated revenues | EBIT reported | of which non-recurring | Total assets | Closing cash | Source (doc, PDF page) |
|----|----|----|----|----|----|----|
| 2021 | 3,221,587 | 386,930 | (30,762) | 3,930,901 | 1,026,081 | AR2022 p.83 (comparative); AR2021 p.75/77/79 original |
| 2022 | 3,158,433 | 263,538 | 8,250 | 3,553,706 | 770,247 | AR2023 p.90 (comparative); AR2022 p.83/85/87 |
| 2023 | 3,075,904 | 329,628 | (5,502) | 3,812,428 | 1,250,198 | AR2024 p.137 (comparative); AR2023 p.90/92/94 |
| 2024 | 3,497,555 | 430,801 | (390) | 4,336,126 | 1,019,711 | AR2025 p.144 (comparative); AR2024 p.137/139/141 |
| 2025 | 3,801,458 | 458,145 | (1,637) | 4,160,508 | 998,448 | AR2025 p.144/146/148 |

Other anchors:
- NFP +770.0 m at 31 Dec 2025 and +686.6 m at 30 Jun 2026, of which lease liabilities 94.0 / 91.1 m (IR_H1_2026 p.18).
- H1 2026 dividends paid 127.9 m and treasury shares bought 28.5 m (IR_H1_2026 p.18).
- Treasury shares 2,574,620 at 30 Jun 2026 (IR_H1_2026, note 26).
- Minority interest (BS) 197.8 m at YE2025. Minorities' share of FY2025 profit: 25.1 m of 341.4 m.
- FY2026 guidance (PR_H1_2026, revised 30 Jul 2026): revenue growth at a mid-single-digit rate; adjusted EBITDA 670-690 m. There is no multi-year strategic plan.
- DLG.MI last completed close before download: 2026-11-06, EUR 45.32.
- Italy 10y yield: Sep 2026 4.362%; Germany 10y on the same series is also available.
- Damodaran: mature ERP 4.23%; Italy Baa2 default spread 1.618%; Italy CRP 2.465%; Italy marginal tax 27.81%.

### Data-quality observations (for evidence/data_quality_log.md in step 1)
- **Restatements:** comparative columns can differ from the original reports. Example: FY2021 minority profit is 684 in AR2021 and 651 in AR2022. Rule proposed in the plan: take each year from the latest report that presents it, and log every difference larger than 0.1 m.
- **La Marzocco:** consolidated during 2024 (business combination 302.3 m cash out, minority interest +178.7 m). FY2021-23 are not like-for-like with FY2024-25.
- **FY2021 acquisition:** Capital Brands was acquired in 2021, and FY2021 carries -30.8 m of non-recurring items.
- **FY2025 reclassification:** production payroll and service costs were reclassified. Line items move; EBIT does not.
- **Two non-recurring measures:** the IS "of which non-recurring" column (brief definition) is different from management's "non-recurring / share-based plan" (-35.9 m in FY2025, which includes stock-option cost). The brief's definition keeps share-based cost inside adjusted EBIT, but the 2026 EBITDA guidance excludes it.
- **Interim prices:** the Yahoo bar for 2026-11-09 is intraday and must not be used as a close.

## Coverage

| Brief item | Table(s) and columns | Status |
|------------|----------------------|--------|
| Fiscal years FY2021-25 history | raw_report_lines (AR2022-AR2025 comparative columns plus AR2025), raw_documents | Covered |
| Forecast FY2026E-30E | Derived from history plus guidance in PR_H1_2026 / PRES_H1_2026 lines | Covered (guidance covers FY2026 only) |
| Adjusted EBIT | raw_report_lines: IS "EBIT" row with its "of which non-recurring" column; note 8 "Non-recurring income/(expenses)" for item detail and page | Covered |
| FCFF: D&A | IS "Amortization" row (includes right-of-use depreciation); note 15 for the lease part | Covered |
| FCFF: capex | CF "Investments in intangible assets", "Investments in property, plant and equipment"; note 15 right-of-use "Additions" | Covered |
| FCFF: change in NWC | BS TRADE RECEIVABLES, INVENTORIES, TRADE PAYABLES (5 year-ends plus YE2020 from AR2021) | Covered |
| Tax rate (historical) | IS "Taxes", "PROFIT (LOSS) BEFORE TAXES" | Covered |
| Tax rate (marginal) | raw_damodaran_taxrates where country = 'Italy' (27.81%) | Covered |
| NWC % revenue | as above | Covered |
| Cost of equity: rf | raw_ecb_yield_10y country = 'IT', latest period | **Covered with change**: monthly average, not the price date (Decision 2) |
| Cost of equity: beta | raw_damodaran_beta_europe where industry_name = 'Furn/Home Furnishings' (unlevered_beta or unlevered_beta_corrected_for_cash); sensitivity line from raw_damodaran_beta_global, same industry; raw_damodaran_indname for the industry mapping | **Covered with change** (plan Decision 3) |
| Cost of equity: ERP and Italy default spread | raw_damodaran_params mature_market_erp (4.23%); raw_damodaran_ctryprem Italy rating_based_default_spread (1.618%) | Covered; double counting noted as a limitation (Amendment) |
| Cost of debt | IS note 9 interest on loans and bonds (raw_report_lines); BS financial payables notes 32-33; cross-check against the BTP rate | Covered |
| WACC weights | price x shares (raw_yahoo_prices, note 28/26 shares); debt from BS | **Covered with change** (net cash, plan Decision 5) |
| Terminal value, Gordon | forecast table | Covered |
| Terminal value, exit multiple | raw_damodaran_vebitda_europe / _global ev_ebitda, industry 'Furn/Home Furnishings' | Covered (Amendment: industry multiple only) |
| Discounting | price date 2026-11-06 from raw_yahoo_prices | Covered (plan Decision 1) |
| Net debt | AR2025 BS financial payables and leases, cash; IR_H1_2026 NFP table | Covered (plan Decision 4) |
| Equity bridge: minorities | BS MINORITY INTEREST (197.8 m at YE2025), book value | Covered (Amendment: book value, flagged as a simplification) |
| Equity bridge: associates | BS Equity investments 5.6 m (YE2025) | Covered; immaterial (0.1% of assets), logged and not added |
| Diluted shares excl. treasury | note 28 share capital (151.06-151.29 m shares at EUR 1.5 par), note 26 treasury shares, note 31 diluted EPS denominators, stock option / performance share plans | Covered |
| Market price | raw_yahoo_prices DLG.MI close on 2026-11-06 = 45.32 | Covered (download-date bar is intraday; Decision 2) |
| Monte Carlo | computed; seed fixed | Covered (plan Decision 6 on distributions) |
| Sheet 1 Statements_5Y (condensed) | raw_report_lines, 15 statement pages (only FCFF and bridge lines, plus the totals needed for the tie-out checks) | Covered |
| Sheet 2 Adjustments_Ratios | as above, plus note 8 (3-5 largest non-recurring items) | Covered |
| Sheets 3-7 | derived | Covered |
| Sheet 8 Multiples_Check | raw_damodaran_vebitda_europe / _global, 'Furn/Home Furnishings', ev_ebitda | Covered |
| Sheet 9 Checks | derived | Covered |
| Investment note .docx | python-docx and matplotlib installed | Covered (step 6 of this run, per the Amendment) |
