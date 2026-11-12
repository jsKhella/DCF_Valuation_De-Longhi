# Step 09: Apply the final presentation polish to the three documents. Verdict: PASS WITH NOTES

## Summary for the human (one page max)
- Headline numbers: no analysis figure changed. All 2,985 non-empty cells of the step-8 workbook were compared with the new workbook (Executor) and again by me with my own row mapping and my own copy of the reword rules. Result: 8 text cells changed, each exactly equal to the reworded old text with identical digit runs; 0 numeric or style differences; numeric cells 1,237, formulas 0 ✓
- The §A.3 figures were recomputed from DuckDB: 79.6% / 24.6% / 0.98 / 0.52 (Executor) = 79.6% / 24.6% / 0.98 / 0.52 (Verifier: valuation.tv_share_of_ev; value_per_share / price - 1; price - mc_summary.p10; wacc - 6%) ✓
- Rows: 24 DuckDB tables unchanged (fingerprints equal `verify/fp_step06.txt`). Workbook non-empty cells went from 2,985 to 2,986 (+ the author cell 0.0 A20). Note paragraphs went from 19 to 20 (+ the author line). Guide number tokens went from 389 to 352. All differences are explained ✓
- Checks: check_step09 passes 94/94 and its output is identical to the pasted output. check_step07 passes 82/82 and check_step08 68/68; their edits do not weaken them. Earlier steps still pass: 128/78/148/66/93/25 ✓
- Reproducible: two clean `run.py --fresh` rebuilds gave identical fingerprints. The guide PDF, note docx, chart png and guide_numbers.json are byte-identical between the two rebuilds, and the xlsx differs only in `docProps/core.xml` ✓
- Banned-phrase scan (my own regex over the raw XML text of every xlsx and docx part, plus the PDF page text, outline and metadata): 0 hits ✓
- Notes: one documented deviation from the plan (a 6th reword rule, so 8 cells instead of 7). It is attributed to a human decision, but plan.md does not record it (finding 1). One stale header comment (finding 3). No SURPRISE or FRAGILE.
- Spot-checks: Executor cases 1-5 traced ✓. My own random cells (seed 20261110), '2.1 WACC'!D31 and '5.1 Checks'!D21, traced ✓
- Needs your decision: yes, only to confirm. Please confirm that you approved the 6th rule ("incentive plans" -> "incentive schemes", cell 3.1 G30), and have the orchestrator record that decision under Amendment 3 in plan/plan.md.

## Findings (notes, not failures)
| # | Level | File:line | Problem | Evidence |
|---|---|---|---|---|
| 1 | V2/V4 | plan/plan.md:430, 466, 551 | The plan fixes 5 rules and exactly 7 reworded cells, and says "No decisions were open". The code and checks use 6 rules and 8 cells (3.1 G30 added). The evidence pack and DQ log entry 32 attribute this to a human decision after a CHECK DISPUTED, but the decision is not recorded in plan.md. The Verifier cannot see human messages and so cannot confirm it. | `py/doc_map.py` TEXT_REWORDS has 6 entries. check_step07 F2 and check_step09 expect 8 cells. The DuckDB `forecast_assumptions.note` still reads "incentive plans", and the workbook G30 reads "incentive schemes". Digits are unchanged. Without the rule, G30 would be a banned-word hit ("plans"), so the change is needed to meet the 0-hit requirement. |
| 2 | V2 | checks/check_step09.py (note tokens) | The plan compares note tokens with `verify/baseline_amend2/note_tokens.txt` (61). The check uses the step-8 note's 58 tokens, plus a check that the 61 minus the 58 is exactly {25, 5, 95}, the step-8 rewording (DQ log 29). This is stricter than the plan, not weaker. | My independent check also finds that the step-8 and step-9 note number-token multisets are equal, and that the paragraphs equal the step-8 paragraphs with only the author line inserted at index 1. |
| 3 | V4 doc | py/05_build_report.py:14 | The header comment says "doc_map.reword() (5 fixed rules ...)". There are now 6 rules. | git diff of py/05_build_report.py and py/doc_map.py |

## Verifier details
**V1 Reproduce.**
- `run.py --fresh` ran twice; both runs returned rc 0, about 62 s each.
- `checks/fingerprint.py --save verify/fp_step09.txt <24 tables>` matched `verify/fp_step06.txt` exactly. `--compare` after rebuild 2 returned rc 0.
- Deliverables from rebuild 1 and rebuild 2 were compared: docx, pdf, png and json are byte-identical. In the xlsx, the zip member list is equal and only `docProps/core.xml` differs (dcterms:modified timestamp).
- Regression results:
  - check_step01: 128/128
  - check_step02: 78/78
  - check_step03: 148/148
  - check_step04: 66/66
  - check_step05: 93/93
  - check_step06: 25/25
  - check_step07: 82/82
  - check_step08: 68/68
  - check_step09: 94/94
- After check_step09's own rebuilds, the final report files are identical to my rebuild-1 copies.

**V2 Check audit.**
- Every plan acceptance item for step 9 has a check in check_step09, or (cmap, contents links, token provenance) in check_step08, which still runs.
- check_step07 diff:
  - F1 maps old Valuation rows r > r_end to r + 2 - (r_end - r_h).
  - F2 compares against `reword(old)`, with an exact list of 8 cells, a rule-usage check and a digit-run check.
  - F3 uses `checks/banned.py`.
  - F4 adds 5 layout assertions.
  - No tolerance changed. The count rose from 74 to 82.
- check_step08 diff:
  - E1 uses the shared list with INTERVIEW_MAX = 0.
  - E2 drops "section-3 rows present" and adds the inverse plus the A.3 figures check, as the plan requires.
  - E3 checks for "2026-11-09" instead of "Gate 2".
  - E4 adds note tables, headers and footers.
  - E5 adds the §6 sentence check.
  - The count is 68 (>= 66).
- `checks/banned.py` contains every listed term, with a word-bounded and case-insensitive match, and lowercase "us" handled separately.
- check_step05, check_step06, run.py and fingerprint.py show no diff.
- The pasted check_step09 output is line-identical to my run.
- `verify/baseline_step09/SHA256SUMS.txt`: `sha256sum -c` gives 5/5 OK. Each file is byte-identical to `git show 44d683d:<path>`, checked independently in my script.

