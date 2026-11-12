# Step 07: Rebuild the workbook on the shared Ledger style (polish pass re-verification). Verdict: PASS WITH NOTES

## Summary for the human (one page max)
- Scope: this pass re-verifies the approved polish edits only (Amendment 2, post-verification decision (c)): the chart fonts (note 3), the 3.2 label "Price vs value, %" (note 4), and the docstring and spot-check wording (note 5). The full step was verified in commit 2800625; that section is kept below.
- Headline numbers: unchanged. Baseline cells: 2,691 compared, 0 mismatches. Numeric cells: 1,237. Chart: 54 bins, sum 10,000. Executor = Verifier. My independent raw-OOXML script `verify/verify_step07.py`, rerun on the new workbook, gives output byte-identical to `verify/verify_step07_output.txt` ✓
- What changed in the workbook (zip diff against HEAD): only `xl/charts/chart1.xml` (font runs added), `xl/worksheets/sheet7.xml` (one string: 3.2 B15 "Difference vs base case, %" → "Price vs value, %"), and `docProps/core.xml` (timestamp). After stripping the title and txPr elements, the chart data, references and anchor are unchanged ✓
- Checks: check_step07 74/74. Earlier steps still pass: 01 128/128, 02 78/78, 03 148/148, 04 66/66, 05 93/93, 06 25/25. check_step08 also still passes (65/65). The check edit (line 203: `DM.label_for(name, a)` instead of `DM.LABELS[a]`) still needs an exact match on every row. Its single override is the human-approved relabel, so it is not a weakening ✓
- Reproducible: I ran two `run.py --fresh --through 7` rebuilds. The 24 table fingerprints are identical to each other and to `verify/fp_step06.txt`. The two workbooks differ only in `docProps/core.xml` ✓
- Notes: no SURPRISE and no FRAGILE. Three minor notes, listed below.
- Visual: the render on page 16 shows a Garamond chart title and Gill Sans MT axis text in ink. Page 12 shows "Price vs value, %" on row 15 ✓
- Spot-checks: 3.2 row 15 traced, and 2 random rows (seed 20261117) traced to raw tables ✓
- Needs your decision: no

## Findings (notes, none blocking)
| # | Level | File:line | Problem | Evidence |
|---|---|---|---|---|
| 1 | V2 | checks/check_step07.py:209; plan/plan.md:256 | The check's message and the plan's Design text still say "B equals LABELS[A]". The code now compares to `label_for(sheet, key)`, which equals LABELS[A] except for the one approved override. The documentation is out of step with the rule, but the rule itself is no looser. | `LABEL_OVERRIDES` has exactly 1 entry, ("3.2 Valuation", "pct_vs_base") |
| 2 | V4 | py/05_build_report.py `_txpr` (approx. l.713-716) | openpyxl writes an empty run `<a:r><a:t/></a:r>` into each axis `txPr` paragraph. LibreOffice renders it correctly. Excel is not available, so its behaviour is untested. Cosmetic. | chart1.xml, both `<c:txPr>` blocks |
| 3 | V1/V2 | earlier notes 2 and 6 | Still open (they were not in the polish scope). The render "band per sheet" check remains vacuous (INFO: every sheet maps to page 1). Workbook bytes still differ by the `core.xml` timestamp. Earlier notes 1, 3, 4 and 5 are now closed (note 1 INFO list is empty). | check_step07 INFO lines |

## Verifier details
**Commands**
- `run.py --fresh --through 7` (rc 0). Then `fingerprint.py --save verify/fp_step07.txt <24 tables>`, which is identical to `fp_step06.txt`. A second fresh run (rc 0), then `--compare`: "PASS fingerprints identical".
- check_step01-06 and 08: 128, 78, 148, 66, 93, 25 and 65 passes, 0 FAIL. check_step07: 74/74. Its INFO lines are as in the Executor's polish note.
- `verify/verify_step07.py` rerun: output diff against `verify/verify_step07_output.txt` is empty.

**Code review of the polish diff.** Read in full: `git diff` of py/05_build_report.py, py/doc_map.py, checks/check_step07.py and plan.md.
- `LABELS` is unchanged, so 2.1 A47 keeps "Difference vs base case, %" (value -0.3696 = beta_sensitivity pct_vs_base).
- Chart typefaces: Garamond ×2 (title, 14 pt) and Gill Sans MT ×8 (9 pt). The only srgb colour is 1A1A1A.
- The docstring now says "eleven sheets", "3.2 Valuation sheet" and "2.1 WACC sheet". The remaining "nine sheets" in lines 4 and 7 correctly describe the step-5 layout.

