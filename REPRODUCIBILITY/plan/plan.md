# Plan: De'Longhi DCF valuation
Approved by human: yes, 2026-11-09 (Gate 1). Decisions taken: "yes to all recommendations", i.e. option A / the recommended option for Decisions 1-9 as listed below.
Feasibility verdict: GO WITH CHANGES · Estimated total: 1:55

Revised 2026-11-09 for the brief's Amendment (bachelor-level scope, 6 steps). Sources, profile and coverage:
`plan/data_feasibility.md`. Raw data: `data/raw/SOURCES.md`. Step 0 (load and profile) is already registered in
`run.py` and passes; it is reused unchanged, with no new downloads.

Units everywhere: EUR m with 3 decimals kept in DuckDB (as printed in EUR thousand / 1000). Rounding happens only in
the workbook and the note, using the brief's precision rules. Price date = **2026-11-06** unless Decision 2 says
otherwise.

**Deviation from the CURIOSITY template, stated by the human in the Amendment:** the last step is the .docx
investment note (step 6), not the Excel report (step 5). The note only reads the verified workbook, so the workbook is
still the single source of every number.

Fixed by the Amendment (not decisions): condensed statements; only the 3-5 largest one-off items itemised; Damodaran
Europe Furn/Home Furnishings beta relevered plus one beta sensitivity line; no Peers sheet (Multiples_Check uses the
Damodaran Furn/Home Furnishings EV/EBITDA only); minorities at book value (flagged as a simplification); cost of equity
= BTP + beta x (mature ERP + Italy default spread), with no memo lines and the double counting noted as a limitation;
Monte Carlo on growth, EBIT margin and WACC with one simple correlation; WACC x g grid.

## Decisions for the human

1. **Valuation date vs balance-sheet date.** The price is from 6 Nov 2026. The audited balance sheet is 31 Dec 2025; the latest interim is 30 Jun 2026 (seasonal low in cash).
   - **A (recommended):** net debt at 31 Dec 2025 plus the full FY2026E FCFF, each year-end FCFF discounted to 6 Nov 2026 with year fractions (FY2026 at 0.15 years). Deduct the cash already paid to shareholders in 2026: H1 dividends 127.9 m and buybacks 28.5 m (IR_H1_2026 p.18). Consequence: H2 2026 cash moves until 6 Nov are not captured (the Q3 report is not out).
   - B: net debt at 31 Dec 2025 with no distribution adjustment. Simpler, but overstates equity by about 156 m (about EUR 1.05/share).