**V3 Blind recomputation** (`verify/verify_step09.py`, output in `verify/verify_step09_output.txt`, 43/43 OK).
- Method: the script does not import doc_map or any check helper. It uses openpyxl cell-by-cell comparison of the step-8 workbook against the new one, with my own mapping (3.2 row 79 -> 61). It compares value, type, number format, font, fill, alignment, borders and hyperlinks. It checks merges under the flag move, row height (21.0 -> 21.0), new cells (only 0.0 A20), and that the 3.2 fills on rows 1-59 are unchanged.
- Banned scan: run over the text nodes of every XML part of the xlsx and docx (cells, comments, headers and footers, core and app properties, charts) and the sheet names. For the PDF it covers page text (pdfplumber), outline titles and Info (pdfminer).
- Results:
  - The PDF /Author is "Mina Khella" and the outline equals the step-8 outline (22 entries).
  - The guide has 12 pages, all A4.
  - "Reconciliation and checks" occurs 4 times.
  - The §6 sentence is verbatim and the old sentence is absent. "Notes carried" and "Smell test" are gone.
- A.3 figures recomputed: tv 0.79647 -> 79.6%; 56.4724 / 45.32 - 1 = 24.6%; 45.32 - 44.3414 = 0.98; (0.065208 - 0.06) x 100 = 0.52 pp. The 6% bound is parsed from the brief line "WACC outside 6-10%" (`WACC_LOW` in py/07_process_guide.py), not typed.

