# Step 05: Build the Excel report (re-verification after the formatting change). Verdict: PASS WITH NOTES

## Summary for the human (one page max)
- Scope: the uncommitted presentation-only change (new `py/report_style.py`, styling hooks in `py/05_build_report.py`, chart moved to MonteCarlo!D3 and resized, column D width 70 to 60).
- Headline numbers unchanged: value per share 56.47, WACC 6.52%, g 2.00%, MC 80% range 44.34 to 74.08, price 45.32, 12th percentile, gap -19.7%. All were recomputed again by `verify/verify_step05.py` (independent pandas/numpy rebuild, position-mapped read-back of all 1,237 numeric cells): 0 problems ✓
- Values untouched: cell by cell against the verified step-5 commit workbook (b418eaa) and against HEAD: 9 sheets in the same order, 2,699 non-empty cells (3,706 used-range cells), 1,237 numeric cells. **0 differences** in value, type or number format; 0 formulas ✓
- Merges: 11 merged ranges (title rows, Valuation A2:G2 and A77:G77). None of them hides a cell that had a value before ✓
- Checks: steps 1-5 give 128/78/148/66/86 PASS, and step 6 gives 17/17. Step 1-4 tables keep their verified fingerprints. No check file was changed ✓
- Reproducible: two clean `run.py --fresh --through 5` rebuilds gave identical table fingerprints (`verify/fp_step05.txt` is unchanged from the committed version). The two workbooks are identical in values and also in styles, merges, conditional formats, freeze panes, row/column sizes and chart anchor ✓
- Layout checked by computation, since no Excel is available: the chart (oneCellAnchor at D3, 17 x 8.2 cm = 232 pt) ends inside row 18 at the default 15 pt rows. The parameter table's first text in column D is at row 20, so nothing is covered. The sensitivity base-case outline sits on D6 = 56.4724 = value per share. Every Checks result is PASS (green), so nothing is red.
- Notes: the earlier notes 1-3 still apply (unchanged by this change), plus minor cosmetic notes 4-5 below. No SURPRISE, no FRAGILE.
- Spot-checks: `verify/spot_step05.py` was rerun. Executor cases 2 and 4 and my seeded cells Statements_5Y!E13 and F6 still trace to the raw data and PDF lines ✓
- Needs your decision: no new decision. The earlier note 1 (1-decimal adjustment amounts) is still open if you haven't answered it. The Executor also asks you to glance at the MonteCarlo and Valuation sheets in Excel.

## Findings (NOTES only, no errors)
| # | Level | File:line | Problem | Evidence |
|---|-------|-----------|---------|----------|
| 1-3 | V2/V4 | see previous verification below | Unchanged: 1-decimal adjustment amounts, pooled round-trip check, determinism row covers only steps 1-4 | n/a |
| 4 | V2 | checks/check_step05.py:116-135 | The AST "no numeric literals" scan only covers `py/05_build_report.py`, not the new `py/report_style.py`. The new module reads no data and writes no values; its numbers are named layout constants or 0/1/2 offsets. | Manual review of py/report_style.py |
| 5 | cosmetic | py/report_style.py (key-results loop) | Any row whose column-A label is in KEY_NAMES gets the yellow highlight, so Valuation row 72 (`price`, a date value 2026-11-06 in the sources block) and WACC-block row 16 are highlighted as well as the main results. Display only. | Highlighted rows on Valuation: 5, 6, 10, 11, 16, 48, 49, 72 |

## Verifier details
1. Saved the reference workbooks `git show b418eaa:` and `HEAD:report/DeLonghi_DCF_Valuation.xlsx` to the scratchpad.
2. `run.py --fresh --through 5` returned rc 0 (79 s). `fingerprint.py --save verify/fp_step05.txt` (8 tables) gave a file that is byte-identical to the committed one.
3. A second `run.py --fresh --through 5`: `--compare` printed "PASS fingerprints identical". `verify/fp_step01..04.txt` compare: all identical.
4. `verify/verify_step05_restyle.py <ref> <run1> <run2>` (new) compared every cell's value, type and number format against the reference, counted formulas, checked that merges hide no reference values, and compared the full style and layout of run1 vs run2. It reported 0 problems against both b418eaa and HEAD.
5. `checks/check_step01..06.py`: all pass (counts above). `verify/verify_step05.py` gave Problems: 0. The 16 unassigned cells are the 0.002 tolerance constants on the Checks sheet, as before.
6. The Executor's claims in "Formatting change" (9 sheets, 3,706 cells, 1,237 numeric, 0 differences, 86/86, 17/17) all reproduced.