2. **Market-data dates.** Price: DLG.MI close on **6 Nov 2026, EUR 45.32** (last completed session; the 9 Nov bar in the file is intraday). Risk-free: ECB monthly average 10-year Italian yield for **Sep 2026, 4.362%** (latest available; no free daily BTP series). **Recommended: accept both.** Consequence: the risk-free rate is about 5 weeks older than the price.
3. **Beta (Europe variant and the sensitivity line).** The Amendment fixes Damodaran Europe Furn/Home Furnishings, relevered. Two sub-choices:
   - Base: **(recommended) the cash-corrected unlevered beta 0.397** (Damodaran's own recommendation for valuing operating assets; De'Longhi's cash is handled in the bridge, not in beta). Alternative: the raw unlevered beta 0.345. Consequence: cost of equity about 6.8% (0.397) vs about 6.5% (0.345), so WACC lands near or below the 6% lower edge of the smell test. A SURPRISE flag in step 2 is likely and is expected.
   - Sensitivity line: **(recommended) Global Furn/Home Furnishings, cash-corrected, 0.938** (same industry, 383 firms vs 53, and the Europe sample's 130% D/E makes its unlevering suspect). Cost of equity about 10.2%. Alternative: Europe Household Products 0.711 (cost of equity about 8.7%). Shown as one WACC line and one value-per-share line; it does not change the base case.
4. **What counts as cash in net debt.** The brief says debt + leases - cash. The company's NFP (+770.0 m) also nets about 305 m of current financial receivables and non-current financial assets.
   - **A (recommended):** treat as cash-like only the items notes 18 and 24 show as liquid financial assets (deposits, securities, derivative fair values); exclude guarantee deposits and operating receivables; list each item. Consequence: up to about +EUR 2.05/share versus B.
   - B: brief literal, cash only.
5. **WACC debt weight with net cash.** "Net debt plus leases" is negative.
   - **A (recommended):** D = gross financial debt + lease liabilities (about 534 m at YE2025), E = market cap. D/(D+E) is about 7%, and beta is relevered at that D/E.
   - B: all-equity (D = 0). Consequence: A vs B changes WACC by less than 0.3 pp.
6. **Monte Carlo design** (seed 20261109, 10,000 runs, g held at base):
   - Revenue-growth shift: Normal(0, 1.5 pp), one draw per run added to every forecast year's growth (anchored on the "mid-single-digit" guidance width, 4-6%).
   - EBIT-margin shift: Normal(0, 1.0 pp), one draw per run added to every year's margin (FY2021-25 adjusted margins ranged about 8-13%).
   - WACC: Normal(base, 0.75 pp), truncated to [g + 1.0 pp, base + 3.0 pp].
   - Correlation: growth and margin shifts rho = +0.5 (operating leverage); WACC independent.
   - **Recommended: accept.**
7. **Forecast drivers** (each gets a note in Forecast_FCFF):
   - Revenue growth: FY2026E 5.0% (midpoint of "mid-single-digit" guidance; H1 2026 was +5.8%), then a linear fade to g: growth_t = 5.0% - (5.0% - g) x (t - 2026)/5, giving FY2030E 2.6% at g = 2.0%.
   - Adjusted EBIT margin: FY2026E derived from the guidance midpoint (adjusted EBITDA 680 m) less forecast D&A less share-based cost at its FY2025 % of revenue (the guidance excludes share-based cost; the brief's adjusted EBIT keeps it). Then a linear fade to the FY2024-25 average adjusted margin by FY2030E (like-for-like perimeter after La Marzocco). Alternative: hold FY2026E flat.
   - D&A % and capex % of revenue: FY2021-25 averages. NWC % of revenue: held at FY2025.
   - Terminal g = **2.0%** (ECB inflation target; below rf). Grid g 1.0-3.0%.
   - **Recommended: accept, with the fade.**
8. **Forecast tax rate.**
   - **A (recommended):** FY2026E-30E at the normalised FY2021-25 effective rate (median of included years; FY2025 was 24.1%); the terminal-value FCFF at the Italian marginal rate 27.81% (steady state).
   - B: marginal 27.81% throughout (simplest; the brief's default). Consequence: B lowers value by roughly 2-4% vs A.
9. **Right-of-use additions as capex.** The brief adds back lease depreciation (inside "Amortization") and does not deduct lease payments.
   - **A (recommended):** count new right-of-use additions (AR note 15, about 15-25 m a year) as capex, so leased assets are not free. Consequence: about -3% to -5% on value vs B.
   - B: brief literal (cash capex for intangibles and PP&E only).

## Steps

### Step 1: Build the condensed statements and historical ratios
- Goal: produce condensed FY2021-25 statements (the lines FCFF and the bridge need, plus the totals for tie-out), the 3-5 largest one-off adjustments and the historical ratios. Serves sheets 1 (Statements_5Y) and 2 (Adjustments_Ratios) and the brief definitions of adjusted EBIT, NWC and tax rate.
- Inputs: `raw_report_lines`, `raw_documents` (AR2021-AR2025).
- Outputs: `py/01_statements.py` (PDF-line parsing), `sql/01_ratios.sql`; tables `hist_statements` (fy, statement in {IS, BS, CF}, line_item, value_eur_m, doc_id, pdf_page), `hist_adjustments` (fy, item, amount_eur_m, doc_id, pdf_page), `hist_ratios` (one row per fy: revenue, growth, ebit_reported, nonrec, adj_ebit, adj_ebit_margin, da, da_pct, capex_intangible, capex_ppe, capex_rou, capex_total, capex_pct, trade_receivables, inventories, trade_payables, nwc, nwc_pct, delta_nwc, pbt, taxes, eff_tax_rate, tax_included, fcff_hist); `evidence/data_quality_log.md`; `checks/check_step01.py`.
- Line set: IS: total consolidated revenues, amortization, EBIT, EBIT of which non-recurring, net financial income/expenses, PBT, taxes, profit, profit to minorities. BS (YE2020-2025): trade receivables, inventories, trade payables, cash, bank loans and borrowings, other financial payables, lease liabilities, minority interest, total assets, total net equity and liabilities. CF: investments in intangibles, investments in PP&E, cash flow for the period, opening cash, translation difference, closing cash. Each year from the **latest** report that presents it (FY2021 from AR2022, ..., FY2024-25 from AR2025; YE2020 BS from AR2021).
- Adjustments: the 3-5 largest non-recurring items by absolute amount across FY2021-25 from note 8, each with doc and page; per year, one residual row "other non-recurring (not itemised)" so the items sum to the IS non-recurring figure.
- Executor: opus. PDF-text parsing with two-column comparatives, the "of which non-recurring" interleaving and parenthesised negatives.
- Acceptance checks:
  - Coverage: IS and CF have exactly fy 2021-2025; BS has 2020-2025; `(fy, statement, line_item)` unique; no null values; every row has doc_id and pdf_page.
  - Anchors (exact to 0.001 m, FY2021...FY2025): revenues 3,221.587 / 3,158.433 / 3,075.904 / 3,497.555 / 3,801.458; EBIT 386.930 / 263.538 / 329.628 / 430.801 / 458.145; EBIT non-recurring -30.762 / +8.250 / -5.502 / -0.390 / -1.637; total assets 3,930.901 / 3,553.706 / 3,812.428 / 4,336.126 / 4,160.508; closing cash 1,026.081 / 770.247 / 1,250.198 / 1,019.711 / 998.448.
  - Tie-outs (|diff| <= 0.002 m): total assets = total net equity and liabilities (6 year-ends); opening cash + cash flow for the period + translation difference = closing cash; CF closing cash = BS cash; opening cash FY t = closing cash FY t-1; EBIT + net financial = PBT; PBT + taxes = profit.
  - Adjustments: per fy, sum of `hist_adjustments` = -(IS non-recurring) within 0.01 m; between 3 and 5 itemised (non-residual) item names in total.
  - Ratios: `hist_ratios` has exactly one row per fy 2021-2025; adj_ebit = ebit_reported - nonrec (FY2021 = 417.692, FY2025 = 459.782); FY2021 growth uses FY2020 revenue 2,351.257 (37.0% +/- 0.1 pp); nwc = trade receivables + inventories - trade payables; FCFF identity fcff_hist = adj_ebit x (1 - eff_tax_rate) + da - capex_total - delta_nwc (|diff| < 1e-9), capex_rou per Decision 9.
  - Expected ranges (mature appliance maker): adjusted EBIT margin 7-15%; D&A 2.5-4.5% of revenue; capex excl. ROU 1.5-5%; NWC -5% to +15%; effective tax 18-30% (FY2025 = 24.1%). Outside is a FAIL unless disputed with evidence. Tax < 0 or > 40% is excluded (tax_included = false) and logged.
  - Data quality log has entries for: restatements found on the condensed lines (expected at least FY2021 minority profit 0.684 vs 0.651), La Marzocco consolidation (2024), Capital Brands (2021), the FY2025 cost reclassification, the euro-sign encoding, the intraday Yahoo bar.
- Estimated time: 0:35

### Step 2: Estimate the WACC and assemble the equity bridge
- Goal: compute the WACC (with the beta sensitivity line) and the sourced bridge inputs. Serves sheet 4 (WACC), the brief definitions of cost of equity, cost of debt, WACC, net debt, equity bridge and market price.
- Inputs: `hist_statements` (YE2025 BS), `raw_report_lines` (AR2025 notes 9, 18, 24, 26, 28, 31-33; IR_H1_2026 p.18), `raw_yahoo_prices` (DLG.MI), `raw_ecb_yield_10y`, `raw_damodaran_beta_europe`, `raw_damodaran_beta_global`, `raw_damodaran_params`, `raw_damodaran_ctryprem`, `raw_damodaran_taxrates`.
- Outputs: `py/02_wacc_bridge.py`; tables `bridge_inputs` (item, value, unit, as_of, source, treatment, note), `wacc_inputs` (input, value, unit, source), `wacc` (two rows: case in {base, beta_sensitivity}; columns rf, beta_u, d_e, tax_marginal, beta_l, erp_mature, country_spread, ke, kd_pre, kd_post, w_e, w_d, wacc); `checks/check_step02.py`.
- Executor: sonnet
- Acceptance checks:
  - `bridge_inputs` has each item exactly once: bank_debt, other_financial_payables, lease_liabilities, cash, cash_like_financial_assets (Decision 4, itemised in the note), distributions_2026 (Decision 1), minority_book, shares_issued, treasury_shares, dilutive_shares, diluted_shares, price, price_date. Every row has a source.
  - NFP reconciliation: bank debt + other financial payables + leases - cash - all financial receivables/assets (incl. derivative fair values per the NFP table) = -770.0 m (+/- 0.1 m), computed regardless of Decision 4.
  - minority_book = 197.8 m (+/- 0.1); lease_liabilities 94.370 m (NFP table 94.0, +/- 0.5 allowed and logged); shares_issued x 1.5 = BS share capital (+/- 0.01 m); 0 <= dilutive_shares <= 1.3 m.
  - price = 45.32 and price_date = 2026-11-06 (trade_date < 2026-11-09 asserted); market cap = price x diluted shares between 6.0 and 7.5 bn.
  - `wacc` has exactly 2 rows; w_e + w_d = 1; beta_l = beta_u x (1 + (1 - tax_marginal) x d_e); ke = rf + beta_l x (erp_mature + country_spread); wacc = w_e x ke + w_d x kd_post (all |diff| < 1e-12).
  - Inputs equal raw cells exactly: rf 4.362% (IT, 2026-09); erp 4.23%; Italy default spread 1.618%; tax 27.81%; base beta_u = Europe Furn/Home cell per Decision 3; sensitivity beta_u = the Decision 3 cell.
  - Cost of debt: kd_pre = FY2025 interest on loans and bonds / average gross financial debt excl. leases (YE2024, YE2025); if outside [rf - 1 pp, rf + 3 pp], log it and use rf + Damodaran spread, with the reason recorded.
  - Smell test (SURPRISE, not FAIL): base WACC within 6-10%. Hard FAIL: base WACC outside 4-12%, or g (2.0%) >= rf.
- Estimated time: 0:15

### Step 3: Forecast FCFF and value the base case
- Goal: project FY2026E-30E FCFF and turn it into EV, equity value and value per share with the exit-multiple cross-check. Serves sheets 3 (Forecast_FCFF), 5 (Valuation) and 8 (Multiples_Check), and the headline's base-case numbers.
- Inputs: `hist_ratios`, `raw_report_lines` (PR_H1_2026 guidance), `wacc`, `bridge_inputs`, `raw_damodaran_vebitda_europe`, `raw_damodaran_vebitda_global`, Decisions 1, 7-9.
- Outputs: `py/dcf.py` (pure function `value_per_share(params) -> dict`, reused in step 4); `py/03_forecast_valuation.py`; tables `forecast_assumptions` (driver, rule, value_by_year, source, note), `forecast_fcff` (one row per fy 2026-2030: revenue, growth, adj_ebit_margin, adj_ebit, tax_rate, nopat, da, capex, nwc, delta_nwc, fcff, plus fcff_tv for FY2030 per Decision 8), `valuation` (ordered line items: tau_t, discount factors, PV FCFF per year, sum PV, TV Gordon, PV TV, EV, TV share of EV, debt, leases, cash, cash-like assets, distributions_2026, minorities (book), equity value, diluted shares, value per share, price, upside_pct), `multiples_check` (region, industry, n_firms, ev_ebitda, fy2030_ebitda, tv_exit, ev_exit, value_per_share_exit, pct_vs_gordon, implied_gordon_ev_ebitda); `checks/check_step03.py`.
- Executor: opus. Guidance-to-adjusted-EBIT bridge, terminal-year consistency, year fractions and bridge signs.
- Acceptance checks:
  - `forecast_fcff`: exactly 5 rows, fy 2026-2030; FCFF identity per row (|diff| < 1e-9); FY2026 delta_nwc uses FY2025 actual NWC.
  - FY2026E revenue = 3,801.458 x 1.05 = 3,991.531 m (+/- 0.001); growth path follows the Decision 7 formula (<= 1e-12).
  - Guidance bridge: FY2026E adj_ebit + da + share-based cost = 680 m (+/- 0.5 m). Margin path linear to the FY2030E target (<= 1e-12); all margins 8-16%.
  - FY2030E capex / da >= 0.9, else flagged FRAGILE. Each FCFF FY2026E-30E between 250 and 650 m (FY2025 operating cash flow after capex was 457.8 m); outside is a FAIL unless disputed with evidence.
  - Every driver in `forecast_assumptions` has a non-empty note and source.
  - tau_t = (date(t,12,31) - 2026-11-06) / 365.25: tau_2026 = 0.1506 (+/- 0.0001), tau_2030 = 4.1506. Sum PV, TV = fcff_tv x (1 + g)/(wacc - g), PV TV at tau_2030, EV = sum PV + PV TV, all recomputed in the check (|diff| < 1e-6 m).
  - Bridge: equity = EV + cash + cash_like - bank_debt - other_financial_payables - leases - distributions_2026 - minority_book; value per share = equity / diluted shares; upside_pct = price / value - 1. Recomputed exactly. Minorities at book are flagged in the note column as a simplification.
  - `multiples_check` ev_ebitda equals the raw cells exactly: Europe Furn/Home 9.452668, Global Furn/Home 10.626402 (`ev_ebitda` column, positive-EBITDA firms). Exit value per share is reported with its % difference from Gordon (no range check).
  - Smell tests (SURPRISE): TV share of EV <= 80%; |value / price - 1| <= 30%. Hard FAIL: TV share outside 50-95%; value per share outside EUR 15-120; implied Gordon EV/EBITDA outside 5x-25x.
- Estimated time: 0:25

### Step 4: Run the sensitivity grid and the Monte Carlo
- Goal: compute the WACC x g grid, the beta sensitivity line and the 10,000-run value distribution with the market price's percentile. Serves sheets 6 (Sensitivity) and 7 (MonteCarlo) and the headline's 80% range and percentile.
- Inputs: `py/dcf.py`, `forecast_assumptions`, `forecast_fcff`, `wacc`, `bridge_inputs`, `valuation`, Decision 6.
- Outputs: `py/04_sensitivity_mc.py`; tables `sensitivity` (wacc, g, value_per_share), `beta_sensitivity` (one row: beta_u, wacc, value_per_share, diff_vs_base), `mc_params`, `mc_runs` (run_id, growth_shift, margin_shift, wacc, value_per_share), `mc_summary` (p5, p10, p25, p50, p75, p90, p95, mean, sd, price, price_percentile), `mc_histogram` (bin_lo, bin_hi, count); `checks/check_step04.py`.
- Executor: opus. Correlated sampling, truncation and reproducibility.
- Acceptance checks:
  - `sensitivity`: exactly 25 rows (WACC base -1.0 to +1.0 pp step 0.5 x g 1.0-3.0% step 0.5), unique, no nulls; centre cell = step 3 value per share (|diff| < 1e-9); strictly decreasing in WACC and increasing in g; all cells wacc - g >= 1.0 pp.
  - `beta_sensitivity` wacc equals `wacc` row 'beta_sensitivity' exactly, and its value per share comes from the same `dcf.py` path.
  - `mc_runs`: exactly 10,000 rows, run_id 1..10000 unique, seed 20261109. Running the script twice gives identical `mc_runs` (checks/fingerprint.py).
  - Draw diagnostics: sd(growth_shift) = 1.5 pp +/- 3%; sd(margin_shift) = 1.0 pp +/- 3%; corr = 0.50 +/- 0.03; all wacc within the truncation bounds.
  - Run 0 (zero shifts, base WACC) through the same code path equals the step 3 value per share exactly.
  - p5 < p10 < p25 < p50 < p75 < p90 < p95; |p50 / base - 1| <= 10%. price_percentile = 100 x share of runs with value < 45.32, recomputed. Histogram counts sum to 10,000.
  - Smell test (SURPRISE): market price inside [p10, p90].
- Estimated time: 0:15

### Step 5: Build the Excel report
- Goal: write `report/DeLonghi_DCF_Valuation.xlsx` exactly as amended brief section 6 specifies, values only, from DuckDB tables, with the headline sentence. Serves the whole workbook part of section 6.
- Inputs: all tables from steps 1-4, check results.
- Outputs: `py/05_build_report.py`; `report/DeLonghi_DCF_Valuation.xlsx`; table `report_headline` (the sentence plus each number in it); `checks/check_step05.py`.
- Executor: sonnet
- Acceptance checks:
  - Sheets exactly, in order: Statements_5Y, Adjustments_Ratios, Forecast_FCFF, WACC, Valuation, Sensitivity, MonteCarlo, Multiples_Check, Checks. Headline sentence at the top of Valuation.
  - No formulas (no cell value starting with "="). The script reads only DuckDB; no numeric literals besides formatting/precision constants (grep check).
  - Round-trip: every numeric cell equals its source table value before display rounding (|diff| < 1e-9). Number formats: EUR m `#,##0`, EUR/share `0.00`, % `0.0%`, WACC and g `0.00%`, multiples `0.0"x"`.
  - WACC sheet shows every input with its source, the beta sensitivity line, and a limitation note on Italy risk double counting. Valuation sheet shows minorities at book with the simplification flag.
  - Checks sheet, all PASS: BS balances (6 year-ends), CF reconciles to change in cash (5 years), FCFF tie-out (forecast identity; EV = sum PV + PV TV), sensitivity centre = base, MC run 0 = base, determinism (fingerprint equal across two `python run.py --fresh` runs).
  - MonteCarlo sheet: percentile table, price percentile, native openpyxl bar chart from `mc_histogram`, distribution parameters.
  - Headline numbers equal `valuation`, `wacc` and `mc_summary` at the stated precision.
- Estimated time: 0:15

### Step 6: Write the investment note
- Goal: write `report/DeLonghi_DCF_Valuation_note.docx`, a 2-page note (thesis, main assumptions, valuation range, risks, conclusion vs market price) with one chart, using only workbook numbers. Serves the investment-note part of section 6.
- Inputs: `report/DeLonghi_DCF_Valuation.xlsx` (read back), `report_headline`, `mc_histogram`.
- Outputs: `py/06_build_note.py`, `report/DeLonghi_DCF_Valuation_note.docx`, `report/note_chart.png` (Monte Carlo histogram with a price line); `checks/check_step06.py`.
- Executor: sonnet
- Acceptance checks:
  - Every number in the note (regex on digits) matches a displayed value in the workbook at brief precision. Zero unmatched numbers, except years and page counts on an allowlist.
  - Exactly 1 picture; <= 900 words (proxy for 2 pages at 11 pt); the 5 sections present by heading.
  - The headline sentence is identical to `report_headline`.
  - The risks section names the 3 stated simplifications: minorities at book, Italy risk double counting, low Europe industry beta.
- Estimated time: 0:10

## Risks
- **Beta dominates the answer** (cost of equity about 6.8% on the Europe beta vs about 10.2% on the Global one). The Amendment fixes the base; step 4's beta sensitivity line shows the size. Step 2's WACC smell test (6-10%) will likely flag SURPRISE; that is expected and goes to the final review.
- **Base value likely well above the price** because of the low beta. Step 3's |value/price - 1| <= 30% smell test will flag it; the note must state it.
- **Margin path.** FY2026 guidance implies a margin about 2 pp above the 5-year average. Decision 7 makes the fade explicit; step 3's guidance bridge (680 +/- 0.5 m) stops silent drift.
- **PDF parsing errors** (column misalignment, non-recurring values read as comparatives). Caught by step 1's anchors, tie-outs and cash continuity.
- **Perimeter change (La Marzocco 2024)** distorts 5-year averages. Logged in step 1; Decision 7 uses FY2024-25 for the margin anchor and FY2025 for NWC.
- **Stale dates** (YE2025 net debt, Sep 2026 rf, Nov 2026 price). Decisions 1-2; step 2 forbids the intraday bar.
- **Cash-like assets** (305 m) move value by about EUR 2/share. Step 2 reconciles to NFP 770.0 m.
- **Minorities at book** (197.8 m) likely understate their value share (7.35% of FY2025 profit; H1 2026 minority profit doubled). Stated simplification; flagged in Valuation and the note.
- **Terminal value weight** likely 70-80% of EV. Step 3 smell test; step 4 grid.
- **Environment.** pdftotext is an external binary; step 0 falls back to pdfplumber. Determinism checked in step 5.

## Traceability: final-answer numbers -> producing step
| Final-answer element | Table.column | Step |
|---|---|---|
| Value per share (base) | valuation['value_per_share'] | 3 |
| WACC | wacc.wacc where case = 'base' | 2 |
| g | forecast_assumptions['terminal_g'] | 3 |
| 80% MC range (low / high) | mc_summary.p10, mc_summary.p90 | 4 |
| Market price | bridge_inputs['price'] | 2 |
| Price percentile | mc_summary.price_percentile | 4 |
| % above/below base case | valuation['upside_pct'] | 3 |
| Statements_5Y | hist_statements | 1 |
| Adjustments_Ratios | hist_adjustments, hist_ratios | 1 |
| Forecast_FCFF | forecast_fcff, forecast_assumptions | 3 |
| WACC sheet | wacc_inputs, wacc | 2 |
| Valuation sheet | valuation, bridge_inputs | 3, 2 |
| Sensitivity | sensitivity, beta_sensitivity | 4 |
| MonteCarlo | mc_summary, mc_histogram, mc_params | 4 |
| Multiples_Check | multiples_check | 3 |
| Checks | check outputs from steps 1-4 plus fingerprint | 5 |
| Investment note numbers | read from the workbook | 6 |

## Amendment 2 (2026-11-10): presentation restructure
Approved by human: yes, 2026-11-10 (Gate 1, lean version). Decisions taken: 1 = A (Gill Sans MT body, Garamond headings), 2 = A (keep "▸"), 3 = B (readable-label column), 4 = A (no PDF copy of the note); aesthetic "Ledger"; full visual inspection by the Verifier (not reduced).
Post-verification decisions (human, 2026-11-10): (a) reword guide §6 "All 55 number tokens of the note were matched" to what was actually checked for the rebuilt note; (b) accept as a recorded deviation that 6 guide figures are sourced from evidence/step07.md; (c) polish pass approved: step 8 §6 wording, orphaned §A.2 heading, informal "doesn't"; step 7 chart fonts, label "Price vs value, %" on 3.2, "nine sheets" docstring.
Feasibility verdict: **GO** (presentation only) · Estimated total: 1:15 (execution 0:55 plus verification about 0:20)

**Feasibility.** No new data and no analysis. Every number already exists in DuckDB (steps 1-4 tables and `report_headline`)
or in a verified evidence pack. Everything needed is installed:
- **Fonts:** Garamond (`C:/Windows/Fonts/GARA.TTF`, `GARABD.TTF`, `GARAIT.TTF`), Gill Sans MT (`GIL_____.TTF`, `GILB____.TTF`,
  `GILI____.TTF`) and DejaVu Sans. Digits are equal-width in Garamond and Gill Sans MT (figures line up in tables), and reportlab 5.1 embeds both.
- **Glyphs:** "▸" is in neither Garamond nor Gill Sans MT. Gill Sans MT also lacks "−" and "→".
- **Rendering:** LibreOffice works headless. pypdfium2 5.15.2 is already in the venv (a pdfplumber dependency), so PDF pages can be
  rasterised to PNG with no download. It is pinned as `pypdfium2>=4` in requirements.txt.
- **Banned phrases:** none in the current workbook or note (Planner scan). They occur only in the guide.

**Fixed requirements (human-approved 2026-11-10).**
- **R-A Numbering. Sheets, exactly and in order:** `0.0 Overview`, `1.1 Statements`, `1.2 Adjustments & Ratios`, `2.1 WACC`,
  `2.2 Bridge Inputs`, `3.1 FCFF Forecast`, `3.2 Valuation`, `3.3 Multiples Check`, `4.1 Sensitivity`, `4.2 Monte Carlo`, `5.1 Checks`.
  - Old to new: Statements_5Y → 1.1, Adjustments_Ratios → 1.2, WACC → 2.1, the `bridge_inputs` block of Valuation → 2.2,
    Forecast_FCFF → 3.1, Valuation (rest) → 3.2, Multiples_Check → 3.3, Sensitivity → 4.1, MonteCarlo → 4.2 (native histogram kept),
    Checks → 5.1. These names supersede brief section 6.
  - 0.0 Overview holds: the headline sentence from `report_headline`, a step index with hyperlinks to every sheet, and the names of the guide and the note.
  - **Guide, in order:**
    - cover, then a clickable contents page
    - §0.0: question, answer, and the method map Interview→Plan→Execute→Verify→Review with the Executor and Verifier roles
    - §0 Data & sources: a short table summarised from `data/raw/SOURCES.md` (groups, file counts, retrieval date, licence)
    - §1 (§1.1, §1.2), §2 (§2.1, §2.2), §3 (§3.1-§3.3), §4 (§4.1, §4.2), §5 (§5.1)
    - §6 Investment note
    - §A Appendix: §A.1 audit trail (the 5 spot-check reconciliations, written formally), §A.2 glossary, §A.3 limitations
  - The guide has PDF bookmarks (outline) and its contents entries are links.
- **R-B Navigation.**
  - Every guide section opens with "WORKBOOK ▸ <sheet name>". §1-§5 list their sheets joined by " · ". §0, §0.0 and §6 name
    `0.0 Overview`, and §A names `5.1 Checks`.
  - Every sheet's row 1 is a band "GUIDE ▸ §x.y" (its own id, no page number), plus hyperlinks to `0.0 Overview` and to the previous and next sheet.
  - Every note figure carries a sheet tag such as "[3.2]".
  - Freeze panes sit below the headers. Print setup is landscape where wide, fit to width.
- **R-C Register.**
  - Removed: the portfolio/student cover line, every "Questions you could be asked" block, "what to check yourself",
    "Open point for the human", the internal restyle section, and second-person coaching voice. Guide and note use a formal, impersonal register.
  - Kept: the method, the key numbers, what the Verifier checked (every SURPRISE and FRAGILE note), and the limitations.
  - The 1-decimal display of adjustment amounts is stated as a decision accepted at Gate 2 (2026-11-09).
  - "Interview" is allowed only as the stage name in the §0.0 method map.
- **R-D Ledger identity, defined once in `py/ledger_style.py`.**
  - Palette: paper `F6F1E7`, ink `1A1A1A`, a single accent vermilion `C8361D` (key results and step numerals only), grey
    `6B6B6B`, hairline `BDB6A8`, and at most two neutral tints declared there.
  - Type: headings Garamond, body and tables Gill Sans MT (Decision 1 = A). In the PDF, "▸" is set in embedded DejaVu Sans. In xlsx/docx it
    relies on Office font fallback, verified in the render (Decision 2 = A).
  - Layout: oversized step numerals, hairline rules, no boxed grids, no navy.
  - Note: A4, with its one chart restyled in the palette.
- **R-E Invariants.**
  - Every number is unchanged.
  - Workbook: values only (0 formulas; hyperlinks allowed), built only from DuckDB by code.
  - `python run.py --fresh` rebuilds all three documents.
  - Note: 5 headings, 1 picture, ≤ 900 words, headline paragraph identical to `report_headline`.
  - No extra PDF of the note (Decision 4 = A).
  - File names unchanged: `report/DeLonghi_DCF_Valuation.xlsx`, `report/DeLonghi_DCF_Valuation_note.docx`,
    `report/DeLonghi_DCF_process_guide.pdf`.

**Design (stated, not decisions).**
- **Build order, no cycle.** Without page numbers the workbook needs nothing from the guide, so the order is workbook → note → guide.
  - run.py adds one entry, `7: ["py/07_process_guide.py"]`; steps 0-6 are unchanged.
  - The guide reads its result numbers from DuckDB (read-only).
  - Sheet names and section ids come from a single registry, `py/doc_map.py` (id, sheet name, guide title, prev/next), imported by all three generators.
  - `py/05_build_report.py` keeps building `report_headline`; there is no headline split.
- **Readable-label column (Decision 3 = B), and how the baseline comparison stays strict.**
  - Label sheets: those whose column A holds DuckDB keys, i.e. 1.2, 2.1, 2.2, 3.1, 3.2, 4.2 (fixed list in `doc_map`). On these sheets a
    new column B "Label" is inserted; the other sheets get no column.
  - Labels come from one mapping table `LABELS = {key: label}` in `py/doc_map.py`.
  - Cell mapping: an old cell (r, c) becomes (r + 2, c') with c' = c on non-label sheets; on label sheets c' = 1 for c = 1, else c + 1.
    New rows 1-2 are the band and the title (numeral plus title, as text). Row 3 holds the old A1 text.
  - The one block move: the old Valuation `bridge_inputs` block, from the "Bridge input" header to its last item, goes to `2.2 Bridge Inputs`
    with the same relative rows. It is located by that header label in both files.
  - Strictness: the key column stays in place and is compared exactly. Column B is checked on its own: on every row, B is empty
    or equals `LABELS[A]`; every snake_case key in column A has a label; no label is unused; column B holds text only.
- **Guide number check.** `checks/check_step08.py` extends and replaces `py/07_verify_guide.py`.
  - The guide build writes `report/build/guide_numbers.json`, listing every number token in reading order with its provenance: either a
    DuckDB table.column (or item) plus a format, or a file plus an anchor phrase.
  - Allowed source files: brief, plan, `evidence/step0[1-6].md`, `evidence/data_quality_log.md`, `report/final_review.md` and `data/raw/SOURCES.md`.
- **Visual renders.** `checks/render_png.py` converts each file with
  `"C:\Program Files\LibreOffice\program\soffice.exe" --headless --convert-to pdf --outdir verify/render/stepNN <file>`.
  It then rasterises every page with pypdfium2 at 110 dpi to `verify/render/stepNN/<doc>_pNN.png`. The guide PDF is rendered directly.
- **Baseline.** At the start of step 7, before any change, the verified deliverables at HEAD 59ecd69 are copied to
  `verify/baseline_amend2/`, never modified afterwards:
  - the xlsx, docx, pdf and note_chart.png
  - `SHA256SUMS.txt`
  - a cell dump `xlsx_cells.txt` in the format of `verify/xlsx_dump_run1.txt`
  - the note's number tokens in `note_tokens.txt`

### Decisions for the human (Amendment 2)
None open. Taken by the human on 2026-11-10: 1 = A (Gill Sans MT body and tables, Garamond headings); 2 = A (keep "▸"; DejaVu Sans
embedded in the PDF; Office fallback verified in the render); 3 = B (readable-label column, compared as specified above); 4 = A (no PDF copy
of the note).

### Step 7: Rebuild the workbook on the shared Ledger style
- Goal: produce `report/DeLonghi_DCF_Valuation.xlsx` as the 11 numbered sheets in the Ledger identity, with readable labels, bands and navigation, and every value unchanged. Serves R-A, R-B, R-D and R-E for the workbook.
- Inputs: the step 1-4 tables, `report_headline`, the current `py/05_build_report.py` and `py/report_style.py`, git HEAD 59ecd69.
- Outputs:
  - `verify/baseline_amend2/` (done first)
  - `py/ledger_style.py`: palette, font names and TTF paths, sizes, adapters for openpyxl, reportlab, python-docx and matplotlib
  - `py/doc_map.py`: sheet and section registry, label sheets, `LABELS`
  - `py/report_style.py`: restyled; imports every colour and font from `ledger_style`
  - `py/05_build_report.py`: new sheet map, 0.0 Overview, 2.2 block move, label column, bands, links, freeze panes, print setup
  - `checks/check_step05.py` (edited as listed below)
  - `py/06_build_note.py` and `checks/check_step06.py` (sheet references only)
  - `checks/check_step07.py`
  - `checks/render_png.py`
  - `requirements.txt` (+pypdfium2)
  - `report/DeLonghi_DCF_Valuation.xlsx`
- Executor: sonnet
- Acceptance checks:
  - **Baseline:**
    - The 4 snapshot files are byte-identical to `git show 59ecd69:<path>`.
    - `xlsx_cells.txt` equals `verify/xlsx_dump_run1.txt` line for line (2,698 lines).
  - **Sheets:** the 11 names exactly, in R-A order.
  - **Values:**
    - Every non-empty baseline cell equals its mapped new cell (Design) in value, data type and number format. The only exceptions are
      old row-1 title texts on sheets other than Valuation. The Valuation A1 headline must equal `'3.2 Valuation'!A3` exactly.
    - Numeric cells on sheets 1.1-5.1 total exactly 1,237. 0.0 Overview has 0 numeric cells. No new numeric cell on any sheet.
    - 5.1 Checks rows are identical to the baseline (65 rows, all PASS).
  - **Labels:** the column-B rule in Design holds on every label sheet (0 violations, 0 unlabelled keys, 0 unused labels). Non-label sheets have no inserted column.
  - **Formulas:** 0 (no data_type "f", no string starting with "=").
  - **Hyperlinks:**
    - Every internal hyperlink names an existing sheet and a cell within its used range.
    - Every sheet except 0.0 links to `0.0 Overview`. Prev/next follow R-A order (0.0 has next only, 5.1 has prev only). 0.0 links to all 10 other sheets.
  - **Bands and headline:**
    - Each sheet's band reads exactly "GUIDE ▸ §<own id>", and the id is in `doc_map`.
    - The 0.0 headline cell equals `report_headline` sentence.
  - **Layout:**
    - Freeze panes directly below the first table header; 1.1 also freezes columns A:B.
    - fitToWidth = 1 and fitToHeight = 0 on every sheet. Landscape when the used width exceeds 120 character units.
  - **Fonts and palette:**
    - Every cell font ∈ {Garamond, Gill Sans MT}.
    - Every rgb colour in `xl/styles.xml` and the chart XML ∈ the ledger palette.
    - No hex colour literal in `py/*.py` outside `py/ledger_style.py`. The navy hexes 1F3864, 2F5597 and EEF2F8 appear nowhere in `py/`.
  - **Chart:** exactly 1 native BarChart on `4.2 Monte Carlo`. Its series references point at that sheet, and its values equal `mc_histogram.count` (54 bins, sum 10,000).
  - **check_step05.py edits, non-weakening only:**
    1. `SHEETS` becomes the 11 names.
    2. Every `wb["<old>"]` goes through a fixed old-to-new map. The bridge-block check reads `2.2 Bridge Inputs`.
    3. `Valuation!A1` becomes `'3.2 Valuation'!A3`, plus a new 0.0 headline assertion.
    4. The round-trip pool covers sheets 1.1-4.2 (replacing `SHEETS[:-1]`). The added label column is skipped by header name "Label" only.
    5. The AST no-numeric-literal scan is extended to `report_style.py`, `ledger_style.py` and `doc_map.py` (closes step-5 note 4).

    No tolerance, expected value or check is removed. The PASS count must be ≥ 86. The diff goes in evidence/step07.md.
  - **Regression and determinism:**
    - check_step01-04 pass (128/78/148/66).
    - `py/06_build_note.py` and `checks/check_step06.py` get **sheet-reference edits only** in this step: old names → new names, and
      Valuation A1 → A3 with the display column 3 → 4. This keeps `run.py --fresh` green. After it, check_step06 passes 17/17 and the note text is
      identical to the baseline. The restyle of the note waits for step 8.
    - `checks/fingerprint.py` is unchanged (git diff empty).
    - Two `run.py --fresh --through 5` runs give the 24 fingerprints in `verify/fp_step06.txt` and identical workbooks (values, styles, links).
  - **Banned phrases:** the step-8 list over all workbook strings, 0 hits.
  - **Visual:** PNGs of the first page of every sheet go to `verify/render/step07/`. The Verifier confirms:
    - band and links visible
    - no sheet split across the page width
    - chart clear of the tables
    - vermilion only on numerals and key results
    - "▸" renders without a box
- Estimated time: 0:30 execution, plus about 0:10 verification

### Step 8: Rebuild the process guide and the investment note in the same identity
- Goal: rebuild the process guide and the note in the Ledger identity, formal register, with sheet tags and the numbers unchanged. Serves R-A to R-E for both documents, and the cross-document checks.
- Inputs: the step-7 workbook, `py/ledger_style.py`, `py/doc_map.py`, `report_headline`, `mc_histogram` and the other DuckDB tables (read-only), `data/raw/SOURCES.md`, evidence packs step01-06, `evidence/data_quality_log.md`, `report/final_review.md`, the current `py/07_process_guide.py` and `py/06_build_note.py` (substance to keep), and `verify/baseline_amend2/`.
- Outputs:
  - `py/07_process_guide.py`, producing `report/DeLonghi_DCF_process_guide.pdf` and `report/build/guide_numbers.json`
  - `py/06_build_note.py`, producing `report/DeLonghi_DCF_Valuation_note.docx` and `report/note_chart.png`
  - `checks/check_step06.py` (edited as listed below)
  - `checks/check_step08.py` (guide, note and cross-document checks)
  - `run.py` entry 7
  - `py/07_verify_guide.py` deleted (superseded)
- Executor: sonnet
- Acceptance checks:
  - **Guide structure:**
    - The PDF outline holds exactly the ids §0.0, §0, §1, §1.1, §1.2, §2, §2.1, §2.2, §3, §3.1, §3.2, §3.3, §4, §4.1, §4.2, §5, §5.1, §6,
      §A, §A.1, §A.2, §A.3, in this order (from `doc_map`).
    - The contents page has one link annotation per id, each landing on the page where that heading's text appears.
    - Every page is A4 (595.3 x 841.9 pt ± 0.5). The guide has ≤ 20 pages.
  - **Tags and mapping:**
    - Every section opens with a "WORKBOOK ▸ …" line, and every name in it is an existing workbook sheet (read from the xlsx).
    - Every sheet band's §x.y exists as a guide section heading.
    - The two-part ids that have sheets correspond one-to-one to the 11 sheets.
  - **Guide numbers:**
    - The number tokens extracted from the PDF (pdfplumber; thousands separators removed) equal the `guide_numbers.json` tokens in order. Only
      section ids, "[x.y]" tags, folios, ISO dates and FY/H labels are excluded (by regex). There is no small-integer exemption.
    - Every DuckDB entry, recomputed at its format, matches.
    - Every file entry is found verbatim on a line containing its anchor phrase (this covers the §0 sources table via SOURCES.md).
    - 0 unmatched tokens.
  - **Guide substance:**
    - Every row of final_review.md section 3 (FRAGILE and minor notes) is present.
    - The 5 cases of final_review.md section 4 are in §A.1 with all their numbers.
    - §1.2 states the 1-decimal display as accepted at Gate 2.
    - The 6 limitation items of the current guide are kept.
  - **Note numbers:**
    - The multiset of number tokens (excluding tags) equals the baseline's 55 tokens, unless each change is listed in evidence/step08.md with its workbook cell.
    - Every token matches a displayed value at its own number format on a sheet tagged in the same sentence.
    - Every sentence with a non-allowlisted number has ≥ 1 tag, and every tag is one of the 11 sheet ids.
  - **Note structure:**
    - The 5 headings unchanged, in order.
    - Exactly 1 picture and 1 media file. ≤ 900 words.
    - The headline paragraph equals the `report_headline` sentence exactly; its tags sit in the next paragraph.
    - The 3 simplifications are named in Risks.
  - **Note page:**
    - A4: page_width 7,560,000 EMU and page_height 10,692,000 EMU, ± 1 %.
    - The LibreOffice render has exactly 2 pages, and the last text line on page 2 ends above 90 % of the printable height.
  - **Further check_step06.py edits, non-weakening only** (the sheet-reference edits were already made in step 7):
    - "[x.y]" tags are dropped only when x.y is a `doc_map` sheet id.
    - New checks: A4 page size, and the tag-sheet match above.
    - The PASS count must be ≥ 17.
  - **Banned phrases (guide, note and workbook text):** 0 hits, case-insensitive and word-bounded, for: you, your, yourself, could be asked, portfolio,
    student, recruiter, for the human, the human, check yourself, open point, restyle, plain english, we, our, plus lowercase "us".
    "interview" may appear only on the §0.0 pages, ≤ 3 times.
  - **Fonts and glyphs:**
    - PDF: every font is embedded (FontFile2 present), and the set ⊆ {Garamond, Garamond-Bold, Garamond-Italic, GillSansMT, GillSansMT-Bold,
      GillSansMT-Italic, DejaVuSans}. DejaVuSans is used only for "▸". Every character is in its font's cmap. 0 U+FFFD.
    - docx: fonts ∈ {Garamond, Gill Sans MT}; every `w:color` ∈ the palette or "auto"; no `w:themeColor` on any used style. The chart uses palette colours only.
  - **Determinism and regression:**
    - Two builds give a byte-identical PDF (reportlab invariant), identical docx members and an identical PNG.
    - A full `run.py --fresh` then check_step01-08 all pass.
    - The fingerprints of the 24 tables equal `verify/fp_step06.txt`.
  - **Visual:** PNGs of every guide page and both note pages go to `verify/render/step08/`. The Verifier confirms:
    - no overlap or clipping
    - ivory background
    - vermilion numerals
    - hairline rules
    - the chart in the palette
- Estimated time: 0:30 execution, plus about 0:10 verification

### Risks (Amendment 2)
| Risk | Caught by |
|---|---|
| Silent value change from the restructure (offsets, the label column, the block move) | Step 7's mapped equality against the baseline and the exact count of 1,237 numeric cells |
| A label masks a key | The column-B rule: key column compared exactly, labels only from `LABELS` |
| A check weakened while being edited | Every allowed edit is listed above, the Verifier diffs the check files, and the PASS counts must not fall |
| The formal rewrite changes meaning (a softened FRAGILE note, a number on the wrong label) | Anchor-phrase provenance, and the Verifier reading the guide against final_review.md section 3 |
| Rendering differs between platforms (LibreOffice vs Excel/Word, "▸" fallback) | Only partly covered: LibreOffice is the only renderer here; the 90 % page-2 slack reduces the risk for the note |
| Gate 2 documents (final_review.md, old evidence packs) still cite the old sheet names | Not caught by a check: the orchestrator should add a dated addendum with the old-to-new map rather than rewrite them |

### Traceability additions (Amendment 2)
| Element | Source | Step |
|---|---|---|
| 0.0 headline sentence and step index | report_headline, py/doc_map.py | 7 |
| 2.2 Bridge Inputs | bridge_inputs (block moved from Valuation) | 2, 7 |
| Readable labels | py/doc_map.py LABELS | 7 |
| Guide numbers, incl. §0 sources table | DuckDB or allowed files, per report/build/guide_numbers.json | 8 |
| Note figures and tags | workbook displayed values on the tagged sheet | 8 |


## Amendment 3 (2026-11-10): final polish
Approved by human: yes, 2026-11-10 (Gate 1), including keeping the four plain "sensitivity of the conclusion" items in the limitations appendix. No decisions were open.
Decision taken during step 9 (human, 2026-11-10, after a CHECK DISPUTED): a sixth rewording rule "incentive plans" -> "incentive schemes" (workbook only; cell 3.1 G30), so 6 rules and 8 reworded cells instead of 5 and 7. Recorded in evidence/step09.md and data_quality_log entry 32.
Feasibility verdict: **GO** (presentation only, no new data, no analysis) · Estimated total: 1:10 (execution 0:45 plus verification about 0:25)

**Planner findings (scanned on HEAD 44d683d, so that the step needs no open decision).**
- **Glyphs.** U+00E0 "à" and "@" are in the cmap of all six TTFs (GARA, GARABD, GARAIT, GIL_____, GILB____, GILI____), checked with reportlab `TTFontFile.charToGlyph`.
- **3.2 gap.** In the baseline (`verify/baseline_amend2`, old sheet `Valuation`), the bridge block is old rows 57-75 (header "Bridge input" plus 18 items). Old row 76 is blank. Old row 77 holds the "SIMPLIFICATION FLAG" note (merged A77:G77).
  - Today, 3.2 holds the pointer in A59 (link to `'2.2 Bridge Inputs'!A1`), rows 60-78 are empty, and the flag is in A79 (merged A79:H79). max_row is 79.
  - The flag is the only non-empty baseline cell below the gap.
  - Nothing outside 3.2 addresses 3.2 rows >= 60. The three incoming links target `'3.2 Valuation'!A1`. check_step05 and 06 locate 3.2 content by header or text. The headline stays in A3 and the headline block in rows 6-15. The note tags and guide tags name sheets, not cells.
- **Process terms in the workbook.** There are 7 text cells, all copied from DuckDB source/note columns, so they cannot be edited at the source without changing the fingerprints:
  - 2.2 H7, F13, F17, H17
  - 3.1 F26, F27
  - 3.2 H46 (same text as 2.2 F13)

  F17's "Performance Shares Plan" is the company's incentive programme, but it is reworded too, so the scan needs no exception. There are no hits on 5.1 Checks: no check name or source contains SURPRISE, FRAGILE or a role name, so nothing on 5.1 is renamed. The 5.1 sheet is still scanned.
- **Process terms in the note.** None in the text. The core properties say author/last_modified_by "CURIOSITY".
- **Process terms in the guide.** Hits on pp.3-12: the §0.0 method map (Interview, Plan, Executor, Verifier), "Pre-registered surprises", 6 headings "What the Verifier checked", "Gate 2" in §1.2, "smell test" in §2.1, §3.2, §A.2 and §A.3, and the "Notes carried to the final review" list (SURPRISE, FRAGILE, plan, Verifier). The PDF metadata Author is "CURIOSITY".
- **Properties.** The xlsx creator is "CURIOSITY".
- **Note page 2.** Fill is 0.29 of the printable height (step 8 check), so one author line on page 1 cannot overflow page 2.
- **DQ log entry 30** was already corrected in the polish pass (it says the guide no longer quotes "all 55 number tokens"). It is not stale, so it gets no edit.
- **Wording adopted (fixed here, not a decision).**
  - "smell tests" / "pre-registered surprises" become **"plausibility bounds"**. A result outside a bound is "re-examined", not "flagged".
  - The verification sub-heading becomes **"Reconciliation and checks"**.
  - The checks keep working because they read numbers and anchor phrases, not those words. The brief anchors used by `FT(BRIEF, ...)` ("WACC outside 6-10%", etc.) contain no banned word and stay as they are.
  - §5 keeps its doc_map title "Checks". The human's "Verification & reproducibility" refers to this section, and requirement 7 keeps the labels.

### Decisions for the human (Amendment 3)
None open.

### Step 9: Apply the final presentation polish to the three documents
- Goal: apply the human's fixed polish list (author line, 3.2 gap closed, process vocabulary removed, guide §5/§6 reworded) to the workbook, note and guide, with every figure unchanged. Serves R-A to R-E and Amendment 3 requirements 1-9.
- Inputs: HEAD 44d683d deliverables, `py/doc_map.py`, `py/ledger_style.py`, `py/05_build_report.py`, `py/06_build_note.py`, `py/07_process_guide.py`, `checks/check_step05-08.py`, `verify/baseline_amend2/`, `verify/fp_step06.txt`, evidence packs step01-07, `report/final_review.md`, `brief/research_brief.md`.
- Outputs:
  - **Baseline (done first, never modified):** `verify/baseline_step09/` holds the HEAD 44d683d xlsx, docx, pdf, note_chart.png, guide_numbers.json, `SHA256SUMS.txt`, plus a cell dump `xlsx_cells.txt` and the note paragraph list `note_paras.txt`.
  - **`py/doc_map.py`, author constants** (strings, no numeric literals):
    - `AUTHOR_NAME = "Mina Khella"`
    - `AUTHOR_EMAIL = "mina.khellas@gmail.com"`
    - `AUTHOR_AFFILIATION = "Undergraduate in Statistics and Economics, Università degli studi di Milano Bicocca"`
    - `AUTHOR_LINE` = the three joined by " · "
  - **`py/doc_map.py`, rewording rules:** `TEXT_REWORDS`, an ordered list of 5 (old substring, new substring) rules. They contain no digit and no banned word:
    1. "The plan's 'NFP table" → "The figure quoted as 'NFP table"
    2. "(The plan cites" → "(An earlier reference cites"
    3. "Performance Shares Plan rights" → "performance-share rights"
    4. "the plan's estimate" → "an assumption fixed in advance"
    5. ", plan/plan.md" → ", fixed in advance"

    A function `reword(text)` applies the rules. It is used only on text cells at workbook build time; DuckDB is untouched.
  - **`py/05_build_report.py`:**
    1. **3.2 gap closed.** `target()` maps old Valuation rows r > r_end_old to r + 2 - (r_end_old - r_h_old), i.e. r - 16, so old 76 → 60 and old 77 → 61. This also moves REG notes/sections, the merge (A79:H79 → A61:H61), the row height and the cell style.
    2. `reword()` applied to every copied string cell.
    3. Author line in `'0.0 Overview'!A20` (one text cell, body font, `SMALL_PT`, grey, no hyperlink, index rows 1-18 untouched).
    4. `wb.properties.creator` and `lastModifiedBy` = `AUTHOR_NAME`.
  - **`py/06_build_note.py`:**
    - One Normal-style paragraph directly under the title holding `AUTHOR_LINE` (Gill Sans MT, `SMALL_PT`, grey, plain text, no hyperlink).
    - core_properties author and last_modified_by = `AUTHOR_NAME`. Comments "".
  - **`py/07_process_guide.py`:**
    - **Cover:** an author block under the subtitle (name; e-mail; affiliation). `author=AUTHOR_NAME` in the PDF metadata.
    - **§0.0:**
      - The method map is rewritten impersonally, with 6 stages: Definition, Checks first, Analysis, Independent recomputation, Rebuild, Approval. They state that objectives and definitions were fixed in advance, checks were written before the analysis, every figure was recomputed by a second independent method, two clean rebuilds were compared by table fingerprints, and nothing was edited by hand.
      - The "Pre-registered surprises" bullet becomes "Plausibility bounds fixed in advance", with the same 5 bounds, the same FT(BRIEF) provenance and the same tokens. A result outside a bound is re-examined.
    - **§1.1, §2.1, §3.1, §4.2:** each "What the Verifier checked" becomes one paragraph "Reconciliation and checks", in impersonal wording, with the existing FT(EVn) provenance.
      - §4.1's paragraph merges into §4.2, so there is one per step.
      - §2.1's smell-test/notes sentence is dropped. Its substance goes to §A.3.
    - **§1.2:** "accepted at Gate 2 (2026-11-09)" becomes "accepted on 2026-11-09".
    - **§3.2:** "Pre-registered smell tests:" becomes "Plausibility bounds fixed in advance:". The table is unchanged.
    - **§5:** a short table, one row per stage, with the columns *What was reconciled* and *Checks / figures recomputed*. Every number comes from FT(EV01-04, EV07) or DuckDB, as before:
      - 0 Raw data: files loaded unchanged, SHA-256 recorded (SOURCES.md)
      - 1: balance sheets balance, cash flow agrees with the change in cash; 105 values, 128 checks
      - 2: bridge and WACC rebuilt from raw lines; 42/42, 78 checks
      - 3: FCFF identity, bridge recomputed; 20 numbers, 148 checks
      - 4: 25 grid cells; 10,000 runs reproduced bit-for-bit under the fixed seed; 66 checks
      - Workbook: 65 reconciliation rows PASS; 2,691 cells compared with the earlier build, 0 mismatches; 1,237 numeric cells; 0 formulas
      - Note: each figure matched to its tagged sheet
      - Rebuild: two clean rebuilds, identical fingerprints for 24 tables

      No PASS count of check_step05-09 is cited, because step 9 changes those.
    - **§5.1:** the "Notes carried to the final review" heading and its 12-item list are deleted.
    - **§6:** the last bullet's first sentence becomes exactly: "Each figure in the note was matched by script, at the display precision of the cell, against a cell on the sheet named by its tag; dates and year labels are not figures and are exempt." The two following sentences of that bullet are kept.
    - **§A.2:** the glossary entry "Smell test" becomes "Plausibility bound" (a limit fixed in advance; a result outside it is re-examined; same 80% example, same FT).
    - **§A.3:** item 4 becomes a plain "sensitivity of the conclusion" limitation that keeps the word "narrowly". It states, with DuckDB or FT(FINAL) provenance:
      - TV share 79.6% vs the 80% bound
      - value vs price 24.6% vs the 30% bound
      - the price EUR 0.98 above the Monte Carlo p10
      - the base WACC 0.52 pp above the 6% lower bound
      - The beta-sign item stays as it is.
  - **`checks/check_step07.py`** (edits listed below)
  - **`checks/check_step08.py`** (edits listed below)
  - **`checks/check_step09.py`** (new)
  - **`run.py`**: unchanged; if it needs a change, list it.
  - **Renders:** `verify/render/step09/`
  - **Regenerated deliverables:** the 3 deliverables, `note_chart.png` and `report/build/guide_numbers.json`
- Executor: sonnet
- Acceptance checks:
  - **Baseline snapshot:** the files in `verify/baseline_step09/` are byte-identical to `git show 44d683d:<path>`.
  - **Workbook values under the new 3.2 mapping** (check_step07 edit F1). The mapping:
    - Old Valuation rows 1-56 → r + 2. Old rows 57-75 → 2.2, as before.
    - Old rows >= 76 → r - 16. So old A77 → `'3.2 Valuation'!A61`, merged A61:H61, with the same font, fill, alignment and row height as today's A79.
    - The pointer stays at A59 with its link to `'2.2 Bridge Inputs'!A1`.
    - On 3.2, max_row = 61, row 60 is empty, and rows 62 and beyond do not exist.

    Required results:
    - Every non-empty baseline cell is compared: still 2,691 compared and 8 title texts exempt, 0 mismatches in value, type and number format.
    - The only allowed text difference is `new == reword(old)`. Exactly 7 cells differ from their baseline text: 2.2 H7, F13, F17, H17; 3.1 F26, F27; 3.2 H46.
    - Each of the 5 rules is used at least once. In each reworded cell the sequence of digit runs is identical to the old text.
    - Numeric cells on 1.1-5.1 = 1,237. 0.0 has 0 numeric cells. Formulas = 0.
    - 5.1 Checks: 65 rows, all PASS, identical to the step-8 workbook.
  - **Workbook diff against the step-8 workbook (`verify/baseline_step09`).** Comparing every cell's value, style id, merge and hyperlink, the only differences are:
    1. the 7 reworded cells
    2. 3.2 A79 → A61 (and the removed empty rows)
    3. the new 0.0 A20 author cell
    4. docProps
  - **Workbook navigation:** every hyperlink resolves to an existing sheet and to a cell within its used range. 0.0 links to the 10 sheets; prev/next are unchanged.
  - **Author line present** (exact `AUTHOR_LINE` text):
    - `'0.0 Overview'!A20`
    - the note paragraph directly after the title
    - the guide cover page text (pdfplumber page 1 contains name, e-mail and affiliation, with "Università" extracted intact)

    **Author in the properties:** xlsx core creator = `AUTHOR_NAME`, docx core author = `AUTHOR_NAME`, PDF /Author = `AUTHOR_NAME`. No property anywhere equals "CURIOSITY".
  - **Glyphs:**
    - Every character of the PDF is in its font's cmap (existing check), and there is 0 U+FFFD in any of the three.
    - The cell font of 0.0 A20 is Gill Sans MT, and the docx run font is Gill Sans MT.
    - "à" is visible in the renders of the guide cover, 0.0 and note p.1.
  - **Extended banned-phrase scan** (check_step09; check_step08's `BANNED` is extended to the same list, and `INTERVIEW_MAX` goes from 3 to 0).
    - Case-insensitive, word-bounded. The previous list plus: `interview\w*`, `planner`, `plan(s|ned|ning|'s)?`, `executor(s)?`, `verifier(s|'s)?`, `surpris\w*`, `fragile`, `smell`, `gate`, `curiosity`, `pre-registered`, `notes carried`, `final review`, `the human`, `for the human`, `portfolio`, `you`, `your`, plus lowercase "us".
    - Scope: PDF page text, outline titles and Info metadata; docx body, tables, every section header and footer, and core and app properties; every xlsx cell string on all 11 sheets (5.1 included), cell comments, sheet header/footer, sheet names, and docProps core and app.
    - Result: 0 hits. **No exclusion**, the author line included (the Planner checked that it holds no listed word).
    - Words still allowed: "verification", "verified", "check(s)", "review" outside "final review", "decision", "approved".
  - **Guide structure, unchanged:**
    - The outline is identical to the step-8 PDF (22 ids, same titles, same order). The contents page is unchanged in its entries, and its links land on the pages where the heading text appears.
    - Every band's §x.y exists as a heading. Every "WORKBOOK ▸" name is an existing sheet.
    - The page count is <= 20 and every page is A4.
  - **Guide content:**
    - The text "Reconciliation and checks" occurs exactly once in each of §1.1, §2.1, §3.1 and §4.2, and in no other §1-§4 section.
    - §5 has rows for stages 0-4, workbook, note and rebuild.
    - No §1-§5 text contains any of the 12 final_review section-3 explanations. This **replaces** check_step08's "every row of final_review section 3 present", by the human's requirement 6.
    - §A.3 still contains all 6 `LIMITATION_PHRASES`, and contains the figures 79.6%, 24.6%, 0.98 and 0.52, each with provenance.
    - §6 contains the new sentence verbatim, and the old sentence ("Every number in the note was checked by script") is absent.
  - **Guide numbers:**
    - check_step08's token check passes: PDF tokens equal the JSON tokens in order, every DuckDB entry recomputes, every file entry is verbatim on its anchor line and comes from the allowed sources, and 0 tokens are unmatched.
    - The token count is reported. It will fall from 389, because the notes list is removed; that is expected.
    - The new §5 and §6 sentences carry no digit without a provenance entry.
  - **Note:**
    - The number-token multiset equals `verify/baseline_amend2/note_tokens.txt` (61).
    - The paragraphs equal `note_paras.txt` except for the one inserted author paragraph.
    - 5 headings, 1 picture, <= 900 words. The headline paragraph equals `report_headline`, and its tags are in the next paragraph.
    - A4, exactly 2 pages in the LibreOffice render, and page-2 fill <= 0.90.
  - **check_step07.py edits, non-weakening only:**
    - F1: the 3.2 row rule above.
    - F2: baseline text compared to `reword(old)`, with the exact 7-cell, rule-usage and digit-run assertions.
    - F3: the banned list imported from the extended list.
    - F4: new assertions on the 3.2 layout (max_row 61, row 60 empty, the flag's merge, style and height follow it).
    - The PASS count is >= 74.
  - **check_step08.py edits, non-weakening except where a requirement removes content:**
    - E1: the extended `BANNED` list, with `INTERVIEW_MAX` = 0.
    - E2: the section-3-rows-present check is replaced by its inverse plus the §A.3 figures check (requirement 6).
    - E3: the §1.2 check requires "1 decimal", "accepted" and "2026-11-09" (the "Gate 2" text is removed by requirement 4).
    - E4: the note scan includes tables, headers and footers.
    - E5: the §6 sentence check.
    - No tolerance is loosened. The PASS count must stay >= 66, because every removed check has a replacement.
  - **check_step05.py and check_step06.py:** expected unchanged (they locate 3.2 content by header and text). Any edit needed must be listed and judged by the Verifier.
  - **Regression:** a full `run.py --fresh`, then check_step01-09 all pass: 128/78/148/66 unchanged, 05 >= 93, 06 >= 25, 07 >= 74, 08 >= 66.
  - **Determinism:** the 24 table fingerprints equal `verify/fp_step06.txt`. Two `run.py --fresh` rebuilds give a byte-identical guide PDF, guide_numbers.json, note docx and note_chart.png. The xlsx differs only in `docProps/core.xml`.
  - **Visual** (PNGs in `verify/render/step09/`, inspected by the Verifier):
    - guide cover (author block, "à")
    - guide §0.0 (method map, no role names)
    - guide §5 (table fits, no overlap)
    - guide §A (A.1-A.3)
    - '3.2 Valuation' (no gap: pointer at row 59, flag at row 61, key rows still vermilion)
    - '0.0 Overview' (author line small and grey)
    - note p.1 (author line under the title)
- Estimated time: 0:45 execution, plus about 0:25 verification (this is at the per-step limit; the edits are many but each is mechanical)

**After step 9 passes (orchestrator, not the Executor):**
- Append to `report/final_review.md` a short dated addendum (2026-11-10, Amendment 3). It says what step 9 changed, and that `final_review.md` is an internal document that still uses process terms and is not one of the three deliverables. Do not rewrite anything above it.
- The addendum must not repeat any anchor phrase used in `guide_numbers.json`. check_step08 is rerun after the addendum is added.
- No edit to `evidence/data_quality_log.md` (entry 30 is already current).

### Risks (Amendment 3)
| Risk | Caught by |
|---|---|
| The gap rule moves a cell other than the flag, or drops its style | F1/F4 in check_step07: all 2,691 baseline cells compared under the explicit rule, plus the step-8 workbook diff limited to the listed cells |
| A rewording changes a figure inside a text cell | Digit-run identity per reworded cell, and the exact list of 7 cells |
| Removing the notes list loses a substantive limitation | §A.3 figures check (79.6%, 24.6%, 0.98, 0.52), the 6 `LIMITATION_PHRASES`, and the beta-sign item |
| A role or process word survives in a place the old scan skipped (properties, headers, comments, outline) | The extended check_step09 scan over every text surface |
| The author line breaks the number or banned scans | It holds no digit and no listed word; checked by the same scans with no exclusion |

### Traceability additions (Amendment 3)
| Element | Source | Step |
|---|---|---|
| Author line and file-property author | `py/doc_map.py` `AUTHOR_*` | 9 |
| Reworded workbook source texts | `py/doc_map.py` `TEXT_REWORDS` applied to DuckDB text | 9 |
| Guide §5 per-stage figures | evidence/step01-04.md, evidence/step07.md, DuckDB, via guide_numbers.json | 9 |
| §A.3 sensitivity figures | DuckDB or report/final_review.md, via guide_numbers.json | 9 |
