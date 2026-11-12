# Step 06: Write the investment note. Verdict: PASS WITH NOTES

## Summary for the human (one page max)
- Headline numbers: all 55 number tokens in the note (Executor) = 55/55 (Verifier, method: each token mapped in reading order, with its unit, to one named DuckDB source value formatted at brief precision, then located as a displayed workbook cell) ✓. Headline paragraph = `report_headline` = Valuation!A1, character for character ✓.
- Rows: no new tables. Chart bars = `mc_histogram` (54 bins, 10,000 runs) = my re-binning of `mc_runs` (0 bins differ) ✓.
- Checks: 17/17 pass; all planned checks present and not weakened (allowlist slightly wider in wording, see note 3); steps 1-5 checks still pass (128, 78, 148, 66, 86) ✓.
- Reproducible: two clean `run.py --fresh --through 6` rebuilds; all 24 non-raw table fingerprints identical; the docx package members are byte-identical between runs (only zip timestamps differ); the chart PNG is byte-identical ✓. Workbook cells identical to the step-5-verified dump ✓.
- Format: rendered with LibreOffice to PDF = exactly 2 pages; 552 words; 1 picture; 5 headings in order; 3 simplifications named in Risks ✓.
- Notes: FRAGILE (carried, disclosed): the conclusion flips under the Global beta line (EUR 35.60 < price 45.32). Minor wording and documentation notes below.
- Spot-checks: Executor cases 1-5 traced ✓; own cases (seed 20261109) cash-like assets 305 and MC p10 44.34 traced to raw ✓.
- Needs your decision: no

## Findings (notes only, no errors)
| # | Level | File:line | Problem | Evidence |
|---|---|---|---|---|
| 1 | V4 wording | py/06_build_note.py:178-179 | "The forecast tax rate is 24.1%" is true for FY2026E-30E but omits that the terminal FCFF uses the marginal 27.81% (Decision 8A). No number is wrong. | forecast_fcff.tax_rate = 0.241299 every year; valuation.fcff_tv note: "tax at the marginal rate". |
| 2 | V4 docs | py/06_build_note.py:166-170, 194, 202, 208, 217 | Qualitative comparisons are typed text, not asserted in code ("net cash ... exceed", "both below the Gordon-growth value", "below the market price", "only just above its lower end", "above the five-year average"). All are true today; a future rerun with different inputs would not catch them. | 998+305=1,303 > 227+212+94=533; 48.28 and 52.57 < 56.47; 35.60 < 45.32; 45.32 vs p10 44.34; 12.8% > 5-yr mean 11.27%. |
| 3 | V2 | checks/check_step06.py:86-95 | The number match is unit-less (a token "6.52" would match any displayed 6.52) and the allowlist also covers dates, FY/H labels and "80% Monte Carlo", beyond the plan's "years and page counts". Not a weakening of substance (DQ log 25 states it), but weaker than the plan's intent. | Verifier's unit-aware, ordered match passes 55/55, so no mismatch is hidden. |
| 4 | V5 | py/06_build_note.py:149-151 | Page size is US Letter (8.5 x 11 in), not A4. Brief does not specify. | sections[0].page_width = 7,772,400 EMU. Renders to 2 pages either way (checked on Letter). |
| 5 | V6 FRAGILE | note, Risks bullet 1 and Conclusion | Carried from steps 2-4: the sign of the conclusion depends on beta. Base 56.47 > price; Global beta 35.60 < price (-37.0%). The note states this explicitly. | wacc row beta_sensitivity 9.62%; beta_sensitivity.value_per_share 35.599619. |

## Verifier details
Commands run (venv python):
- `run.py --fresh --through 6` twice (rc=0 both, about 81 s each); `checks/fingerprint.py --save/--compare verify/fp_step06.txt` on all 24 non-raw tables: "PASS fingerprints identical".
- docx run1 vs run2: same member list, every member byte-identical. PNG sha256 22fd3129... in both runs and in the Executor's copy.
- `checks/check_step01..06.py`: 128/128, 78/78, 148/148, 66/66, 86/86, 17/17. Step 6 output equals the pasted output (line endings only).
- `verify/verify_step06.py` (independent): ordered unit-aware match 55/55 PASS; every value located as a displayed workbook cell (e.g. EV 8,033 Valuation!D37; TV share 79.6% Valuation!D38; ke 6.82% WACC!B32; beta line 35.60 WACC!B42, -37.0% WACC!B45, 9.62% WACC!B41; exit 48.28/52.57 at 9.5x/10.6x Valuation!C54:D55; tax 24.1% Forecast_FCFF!B8); histogram re-bin 0 differences; 1 `<w:drawing>`, 1 media file.
- LibreOffice headless PDF conversion: 2 pages.
- Level 15: workbook cell dump (2,699 non-empty cells, 0 formulas) identical to `verify/xlsx_dump_run1.txt` from step 5. Level 16: every headline number traces to `valuation`, `wacc`, `mc_summary`, `bridge_inputs` (verified in steps 2-4) via `report_headline`. Level 17: full fresh rebuild and all checks pass (above).