## Previous verification (before the formatting change)
### Step 05: Build the Excel report. Verdict: PASS WITH NOTES

## Summary for the human (one page max)
- Headline numbers (Executor = Verifier), all identical to full float precision:
  - Value per share 56.47 (56.47243714823831) = 56.47. Verifier method: discounting redone in pandas from `forecast_fcff` + `wacc` components; bridge taken from `bridge_inputs` ✓
  - WACC 6.52% = 6.52%. Verifier method: rebuilt from rf, beta, D/E, ERP, spread, kd and weights ✓
  - g 2.00% = 2.00% ✓
  - MC 80% range 44.34 to 74.08 = 44.34 to 74.08. Verifier method: numpy linear percentiles over the 10,000 `mc_runs` rows ✓
  - Price 45.32 = 45.32. Verifier method: `raw_yahoo_prices` DLG.MI close on 2026-11-06 (45.3199997, rounded) ✓
  - Price percentile 12.03 / "12th" = 1,203 of 10,000 runs below 45.32 ✓
  - Gap -19.7% ("below") = -0.19748460862 ✓
  - The headline sentence I re-assembled from these numbers is character-identical to Valuation!A1 and to `report_headline` ✓
- Workbook read-back (level 15): I mapped each of the 1,237 numeric cells to one source value by its sheet position, row label and column header. 1,221 cells matched (|diff| <= 1e-9), with 0 mismatches. The other 16 are the 0.002 m tolerance constants in the Checks sheet (from plan step 1). 9 sheets in the brief's order; no formulas; 1 native bar chart.
- Rows: 153 statement values, 10 adjustments, 120 ratio values, 67 forecast values, 35 valuation lines, 25 grid cells and 54 histogram bins are all present, and every difference is explained in the row-flow table ✓
- Checks: 86/86 pass. No planned check is missing, but 2 are implemented more weakly than the plan's wording (notes 1 and 2). Earlier steps still pass (128/78/148/66), and the step 1-4 tables keep the same fingerprints as their verified packs ✓
- Reproducible: two clean `run.py --fresh --through 5` rebuilds gave identical fingerprints (`report_headline`, `mc_runs` and 6 others) and an identical workbook (all 2,699 non-empty cells, values and formats) ✓
- Notes: one minor precision deviation (adjustment amounts shown with 1 decimal) and two check-implementation notes. No SURPRISE: WACC is inside 6-10%, TV share 79.6% is <= 80%, |value/price - 1| = 24.6% is <= 30%, g is < 2.5%, and the price is inside [p10, p90]. That last one is narrow: the price is EUR 0.98 above p10, a step-4 result that I only observed here.
- Spot-checks: Executor cases 1-5 traced. My own cases: the YE2020 totals traced to the AR2021 PDF lines, plus 2 seeded random cells, Statements_5Y!E13 and F6, traced to the PDF lines ✓
- Needs your decision: minor. Do you accept the 1-decimal display of the itemised adjustment amounts (note 1)? I recommend accepting it.

## Findings (NOTES only, no errors)
| # | Level | File:line | Problem | Evidence |
|---|-------|-----------|---------|----------|
| 1 | V4/15 precision | py/05_build_report.py:288 | Adjustments_Ratios!C4:C13 (itemised adjustment amounts, EUR m) use the hard-coded format `#,##0.0`. Brief section 6 says "EUR m with no decimals", and the file header (lines 19-21) says EUR m has no decimals. The deviation isn't recorded in the evidence pack or the DQ log. It's a sensible choice, since items like 0.39 and -0.289 would display as 0, but it's undocumented. The same values in the `nonrec` ratio row (`#,##0`) display as "-0" (FY2024) and "-2" (FY2025), so the two blocks show different precision. The step 6 note must use whichever precision is accepted. | verify/verify_step05.py section C: "Adjustments amounts (EUR m) format: {'#,##0.0'}" |
| 2 | V2 | checks/check_step05.py:188-206, 409-413 | The plan asks that every numeric cell equal *its* source value. The generic round-trip only tests whether each cell equals *any* value in 16 pooled tables. Targeted lookups cover the key blocks but not the source and page blocks, the Checks sheet, or the format of the adjustment amounts (which is why note 1 went undetected). | My position-mapped read-back of all 1,237 cells found 0 mismatches, so the results are unaffected. |
| 3 | V2 | py/05_build_report.py:189-208 | The determinism row on the Checks sheet fingerprints only the step 1-4 tables (scratch rebuilds `--through 4`). The workbook and `report_headline` aren't covered. | I covered this gap: two fresh rebuilds gave identical `report_headline` fingerprints and identical workbook cells. |