**V4 Code review.**
- `target()` in py/05_build_report.py moves only rows > r_end. Old row 76 is blank, so only the flag moves.
- `reword()` is applied only to copied string cells. DuckDB is untouched (`forecast_assumptions.note` still holds the original text).
- The author cell clears the borders on row 20 (this explains the Executor's "hairline" fix).
- The note author paragraph is inserted directly after the title. core author, last_modified_by and comments are set.
- Guide: §4.1's paragraph is merged into §4.2. In §5, every figure goes through FT() with the evidence anchors, and no step-5 to step-9 PASS counts are cited.
- No numeric literal was added to the analysis.
- DQ log entry 32 is present. The documentation is accurate except finding 3.

**V5 Smell.** This step is presentation only, and no figure moved. The guide token count fell from 389 to 352, consistent with deleting the 12-item notes list and adding the §5 table and the A.3 figures.

**V6 Sensitivity.** Not applicable (no judgment threshold).

**V7 Spot-checks.**
1. The flag moved: old A79 merged A79:H79 is now A61 merged A61:H61, with identical style and height, and row 60 empty. Pointer A59 links to `'2.2 Bridge Inputs'!A1` ✓
2. 2.2 H7 now reads "The figure quoted as 'NFP table 94.0'..." with digit runs equal ✓
3. 3.1 G30: DuckDB says "incentive plans" and the workbook says "incentive schemes" ✓
4. The A.3 figures are recomputed as above. The guide_numbers.json entries 344, 346, 348 and 350 are db-kind, and 345, 347 and 351 quote the brief anchors ✓
5. The author line appears in 0.0 A20 (Gill Sans MT 9 pt grey, no link), in note paragraph 2 and on the guide cover. "Università" is visible in the renders (guide p.1, note p.1, workbook p.1) ✓
6. My own random cells (seed 20261110):
   - '2.1 WACC'!D31 = 0.99170 = `wacc.beta_l` (beta_sensitivity case) ✓
   - '5.1 Checks'!D21 = 998.448 = `valuation` cash ✓
   - Both are unchanged against the step-8 workbook.

**Visual** (inspected): guide p.1 (author block), p.3 (6-stage method map, no role names), p.9 (§5 table fits, no overlap), p.11 to 12 (A.2 "Plausibility bound", A.3 with the four figures), workbook p.1 (author line small and grey) and p.13 (3.2: pointer, one empty row, flag; key rows still vermilion), note p.1 (author line under the title). No defects found.
---
(Executor's section follows)

# Step 09: Apply the final presentation polish to the three documents. Status: AWAITING VERIFICATION

## What was done
- **Baseline first.** `verify/baseline_step09/` holds the HEAD 44d683d xlsx, docx, pdf, chart png and `guide_numbers.json`, with `SHA256SUMS.txt`, the cell dump `xlsx_cells.txt` and the note paragraphs `note_paras.txt`. Each file is byte-identical to `git show 44d683d:<path>`.
- **Workbook** (`py/doc_map.py`, `py/05_build_report.py`): the rows of 3.2 below the moved bridge block close up (the flag moves from A79 to A61, merged A61:H61, row 60 empty, max_row 61); the 6 `TEXT_REWORDS` rules are applied to text cells at build time (8 cells change, DuckDB untouched); `0.0 Overview!A20` holds the author line (Gill Sans MT, 9 pt, grey, no link); the xlsx creator and last-modified-by are the author name.
- **Note** (`py/06_build_note.py`): one Normal-style author paragraph directly under the title (Gill Sans MT, 9 pt, grey, plain text); core author and last-modified-by are the author name, comments are empty.
- **Guide** (`py/07_process_guide.py`): author block on the cover; the §0.0 method map rewritten impersonally (6 stages); "Plausibility bounds fixed in advance"; one "Reconciliation and checks" paragraph in §1.1, §2.1, §3.1 and §4.2 (§4.1's merged into §4.2); §1.2 "accepted on 2026-11-09"; §3.2 "Plausibility bounds fixed in advance:"; a new §5 stage table; the "Notes carried to the final review" list deleted; the §6 sentence replaced; glossary "Plausibility bound"; §A.3 item 4 rewritten with the 4 figures (79.6%, 24.6%, 0.98, 0.52) and DuckDB / brief provenance. The guide has 352 number tokens (389 before; the notes list is gone, the §5 table and A.3 figures are new).
- **Checks.** New `checks/check_step09.py` and `checks/banned.py` (the extended banned list, shared). Edits to `checks/check_step07.py` (F1-F4) and `checks/check_step08.py` (E1-E5) are listed below.

## Files
| File | Purpose |
|---|---|
| `checks/check_step09.py` | New. 94 checks: baseline snapshot, workbook diff against the step-8 workbook, author line, glyphs, extended banned scan on every text surface, guide structure and content, note, two fresh rebuilds, regression counts of check_step01-08, renders |
| `checks/banned.py` | New. The extended banned list (word-bounded, case-insensitive; lowercase "us") used by check_step07, 08 and 09 |
| `py/doc_map.py` | `AUTHOR_NAME/EMAIL/AFFILIATION/LINE`, `TEXT_REWORDS`, `reword()` (strings only, no digit) |
| `py/05_build_report.py` | 3.2 gap rule in `target()`, `reword()` on copied strings, author line A20, creator and lastModifiedBy |
| `py/06_build_note.py` | Author paragraph, core properties |
| `py/07_process_guide.py` | Guide rewording and the new §5 / §A.3 content, PDF author |
| `checks/check_step07.py`, `checks/check_step08.py` | Edits F1-F4 and E1-E5 (below) |
| `verify/baseline_step09/` | Baseline snapshot (HEAD 44d683d), never modified |
| `verify/render/step09/` | PNGs of the guide (12 pages), the note (2 pages) and the workbook (20 pages) |
| `evidence/data_quality_log.md` | Entry 32 added |
| `report/*.xlsx`, `*.docx`, `*.pdf`, `note_chart.png`, `report/build/guide_numbers.json` | Regenerated deliverables |

`run.py`, `checks/check_step05.py`, `checks/check_step06.py` and `checks/fingerprint.py` are unchanged (git diff empty).

## Row flow
The step writes no DuckDB table; the 24 table fingerprints equal `verify/fp_step06.txt` after each of two fresh rebuilds.

| Table / file | Rows in | Rows out | Why the difference |
|---|---|---|---|
| 24 DuckDB tables | 24 | 24 | unchanged (fingerprints identical) |
| Workbook non-empty cells | 2,985 (step-8 dump) | 2,986 | +1: the new author cell 0.0 A20. The flag moved (A79 to A61), 7 texts reworded, 0 other value changes |
| Guide number tokens | 389 | 352 | notes list deleted, "What the Verifier checked" sentences merged, §5 table and §A.3 figures added |
| Note paragraphs | 19 | 20 | +1: the author paragraph |

## Check results
Full, unedited output of `python checks/check_step09.py` (run on the final code; it rebuilds everything from `data/raw/` twice first):

```
PASS  baseline DeLonghi_DCF_Valuation.xlsx is byte-identical to git show 44d683d:report/DeLonghi_DCF_Valuation.xlsx  (actual=True expected=True)
PASS  baseline DeLonghi_DCF_Valuation_note.docx is byte-identical to git show 44d683d:report/DeLonghi_DCF_Valuation_note.docx  (actual=True expected=True)
PASS  baseline DeLonghi_DCF_process_guide.pdf is byte-identical to git show 44d683d:report/DeLonghi_DCF_process_guide.pdf  (actual=True expected=True)
PASS  baseline note_chart.png is byte-identical to git show 44d683d:report/note_chart.png  (actual=True expected=True)
PASS  baseline guide_numbers.json is byte-identical to git show 44d683d:report/build/guide_numbers.json  (actual=True expected=True)
PASS  SHA256SUMS.txt matches the 5 snapshot files  (actual=(5, True) expected=(5, True))
PASS  baseline xlsx_cells.txt equals a fresh dump of the baseline workbook  (actual=True expected=True)
PASS  baseline note_paras.txt equals the paragraphs of the baseline docx  (actual=["De'Longhi: DCF investment note", "De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value.", 'Figures above: [3.2].', 'Thesis', "The discounted cash flow values De'Longhi at EUR 56.47 per share, against a market price of EUR 45.32 on 6 November 2026 [3.2]. Enterprise value is EUR 8,033 m, of which the terminal value is 79.6% [3.2]. The company holds net cash: cash of EUR 998 m and cash-like financial assets of EUR 305 m exceed bank debt, other financial payables and leases [3.2]. After deducting those liabilities, the 2026 distributions of EUR 156 m and minorities, equity value is EUR 8,448 m on 149.6 m diluted shares [3.2]. The shares therefore look moderately cheap, and the size of the gap depends mainly on the discount rate.", 'Main assumptions', 'Revenue grows 5.0% in FY2026E (midpoint of the mid-single-digit guidance) and fades linearly towards the terminal growth rate g of 2.00% [3.1] [3.2].', 'The adjusted EBIT margin starts at 12.8% in FY2026E (derived from the adjusted EBITDA guidance of EUR 680 m) and fades to 12.2% by FY2030E, the average of FY2024 and FY2025 [3.1]. The forecast tax rate is 24.1% [3.1].', 'Cost of equity is 6.82%: risk-free rate 4.36%, relevered beta 0.420 (unlevered Damodaran Europe Furniture/Home Furnishings beta 0.397), mature equity risk premium 4.23% plus an Italy default spread of 1.62% [2.1]. After-tax cost of debt is 2.77% at a debt weight of 7.3% [2.1]. The resulting WACC is 6.52% [3.2].', 'Valuation range', 'A Monte Carlo of growth, margin and WACC gives an 80% range of EUR 44.34 to EUR 74.08 per share, with a median of EUR 56.36 and a band from the fifth to the ninety-fifth percentile of EUR 41.61 to EUR 81.09 [3.2] [4.2]. The market price sits at the 12th percentile of the simulated values [3.2]. An exit-multiple cross-check gives EUR 48.28 per share at the Damodaran Europe multiple of 9.5x and EUR 52.57 at the Global multiple of 10.6x, both below the Gordon-growth value [3.2].', '', 'Risks', 'Beta dominates. The base case uses the low Europe industry beta of 0.397 [2.1]. With the Global Furniture/Home Furnishings beta of 0.938 the WACC is 9.62% and value falls to EUR 35.60 per share (-37.0%), below the market price [2.1].', "Minorities at book value are deducted in the equity bridge. This is a simplification that likely understates the minorities' share of value (book value EUR 198 m) [3.2].", 'Italy risk double counting: the risk-free rate is an Italian government yield and the cost of equity also adds an Italy default spread, which raises the discount rate and lowers value. This is a stated limitation.', 'Terminal value is 79.6% of enterprise value, so small changes in WACC or g move the answer materially [3.2]. The FY2026E margin of 12.8% sits above the five-year average, and the forecast fades it [3.1].', 'Conclusion vs market price', 'At EUR 45.32 the market price is 19.7% below the base-case value of EUR 56.47, but it lies inside the 80% range (EUR 44.34 to EUR 74.08) and only just above its lower end [3.2]. The base case is therefore a moderately positive signal, not a clear mispricing, and it relies on a low-beta discount rate. With the higher Global beta the value is below the price. The shares can be read as fairly valued to moderately undervalued.'] expected=["De'Longhi: DCF investment note", "De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value.", 'Figures above: [3.2].', 'Thesis', "The discounted cash flow values De'Longhi at EUR 56.47 per share, against a market price of EUR 45.32 on 6 November 2026 [3.2]. Enterprise value is EUR 8,033 m, of which the terminal value is 79.6% [3.2]. The company holds net cash: cash of EUR 998 m and cash-like financial assets of EUR 305 m exceed bank debt, other financial payables and leases [3.2]. After deducting those liabilities, the 2026 distributions of EUR 156 m and minorities, equity value is EUR 8,448 m on 149.6 m diluted shares [3.2]. The shares therefore look moderately cheap, and the size of the gap depends mainly on the discount rate.", 'Main assumptions', 'Revenue grows 5.0% in FY2026E (midpoint of the mid-single-digit guidance) and fades linearly towards the terminal growth rate g of 2.00% [3.1] [3.2].', 'The adjusted EBIT margin starts at 12.8% in FY2026E (derived from the adjusted EBITDA guidance of EUR 680 m) and fades to 12.2% by FY2030E, the average of FY2024 and FY2025 [3.1]. The forecast tax rate is 24.1% [3.1].', 'Cost of equity is 6.82%: risk-free rate 4.36%, relevered beta 0.420 (unlevered Damodaran Europe Furniture/Home Furnishings beta 0.397), mature equity risk premium 4.23% plus an Italy default spread of 1.62% [2.1]. After-tax cost of debt is 2.77% at a debt weight of 7.3% [2.1]. The resulting WACC is 6.52% [3.2].', 'Valuation range', 'A Monte Carlo of growth, margin and WACC gives an 80% range of EUR 44.34 to EUR 74.08 per share, with a median of EUR 56.36 and a band from the fifth to the ninety-fifth percentile of EUR 41.61 to EUR 81.09 [3.2] [4.2]. The market price sits at the 12th percentile of the simulated values [3.2]. An exit-multiple cross-check gives EUR 48.28 per share at the Damodaran Europe multiple of 9.5x and EUR 52.57 at the Global multiple of 10.6x, both below the Gordon-growth value [3.2].', '', 'Risks', 'Beta dominates. The base case uses the low Europe industry beta of 0.397 [2.1]. With the Global Furniture/Home Furnishings beta of 0.938 the WACC is 9.62% and value falls to EUR 35.60 per share (-37.0%), below the market price [2.1].', "Minorities at book value are deducted in the equity bridge. This is a simplification that likely understates the minorities' share of value (book value EUR 198 m) [3.2].", 'Italy risk double counting: the risk-free rate is an Italian government yield and the cost of equity also adds an Italy default spread, which raises the discount rate and lowers value. This is a stated limitation.', 'Terminal value is 79.6% of enterprise value, so small changes in WACC or g move the answer materially [3.2]. The FY2026E margin of 12.8% sits above the five-year average, and the forecast fades it [3.1].', 'Conclusion vs market price', 'At EUR 45.32 the market price is 19.7% below the base-case value of EUR 56.47, but it lies inside the 80% range (EUR 44.34 to EUR 74.08) and only just above its lower end [3.2]. The base case is therefore a moderately positive signal, not a clear mispricing, and it relies on a low-beta discount rate. With the higher Global beta the value is below the price. The shares can be read as fairly valued to moderately undervalued.'])
PASS  workbook: same 11 sheets in the same order as the step-8 workbook  (actual=['0.0 Overview', '1.1 Statements', '1.2 Adjustments & Ratios', '2.1 WACC', '2.2 Bridge Inputs', '3.1 FCFF Forecast', '3.2 Valuation', '3.3 Multiples Check', '4.1 Sensitivity', '4.2 Monte Carlo', '5.1 Checks'] expected=['0.0 Overview', '1.1 Statements', '1.2 Adjustments & Ratios', '2.1 WACC', '2.2 Bridge Inputs', '3.1 FCFF Forecast', '3.2 Valuation', '3.3 Multiples Check', '4.1 Sensitivity', '4.2 Monte Carlo', '5.1 Checks'])
PASS  workbook diff: the only value differences are the 8 reworded cells  (actual=['2.2 Bridge Inputs!F13', '2.2 Bridge Inputs!F17', '2.2 Bridge Inputs!H17', '2.2 Bridge Inputs!H7', '3.1 FCFF Forecast!F26', '3.1 FCFF Forecast!F27', '3.1 FCFF Forecast!G30', '3.2 Valuation!H46'] expected=['2.2 Bridge Inputs!F13', '2.2 Bridge Inputs!F17', '2.2 Bridge Inputs!H17', '2.2 Bridge Inputs!H7', '3.1 FCFF Forecast!F26', '3.1 FCFF Forecast!F27', '3.1 FCFF Forecast!G30', '3.2 Valuation!H46'])
PASS  workbook diff: no style difference on any baseline cell (3.2 A79 compared with A61)  (actual=[] expected=[])
PASS  workbook diff: no hyperlink difference  (actual=[] expected=[])
PASS  workbook diff: no content below the old used range other than the moved flag and the author cell  (actual=[] expected=[])
PASS  workbook diff: merges equal, the flag merge A79:H79 became A61:H61  (actual={} expected={})
PASS  workbook diff: row heights (flag row moved), column widths and freeze panes equal  (actual=[] expected=[])
PASS  3.2: max_row 61, row 60 empty, pointer at A59 linking to 2.2, flag text in A61  (actual=(61, [None, None, None, None, None, None, None, None], "'2.2 Bridge Inputs'!A1", True) expected=(61, [None, None, None, None, None, None, None, None], "'2.2 Bridge Inputs'!A1", True))
PASS  3.2: no cell below row 61  (actual=[] expected=[])
PASS  numeric cells: 1,237 on 1.1-5.1, 0 on 0.0  (actual=(1237, 0) expected=(1237, 0))
PASS  formulas: 0  (actual=0 expected=0)
PASS  5.1 Checks: 65 rows, all PASS, identical to the step-8 workbook  (actual=(65, True, True) expected=(65, True, True))
PASS  navigation: every hyperlink resolves to an existing sheet and a cell in its used range  (actual=[] expected=[])
PASS  navigation: 0.0 links to the 10 other sheets  (actual=['1.1 Statements', '1.2 Adjustments & Ratios', '2.1 WACC', '2.2 Bridge Inputs', '3.1 FCFF Forecast', '3.2 Valuation', '3.3 Multiples Check', '4.1 Sensitivity', '4.2 Monte Carlo', '5.1 Checks'] expected=['1.1 Statements', '1.2 Adjustments & Ratios', '2.1 WACC', '2.2 Bridge Inputs', '3.1 FCFF Forecast', '3.2 Valuation', '3.3 Multiples Check', '4.1 Sensitivity', '4.2 Monte Carlo', '5.1 Checks'])
INFO  package members that differ from the step-8 workbook: ['docProps/core.xml', 'xl/styles.xml', 'xl/worksheets/sheet1.xml', 'xl/worksheets/sheet10.xml', 'xl/worksheets/sheet11.xml', 'xl/worksheets/sheet2.xml', 'xl/worksheets/sheet3.xml', 'xl/worksheets/sheet4.xml', 'xl/worksheets/sheet5.xml', 'xl/worksheets/sheet6.xml', 'xl/worksheets/sheet7.xml', 'xl/worksheets/sheet8.xml', 'xl/worksheets/sheet9.xml']
PASS  doc_map.TEXT_REWORDS holds exactly the 5 plan rules plus the human-approved sixth  (actual=[("The plan's 'NFP table", "The figure quoted as 'NFP table"), ('(The plan cites', '(An earlier reference cites'), ('Performance Shares Plan rights', 'performance-share rights'), ("the plan's estimate", 'an assumption fixed in advance'), (', plan/plan.md', ', fixed in advance'), ('incentive plans', 'incentive schemes')] expected=[("The plan's 'NFP table", "The figure quoted as 'NFP table"), ('(The plan cites', '(An earlier reference cites'), ('Performance Shares Plan rights', 'performance-share rights'), ("the plan's estimate", 'an assumption fixed in advance'), (', plan/plan.md', ', fixed in advance'), ('incentive plans', 'incentive schemes')])
PASS  reworded cells: new text = old text with the ordered rules applied (8 cells)  (actual=[] expected=[])
PASS  reworded cells: the sequence of digit runs is identical to the old text  (actual=[] expected=[])
PASS  each of the 6 rules is used at least once  (actual=[] expected=[])
PASS  reword rules contain no digit and no banned word  (actual=[] expected=[])
PASS  author: '0.0 Overview'!A20 equals AUTHOR_LINE exactly  (actual='Mina Khella · mina.khellas@gmail.com · Undergraduate in Statistics and Economics, Università degli studi di Milano Bicocca' expected='Mina Khella · mina.khellas@gmail.com · Undergraduate in Statistics and Economics, Università degli studi di Milano Bicocca')
PASS  author: A20 is Gill Sans MT, small, grey, with no hyperlink  (actual=('Gill Sans MT', 9.0, '6B6B6B', None) expected=('Gill Sans MT', 9, '6B6B6B', None))
PASS  author: doc_map constants hold the exact strings  (actual=('Mina Khella', 'mina.khellas@gmail.com', 'Undergraduate in Statistics and Economics, Università degli studi di Milano Bicocca', 'Mina Khella · mina.khellas@gmail.com · Undergraduate in Statistics and Economics, Università degli studi di Milano Bicocca') expected=('Mina Khella', 'mina.khellas@gmail.com', 'Undergraduate in Statistics and Economics, Università degli studi di Milano Bicocca', 'Mina Khella · mina.khellas@gmail.com · Undergraduate in Statistics and Economics, Università degli studi di Milano Bicocca'))
PASS  author: the note paragraph directly after the title is AUTHOR_LINE (Normal style)  (actual=('Mina Khella · mina.khellas@gmail.com · Undergraduate in Statistics and Economics, Università degli studi di Milano Bicocca', 'Normal') expected=('Mina Khella · mina.khellas@gmail.com · Undergraduate in Statistics and Economics, Università degli studi di Milano Bicocca', 'Normal'))
PASS  author: note runs are Gill Sans MT, small, grey, no hyperlink  (actual=({'Gill Sans MT'}, {9.0}, {'6B6B6B'}, 0) expected=({'Gill Sans MT'}, {9.0}, {'6B6B6B'}, 0))
PASS  author: guide page 1 holds the name, the e-mail and the affiliation ('Università' intact)  (actual=[] expected=[])
PASS  author: PDF /Author, xlsx creator and docx core author equal AUTHOR_NAME  (actual=('Mina Khella', 'Mina Khella', 'Mina Khella') expected=('Mina Khella', 'Mina Khella', 'Mina Khella'))
PASS  author: no document property equals or contains CURIOSITY  (actual=[] expected=[])
PASS  author: docx comments property is empty  (actual='' expected='')
PASS  glyphs: 0 U+FFFD in the workbook, the note and the guide  (actual={'xlsx': 0, 'docx': 0, 'pdf': 0} expected={'xlsx': 0, 'docx': 0, 'pdf': 0})
PASS  glyphs: 'Università' present in the three documents  (actual=(True, True, True) expected=(True, True, True))
PASS  banned phrases in guide pages: 0 hits  (actual=[] expected=[])
PASS  banned phrases in guide metadata: 0 hits  (actual=[] expected=[])
PASS  banned phrases in guide outline: 0 hits  (actual=[] expected=[])
PASS  banned phrases in note body: 0 hits  (actual=[] expected=[])
PASS  banned phrases in note header/footer: 0 hits  (actual=[] expected=[])
PASS  banned phrases in note properties: 0 hits  (actual=[] expected=[])
PASS  banned phrases in xlsx cells: 0 hits  (actual=[] expected=[])
PASS  banned phrases in xlsx comments: 0 hits  (actual=[] expected=[])
PASS  banned phrases in xlsx header/footer: 0 hits  (actual=[] expected=[])
PASS  banned phrases in xlsx sheet names: 0 hits  (actual=[] expected=[])
PASS  banned phrases in xlsx properties: 0 hits  (actual=[] expected=[])
PASS  banned phrases in xlsx charts: 0 hits  (actual=[] expected=[])
PASS  guide: at most 20 pages  (actual=12 expected in [1, 20])
PASS  guide: every page is A4  (actual=[] expected=[])
PASS  guide: outline identical to the step-8 PDF (22 ids, same titles, same order)  (actual=(True, 22) expected=(True, 22))
PASS  guide: outline ids equal doc_map SECTIONS  (actual=['0.0', '0', '1', '1.1', '1.2', '2', '2.1', '2.2', '3', '3.1', '3.2', '3.3', '4', '4.1', '4.2', '5', '5.1', '6', 'A', 'A.1', 'A.2', 'A.3'] expected=['0.0', '0', '1', '1.1', '1.2', '2', '2.1', '2.2', '3', '3.1', '3.2', '3.3', '4', '4.1', '4.2', '5', '5.1', '6', 'A', 'A.1', 'A.2', 'A.3'])
PASS  guide: every section heading found once in the body  (actual=[] expected=[])
PASS  guide: every section opens with a WORKBOOK line naming existing sheets  (actual=[] expected=[])
PASS  guide: every sheet band id is a guide heading  (actual=[] expected=[])
PASS  guide: 'Reconciliation and checks' occurs exactly once in 1.1, 2.1, 3.1, 4.2 and in no other section 1-4  (actual={} expected={})
PASS  guide: section 5 has a row for stages 0-4, workbook, note and rebuild  (actual=[] expected=[])
PASS  guide: none of the 12 final_review section-3 explanations appears in sections 1-5 (12 rows read)  (actual=(12, []) expected=(12, []))
PASS  guide: A.3 still contains all 6 limitation phrases  (actual=[] expected=[])
PASS  guide: A.3 contains the figures 79.6%, 24.6%, 0.98 and 0.52  (actual=[] expected=[])
PASS  guide: the four A.3 figures each have a provenance entry (db or file) inside the A.3 token range  (actual=[] expected=[])
PASS  guide: section 6 holds the new sentence verbatim and not the old one  (actual=(True, False) expected=(True, False))
PASS  guide: PDF number tokens equal guide_numbers.json tokens in order  (actual=(True, 352, 352) expected=(True, 352, 352))
INFO  guide number tokens: 352 (step-8 baseline: 389)
PASS  guide 0.0: method stages Definition, Checks first, Analysis, Independent recomputation (the label wraps in its table cell), Rebuild, Approval; 'Plausibility bounds fixed in advance'  (actual=[] expected=[])
PASS  guide A.2: glossary entry 'Plausibility bound' replaces 'Smell test'  (actual=(True, False) expected=(True, False))
PASS  guide 1.2: states '1 decimal', 'accepted' and '2026-11-09'  (actual=[] expected=[])
PASS  note tokens: multiset equals the step-8 note's tokens (58 = the 61 of baseline_amend2 less the 3 step-8 rewordings)  (actual=(True, 58, ['25', '5', '95']) expected=(True, 58, ['25', '5', '95']))
PASS  note paragraphs equal note_paras.txt except the one inserted author paragraph  (actual=["De'Longhi: DCF investment note", "De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value.", 'Figures above: [3.2].', 'Thesis', "The discounted cash flow values De'Longhi at EUR 56.47 per share, against a market price of EUR 45.32 on 6 November 2026 [3.2]. Enterprise value is EUR 8,033 m, of which the terminal value is 79.6% [3.2]. The company holds net cash: cash of EUR 998 m and cash-like financial assets of EUR 305 m exceed bank debt, other financial payables and leases [3.2]. After deducting those liabilities, the 2026 distributions of EUR 156 m and minorities, equity value is EUR 8,448 m on 149.6 m diluted shares [3.2]. The shares therefore look moderately cheap, and the size of the gap depends mainly on the discount rate.", 'Main assumptions', 'Revenue grows 5.0% in FY2026E (midpoint of the mid-single-digit guidance) and fades linearly towards the terminal growth rate g of 2.00% [3.1] [3.2].', 'The adjusted EBIT margin starts at 12.8% in FY2026E (derived from the adjusted EBITDA guidance of EUR 680 m) and fades to 12.2% by FY2030E, the average of FY2024 and FY2025 [3.1]. The forecast tax rate is 24.1% [3.1].', 'Cost of equity is 6.82%: risk-free rate 4.36%, relevered beta 0.420 (unlevered Damodaran Europe Furniture/Home Furnishings beta 0.397), mature equity risk premium 4.23% plus an Italy default spread of 1.62% [2.1]. After-tax cost of debt is 2.77% at a debt weight of 7.3% [2.1]. The resulting WACC is 6.52% [3.2].', 'Valuation range', 'A Monte Carlo of growth, margin and WACC gives an 80% range of EUR 44.34 to EUR 74.08 per share, with a median of EUR 56.36 and a band from the fifth to the ninety-fifth percentile of EUR 41.61 to EUR 81.09 [3.2] [4.2]. The market price sits at the 12th percentile of the simulated values [3.2]. An exit-multiple cross-check gives EUR 48.28 per share at the Damodaran Europe multiple of 9.5x and EUR 52.57 at the Global multiple of 10.6x, both below the Gordon-growth value [3.2].', '', 'Risks', 'Beta dominates. The base case uses the low Europe industry beta of 0.397 [2.1]. With the Global Furniture/Home Furnishings beta of 0.938 the WACC is 9.62% and value falls to EUR 35.60 per share (-37.0%), below the market price [2.1].', "Minorities at book value are deducted in the equity bridge. This is a simplification that likely understates the minorities' share of value (book value EUR 198 m) [3.2].", 'Italy risk double counting: the risk-free rate is an Italian government yield and the cost of equity also adds an Italy default spread, which raises the discount rate and lowers value. This is a stated limitation.', 'Terminal value is 79.6% of enterprise value, so small changes in WACC or g move the answer materially [3.2]. The FY2026E margin of 12.8% sits above the five-year average, and the forecast fades it [3.1].', 'Conclusion vs market price', 'At EUR 45.32 the market price is 19.7% below the base-case value of EUR 56.47, but it lies inside the 80% range (EUR 44.34 to EUR 74.08) and only just above its lower end [3.2]. The base case is therefore a moderately positive signal, not a clear mispricing, and it relies on a low-beta discount rate. With the higher Global beta the value is below the price. The shares can be read as fairly valued to moderately undervalued.'] expected=["De'Longhi: DCF investment note", "De'Longhi is worth EUR 56.47 per share (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is EUR 44.34 to EUR 74.08; the market price of EUR 45.32 sits at the 12th percentile, i.e. 19.7% below the base-case value.", 'Figures above: [3.2].', 'Thesis', "The discounted cash flow values De'Longhi at EUR 56.47 per share, against a market price of EUR 45.32 on 6 November 2026 [3.2]. Enterprise value is EUR 8,033 m, of which the terminal value is 79.6% [3.2]. The company holds net cash: cash of EUR 998 m and cash-like financial assets of EUR 305 m exceed bank debt, other financial payables and leases [3.2]. After deducting those liabilities, the 2026 distributions of EUR 156 m and minorities, equity value is EUR 8,448 m on 149.6 m diluted shares [3.2]. The shares therefore look moderately cheap, and the size of the gap depends mainly on the discount rate.", 'Main assumptions', 'Revenue grows 5.0% in FY2026E (midpoint of the mid-single-digit guidance) and fades linearly towards the terminal growth rate g of 2.00% [3.1] [3.2].', 'The adjusted EBIT margin starts at 12.8% in FY2026E (derived from the adjusted EBITDA guidance of EUR 680 m) and fades to 12.2% by FY2030E, the average of FY2024 and FY2025 [3.1]. The forecast tax rate is 24.1% [3.1].', 'Cost of equity is 6.82%: risk-free rate 4.36%, relevered beta 0.420 (unlevered Damodaran Europe Furniture/Home Furnishings beta 0.397), mature equity risk premium 4.23% plus an Italy default spread of 1.62% [2.1]. After-tax cost of debt is 2.77% at a debt weight of 7.3% [2.1]. The resulting WACC is 6.52% [3.2].', 'Valuation range', 'A Monte Carlo of growth, margin and WACC gives an 80% range of EUR 44.34 to EUR 74.08 per share, with a median of EUR 56.36 and a band from the fifth to the ninety-fifth percentile of EUR 41.61 to EUR 81.09 [3.2] [4.2]. The market price sits at the 12th percentile of the simulated values [3.2]. An exit-multiple cross-check gives EUR 48.28 per share at the Damodaran Europe multiple of 9.5x and EUR 52.57 at the Global multiple of 10.6x, both below the Gordon-growth value [3.2].', '', 'Risks', 'Beta dominates. The base case uses the low Europe industry beta of 0.397 [2.1]. With the Global Furniture/Home Furnishings beta of 0.938 the WACC is 9.62% and value falls to EUR 35.60 per share (-37.0%), below the market price [2.1].', "Minorities at book value are deducted in the equity bridge. This is a simplification that likely understates the minorities' share of value (book value EUR 198 m) [3.2].", 'Italy risk double counting: the risk-free rate is an Italian government yield and the cost of equity also adds an Italy default spread, which raises the discount rate and lowers value. This is a stated limitation.', 'Terminal value is 79.6% of enterprise value, so small changes in WACC or g move the answer materially [3.2]. The FY2026E margin of 12.8% sits above the five-year average, and the forecast fades it [3.1].', 'Conclusion vs market price', 'At EUR 45.32 the market price is 19.7% below the base-case value of EUR 56.47, but it lies inside the 80% range (EUR 44.34 to EUR 74.08) and only just above its lower end [3.2]. The base case is therefore a moderately positive signal, not a clear mispricing, and it relies on a low-beta discount rate. With the higher Global beta the value is below the price. The shares can be read as fairly valued to moderately undervalued.'])
PASS  note: 5 headings  (actual=['Thesis', 'Main assumptions', 'Valuation range', 'Risks', 'Conclusion vs market price'] expected=['Thesis', 'Main assumptions', 'Valuation range', 'Risks', 'Conclusion vs market price'])
PASS  note: 1 picture, at most 900 words  (actual=(1, True) expected=(1, True))
PASS  note: headline paragraph equals report_headline and its tags are in the next paragraph  (actual=(True, True) expected=(True, True))
PASS  note: A4 width (EMU, 1%)  (actual=7560310 expected=7560000 rel_tol=0.01)
PASS  note: A4 height (EMU, 1%)  (actual=10692130 expected=10692000 rel_tol=0.01)
PASS  two fresh rebuilds (run.py --fresh --through 7) succeed  (actual=(0, 0) expected=(0, 0))
PASS  two fresh rebuilds: the 24 fingerprints equal verify/fp_step06.txt  (actual=((0, 24), (0, 24)) expected=((0, 24), (0, 24)))
PASS  two fresh rebuilds: byte-identical guide PDF  (actual=True expected=True)
PASS  two fresh rebuilds: byte-identical guide_numbers.json  (actual=True expected=True)
PASS  two fresh rebuilds: identical note docx members  (actual=True expected=True)
PASS  two fresh rebuilds: identical note_chart.png  (actual=True expected=True)
PASS  two fresh rebuilds: the workbook differs only in docProps/core.xml (or not at all)  (actual=[] expected=[])
PASS  check_step01.py passes 128/128  (actual=(128, 128, 0) expected=(128, 128, 0))
PASS  check_step02.py passes 78/78  (actual=(78, 78, 0) expected=(78, 78, 0))
PASS  check_step03.py passes 148/148  (actual=(148, 148, 0) expected=(148, 148, 0))
PASS  check_step04.py passes 66/66  (actual=(66, 66, 0) expected=(66, 66, 0))
PASS  check_step05.py passes with at least 93 checks and none failing  (actual=(True, True, 0) expected=(True, True, 0))
PASS  check_step06.py passes with at least 25 checks and none failing  (actual=(True, True, 0) expected=(True, True, 0))
PASS  check_step07.py passes with at least 74 checks and none failing  (actual=(True, True, 0) expected=(True, True, 0))
PASS  check_step08.py passes with at least 66 checks and none failing  (actual=(True, True, 0) expected=(True, True, 0))
INFO  pass counts: {'01': (128, 128, 0), '02': (78, 78, 0), '03': (148, 148, 0), '04': (66, 66, 0), '07': (82, 82, 0), '05': (93, 93, 0), '06': (25, 25, 0), '08': (68, 68, 0)}
PASS  renders: guide pages, note pages (exactly 2) and workbook pages written to verify/render/step09  (actual=(True, 2, True) expected=(True, 2, True))
PASS  note: page 2 of the render ends above 90 % of the printable height  (actual=0.2907970497515148 expected in [0.0, 0.9])
PASS  note render: 'Università' extracted from page 1 and no U+FFFD  (actual=(True, False) expected=(True, False))
PASS  workbook render: the author line is extracted on the 0.0 page  (actual=True expected=True)

94/94 checks passed
```
`check_step07.py` and `check_step08.py` (run separately on the same code): 82/82 and 68/68 checks passed. Regression: check_step01-04 128/78/148/66, check_step05 93/93, check_step06 25/25, all PASS. `run.py --fresh --through 7` finished without error.

## Human decision on the former CHECK DISPUTED (resolved)
- **Dispute.** `3.1 FCFF Forecast!G30` (source text "...other incentive plans.") matched the banned word "plans" and was not reachable by the 5 reword rules.
- **Decision by the human:** add a sixth rule ("incentive plans" -> "incentive schemes", no digits) to `TEXT_REWORDS` in `py/doc_map.py`, applied only when the workbook is built (DuckDB text in `forecast_assumptions.note` unchanged), and change the expected reworded cells from 7 to 8 in check_step07 (F2) and check_step09.
- **Applied.** Rule added; 8 reworded cells (3.1 G30 added); rule count 6. No other check changed: the banned scans still run over every cell with the same list, the changed cells are exactly the 8 listed, every rule is used, digit runs identical. Banned-phrase scans: 0 hits. Data quality log entry 32 updated.

## Spot-check cases for the human (3 to 5)
1. **Flag cell moved (edge case: layout).** Step-8 workbook `3.2 Valuation!A79` (merged A79:H79) is now `A61` (merged A61:H61). Text unchanged: "SIMPLIFICATION FLAG: minorities at book value (not market value) are deducted..."; same font, fill, alignment, row height. Pointer stays at A59 (link to `'2.2 Bridge Inputs'!A1`), row 60 is empty. Correct because requirement "3.2 gap closed" maps old row r > 75 to r - 16 (old 77 in the pre-Amendment-2 layout to 61).
2. **Reworded cell, digits kept (typical).** `2.2 Bridge Inputs!H7`: old "...The plan's 'NFP table 94.0' is the same figure rounded." New "...The figure quoted as 'NFP table 94.0' is the same figure rounded." Rule 1; the digit runs (26, 739, 67, 631, 94, 0) are identical.
3. **Sixth rule (the resolved dispute).** `3.1 FCFF Forecast!G30`: DuckDB `forecast_assumptions.note` still reads "...the rest of management's bucket is other incentive plans."; the workbook cell now reads "...other incentive schemes." (rule 6, no digits in the cell changed). No banned-phrase hit is left in the three documents.
4. **Guide §A.3 item 4 (new content with provenance).** "...the terminal value is 79.6% of enterprise value against a bound of 80%; the base-case value is 24.6% above the price against a bound of 30%; the market price is EUR 0.98 above the Monte Carlo 10th percentile; and the base WACC is 0.52 pp above the lower bound of 6%." 79.6% = valuation.tv_share_of_ev; 24.6% = value / price - 1 (56.47 / 45.32 - 1); 0.98 = price 45.32 minus mc_summary.p10 44.34; 0.52 = (WACC 6.5208% minus the brief's 6% bound, parsed from brief_research_brief "WACC outside 6-10%") in pp. The bounds are quoted from the brief with anchors.
5. **Author line (boundary: non-ASCII, "à").** `0.0 Overview!A20`, the note paragraph after the title and guide page 1 all read "Mina Khella · mina.khellas@gmail.com · Undergraduate in Statistics and Economics, Università degli studi di Milano Bicocca". The "à" is in the cmap of the Gill Sans fonts and is extracted intact from the PDF page 1 and from the LibreOffice renders of the note and the workbook.

## Deviations, disputes, changes to earlier steps
- **Former CHECK DISPUTED (3.1 G30, "plans"):** resolved by the human, see the decision section above. Further check edits for it: check_step07 F2 and check_step09 expect 8 cells and 6 rules instead of 7 and 5 (counts and the G30 cell only; no check loosened).
- **Plan wording of the note-token check.** The plan says the note's number-token multiset "equals `verify/baseline_amend2/note_tokens.txt` (61)". That file is the pre-step-8 note: step 8 reworded three tokens ("25", "5", "95") on purpose (data quality log entry 29), so the current note has 58 tokens. `check_step09` therefore checks the stricter pair: the multiset equals the tokens of the HEAD 44d683d note (58), and `baseline_amend2` minus the new note is exactly {25, 5, 95}. No token changed in step 9. Flagged for the Verifier.
- **Check edits (non-weakening).**
  - `check_step07.py`: F1 mapping rule for old 3.2 rows > 75 (`r + 2 - (r_end_old - r_h_old)`); F2 text compared to `reword(old)` plus 3 new checks (exactly the 7 reworded cells (8 after the human decision), each of the 5 rules used (6), digit runs identical); F3 the banned list is `checks/banned.py`; F4 5 new 3.2 layout checks. The check count rises (74 to 82).
  - `check_step08.py`: E1 the extended `BANNED` and `INTERVIEW_MAX = 0`; E2 the section-3-rows-present check is replaced by its inverse plus a new A.3 figures check; E3 the §1.2 check requires "1 decimal", "accepted" and "2026-11-09"; E4 the note scan includes tables, headers and footers; E5 the §6 sentence check. The count rises (66 to 68).
  - `check_step05.py`, `check_step06.py`: no edit was needed.
- **First run of the new check.** A first run of `check_step09.py` started before the code edits by mistake (a background run whose output was not kept) and a second run stopped on a `None` border in my own `sig()` helper (fixed in the check). Both are check-script issues, no product code was involved.
- **Own check wording.** The guide §5 row labels ("Rates and bridge" etc.) and the wrapped label "Independent recomputation" are my choices, not fixed by the plan; the check looks for them as written.
- **Visual.** I viewed guide p.1 (cover with the author block, "à"), p.3 (§0.0 method map, no role names), p.9 (§5 table fits), p.10 (§6, §A.1), the note p.1 (author line under the title), workbook p.1 (0.0, author line small and grey) and the two pages of 3.2 (pointer, empty row, flag with no gap; key rows still vermilion). One layout defect was found and fixed during the work: a stray hairline under the author row on 0.0 (the border of B20/C20 is now cleared). Not inspected by me: guide §A.2/A.3 pages (11 and 12 in `verify/render/step09/`); the Verifier inspects them.

<!-- The Verifier appends its section below. -->