**Spot-checks traced**
| Case | Cell | Value | Independent trace |
|---|---|---|---|
| P1 | '3.2 Valuation'!A15:C15 | pct_vs_base, "Price vs value, %", -0.1974846086235579 | 45.32 / 56.47243714823831 - 1 = -0.19748460862355788. The price comes from raw_yahoo_prices DLG.MI 2026-11-06 close 45.31999969482422 (rounded to 0.01). The value equals valuation.value_per_share. |
| R1 (seed) | '2.1 WACC'!A6:C6 | rf, "Risk-free rate", 0.04362 | raw_ecb_yield_10y IT 2026-09 = 4.362 % |
| R2 (seed) | '3.2 Valuation'!A8:C8 | wacc, "WACC", 0.06520792331945185 | wacc case 'base', last column = 0.06520792331945185 |

## Earlier verification (commit 2800625, first attempt): PASS WITH NOTES

### Summary for the human (one page max)
- Headline numbers:
  - Baseline cells carried over unchanged: 2,691 compared, 0 mismatches (Executor) = 2,691 compared, 0 mismatches (Verifier). Method: raw OOXML parse with no openpyxl, baseline read from `git show 59ecd69`, raw `<v>` text plus number format compared, sheet map and label rule hard-coded from the plan. ✓
  - Numeric cells: 1,237 (Executor) = 1,237 (Verifier). 0 on 0.0 Overview, and 0 numeric cells that do not come from a baseline cell. ✓
  - Chart: 54 bins summing to 10,000, equal to `mc_histogram.count` (Executor) = same (Verifier, read from the chart XML reference and the sheet XML). ✓
  - Headline sentence: on `0.0 Overview`!A3 and `3.2 Valuation`!A3 it equals `report_headline` and the baseline Valuation!A1. ✓
- Rows: 2,699 non-empty baseline cells map to new cells. The 8 old row-1 titles are exempt in the check, but all 8 are in fact identical at their mapped cell. 5.1 Checks has 65 rows, all PASS. The note text and chart are byte-identical to the baseline (paragraphs and every docx member). ✓
- Checks: check_step07 passes 74/74, and its output matches the evidence pack. None of the plan's checks is missing or weakened. The plan's hex-literal rule is scoped (note 1). The check_step05 diff is non-weakening (93/93, floor 86) and check_step06 has sheet-reference edits only (17/17). Steps 01 to 04 still pass (128, 78, 148, 66). ✓
- Reproducible: two `run.py --fresh --through 7` runs gave identical fingerprints for all 24 tables, equal to `verify/fp_step06.txt`. Every workbook zip member is identical except `docProps/core.xml` (save timestamp). ✓
- Notes: no SURPRISE and no FRAGILE. Minor notes 1 to 6 are listed below.
- Visual: confirmed on the 20 PNG pages. Each sheet's first page shows its band and links. No sheet is split across the page width. The chart is clear of the tables. Vermilion appears only on the step numerals and on key results. "▸" renders as a glyph, not a box (LibreOffice only).
- Spot-checks: the Executor's cases 1 to 5 and 2 random cases (seed 20261110) are all traced to DuckDB and raw report lines ✓
- Needs your decision: no

### Findings (notes, none blocking)
| # | Level | File:line | Problem | Evidence |
|---|---|---|---|---|
| 1 | V2 | checks/check_step07.py:63,301 | The plan's rule "no hex colour literal in py/*.py outside ledger_style.py" exempts `06_build_note.py` and `07_process_guide.py`. This deviation is documented, and the plan restricts step 7 to sheet-reference edits of 06. Six literals remain, including a navy `#1F3A5F` in 07 (not one of the 3 banned navy hexes). | INFO line in the check output. Step 8 must bring this to 0, with no exemption. |
| 2 | V2 | checks/check_step07.py:368-375 | The render check "band for every sheet, in sheet order" is vacuous. Page 1 (the 0.0 index) contains every "§x.y", so all 11 sheets resolve to page 1 (see the INFO line). | Bands were confirmed visually on pages 1, 2, 7, 8, 10, 11, 12, 14, 15, 16 and 19. Step 8 should match the band at the top of each page instead. |
| 3 | V5 | py/05_build_report.py:700-720 | The chart title and axis text have no font set and render in the default chart font (Calibri-like), not Garamond or Gill Sans MT. The plan's font check covers cells only. | Visible on render page 16. Cosmetic. |
| 4 | V4 | py/doc_map.py LABELS `pct_vs_base` | One key, two meanings. On 3.2 (headline row 15) the value is price/value - 1 (-19.7%). On 2.1 it is the beta-sensitivity value vs base (-37.0%). The single label "Difference vs base case, %" fits both but is vague on 3.2. The Source column on 3.2 states the formula. | `'3.2 Valuation'!A15:E15` |
| 5 | V4 | evidence/step07.md, spot-check 5; py/05_build_report.py docstring | The pack says the 4.1 grid header is row 7. It is row 5 (freeze pane A6); the cell D8 is correct. The "Brief definitions" docstring of 05 still says "nine sheets" and "Valuation sheet". | `ws.freeze_panes` = A6 on 4.1 |
| 6 | V1 | py/05_build_report.py:839 | `FIXED_DATETIME` does not stop openpyxl from stamping `dcterms:modified` at save, so the workbook bytes differ between runs. The plan asks for identical values, styles and links, which holds. | zip diff: only `docProps/core.xml` differs |