## Verifier details
Commands run (venv Python):
1. `run.py --fresh --through 5` finished with rc 0 in about 79 s. `checks/fingerprint.py --save verify/fp_step05.txt report_headline hist_statements hist_ratios wacc valuation mc_summary mc_runs sensitivity`. Workbook dumped to verify/xlsx_dump_run1.txt.
2. A second `run.py --fresh --through 5`: `--compare` printed "PASS fingerprints identical", and `diff xlsx_dump_run1.txt xlsx_dump_run2.txt` found them identical (2,699 cells, values plus number formats).
3. `checks/check_step01..05.py` gave 128/128, 78/78, 148/148, 66/66 and 86/86. My step 5 check output matches the pasted output in the Executor section line for line.
4. Regression: compared against the earlier verified fingerprints `verify/fp_step01..04.txt`, all identical. Git diff: `run.py` gained only the step-5 entry, and the DQ log gained entries 23-24.
5. `verify/verify_step05.py` produced the headline recomputation (A), the read-back of every numeric cell (B) and the format inventory (C). Exit 0, 0 problems.
6. `verify/spot_step05.py` traced cases to the raw tables.

V2 plan-vs-check audit (step 5 acceptance checks):

| Plan check | In check_step05.py | Status |
|---|---|---|
| Sheets exactly, in order; headline at top of Valuation | l.105, l.165-168 | present |
| No formulas; reads DuckDB only; no numeric literals (grep) | l.108-140 (AST scan, 0/1/2 allowed) | present |
| Round-trip every numeric cell (< 1e-9); formats | l.188-206 pool plus targeted l.209-415 | present, generic part weaker (note 2) |
| WACC inputs with sources, beta line, Italy double-count note; minorities flag | l.287-341 | present |
| Checks sheet all PASS with BS (6), CF (5), FCFF, EV, sensitivity centre, MC run 0, determinism | l.418-432 | present |
| MonteCarlo percentile table, price percentile, native bar chart, parameters | l.374-396 | present |
| Headline numbers equal valuation/wacc/mc_summary at stated precision | l.156-173 | present |

V4 code review (py/05_build_report.py): no joins that fan out. The CF reconciliation join (l.536-542) is keyed on (fy, line_item), and the 5 rows it returns match the 5 CF years. Values are written unrounded, and rounding is display-only. The sign rule (`up > 0` gives "above") and the ordinal rule (11th-13th) are correct, and round(12.03) = 12. The headline reads `valuation`, `wacc`, `mc_summary` and `bridge_inputs`, which matches the plan's traceability table. Header comments are present and true, except the precision claim (note 1).