Spot-checks traced:
| Case | Note | Independent source | Result |
|---|---|---|---|
| E1 headline | sentence | report_headline.sentence and Valuation!A1, string equality | ✓ |
| E2 TV share | 79.6% | valuation.tv_share_of_ev 0.796467 = pv_tv 6,397.937 / ev 8,032.898 | ✓ |
| E3 ke, betas | 6.82%, 0.420, 0.397 | wacc base: ke 0.068159 = 0.04362 + 0.419599 x (0.0423 + 0.016181) | ✓ |
| E4 beta line | 35.60, 9.62%, -37.0% | beta_sensitivity 35.599619; 35.5996/56.4724 - 1 = -0.36961 | ✓ |
| E5 small integers | 5th/95th, 80%, 12th | labels; 12th = round(12.03); share of mc_runs < 45.32 = 12.03% recomputed with numpy | ✓ |
| V1 (random) cash-like 305 | EUR 305 m | raw_report_lines AR2025 p.171 lines 50, 52, 53: 6.743 + 72.541 + 165.117 = 244.401 (= total 244.795 - leasing advances 0.394), plus non-current liquidity investments 60.343 (note 18, traced in step 2) = 304.744 | ✓ |
| V2 (random) MC p10 | EUR 44.34 | numpy percentile of mc_runs.value_per_share: linear 44.3414, lower 44.3395, higher 44.3416, all display 44.34 | ✓ |

---
# Step 06: Write the investment note. Status: AWAITING VERIFICATION

## What was done
- `py/06_build_note.py` reads the verified workbook (`report/DeLonghi_DCF_Valuation.xlsx`) with openpyxl and writes `report/DeLonghi_DCF_Valuation_note.docx`. Every number is formatted from the source cell's own number format, so the note shows the workbook's display precision.
- Sections as headings: Thesis, Main assumptions, Valuation range, Risks, Conclusion vs market price. The headline sentence (Valuation!A1, asserted equal to `report_headline`) sits under the title.
- One chart, `report/note_chart.png`: Monte Carlo histogram from `mc_histogram` with lines for the market price and the base case. It is the only picture.
- Risks name the three simplifications: minorities at book value, Italy risk double counting, low Europe industry beta (plus the beta-sensitivity result and terminal value weight).
- `run.py` registers step 6; `python run.py --fresh --through 6` rebuilds everything (about 86 s).

## Files
| File | Purpose |
|---|---|
| py/06_build_note.py | Builds the docx and the chart from the workbook and `report_headline` / `mc_histogram` |
| checks/check_step06.py | Acceptance checks (regex number match against workbook displayed values, picture count, words, headings, headline, risk phrases) |
| report/DeLonghi_DCF_Valuation_note.docx, report/note_chart.png | Outputs |
| run.py | Step 6 entry added |
| evidence/data_quality_log.md | Entry 25 added |

## Row flow
| Table | Rows in | Rows out | Why the difference |
|---|---|---|---|
| mc_histogram | 54 bins | 54 bars | Plotted unchanged |
| report_headline | 1 sentence row | 1 sentence in the note | Compared for exact equality |
No new tables.

## Check results
build py/06_build_note.py rc=0 
PASS  note builds  (actual=0 expected=0)
PASS  docx and chart png exist  (actual=(True, True) expected=(True, True))
PASS  numbers in note: count found > 20  (actual=True expected=True)
PASS  zero unmatched numbers (vs workbook displayed values)  (actual=[] expected=[])
PASS  exactly 1 picture (inline shapes)  (actual=1 expected=1)
PASS  exactly 1 media file in package  (actual=1 expected=1)
PASS  word count <= 900  (actual=552 expected in [1, 900])
PASS  heading present: Thesis  (actual=True expected=True)
PASS  heading present: Main assumptions  (actual=True expected=True)
PASS  heading present: Valuation range  (actual=True expected=True)
PASS  heading present: Risks  (actual=True expected=True)
PASS  heading present: Conclusion vs market price  (actual=True expected=True)
PASS  headline sentence in note identical to report_headline  (actual=True expected=True)
PASS  headline sentence identical to Valuation!A1  (actual="De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value." expected="De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value.")
PASS  risks section names: minorities at book  (actual=True expected=True)
PASS  risks section names: Italy risk double counting  (actual=True expected=True)
PASS  risks section names: low Europe industry beta  (actual=True expected=True)

17/17 checks passed

## Spot-check cases for the human
1. Headline sentence: note paragraph 1 equals Valuation!A1 and `report_headline` (value 56.47, WACC 6.52%, g 2.00%, range 44.34-74.08, price 45.32, 12th percentile, 19.7% below).
2. Terminal value share: note says 79.6% in Thesis and Risks = Valuation `tv_share_of_ev` 0.79647 shown at `0.0%`.
3. Cost of equity 6.82% = WACC sheet base column `ke` 0.068159 shown at `0.00%`; relevered beta 0.420 from `beta_l`; unlevered 0.397.
4. Beta risk line: value 35.60 per share at WACC 9.62% (-37.0%) = WACC sheet "Beta sensitivity line" block; consistent with the sentence "below the market price" (35.60 < 45.32).
5. Edge case, small integers: "5th to 95th percentile" and "80% range" are plain labels; the regex matches small integers loosely (DQ log 25). Dates (6 November 2026), years and FY/H labels are allowlisted by pattern. The qualitative statement "price only just above the lower end of the 80% range" rests on 45.32 vs p10 44.34.

## Deviations, disputes, changes to earlier steps
None. Two judgement notes for the Verifier: (a) the page limit is checked by the 900-word proxy only (552 words plus one 2.5 inch chart at 10 pt); I did not render pages. (b) The conclusion wording ("fairly valued to moderately undervalued") is my interpretation of the verified numbers, not a figure.

<!-- The Verifier appends its section below. -->