### Verifier details
**Commands**
- `.venv/Scripts/python.exe run.py --fresh --through 7` (rc 0), then `checks/fingerprint.py --save verify/fp_step07.txt <24 tables>`; it is identical to `verify/fp_step06.txt`.
- A second `run.py --fresh --through 7` (rc 0), then `--compare verify/fp_step07.txt` gave "PASS  fingerprints identical".
- check_step01 to 06: 128/128, 78/78, 148/148, 66/66, 93/93, 17/17. check_step07: 74/74 (2 min 40 s; its own 2 fresh runs included). The INFO lines are identical to the pack.
- `verify/verify_step07.py` writes its output to `verify/verify_step07_output.txt`.

**Blind recomputation (verify/verify_step07.py).** The baseline xlsx comes from git, not the snapshot. Both files are parsed via zipfile and ElementTree (shared strings, cellXfs, numFmts). The plan's map is hard-coded: the old-to-new sheet names, the label sheets 1.2/2.1/2.2/3.1/3.2/4.2, and the bridge block from the "Bridge input" header (old rows 57-75, new 2.2 row 4).

| Quantity | Executor | Verifier |
|---|---|---|
| Baseline non-empty cells | 2,699 | 2,699 |
| Compared / exempt / mismatched | 2,691 / 8 / 0 | 2,691 / 8 / 0 (exempt titles that differ: 0) |
| Numeric cells, 1.1-5.1 / 0.0 | 1,237 / 0 | 1,237 / 0; unmapped numeric cells 0 |
| Formulas | 0 | 0 (no `<f>` element) |
| Chart | 1 BarChart, `'4.2 Monte Carlo'!$D$36:$D$89` | same, values = mc_histogram.count, 54 bins, sum 10,000 = rows of mc_runs |
| 5.1 PASS rows | 65 | 65, no non-PASS |

**Other independent checks**
- **styles.xml:** fonts {Garamond, Gill Sans MT}. Colours are the 6 palette values only, with no theme or indexed colours. The chart uses srgb 1A1A1A only.
- **Banned phrases:** 0 hits for the step-8 list over all sheet and chart text, plus "us" and "interview" (raw XML scan).
- **check_step05 diff:** read line by line. The changes are the sheet map `NEW`, value columns found by header name, A1 to A3 plus a new 0.0 assertion, pool `SHEETS[1:-1]`, the AST scan extended to the 3 modules (+3 checks), and the bridge check on 2.2 plus "not on 3.2". No tolerance or expected value changed, and no check was removed.
- **check_step06 and 06_build_note.py diffs:** sheet names and column or row offsets only. The note docx has the same 18 paragraphs, and every zip member is identical to 59ecd69. note_chart.png is byte-identical.
- **Labels:** all 137 key-to-label pairs were read. None contradicts its key (see note 4).

**Spot-checks traced**
| Case | Workbook cell | Value | Independent trace |
|---|---|---|---|
| E1 | '3.2 Valuation'!C7 (B7 "Value per share") | 56.47243714823831, format 0.00 | (ev 8032.898 + cash 998.448 + cash-like 304.744 - bank 227.043 - other 212.18 - leases 94.37 - distrib 156.4 - minorities 197.801) / 149.6003 = 56.47243714823831 |
| E2 | '2.2 Bridge Inputs'!A5:C5 | bank_debt, "Bank debt", 227.043 | raw_report_lines AR2025 p.176 l.39 "Total banks loans and borrowings ... 227,043" (p.147 l.26 191,166 + l.37 35,877) |
| E3 | '1.1 Statements'!H13 | -108.586 (FY2025 taxes) | raw_report_lines AR2025 p.144 l.37 "Taxes 10 (108,586) (104,424)" |
| E4 | '0.0 Overview'!A3 = '3.2 Valuation'!A3 | headline sentence | = report_headline 'sentence' = baseline Valuation!A1 |
| E5 | '4.1 Sensitivity'!D8 | 56.47243714823831 | A8 = WACC 6.52%, D header g 2.00%; equals valuation.value_per_share |
| R1 (seed) | baseline Adjustments_Ratios!E38 → '1.2 Adjustments & Ratios'!F40 | 0.2432005664 (eff_tax_rate FY2024) | -(-104.424)/429.374 from hist_statements, and raw AR2025 p.144 l.36-37 |
| R2 (seed) | baseline Statements_5Y!E136 → '1.1 Statements'!E138 | 144 (PDF page of FY2024 net financial income) | raw_report_lines AR2025 p.144 l.35 "Net financial income (expenses) ... (1,427)" |