V5 magnitudes: value per share 56.47 sits inside the hard band 15-120. MC p5/p50/p95 = 41.61/56.36/81.09, max 161.4 (right skew, DQ #21). Units are as labelled (EUR m, EUR/share, decimals displayed as %).

V6 sensitivity: step 5 has no modelling judgement. The ordinal rounding gives 12th whether rounded or floored (12.03), so the conclusion can't flip.

V7 traced cases:

| Case | Workbook | Independent trace | OK |
|---|---|---|---|
| E1 value per share | Valuation!B5 = 56.47243714823831 | pandas EV/bridge rebuild = 56.47243714823831 | ✓ |
| E2 price percentile | MonteCarlo 12.03; sentence "12th" | `COUNT(*) WHERE value_per_share < 45.32` = 1,203 of 10,000 | ✓ |
| E3 gap sign | Valuation!B13 = -0.19748 | 45.32 / 56.47244 - 1 = -0.19748, so "below" | ✓ |
| E4 YE2020 BS | Checks!C4/D4 = 2,945.569 | AR2021 p.77 l.32 "Total assets ... 2,945,569"; p.78 l.35 "Total net equity and liabilities ... 2,945,569" | ✓ |
| E5 determinism | mc_runs 10000 / 92558926622417105030481 | Same value in verify/fp_step05.txt and fp_step04.txt | ✓ |
| V1 (seed 20261109) | Statements_5Y!E13 BS bank loans long-term FY2022 = 477.582 | AR2023 p.93 l.16 "...(long-term portion) 33 300,844 477,582" (second column = FY2022) | ✓ |
| V2 (seed 20261109) | Statements_5Y!F6 IS EBIT FY2023 = 329.628 | AR2024 p.137 l.34 "EBIT 430,801 (390) 329,628 (5,502)" | ✓ |

---
(Executor's section follows)

# Step 05: Build the Excel report. Status: AWAITING VERIFICATION

## What was done
- `py/05_build_report.py` writes `report/DeLonghi_DCF_Valuation.xlsx` (nine sheets in the brief's order, values only, no formulas) from DuckDB. Cells hold the unrounded table values; rounding is a number format only (EUR m `#,##0`, EUR/share `0.00`, % `0.0%`, WACC and g `0.00%`, multiples `0.0"x"`).
- Valuation!A1 carries the headline sentence, also stored in the new table `report_headline` (sentence plus each number): "De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value."
- The Checks sheet (65 rows, all PASS) lists: BS balances (6 year-ends), CF reconciles (5 years) and CF closing cash = BS cash, historical and forecast FCFF identities, NOPAT, sum PV, TV, PV TV, EV = sum PV + PV TV, equity bridge, value per share, sensitivity centre = base, MC run 0 = base, beta WACC, histogram sum, price percentile recount, the pass counts of `check_step01..04.py` (run by the script), and determinism.
- Determinism: the script rebuilds a scratch copy of the pipeline twice (`run.py --fresh --through 4`) and compares fingerprints of 16 step 1-4 tables with each other and with the live database (cannot delete the live DB while running inside it).
- MonteCarlo sheet: statistics/percentile table, price percentile, parameters, histogram table and one native openpyxl bar chart. WACC sheet: every input with source, both cases, beta sensitivity line, limitation notes (Italy double counting, low Europe beta). Valuation: minorities at book flagged in the table note and in a separate SIMPLIFICATION FLAG line.

## Files
| File | Purpose |
|------|---------|
| `py/05_build_report.py` | Runs step 1-4 check scripts and the determinism test, builds `report_headline` and the workbook |
| `checks/check_step05.py` | 86 acceptance checks (rebuilds the workbook, reads it back) |
| `report/DeLonghi_DCF_Valuation.xlsx` | The report |
| `run.py` | Step 5 registered |
| `evidence/data_quality_log.md` | Step 5 entries 23-24 |

## Row flow
| Table | Rows in | Rows out | Why the difference |
|-------|---------|----------|--------------------|
| hist_statements -> Statements_5Y | 153 | 28 line rows x 6 FY columns (153 values) + 153 source rows | pivot; the source block lists doc and page per row |
| hist_adjustments / hist_ratios -> Adjustments_Ratios | 10 / 5 | 10 rows / 25 ratio rows x 5 FY | ratios pivoted (tax_included shown as yes/no text) |
| forecast_fcff / forecast_assumptions -> Forecast_FCFF | 5 / 19 | 15 line rows x 5 FY / 19 driver rows | pivot |
| wacc_inputs, wacc, beta_sensitivity -> WACC | 19 / 2 / 1 | 19 / 13 rows x 2 cases / 6 | pivot |
| valuation, multiples_check, bridge_inputs -> Valuation | 35 / 2 / 18 | all rows | plus headline block |
| sensitivity -> Sensitivity | 25 | 5 x 5 grid | |
| mc_summary, mc_params, mc_histogram -> MonteCarlo | 1 / 11 / 54 | 15 / 11 / 54 rows + 1 chart | |
| (computed) -> report_headline | | 10 | sentence + 9 numbers |

## Check results
```
PASS  py/05_build_report.py runs without error  (actual=True expected=True)
PASS  sheet names and order  (actual=['Statements_5Y', 'Adjustments_Ratios', 'Forecast_FCFF', 'WACC', 'Valuation', 'Sensitivity', 'MonteCarlo', 'Multiples_Check', 'Checks'] expected=['Statements_5Y', 'Adjustments_Ratios', 'Forecast_FCFF', 'WACC', 'Valuation', 'Sensitivity', 'MonteCarlo', 'Multiples_Check', 'Checks'])
PASS  no formulas (cells with data_type f or text starting with '=')  (actual=0 expected=0)
PASS  py/05_build_report.py: no numeric literals outside named UPPER_CASE constants (0, 1, 2 allowed as offsets)  (actual=[] expected=[])
PASS  py/05_build_report.py reads DuckDB only (no pandas read_csv/read_excel, no open() of data files)  (actual=[] expected=[])
PASS  py/05_build_report.py writes no formulas (no '=' string literal start)  (actual=[] expected=[])
INFO  expected sentence: De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value.
PASS  report_headline has exactly one 'sentence' row  (actual=1 expected=1)
PASS  report_headline sentence = sentence rebuilt from valuation, wacc, mc_summary, bridge_inputs  (actual="De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value." expected="De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value.")
PASS  Valuation!A1 = headline sentence (top of sheet)  (actual="De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value." expected="De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value.")
PASS  report_headline.value_per_share = source value  (actual=56.47243714823831 expected=56.47243714823831 rel_tol=1e-12)
PASS  report_headline.wacc = source value  (actual=0.06520792331945185 expected=0.06520792331945185 rel_tol=1e-12)
PASS  report_headline.g = source value  (actual=0.02 expected=0.02 rel_tol=1e-12)
PASS  report_headline.mc_p10 = source value  (actual=44.34140546422919 expected=44.34140546422919 rel_tol=1e-12)
PASS  report_headline.mc_p90 = source value  (actual=74.07999911948627 expected=74.07999911948627 rel_tol=1e-12)
PASS  report_headline.price = source value  (actual=45.32 expected=45.32 rel_tol=1e-12)
PASS  report_headline.price_percentile = source value  (actual=12.03 expected=12.03 rel_tol=1e-12)
PASS  report_headline.pct_vs_base = source value  (actual=-0.19748460862355788 expected=-0.19748460862355788 rel_tol=1e-12)
INFO  Statements_5Y: 459 numeric cells
PASS  round-trip Statements_5Y: numeric cells not equal to any source-table value (|diff| < 1e-9)  (actual=(0, None) expected=(0, None))
PASS  Statements_5Y has numeric cells  (actual=459 expected in [1, 1000000])
INFO  Adjustments_Ratios: 160 numeric cells
PASS  round-trip Adjustments_Ratios: numeric cells not equal to any source-table value (|diff| < 1e-9)  (actual=(0, None) expected=(0, None))
PASS  Adjustments_Ratios has numeric cells  (actual=160 expected in [1, 1000000])
INFO  Forecast_FCFF: 84 numeric cells
PASS  round-trip Forecast_FCFF: numeric cells not equal to any source-table value (|diff| < 1e-9)  (actual=(0, None) expected=(0, None))
PASS  Forecast_FCFF has numeric cells  (actual=84 expected in [1, 1000000])
INFO  WACC: 51 numeric cells
PASS  round-trip WACC: numeric cells not equal to any source-table value (|diff| < 1e-9)  (actual=(0, None) expected=(0, None))
PASS  WACC has numeric cells  (actual=51 expected in [1, 1000000])
INFO  Valuation: 88 numeric cells
PASS  round-trip Valuation: numeric cells not equal to any source-table value (|diff| < 1e-9)  (actual=(0, None) expected=(0, None))
PASS  Valuation has numeric cells  (actual=88 expected in [1, 1000000])
INFO  Sensitivity: 41 numeric cells
PASS  round-trip Sensitivity: numeric cells not equal to any source-table value (|diff| < 1e-9)  (actual=(0, None) expected=(0, None))
PASS  Sensitivity has numeric cells  (actual=41 expected in [1, 1000000])
INFO  MonteCarlo: 188 numeric cells
PASS  round-trip MonteCarlo: numeric cells not equal to any source-table value (|diff| < 1e-9)  (actual=(0, None) expected=(0, None))
PASS  MonteCarlo has numeric cells  (actual=188 expected in [1, 1000000])
INFO  Multiples_Check: 20 numeric cells
PASS  round-trip Multiples_Check: numeric cells not equal to any source-table value (|diff| < 1e-9)  (actual=(0, None) expected=(0, None))
PASS  Multiples_Check has numeric cells  (actual=20 expected in [1, 1000000])
PASS  Statements_5Y: all 153 hist_statements values at (statement, line item, FY) equal source  (actual=0 expected=0)
PASS  Statements_5Y: number format '#,##0' on all of them  (actual=0 expected=0)
PASS  Statements_5Y: BS has a FY2020 column, header FY2020..FY2025  (actual=['FY2020', 'FY2021', 'FY2022', 'FY2023', 'FY2024', 'FY2025'] expected=['FY2020', 'FY2021', 'FY2022', 'FY2023', 'FY2024', 'FY2025'])
PASS  Adjustments_Ratios: all 120 hist_ratios values equal source  (actual=0 expected=0)
PASS  Adjustments_Ratios: ratio formats (% to 1 decimal, EUR m no decimals)  (actual=0 expected=0)
PASS  Adjustments_Ratios: adjustment amounts = hist_adjustments (sorted)  (actual=[-7.258, -3.933, -0.992, -0.289, 0.39, 5.406, 5.502, 5.57, 10.667, 14.978] expected=[-7.258, -3.933, -0.992, -0.289, 0.39, 5.406, 5.502, 5.57, 10.667, 14.978])
PASS  Adjustments_Ratios: adjustments carry doc and page (no empty source cells)  (actual=0 expected=0)
PASS  Forecast_FCFF: all 67 forecast_fcff values equal source  (actual=0 expected=0)
PASS  Forecast_FCFF: formats (% 1 decimal, EUR m 0 decimals)  (actual=0 expected=0)
PASS  Forecast_FCFF: assumptions block lists every driver with non-empty rule, source and note  (actual=0 expected=0)
PASS  Forecast_FCFF: driver names equal forecast_assumptions  (actual=['revenue_fy2025', 'nwc_fy2025', 'growth_fy2026', 'terminal_g', 'growth_fade_years', 'guidance_adj_ebitda_fy2026', 'adj_ebitda_fy2025_mgmt', 'share_based_cost_fy2025', 'share_based_pct', 'da_pct', 'capex_pct', 'nwc_pct', 'adj_ebit_margin_fy2026', 'adj_ebit_margin_target_fy2030', 'tax_rate_forecast', 'tax_rate_terminal', 'revenue_growth', 'adj_ebit_margin', 'wacc'] expected=['revenue_fy2025', 'nwc_fy2025', 'growth_fy2026', 'terminal_g', 'growth_fade_years', 'guidance_adj_ebitda_fy2026', 'adj_ebitda_fy2025_mgmt', 'share_based_cost_fy2025', 'share_based_pct', 'da_pct', 'capex_pct', 'nwc_pct', 'adj_ebit_margin_fy2026', 'adj_ebit_margin_target_fy2030', 'tax_rate_forecast', 'tax_rate_terminal', 'revenue_growth', 'adj_ebit_margin', 'wacc'])
PASS  WACC: all 19 inputs shown with value and a source  (actual=0 expected=0)
PASS  WACC: rf displayed as 0.00%  (actual='0.00%' expected='0.00%')
PASS  WACC: both wacc rows (base, beta_sensitivity) equal source for every column  (actual=0 expected=0)
PASS  WACC: base wacc number format 0.00%  (actual='0.00%' expected='0.00%')
PASS  WACC: beta sensitivity line present with value per share = source  (actual=True expected=True)
PASS  WACC: limitation note on Italy risk double counting  (actual=True expected=True)
PASS  WACC: note on low Europe industry beta  (actual=True expected=True)
PASS  Valuation: all 35 valuation lines equal source  (actual=0 expected=0)
PASS  Valuation: number formats on key lines (WACC/g 0.00%, EUR/share 0.00, % 0.0%, EUR m #,##0)  (actual=[] expected=[])
PASS  Valuation: minorities at book line carries the SIMPLIFICATION flag  (actual=True expected=True)
PASS  Valuation: explicit simplification flag text for minorities at book  (actual=True expected=True)
PASS  Valuation: exit-multiple cross-check block shows Gordon vs exit % difference  (actual=True expected=True)
PASS  Valuation: bridge_inputs block lists all items with a source  (actual=0 expected=0)
PASS  Valuation: headline numbers block equals report_headline (excl. sentence)  (actual=True expected=True)
PASS  Sensitivity: all 25 grid cells at (WACC row, g column) equal source  (actual=0 expected=0)
PASS  Sensitivity: formats (axes 0.00%, cells 0.00)  (actual=0 expected=0)
PASS  Sensitivity: beta sensitivity line shown  (actual=True expected=True)
PASS  MonteCarlo: percentile table (p5..p95), mean, sd, price, price percentile, base, run 0 equal mc_summary  (actual=0 expected=0)
PASS  MonteCarlo: p10 format 0.00 and price percentile format 0.0  (actual=('0.00', '0.0') expected=('0.00', '0.0'))
PASS  MonteCarlo: distribution parameters equal mc_params  (actual=True expected=True)
PASS  MonteCarlo: histogram rows equal mc_histogram (bin_lo, bin_hi, count)  (actual=[(27.5, 30, 3), (30, 32.5, 8), (32.5, 35, 36), (35, 37.5, 92), (37.5, 40, 177), (40, 42.5, 318), (42.5, 45, 485), (45, 47.5, 674), (47.5, 50, 819), (50, 52.5, 908), (52.5, 55, 947), (55, 57.5, 950), (57.5, 60, 822), (60, 62.5, 755), (62.5, 65, 613), (65, 67.5, 517), (67.5, 70, 398), (70, 72.5, 317), (72.5, 75, 254), (75, 77.5, 219), (77.5, 80, 131), (80, 82.5, 130), (82.5, 85, 87), (85, 87.5, 90), (87.5, 90, 60), (90, 92.5, 35), (92.5, 95, 34), (95, 97.5, 23), (97.5, 100, 24), (100, 102.5, 12), (102.5, 105, 14), (105, 107.5, 13), (107.5, 110, 6), (110, 112.5, 9), (112.5, 115, 4), (115, 117.5, 2), (117.5, 120, 2), (120, 122.5, 5), (122.5, 125, 1), (125, 127.5, 1), (127.5, 130, 1), (130, 132.5, 0), (132.5, 135, 0), (135, 137.5, 0), (137.5, 140, 0), (140, 142.5, 1), (142.5, 145, 0), (145, 147.5, 0), (147.5, 150, 1), (150, 152.5, 0), (152.5, 155, 1), (155, 157.5, 0), (157.5, 160, 0), (160, 162.5, 1)] expected=[(27.5, 30.0, 3), (30.0, 32.5, 8), (32.5, 35.0, 36), (35.0, 37.5, 92), (37.5, 40.0, 177), (40.0, 42.5, 318), (42.5, 45.0, 485), (45.0, 47.5, 674), (47.5, 50.0, 819), (50.0, 52.5, 908), (52.5, 55.0, 947), (55.0, 57.5, 950), (57.5, 60.0, 822), (60.0, 62.5, 755), (62.5, 65.0, 613), (65.0, 67.5, 517), (67.5, 70.0, 398), (70.0, 72.5, 317), (72.5, 75.0, 254), (75.0, 77.5, 219), (77.5, 80.0, 131), (80.0, 82.5, 130), (82.5, 85.0, 87), (85.0, 87.5, 90), (87.5, 90.0, 60), (90.0, 92.5, 35), (92.5, 95.0, 34), (95.0, 97.5, 23), (97.5, 100.0, 24), (100.0, 102.5, 12), (102.5, 105.0, 14), (105.0, 107.5, 13), (107.5, 110.0, 6), (110.0, 112.5, 9), (112.5, 115.0, 4), (115.0, 117.5, 2), (117.5, 120.0, 2), (120.0, 122.5, 5), (122.5, 125.0, 1), (125.0, 127.5, 1), (127.5, 130.0, 1), (130.0, 132.5, 0), (132.5, 135.0, 0), (135.0, 137.5, 0), (137.5, 140.0, 0), (140.0, 142.5, 1), (142.5, 145.0, 0), (145.0, 147.5, 0), (147.5, 150.0, 1), (150.0, 152.5, 0), (152.5, 155.0, 1), (155.0, 157.5, 0), (157.5, 160.0, 0), (160.0, 162.5, 1)])
PASS  MonteCarlo: exactly 1 native chart, a bar chart  (actual=['BarChart'] expected=['BarChart'])
PASS  MonteCarlo: histogram counts sum to 10,000  (actual=10000 expected=10000)
PASS  Multiples_Check: all 20 numeric values equal multiples_check  (actual=0 expected=0)
PASS  Multiples_Check: multiples formatted 0.0"x"  (actual=0 expected=0)
PASS  Multiples_Check: Europe ev_ebitda = 9.452668 exactly  (actual=9.452668 expected=9.452668)
INFO  Checks sheet has 65 rows
PASS  Checks sheet: every row is PASS  (actual=[] expected=[])
PASS  Checks sheet lists 'balance sheet balances'  (actual=True expected=True)
PASS  Checks sheet lists 'cash flow reconciles'  (actual=True expected=True)
PASS  Checks sheet lists 'fcff identity'  (actual=True expected=True)
PASS  Checks sheet lists 'ev = sum pv'  (actual=True expected=True)
PASS  Checks sheet lists 'sensitivity centre'  (actual=True expected=True)
PASS  Checks sheet lists 'mc run 0'  (actual=True expected=True)
PASS  Checks sheet lists 'determinism'  (actual=True expected=True)
PASS  Checks sheet lists 'check_step01'  (actual=True expected=True)
PASS  Checks sheet lists 'check_step04'  (actual=True expected=True)
PASS  Checks sheet: 6 BS year-ends + 5 CF years + forecast + others  (actual=65 expected in [25, 200])
PASS  Checks sheet: 'balance sheet balances' appears once per year  (actual=6 expected=6)
PASS  Checks sheet: 'cash flow reconciles' appears once per year  (actual=5 expected=5)
PASS  Checks sheet: 'fcff identity' appears once per year  (actual=5 expected=5)
PASS  independent: max |total assets - total net equity and liabilities| over 6 year-ends <= 0.002  (actual=0.0 expected=0.0 rel_tol=1e-12)
PASS  workbook creator set  (actual=True expected=True)

86/86 checks passed
```

## Spot-check cases for the human
1. **Typical: headline value per share.** `valuation.value_per_share` = 56.472437 (equity 8,448.296 m / 149.600349 m shares). Workbook Valuation!A1 shows 56.47; cell B5 holds 56.47243714823831 formatted `0.00`.
2. **Edge: price percentile.** `mc_summary.price_percentile` = 12.03 (1,203 of 10,000 runs below 45.32). The sentence says "12th" (rounded integer, DQ #23); MonteCarlo sheet shows 12.0.
3. **Edge: sign of the gap.** `upside_pct` = 45.32 / 56.472437 - 1 = -0.197485, so the sentence says "19.7% below the base-case value" (price below value, as the brief's "above/below" slot).
4. **Boundary: YE2020 balance sheet.** Checks sheet row "Balance sheet balances YE2020": total assets 2,945.569 = total net equity and liabilities 2,945.569 (the only year with no IS/CF column in Statements_5Y; FY2020 cells for IS/CF are intentionally blank).
5. **Determinism row.** Checks sheet "Determinism: mc_runs fingerprint identical ..." compares the live fingerprint (10000 rows / 92558926622417105030481, same as the step 4 pack) with two scratch rebuilds.

## Deviations, disputes, changes to earlier steps
- No changes to earlier steps (`run.py` only gained the step-5 entry).
- Check-script note: my AST check "no numeric literals outside named constants" allows 0, 1, 2 (offsets) and anything assigned to UPPER_CASE module-level names (including tuple targets); the tuple-target allowance was added to the check while it was still being first written, before any pass.
- `py/05_build_report.py` takes about 1.5 minutes because it runs check_step01..04 and two scratch rebuilds; `check_step05.py` runs it again, so that check takes about the same.
- The step 6 note will need numbers at workbook precision; the percentile appears as "12th" in the sentence and "12.0" on the MonteCarlo sheet (plus the integer 12 in the headline block of Valuation).

<!-- The Verifier appends its section below. -->

## Formatting change (presentation only, 2026-11-09, human request)
- **What changed.** New helper `py/report_style.py` (named palette/style constants and `style_sheet(ws)`), called once per sheet from `py/05_build_report.py` just before the workbook is saved. Navy title bar on every sheet (A1 text merged across the columns), navy header rows with white bold text, light banded rows, thin grey borders, numbers right-aligned and text left-aligned, long text wrapped, gridlines hidden, freeze panes under the first header row (Statements_5Y also freezes columns A:B), landscape and fit-to-width printing, tab colours by group (blue data, green WACC/Valuation, orange Sensitivity/MonteCarlo, brown Multiples, grey Checks). Valuation: headline sentence in 16 pt bold white on navy, merged A1:G1; value per share, WACC, price and price percentile rows highlighted in yellow; equity bridge block (ev down to value_per_share) outlined and tinted; simplification flag merged and tinted. Sensitivity: red-white-green colour scale on the WACC x g grid, base-case cell outlined with a medium border. MonteCarlo: histogram recoloured, shorter title, no horizontal gridlines, moved to D3 and resized (17 x 8.2 cm) to sit beside the percentile table (column D narrowed 70 to 60). Checks: PASS green, FAIL red (direct fill).
- **Not changed.** No cell value, position, sheet name or order, and no number format. Still values only, no formulas.
- **Proof.** `before.xlsx` (copy of the verified workbook, taken before the rebuild) vs the rebuilt workbook, every cell compared (value, data type, and number format for numerics): 9 sheets, same order and names, 3,706 cells, 1,237 numeric cells, 0 differences, 0 formulas. Valuation!A1 unchanged.
- **Re-run.** `python run.py --through 6` rebuilt cleanly; `checks/check_step05.py` 86/86 passed; `checks/check_step06.py` 17/17 passed.
- **Not verified visually.** No Excel/LibreOffice was available here, so row heights for wrapped text and the chart placement were set by estimate; the human should glance at the MonteCarlo and Valuation sheets.