---
(Executor's section follows)

# Step 07: Rebuild the workbook on the shared Ledger style. Status: AWAITING VERIFICATION

## What was done
- Snapshotted the verified deliverables at commit 59ecd69 to `verify/baseline_amend2/` before any change (xlsx, docx, pdf, note_chart.png, `SHA256SUMS.txt`, `xlsx_cells.txt` cell dump, `note_tokens.txt`).
- Defined the Ledger identity once in `py/ledger_style.py` (palette, Garamond/Gill Sans MT, sizes, adapters) and the sheet/section/label registry once in `py/doc_map.py`.
- `py/05_build_report.py` still builds the nine step-5 sheets in memory (old layout), then `relayout()` places every cell on the 11 numbered sheets: 2 rows inserted on top (band "GUIDE ▸ §x.y" with links, numeral + title), readable-label column B on 1.2, 2.1, 2.2, 3.1, 3.2, 4.2, the bridge block moved to 2.2 (with a pointer line left on 3.2), 0.0 Overview added, native chart rebuilt on 4.2. `py/report_style.py` was rewritten (paper, hairlines, vermilion on key results only; no navy, no colour scale).
- `checks/check_step05.py` was edited as the plan lists (sheet map, header-name lookups for the shifted columns, `3.2 Valuation!A3`, round-trip pool 1.1-4.2, AST scan extended to the 3 style modules). `py/06_build_note.py` and `checks/check_step06.py` got reference edits only (sheet names, A1 to A3, value/display columns shifted by the label column). The note text is identical to the baseline (18 paragraphs).
- Added `checks/render_png.py` (LibreOffice to PDF to PNG at 110 dpi), `checks/xlsx_dump.py`, `checks/note_tokens.py`; `pypdfium2>=4` in `requirements.txt`. PNGs of every workbook page are in `verify/render/step07/`.

## Files
| File | Purpose |
|---|---|
| `checks/check_step07.py` | all step-7 acceptance checks (written first; it failed against the old workbook at "sheet names") |
| `py/ledger_style.py` | palette, fonts, sizes, openpyxl/reportlab/python-docx/matplotlib adapters |
| `py/doc_map.py` | SHEETS, SECTIONS, label sheets, `LABELS`, old-to-new sheet map |
| `py/report_style.py` | restyled `style_sheet(ws, info)` (imports only from ledger_style and doc_map) |
| `py/05_build_report.py` | old-layout builders + `relayout()`, Overview, links, chart |
| `checks/check_step05.py`, `checks/check_step06.py`, `py/06_build_note.py` | edited as listed above |
| `checks/render_png.py`, `checks/xlsx_dump.py`, `checks/note_tokens.py` | render and dump helpers |
| `verify/baseline_amend2/` | baseline snapshot (never modified afterwards) |
| `verify/render/step07/` | PDF and 20 PNG pages of the workbook |
| `report/DeLonghi_DCF_Valuation.xlsx` | rebuilt workbook |

## Row flow
| Table | Rows in | Rows out | Why the difference |
|---|---|---|---|
| Workbook cells (non-empty, baseline) | 2,699 | 2,699 mapped, plus new cells | every baseline cell is on its mapped new cell (value, type, number format); new text cells: bands, links, titles, 0.0 Overview, 2.2 description, 3.2 pointer line, readable labels |
| Numeric cells | 1,237 | 1,237 | none added or lost; 0.0 Overview has 0 |
| 5.1 Checks rows | 65 | 65 | identical, all PASS |
| DuckDB tables | 24 fingerprints | 24 identical | no table changed (`verify/fp_step06.txt`) |

## Check results
Output of `python run.py --fresh --through 7` (rc 0) followed by `python checks/check_step07.py`:

```
PASS  baseline snapshot DeLonghi_DCF_Valuation.xlsx is byte-identical to git show 59ecd69:report/DeLonghi_DCF_Valuation.xlsx  (actual=True expected=True)
PASS  baseline snapshot DeLonghi_DCF_Valuation_note.docx is byte-identical to git show 59ecd69:report/DeLonghi_DCF_Valuation_note.docx  (actual=True expected=True)
PASS  baseline snapshot DeLonghi_DCF_process_guide.pdf is byte-identical to git show 59ecd69:report/DeLonghi_DCF_process_guide.pdf  (actual=True expected=True)
PASS  baseline snapshot note_chart.png is byte-identical to git show 59ecd69:report/note_chart.png  (actual=True expected=True)
PASS  baseline xlsx_cells.txt equals verify/xlsx_dump_run1.txt line for line  (actual=True expected=True)
PASS  baseline xlsx_cells.txt line count (non-empty cells; the plan's 2,698 counts newline characters)  (actual=2699 expected=2699)
PASS  baseline xlsx_cells.txt equals a fresh dump of the baseline workbook  (actual=True expected=True)
PASS  SHA256SUMS.txt matches the 4 snapshot files  (actual=True expected=True)
PASS  baseline note_tokens.txt exists and is not empty  (actual=True expected=True)
PASS  workbook builds (last fresh run exit codes)  (actual=[0, 0] expected=[0, 0])
PASS  sheet names and order (R-A)  (actual=['0.0 Overview', '1.1 Statements', '1.2 Adjustments & Ratios', '2.1 WACC', '2.2 Bridge Inputs', '3.1 FCFF Forecast', '3.2 Valuation', '3.3 Multiples Check', '4.1 Sensitivity', '4.2 Monte Carlo', '5.1 Checks'] expected=['0.0 Overview', '1.1 Statements', '1.2 Adjustments & Ratios', '2.1 WACC', '2.2 Bridge Inputs', '3.1 FCFF Forecast', '3.2 Valuation', '3.3 Multiples Check', '4.1 Sensitivity', '4.2 Monte Carlo', '5.1 Checks'])
PASS  sheet names are the 11 expected names  (actual=['0.0 Overview', '1.1 Statements', '1.2 Adjustments & Ratios', '2.1 WACC', '2.2 Bridge Inputs', '3.1 FCFF Forecast', '3.2 Valuation', '3.3 Multiples Check', '4.1 Sensitivity', '4.2 Monte Carlo', '5.1 Checks'] expected=['0.0 Overview', '1.1 Statements', '1.2 Adjustments & Ratios', '2.1 WACC', '2.2 Bridge Inputs', '3.1 FCFF Forecast', '3.2 Valuation', '3.3 Multiples Check', '4.1 Sensitivity', '4.2 Monte Carlo', '5.1 Checks'])
PASS  2.2 Bridge Inputs holds the bridge block header  (actual=True expected=True)
INFO  old bridge block rows 57-75; new header row 4
PASS  every baseline cell (2691 compared, 8 old title texts exempt) equals its mapped new cell in value, type and number format  (actual=(0, []) expected=(0, []))
PASS  3.2 Valuation!A3 equals the baseline Valuation!A1 headline  (actual="De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value." expected="De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value.")
PASS  numeric cells on 1.1-5.1 total exactly 1,237  (actual=1237 expected=1237)
PASS  0.0 Overview has 0 numeric cells  (actual=0 expected=0)
PASS  5.1 Checks rows identical to the baseline  (actual=True expected=True)
PASS  5.1 Checks has 65 rows, all PASS  (actual=(65, True) expected=(65, True))
PASS  label sheets: column B is empty or equals LABELS[A] on every row (headers read 'Label')  (actual=[] expected=[])
PASS  label sheets: every key-like text in column A has a label  (actual=[] expected=[])
PASS  label sheets: no label in LABELS is unused  (actual=[] expected=[])
PASS  non-label sheets have no 'Label' header cell  (actual=[] expected=[])
PASS  formulas: 0 (no data_type f, no string starting with '=')  (actual=0 expected=0)
PASS  internal hyperlinks name an existing sheet and a cell in its used range  (actual=[] expected=[])
PASS  row 1 links: every sheet except 0.0 links to 0.0; prev/next follow R-A order (0.0 next only, 5.1 prev only)  (actual={'0.0 Overview': ['1.1 Statements'], '1.1 Statements': ['0.0 Overview', '1.2 Adjustments & Ratios'], '1.2 Adjustments & Ratios': ['0.0 Overview', '1.1 Statements', '2.1 WACC'], '2.1 WACC': ['0.0 Overview', '1.2 Adjustments & Ratios', '2.2 Bridge Inputs'], '2.2 Bridge Inputs': ['0.0 Overview', '2.1 WACC', '3.1 FCFF Forecast'], '3.1 FCFF Forecast': ['0.0 Overview', '2.2 Bridge Inputs', '3.2 Valuation'], '3.2 Valuation': ['0.0 Overview', '3.1 FCFF Forecast', '3.3 Multiples Check'], '3.3 Multiples Check': ['0.0 Overview', '3.2 Valuation', '4.1 Sensitivity'], '4.1 Sensitivity': ['0.0 Overview', '3.3 Multiples Check', '4.2 Monte Carlo'], '4.2 Monte Carlo': ['0.0 Overview', '4.1 Sensitivity', '5.1 Checks'], '5.1 Checks': ['0.0 Overview', '4.2 Monte Carlo']} expected={'0.0 Overview': ['1.1 Statements'], '1.1 Statements': ['0.0 Overview', '1.2 Adjustments & Ratios'], '1.2 Adjustments & Ratios': ['0.0 Overview', '1.1 Statements', '2.1 WACC'], '2.1 WACC': ['0.0 Overview', '1.2 Adjustments & Ratios', '2.2 Bridge Inputs'], '2.2 Bridge Inputs': ['0.0 Overview', '2.1 WACC', '3.1 FCFF Forecast'], '3.1 FCFF Forecast': ['0.0 Overview', '2.2 Bridge Inputs', '3.2 Valuation'], '3.2 Valuation': ['0.0 Overview', '3.1 FCFF Forecast', '3.3 Multiples Check'], '3.3 Multiples Check': ['0.0 Overview', '3.2 Valuation', '4.1 Sensitivity'], '4.1 Sensitivity': ['0.0 Overview', '3.3 Multiples Check', '4.2 Monte Carlo'], '4.2 Monte Carlo': ['0.0 Overview', '4.1 Sensitivity', '5.1 Checks'], '5.1 Checks': ['0.0 Overview', '4.2 Monte Carlo']})
PASS  0.0 Overview links to all 10 other sheets  (actual=['1.1 Statements', '1.2 Adjustments & Ratios', '2.1 WACC', '2.2 Bridge Inputs', '3.1 FCFF Forecast', '3.2 Valuation', '3.3 Multiples Check', '4.1 Sensitivity', '4.2 Monte Carlo', '5.1 Checks'] expected=['1.1 Statements', '1.2 Adjustments & Ratios', '2.1 WACC', '2.2 Bridge Inputs', '3.1 FCFF Forecast', '3.2 Valuation', '3.3 Multiples Check', '4.1 Sensitivity', '4.2 Monte Carlo', '5.1 Checks'])
PASS  each band reads exactly 'GUIDE ▸ §<own id>'  (actual=[] expected=[])
PASS  each band id is in doc_map SECTIONS  (actual=[] expected=[])
PASS  0.0 Overview headline cell equals the report_headline sentence  (actual="De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value." expected="De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value.")
PASS  3.2 Valuation A3 equals the report_headline sentence  (actual="De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value." expected="De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value.")
PASS  row 2 of every sheet reads '<id>  <title>' (numeral and title as text)  (actual=[] expected=[])
PASS  0.0 names the guide and the note  (actual=True expected=True)
PASS  freeze panes directly below the first table header (1.1 also freezes A:B)  (actual=[] expected=[])
PASS  fitToWidth 1, fitToHeight 0, landscape when the used width exceeds 120 units  (actual=[] expected=[])
PASS  every cell font is Garamond or Gill Sans MT  (actual=[] expected=[])
PASS  every rgb colour in xl/styles.xml is in the ledger palette  (actual=[] expected=[])
PASS  every rgb colour in the chart XML is in the ledger palette  (actual=[] expected=[])
PASS  no hex colour literal in py/*.py outside ledger_style.py (step-8 files 06/07 are scoped out, see INFO)  (actual=[] expected=[])
INFO  hex literals still present in step-8 files (restyled in step 8): [('06_build_note.py', '8fb4d9'), ('06_build_note.py', 'c0392b'), ('06_build_note.py', '1f3b57'), ('07_process_guide.py', '1F3A5F'), ('07_process_guide.py', 'B0B8C4'), ('07_process_guide.py', 'EEF2F7')]
PASS  navy hexes 1F3864, 2F5597, EEF2F8 appear nowhere in py/  (actual=[] expected=[])
PASS  4.2 Monte Carlo: exactly 1 native BarChart  (actual=['BarChart'] expected=['BarChart'])
PASS  0.0 Overview: no chart  (actual=0 expected=0)
PASS  1.1 Statements: no chart  (actual=0 expected=0)
PASS  1.2 Adjustments & Ratios: no chart  (actual=0 expected=0)
PASS  2.1 WACC: no chart  (actual=0 expected=0)
PASS  2.2 Bridge Inputs: no chart  (actual=0 expected=0)
PASS  3.1 FCFF Forecast: no chart  (actual=0 expected=0)
PASS  3.2 Valuation: no chart  (actual=0 expected=0)
PASS  3.3 Multiples Check: no chart  (actual=0 expected=0)
PASS  4.1 Sensitivity: no chart  (actual=0 expected=0)
PASS  5.1 Checks: no chart  (actual=0 expected=0)
PASS  chart value reference points at 4.2 Monte Carlo  (actual=True expected=True)
PASS  chart values equal mc_histogram.count (54 bins, sum 10,000)  (actual=(True, 54, 10000) expected=(True, 54, 10000))
PASS  check_step05.py: number of c.* check calls not reduced vs HEAD  (actual=True expected=True)
PASS  check_step05.py keeps tolerance 'TOL = 1e-9' (1 at HEAD)  (actual=True expected=True)
PASS  check_step05.py keeps tolerance 'rel=1e-12' (2 at HEAD)  (actual=True expected=True)
PASS  check_step05.py keeps tolerance '< 1e-9' (2 at HEAD)  (actual=True expected=True)
PASS  check_step05.py: SHEETS is the 11 names  (actual=True expected=True)
PASS  check_step05.py: AST scan covers report_style.py, ledger_style.py and doc_map.py  (actual=True expected=True)
PASS  check_step01.py passes 128/128  (actual=(128, 128, 0) expected=(128, 128, 0))
PASS  check_step02.py passes 78/78  (actual=(78, 78, 0) expected=(78, 78, 0))
PASS  check_step03.py passes 148/148  (actual=(148, 148, 0) expected=(148, 148, 0))
PASS  check_step04.py passes 66/66  (actual=(66, 66, 0) expected=(66, 66, 0))
PASS  check_step06.py passes 17/17  (actual=(17, 17, 0) expected=(17, 17, 0))
PASS  check_step05.py passes with >= 86 checks, none failing  (actual=(True, True, 0) expected=(True, True, 0))
PASS  checks/fingerprint.py unchanged (git diff empty)  (actual=0 expected=0)
PASS  fresh run 1: the 24 fingerprints equal verify/fp_step06.txt  (actual=(0, 'PASS  fingerprints identical') expected=(0, 'PASS  fingerprints identical'))
PASS  fresh run 2: the 24 fingerprints equal verify/fp_step06.txt  (actual=(0, 'PASS  fingerprints identical') expected=(0, 'PASS  fingerprints identical'))
PASS  two fresh runs give identical workbooks (values, formats, styles, links, sizes, anchors)  (actual=True expected=True)
PASS  banned phrases (step-8 list) in all workbook strings: 0 hits  (actual=[] expected=[])
PASS  'interview' appears only on 0.0 Overview, at most 3 times  (actual=(True, []) expected=(True, []))
PASS  render_png.py ran without error  (actual=0 expected=0)
PASS  PNG pages written to verify/render/step07 (one per workbook page, at least one per sheet)  (actual=20 expected in [11, 200])
PASS  the rendered PDF shows the band 'GUIDE … §<id>' for every sheet, in sheet order  (actual=(True, True) expected=(True, True))
INFO  first page per sheet in the render: {'0.0': 1, '1.1': 1, '1.2': 1, '2.1': 1, '2.2': 1, '3.1': 1, '3.2': 1, '3.3': 1, '4.1': 1, '4.2': 1, '5.1': 1}

74/74 checks passed
```
Regression counts (run separately after the final rebuild): check_step01 128/128, 02 78/78, 03 148/148, 04 66/66, 05 93/93 (plan floor 86), 06 17/17.

check_step05 diff versus HEAD (summary; `git diff checks/check_step05.py` shows it all): SHEETS and a new `NEW` map; `wb["<old>"]` replaced through `NEW[...]`; value columns of the label sheets located by header name (`header_map`) instead of fixed column numbers; `Valuation!A1` replaced by `'3.2 Valuation'!A3` plus a new `'0.0 Overview'!A3` headline assertion; round-trip pool `SHEETS[1:-1]`; AST literal scan made a function and applied to `05_build_report.py`, `report_style.py`, `ledger_style.py`, `doc_map.py` (+3 checks); bridge check reads `2.2 Bridge Inputs` and also asserts the block is gone from 3.2. No tolerance, expected value or check was removed (check_step07 asserts that the number of `c.*` calls is not below HEAD and that the tolerance strings are kept).

## Spot-check cases for the human (3 to 5)
1. Typical headline value: baseline `Valuation!B5` = 56.47243714823831 (`0.00`) is now `'3.2 Valuation'!C7` = same value, same format. The row is labelled `value_per_share`, and B7 reads "Value per share". Shift: +2 rows (band, title) and +1 column (label).
2. Moved block: baseline `Valuation!A58:B58` = `bank_debt`, 227.043 (`#,##0`) is now `'2.2 Bridge Inputs'!A5:C5` = `bank_debt`, label "Bank debt", 227.043. The header "Bridge input" is at row 4 of 2.2 (baseline row 57). 3.2 keeps a pointer line (A59) linking to 2.2 where the block used to be.
3. Non-label sheet, negative value: baseline `Statements_5Y!H11` = -108.586 (`taxes`, FY2025) is now `'1.1 Statements'!H13`, same value (only +2 rows).
4. Edge, title exemption: baseline `Valuation!A1` (headline sentence) moves to `'3.2 Valuation'!A3` and is repeated on `'0.0 Overview'!A3`; both equal `report_headline` exactly. The old row-1 title texts of the other sheets are kept as row 3 with identical text and are exempt only in the check.
5. Edge, sensitivity base cell: baseline `Sensitivity!D6` = 56.47243714823831 (base WACC 6.52%, g 2.00%) is now `'4.1 Sensitivity'!D8`, a vermilion value in an ink outline. 4.1 has no label column. Its freeze row (A6) follows the grid header, which is row 5, and needed the grid header to be registered in the builder.

## Deviations, disputes, changes to earlier steps
- **Changes to earlier steps (all listed in the plan):** `checks/check_step05.py` (edits above), `py/06_build_note.py` and `checks/check_step06.py` (reference edits only), `py/05_build_report.py` and `py/report_style.py` (step-5 files, rebuilt). Re-run here: check_step05 93/93 and check_step06 17/17.
- **Hex-literal check is scoped.** Plan wording: "No hex colour literal in `py/*.py` outside `py/ledger_style.py`". `py/06_build_note.py` (3 chart colours) and `py/07_process_guide.py` (3 colours) still hold hex literals. The plan allows only sheet-reference edits to 06 in step 7, and both files are rebuilt in step 8. `check_step07.py` therefore applies the rule to every other `py/*.py` file and prints the 6 remaining literals as INFO. The navy hexes 1F3864, 2F5597, EEF2F8 appear nowhere in `py/` (checked on all files). Step 8 must clear the INFO list.
- **Baseline line count.** The plan says `xlsx_cells.txt` has 2,698 lines. The file has 2,699 non-empty cells and 2,698 newline characters (the original dump has no trailing newline). Equality with `verify/xlsx_dump_run1.txt` is line for line, so the baseline requirement is met.
- **Baseline note tokens.** `verify/baseline_amend2/note_tokens.txt` holds 61 tokens under the check_step06 scrub, not the 55 quoted in the step-8 plan. Step 8 should state which rule gives 55; step 7 does not use this file beyond creating it.
- **3.2 Valuation has a gap** of about 20 empty rows where the bridge block used to be (the strict cell mapping keeps everything else in place). A pointer line with a link to 2.2 sits at the top of the gap.
- **"Label" header words.** Header cells in column A of key tables (Ratio, Input, Item, ...) get "Label" in column B. `doc_map.LABEL_KEY_HEADERS` lists them, and `check_step07` treats them as header rows (they are not in `LABELS`).
- **Environment.** No Excel is available: the layout was verified through the LibreOffice render (PNGs). "▸" renders in LibreOffice through font fallback; Excel's fallback is untested.
- No CHECK DISPUTED.

## Polish pass (notes 3, 4, 5; approved under Amendment 2, "Post-verification decisions")
- **Note 3:** `py/05_build_report.py` `chart_fonts()` sets the 4.2 chart title to Garamond (14 pt) and the axis titles and tick labels to Gill Sans MT (9 pt), ink colour. Chart XML now holds only the typefaces Garamond (2) and Gill Sans MT (8). Chart data, categories, anchor and size are unchanged (54 bins, sum 10,000 still PASS). A named constant `CHART_PT_SCALE` was added to satisfy check_step05's numeric-literal rule.
- **Note 4:** `py/doc_map.py` gained `LABEL_OVERRIDES` and `label_for(sheet, key)`: on `3.2 Valuation`, `pct_vs_base` now reads "Price vs value, %" (B15). On `2.1 WACC` it stays "Difference vs base case, %". `LABELS` is unchanged.
- **Check edit (needs your eye, not a loosening):** `checks/check_step07.py` line 203 now compares column B to `DM.label_for(name, a)` instead of `DM.LABELS[a]`. Without it the label check would flag the approved relabel. The check is as strict as before (exact text match on every row).
- **Note 5:** the 05 docstring now says "eleven sheets", "3.2 Valuation sheet" and "2.1 WACC sheet"; the spot-check 5 text above now says the 4.1 grid header is row 5 (freeze pane A6).
- **Numbers:** no number changed. The "no baseline cell mismatch" check (2,691 compared, 0 mismatches), the 1,237 numeric cells and the 24 table fingerprints all still PASS. The only workbook text change is 3.2 B15 (a new label cell, not a baseline cell).
- **Rerun:** `run.py --fresh --through 7` rc 0. check_step07 74/74 (output above is unchanged except that the hex-literal INFO list is now empty, since step 8 has already cleared it). Regression: check_step01 128/128, 02 78/78, 03 148/148, 04 66/66, 05 93/93, 06 25/25 (check_step06 is 25 at the current HEAD, not changed here).

<!-- The Verifier appends its section below. -->
