# Step 08: Rebuild the process guide and the investment note in the same identity (polish pass re-verification). Verdict: PASS WITH NOTES

## Summary for the human (one page max)
- Scope: the polish pass the human approved on 2026-11-10 (Amendment 2, decisions a to c). Four changes are in scope: the reworded §6 sentence, §A.2 kept with its table, "doesn't" changed to "does not", and the allowed-source check that includes `evidence/step07.md`.
- Headline numbers (the figures in the documents):
  - Guide: 389 number tokens (Executor) = 389 (Verifier: text from pypdfium2 and an own tokenizer), same order, 0 differences ✓. The count fell from 390 to 389 because the removed "All 55 number tokens" sentence took its token "55" with it. No other token changed.
  - Provenance: 200 DuckDB entries re-formatted = printed ✓. All 176 file entries were found verbatim on their anchor line, and every one comes from an allowed file. `evidence/step07.md` accounts for 6 of them, as accepted in decision (b) ✓.
  - Own SQL: value 56.47, price 45.32, MC p10 44.34, median 56.36, p90 74.08, 1,203 runs below price, 19.7% below, 24.6% above. All of them are in the guide ✓.
  - Note and workbook unchanged: the docx is byte-identical to HEAD. The xlsx differs from HEAD only in `docProps/core.xml` (a timestamp) ✓.
- Rows: the step writes no table, and the 24 DuckDB tables match `verify/fp_step06.txt` ✓.
- Checks: 66/66 pass, and my output is identical to the pasted output line for line ✓.
  - Diff of `check_step08.py`: one check added (allowed sources) and one comment corrected (0.3 % to 0.5 %, now matching the code). Nothing removed or loosened ✓.
  - check_step01-07 pass 128/78/148/66/93/25/74 ✓.
- Reproducible: two `run.py --fresh --through 7` rebuilds ✓.
  - The PDF (`4939aac5...`), docx, chart PNG and guide_numbers.json are byte-identical in both rebuilds and equal the Executor's files.
- Polish verified, with renders of pages 10 to 12 inspected:
  - The guide has no contraction left, and "Changing the seed does not move it outside" is on p.10.
  - The text "55 number tokens" appears nowhere.
  - §A.2 now starts p.12 together with its table. The trade-off is about 40 % blank space at the foot of p.11, which is cosmetic.
- Notes: no SURPRISE, no FRAGILE. 3 minor notes on documentation and wording (below).
- Spot-checks: the 4 polish edits, plus 2 seeded random guide tokens (seed 808: #186 "5.52", #231 "44.34"), all traced ✓.
- Needs your decision: no. Notes 1 and 2 are stale text that the Executor should correct at commit time; neither changes a number in the deliverables.

## Findings (only if FAIL or NOTES)
| # | Level | File:line | Problem | Evidence |
|---|---|---|---|---|
| 1 | V4 doc | `evidence/step08.md`, Executor section: "Polish pass (no number changed; guide still 390 tokens, ...)", "What was done" ("390 tokens: 200 db, 9 db_text, 177 file, 4 file_rows") and the Row-flow row "390 PDF tokens / 390 JSON entries" | The guide now has **389** tokens (176 file entries), not 390 (177). The sentence that was removed carried the token "55". The pasted check output (389) is right; the hand-written prose is stale. | `guide_numbers.json`: 389 entries {db 200, file 176, db_text 9, file_rows 4}. check_step08: "count (actual=389 expected=389)". |
| 2 | V4 doc | `evidence/data_quality_log.md:75` (entry 30, handling column) | The entry still says "The guide quotes the verified evidence-pack phrase 'all 55 number tokens' with that anchor, unchanged." After the polish that is no longer true: the phrase is gone from the guide and from guide_numbers.json. | Searching the guide text and the JSON for "55 number tokens" finds 0 hits. |
| 3 | V4 wording | `py/07_process_guide.py:553` (guide p.10, §6, last bullet) | "Every number in the note was checked by script against the cells of the sheets named by the tags of its sentence" slightly overstates what `check_step06.py:147-192` does. (a) Years, dates, FY/H labels and the headline's "80% Monte Carlo" are exempted. (b) The headline paragraph is matched against the tags of the **next** paragraph. (c) The "80" in "80% range" matches only through the 3.2!A3 headline **text** cell, not a numeric cell (earlier note 3, still true). The substance is correct and it is far better than the old "55 tokens" claim, so this is minor. A strictly exact wording would add "other than dates and year labels". | `verify/verify_step08_output.txt`: numeric-only tag match DIFF on ('80', [3.2, 4.2]) and ('80', [3.2]). check_step06.py lines 94-99, 175-178. |

## Verifier details
**V1 Reproduce**
- I saved the Executor's 4 output files, then ran `run.py --fresh --through 7` (rc 0, 78 s).
- `fingerprint.py --compare verify/fp_step06.txt <24 tables>` gives PASS. I saved the result as `verify/fp_step08.txt` (unchanged against git).
- I ran a second `run.py --fresh --through 7` (rc 0), then `--compare verify/fp_step08.txt`, which gives PASS.
- SHA-256 hashes, identical in run 1, run 2 and the Executor's files:

  | File | SHA-256 |
  |---|---|
  | PDF | `4939aac5...4169` |
  | docx | `e859f929...3bc2` (= HEAD) |
  | PNG | `dede2b11...8086` |
  | JSON | `2f03caab...bdf1` |

- The xlsx members are identical to HEAD except `docProps/core.xml`.
- The git diff touches no other code: `06_build_note.py`, `check_step06.py`, `run.py`, `doc_map.py`, `ledger_style.py` and `guide_tokens.py` are all unchanged.
- Regression: check_step01 to 08 give 128/78/148/66/93/25/74/66, with 0 FAIL.

**V2 Check audit**
- `git diff checks/check_step08.py`:
  - one added check, "file entries only from the allowed source files". The plan list plus `evidence/step07.md`, per decision (b). This is stricter than before, because no check enforced the source list earlier.
  - one comment corrected: 0.3 % changed to 0.5 %. The code threshold is unchanged, so earlier note 5a is closed.
- Nothing else changed. The pasted output (67 lines) equals my run exactly.

**V3 Independent recomputation** (`verify/verify_step08.py`, extended with a polish block, output in `verify/verify_step08_output.txt`): 36 OK, 1 DIFF.
- `ALLOWED` now includes `evidence/step07.md`, per decision (b). The allowed-source DIFF from the earlier run is therefore resolved.
- New checks, all OK:
  - no contractions in the guide or note
  - no "55 number tokens" in the guide text or in the JSON anchors
  - the §A.2 heading is on the same page as the first glossary row (p.12), with the contents page excluded
- The one remaining DIFF is the known "80" text-cell match (finding 3, earlier note 3), unchanged from the verified step-6 note.

**V4 Code review of the polish diff** (`py/07_process_guide.py`)
- `SECTION(..., keep=5)`: the default equals the old `CondPageBreak(5 * cm)`, so every other section is unaffected. This is confirmed by the contents landing pages: only A.2 moved, from 10 to 11 (0-based).
- `.replace("doesn't", "does not")` applies only to the quoted final_review explanations. The source row (`final_review.md:30`) is otherwise reproduced verbatim on p.10.
- The new §6 sentence contains no digits, so it carries no unsourced number. The statement about three tokens matching only by coincidence agrees with DQ log 29.

**V5 Visual**: I rasterised guide pp.10-12 myself with pypdfium2.
- §6 is complete on p.10.
- p.11 holds §A and §A.1, with blank space at the foot.
- p.12 opens with §A.2 and its full table, then §A.3.
- No overlap or clipping. Ivory paper, vermilion numerals and hairlines are as before.

**V7 Traces**
1. The "doesn't" source is `final_review.md:30` (Step 4 FRAGILE). The guide p.10 reads "Changing the seed does not move it outside", and the rest of the row is identical ✓.
2. §6 last bullet: the new text is on p.10. The "55" entry (anchor "all 55 number tokens", `evidence/step06.md`) has been removed from the JSON, and the token sequence still matches the PDF ✓.
3. §A.2: the heading and the "Adjusted EBIT" row are both on p.12, and the contents link for A.2 lands on p.12 ✓.
4. Allowed-source check: file entries by source are brief 15, SOURCES 6, step01 2, step02 4, step03 2, step04 8, step06 1, step07 6, final_review 136 (176 in total). All are in the allowed set ✓.

Own random cases (seed 808):
- A: token #186 "5.52". `SELECT min(wacc) FROM sensitivity` returns 0.055208 (5 distinct WACC values), which formats to 5.52%. It is printed on p.8 in the grid row "5.52% 57.15 ..." ✓.
- B: token #231 "44.34". My pandas quantile(0.10) of `mc_runs.value_per_share` is 44.3414, which formats to 44.34 and equals `mc_summary.p10` ✓.

---
# Earlier verification of step 08 (initial build, before the polish pass). Kept for history; superseded above.

## Summary for the human (one page max)
- Headline numbers. This is a presentation step, so the "numbers" are the documents' figures:
  - Guide: 390 number tokens (Executor) = 390 (Verifier: text extracted with pypdfium2, not pdfplumber, and an own tokenizer), same order, 0 differences ✓.
  - Guide provenance: all 200 DuckDB entries re-formatted = printed ✓. All 177 file entries found **verbatim, with their thousands separators**, on a line containing their anchor ✓.
  - Headline figures recomputed from DuckDB with own SQL and all found in the guide: 56.47, 45.32, MC p10 44.34, median 56.36, p90 74.08, 1,203 runs below price, 19.7% below, 24.6% above ✓.
  - Note: 58 tokens (Executor) = 58 (Verifier, raw `word/document.xml` instead of python-docx). Baseline 61 minus new 58 = exactly {25, 5, 95}, nothing added ✓.
- Rows: the 24 DuckDB tables are unchanged (fingerprints = `verify/fp_step06.txt`). The step writes no table ✓.
- Checks: 65/65 pass, and the output is identical to the pasted output. check_step06 went from 17 to 25 (8 added, none removed). check_step01-07 pass 128/78/148/66/93/25/74 ✓. Two small check-text issues are listed below (notes 4 and 5); none hides an error, because my stricter re-tests pass.
- Reproducible: two `run.py --fresh` rebuilds ✓.
  - The PDF, docx, chart PNG and guide_numbers.json are byte-identical across both rebuilds and equal the Executor's files.
  - The xlsx differs only in `docProps/core.xml` (timestamp), as accepted in step 7.
- Visual: all 12 guide pages and both note pages inspected ✓.
  - Ivory paper, vermilion numerals and key result, hairline rules, ▸ rendered, chart in the palette, no overlap or clipping.
  - One widowed heading (note 6).
- Notes: no SURPRISE, no FRAGILE. 6 minor notes (documentation, check text and layout), listed below.
- Spot-checks: Executor cases 1-5 plus 2 seeded random cases (seed 8: guide tokens #84 and #300), all traced ✓.
- Needs your decision: **yes, small.**
  - Note 1: the guide's §6 says "All 55 number tokens of the note were matched". That was true of the step-6 note; the rebuilt note has 58 tokens. Choose whether to reword it before Gate 2.
  - Note 2: guide figures are also sourced from `evidence/step07.md`, which is outside the plan's allowed file list. Accept or not.

## Findings (only if FAIL or NOTES)
| # | Level | File:line | Problem | Evidence |
|---|---|---|---|---|
| 1 | V4 doc accuracy | `report/DeLonghi_DCF_process_guide.pdf` p.10, §6, last bullet (built by `py/07_process_guide.py` from anchor `all 55 number tokens` in `evidence/step06.md`) | The sentence "All 55 number tokens of the note were matched, in reading order..." describes the step-6 verification of the **old** note. The delivered note has 58 tokens (61 in the baseline under the check scrub, minus the 3 rewordings) and was not re-matched under that unit-aware method. Disclosed in DQ log 30, but not in the guide itself. | `verify/verify_step08_output.txt`: new note token count 58. |
| 2 | V2/V4 plan deviation | `report/build/guide_numbers.json` (6 entries); `checks/check_step08.py:223-227` | The plan's Design limits file sources to brief, plan, `evidence/step0[1-6].md`, DQ log, final_review and SOURCES.md. Six guide tokens come from `evidence/step07.md`: 65 Checks rows; 128/78/148/66; 24 tables. The check does not enforce the allowed list, and the evidence pack does not list this as a deviation (only the builder header says `step0[1-7]`). The values are true: I reproduced each one in this verification. | `verify_step08.py`: "file entries only from the plan's allowed files: {'evidence/step07.md': 6}". |
| 3 | V3 | `checks/check_step06.py` (new block, `shown_by_sheet["3.2"] \|= tokens(val["A3"].value)`) | The tag-sheet rule also counts digits in the 3.2!A3 headline **text** cell. As a result, "80" in "an 80% range" [3.2][4.2] and "inside the 80% range" [3.2] passes only through that text. With numeric cells only (the plan says "a displayed value at its own number format"), these 2 tokens have no cell. They are the brief's "80% Monte Carlo range" label, not a figure, and are unchanged from the verified step-6 note. | `verify_step08.py`: numeric-only tag match lists only ('80', [3.2, 4.2]) and ('80', [3.2]). |
| 4 | V2 | `checks/check_step08.py:226-227` | "Found verbatim" is implemented as comma-insensitive token membership (the second `or any(...)` makes the verbatim clause redundant). Slightly looser than the plan wording. | My strict verbatim re-test (printed form with separators, whole-number boundaries) passes 177/177, so nothing is hidden. |
| 5 | V2 | `checks/check_step08.py:407` vs `:413`; `checks/check_step07.py` (EXPECTED_STEP_COUNTS edit) | (a) The comment says 0.3 %, while the code (and the evidence pack) use 0.5 %. (b) check_step07's "check_step06 passes 17/17" became "≥ 17, none failing". This is a necessary consequence of the plan-required step-6 additions and is disclosed, but it is not in the plan's list of allowed edits. | The chart has no non-palette colours in code. All colours come from `LS`, off-palette pixels are anti-aliasing at most 0.4 %, and 97.7 % of pixels are exact palette colours. The threshold choice does not change the result (not FRAGILE). |
| 6 | V5 visual | `verify/render/step08/DeLonghi_DCF_process_guide_p11.png` | The §A.2 Glossary heading and WORKBOOK line sit alone at the bottom of page 11, and the table starts on page 12 (no keep-with-next). Cosmetic. Also, the verbatim final_review quote keeps the contraction "doesn't" (page 10). That is allowed by the banned list, but it is slightly informal for R-C. | Render p11 and p12. |

## Verifier details
**V1 Reproduce**
- `run.py --fresh` (full, steps 0-7): rc 0, 56 s.
- `fingerprint.py --save verify/fp_step08.txt <24 tables>` is identical to `verify/fp_step06.txt`.
- Second `run.py --fresh`, then `--compare`: "PASS fingerprints identical".
- Outputs, run 1 = run 2 = the Executor's pre-run files (SHA-256):
  - PDF `1f3a8075...d065`
  - docx `e859f929...3bc2` (whole file byte-identical; fixed zip times)
  - PNG `dede2b11...8086`
  - JSON `f25661c8...6384`
- Regression: check_step01-08 give 128/78/148/66/93/25/74/65, 0 FAIL.

**V2 Check audit**
- Every plan acceptance item for step 8 maps to a check in check_step08.py or check_step06.py: guide structure, tags and mapping, guide numbers, guide substance, note numbers and structure, note page, banned phrases, fonts and glyphs, determinism and regression, renders.
- Banned list identical to the plan (plus lowercase "us"). "interview" ≤ 3, only on §0.0 pages.
- The baseline is 61 instead of the plan's 55. This is disclosed in DQ 27/30, and I re-derived 61 independently from the baseline docx XML.
- check_step06 diff: only additions (tag drop restricted to doc_map ids, A4, tag rules); no old check removed or loosened.
- The pasted output equals my run line for line.

**V3 Independent recomputation** (`verify/verify_step08.py`, output in `verify/verify_step08_output.txt`): 31 OK, 2 DIFF. Both DIFFs are reconciled as notes 2 and 3.
- Two DIFFs found during development were bugs in my script: JSON tokens stored without separators, and a lookbehind rejecting "p.144". I fixed both, and the strict verbatim test then passed 177/177.
- PDF fonts by raw byte scan: {DejaVuSans, Garamond, -Bold, -Italic, GillSansMT, -Bold}. Each of the 6 FontDescriptors has a FontFile2, and there is no standard-14 font.
- All 12 MediaBoxes are 595.2756 x 841.8898.
- Note page size is 11906 x 16838 twips (A4) and the note has 582 words.

**V4 Code and substance review**
- The 204 db/file_rows entries were read in order against the guide labels. Each SQL item matches its label: grid ranks, sign of FY2022/23 growth, pp scaling of the MC parameters, the bridge items.
- Arithmetic re-done:
  - bridge 8,448.296 / 149.600349 = 56.47
  - NFP -769.993
  - FCFF 388.172 + 132.410 - 160.387 - 5.041 = 355.154
  - market cap 6,779.9
  - debt weight 7.3 %
  - 35.60 vs 56.47 = -37.0 %
- Guide §5.1 "Notes carried" matches all 12 rows of final_review §3 verbatim, so no FRAGILE note is softened. The only change is the step-6 row, correctly updated to "The page size was Letter, not A4; the rebuilt note is A4."
- §A.1 holds all 5 cases with every number, and §A.3 keeps the 6 baseline limitations plus one on rendering.
- `fix_color` in `06_build_note.py` only maps python-docx template colours to ink.
- DQ log entries 29-31 are present.

**V7 Traces** (`verify/spot_step08.txt`)
1. `value_per_share` 56.47243714823831 shows as 56.47; 3.2!A3 = `report_headline` ✓.
2. NFP from the bridge lines = -769.993 = reported 769.993, shown 770.0 ✓.
3. SOURCES.md table rows per heading: company 9, Damodaran 10, ECB 2, Yahoo 7 ✓.
4. Reworded tokens {25, 5, 95}: multiset ✓.
5. '3.2 Valuation'!E39 = 8,032.898 (`#,##0` shows 8,033) and E40 = 0.79647 (`0.0%` shows 79.6 %) ✓.

Own random cases (seed 8):
- A: guide token #84 "24.13" = `median(eff_tax_rate) WHERE tax_included` = 24.13 % ✓. The median of 22.11/24.50/23.49/24.32/24.13 is 24.13.
- B: guide token #300 "5" = "Step 5, Minor" on final_review §3 line "| 5 | Minor | The round-trip check..." ✓.

---
(Executor's section follows)

# Step 08: Rebuild the process guide and the investment note in the same identity. Status: AWAITING VERIFICATION

## What was done
- `py/07_process_guide.py` was rewritten as a formal-register, 12-page A4 guide in the Ledger identity (ivory paper, Garamond headings, Gill Sans MT body, vermilion only on section numerals and the key result, hairline rules). It follows the 22 ids of `py/doc_map.py`, has PDF bookmarks and a contents page with 22 links, and opens every section with a "WORKBOOK ▸ <sheets>" line.
- Every number in the guide is produced either by a DuckDB query plus a format (`D`, `DS`) or inside prose that is verified at build time to occur verbatim on a line of a named file containing an anchor phrase (`FT`, `FR`); a bare number raises an error. The build writes `report/build/guide_numbers.json` (389 tokens after the polish pass: 200 db, 9 db_text, 176 file, 4 file_rows; 390 / 177 before it) [corrected by the orchestrator, 2026-11-10] in reading order. `py/guide_tokens.py` holds the one token rule used by builder and check.
- `py/06_build_note.py` was rebuilt on A4 in the same identity (chart in the palette, ivory background, vermilion on the key result). Every sentence with a figure ends with the sheet tags of the cells it was read from, taken automatically from the cell's sheet; the headline paragraph is followed by its tag paragraph. Two "we/our" sentences were put in the impersonal register, and Risks now starts page 2.
- `checks/check_step08.py` (66 checks) was written first (it failed before any build), `checks/check_step06.py` got the non-weakening edits (tag drop only for doc_map ids, A4, tag-sheet match; 17 to 25 checks), `run.py` entry 7 was added and `py/07_verify_guide.py` was deleted.
- Renders of all 12 guide pages and both note pages are in `verify/render/step08/`.

## Files
| File | Purpose |
|---|---|
| `py/07_process_guide.py` | Builds the guide PDF and `report/build/guide_numbers.json` |
| `py/guide_tokens.py` | Number-token and exclusion rules shared by builder and check (new) |
| `py/06_build_note.py` | Rebuilds the note and its chart (A4, tags, Ledger identity, fixed zip) |
| `checks/check_step08.py` | Guide, note and cross-document checks (new) |
| `checks/check_step06.py` | Edited as listed in the plan (see below) |
| `checks/check_step07.py` | One edit, see "Changes to earlier steps" |
| `run.py` | Entry `7: py/07_process_guide.py` |
| `py/07_verify_guide.py` | Deleted (superseded) |
| `report/DeLonghi_DCF_process_guide.pdf`, `report/build/guide_numbers.json`, `report/DeLonghi_DCF_Valuation_note.docx`, `report/note_chart.png` | Outputs |
| `verify/render/step08/*.png` | Visual material (12 guide pages, 2 note pages) |
| `evidence/data_quality_log.md` | Entries 29 to 31 added |

## Row flow
| Table | Rows in | Rows out | Why the difference |
|---|---|---|---|
| DuckDB tables | 24 fingerprints | 24 identical to `verify/fp_step06.txt` | Step 8 reads the database read-only and writes no table |
| guide number tokens | 389 PDF tokens (390 before the polish pass) | 389 JSON entries | One entry per token, same order; 0 unmatched provenance |
| note number tokens | 61 baseline | 58 | 3 tokens removed by rewording, none added (data quality log 29) |
| `check_step06.py` | 17 checks | 25 checks | 8 checks added, none removed or loosened |

## Check results
Polish pass (notes 1, 2, 6 and the comment of note 5a, human-approved): rerun after the changes below. Command: `.venv/Scripts/python.exe run.py --fresh --through 7`, then `.venv/Scripts/python.exe checks/check_step08.py`. Also run after the same rebuild: check_step01 to 07 give 128, 78, 148, 66, 93, 25 and 74 passes with 0 failures.

```
PASS  note builds (rc)  (actual=0 expected=0)
PASS  guide builds (rc)  (actual=0 expected=0)
PASS  second builds succeed  (actual=(0, 0) expected=(0, 0))
PASS  two builds: byte-identical PDF  (actual='4939aac53f6496ab334a07bd89ff43b035e75b225e7e1d13bc9ac05845ee4169' expected='4939aac53f6496ab334a07bd89ff43b035e75b225e7e1d13bc9ac05845ee4169')
PASS  two builds: identical docx members (all package members)  (actual=(True, 18) expected=(True, 18))
PASS  two builds: identical chart PNG  (actual='dede2b1108004e1e551689db3d8f984b1ae0c17985882b03f1003dd177698086' expected='dede2b1108004e1e551689db3d8f984b1ae0c17985882b03f1003dd177698086')
PASS  two builds: identical guide_numbers.json  (actual='2f03caab65c082ec27b14de612b4a5120b27dd0b4787cb5b37b40f885526bdf1' expected='2f03caab65c082ec27b14de612b4a5120b27dd0b4787cb5b37b40f885526bdf1')
PASS  guide has at most 20 pages  (actual=12 expected in [1, 20])
PASS  every guide page is A4 (595.3 x 841.9 pt, 0.5)  (actual=[] expected=[])
PASS  PDF outline ids, in order  (actual=['0.0', '0', '1', '1.1', '1.2', '2', '2.1', '2.2', '3', '3.1', '3.2', '3.3', '4', '4.1', '4.2', '5', '5.1', '6', 'A', 'A.1', 'A.2', 'A.3'] expected=['0.0', '0', '1', '1.1', '1.2', '2', '2.1', '2.2', '3', '3.1', '3.2', '3.3', '4', '4.1', '4.2', '5', '5.1', '6', 'A', 'A.1', 'A.2', 'A.3'])
PASS  one contents page holds the links  (actual=1 expected=1)
PASS  every section heading appears exactly once outside the contents page  (actual=[] expected=[])
PASS  contents page: one link annotation per id  (actual=22 expected=22)
PASS  contents links land on the pages of the headings  (actual=[2, 3, 3, 3, 4, 4, 4, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 10, 10, 11, 11] expected=[2, 3, 3, 3, 4, 4, 4, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 10, 10, 11, 11])
PASS  every section opens with a WORKBOOK line  (actual=[] expected=[])
PASS  WORKBOOK names are existing sheets and match the section  (actual=[] expected=[])
PASS  every sheet band section id exists as a guide heading  (actual=[] expected=[])
PASS  two-part numeric ids correspond one-to-one to the 11 sheets  (actual=['0.0', '1.1', '1.2', '2.1', '2.2', '3.1', '3.2', '3.3', '4.1', '4.2', '5.1'] expected=['0.0', '1.1', '1.2', '2.1', '2.2', '3.1', '3.2', '3.3', '4.1', '4.2', '5.1'])
PASS  PDF number tokens equal guide_numbers.json tokens in order (count)  (actual=389 expected=389)
PASS  PDF number tokens equal guide_numbers.json tokens in order (first difference)  (actual=None expected=None)
PASS  guide lists at least 100 number tokens  (actual=True expected=True)
PASS  guide numbers: 0 unmatched provenance entries  (actual=[] expected=[])
PASS  guide numbers: file entries only from the allowed source files  (actual=[] expected=[])
PASS  guide numbers: entry kinds are db, db_text, file or file_rows  (actual=[] expected=[])
PASS  final_review section 3 has 12 rows  (actual=12 expected=12)
PASS  every row of final_review section 3 is present in the guide  (actual=[] expected=[])
PASS  final_review section 4 has 5 cases  (actual=5 expected=5)
PASS  the 5 spot-check cases are in the audit trail with all their numbers  (actual=[] expected=[])
PASS  section 1.2 states the 1-decimal display as accepted at Gate 2  (actual=True expected=True)
PASS  six limitation items are kept  (actual=[] expected=[])
PASS  baseline file lists the tokens of the verified step-6 note (61; evidence packs say 55)  (actual=61 expected=61)
PASS  note tokens: baseline minus new equals the 3 listed rewordings  (actual=Counter({'25': 1, '5': 1, '95': 1}) expected=Counter({'25': 1, '5': 1, '95': 1}))
PASS  note tokens: nothing added to the baseline  (actual=Counter() expected=Counter())
PASS  note: the 5 headings unchanged, in order  (actual=['Thesis', 'Main assumptions', 'Valuation range', 'Risks', 'Conclusion vs market price'] expected=['Thesis', 'Main assumptions', 'Valuation range', 'Risks', 'Conclusion vs market price'])
PASS  note: 1 picture and 1 media file  (actual=(1, 1) expected=(1, 1))
PASS  note: at most 900 words  (actual=582 expected in [1, 900])
PASS  note: headline paragraph equals report_headline  (actual=True expected=True)
PASS  note: tags of the headline sit in the next paragraph  (actual=True expected=True)
PASS  note: Risks names minorities at book  (actual=True expected=True)
PASS  note: Risks names italy risk double counting  (actual=True expected=True)
PASS  note: Risks names low europe industry beta  (actual=True expected=True)
PASS  note page width (EMU, 1%)  (actual=7560310 expected=7560000 rel_tol=0.01)
PASS  note page height (EMU, 1%)  (actual=10692130 expected=10692000 rel_tol=0.01)
PASS  banned phrases in guide: 0 hits  (actual=[] expected=[])
PASS  banned phrases in note: 0 hits  (actual=[] expected=[])
PASS  banned phrases in workbook: 0 hits  (actual=[] expected=[])
PASS  'interview' appears at most 3 times  (actual=1 expected in [0, 3])
PASS  'interview' appears only on the section 0.0 pages  (actual=[] expected=[])
PASS  PDF fonts all embedded (FontFile2)  (actual=[] expected=[])
PASS  PDF font set within the allowed set  (actual=[] expected=[])
PASS  PDF: every character is in its font's cmap  (actual=[] expected=[])
PASS  PDF: DejaVuSans used only for the arrow  (actual=[] expected=[])
PASS  PDF: no U+FFFD  (actual=0 expected=0)
PASS  docx fonts within {Garamond, Gill Sans MT}  (actual=[] expected=[])
PASS  docx w:color values within the palette or auto  (actual=[] expected=[])
PASS  docx: no themeColor attribute in the styles  (actual=0 expected=0)
PASS  chart: dominant colours are palette colours  (actual=[] expected=[])
PASS  the 24 table fingerprints equal verify/fp_step06.txt  (actual=(24, 0) expected=(24, 0))
PASS  checks/fingerprint.py is unchanged against HEAD  (actual='' expected='')
PASS  no hex colour literal in py/*.py outside ledger_style.py (no exemption)  (actual={} expected={})
PASS  py/07_verify_guide.py is deleted (superseded)  (actual=False expected=False)
PASS  run.py registers step 7 with the process guide  (actual=True expected=True)
PASS  run.py keeps step 6 on the note builder  (actual=True expected=True)
PASS  guide PNG pages rendered (one per page)  (actual=12 expected=12)
PASS  note renders to exactly 2 pages  (actual=2 expected=2)
PASS  note page 2: last text line ends above 90 % of the printable height  (actual=0.2907970497515148 expected in [0.0, 0.9])

66/66 checks passed
```

## Spot-check cases for the human (3 to 5)
1. **Typical: the answer in the guide (§0.0).** The key line reads "EUR 56.47 per share". Its entry in `guide_numbers.json` is kind `db`, sql `SELECT value FROM valuation WHERE item = 'value_per_share'`, format `.2f`; the raw value is 56.47243714823831. The quoted headline sentence is an entry of kind `db_text` on `report_headline.display` and equals `'3.2 Valuation'!A3`.
2. **File-sourced figure (§A.1, case 2).** The text "net cash of EUR 770.0 m, which matches AR2025 PDF p.177 (769,993)" is copied from `report/final_review.md` section 4 case 2 (anchor `**Step 2, net financial position`); the build verifies each token occurs on that line. The old sheet names (`Statements_5Y`, `Valuation!A1`) are replaced by tags such as [2.2] and [3.2].
3. **Count taken from a source file (§0).** The sources table shows 10 Damodaran files. It is a `file_rows` entry: the number of table rows under the heading "Damodaran Online datasets" in `data/raw/SOURCES.md`. The company documents row shows 9, ECB 2 and Yahoo 7 in the same way.
4. **Edge: reworded note tokens.** Baseline "fades to 12.2% by FY2030E, the FY2024-25 average" contained the token "25", and "a 5th to 95th percentile band" the tokens "5" and "95". None of the three is displayed on the sheets tagged in its sentence (they matched other cells by coincidence: `1.1` E10 and H12, `1.2` I8, `4.2` D73). They now read "the average of FY2024 and FY2025" and "from the fifth to the ninety-fifth percentile". The figures themselves (12.2%, EUR 41.61, EUR 81.09) are unchanged, as are the 58 other tokens.
5. **Tag-sheet match in the note.** Thesis sentence "Enterprise value is EUR 8,033 m, of which the terminal value is 79.6% [3.2]". On `3.2 Valuation` the cells are `ev` = 8,032.898 (format `#,##0` shows 8,033) and `tv_share_of_ev` = 0.79647 (`0.0%` shows 79.6%). The tag was added by the build from the sheet of the cells read, not typed.

## Deviations, disputes, changes to earlier steps
- **Polish pass (no number changed; guide 389 tokens, down from 390 because the removed sentence carried the token "55" [corrected by the orchestrator, 2026-11-10], 12 pages, note unchanged).**
  - Note 1: guide section 6, last bullet, no longer says "All 55 number tokens". It now reads: every number in the note was checked by script against the cells of the sheets named by the tags of its sentence, at the display format of the cell; three tokens that matched a cell only by coincidence were reworded in words; the headline paragraph equals the workbook headline. The sentence contains no digits, so the guide number check has nothing unsourced in it.
  - Note 6: the section A.2 heading now stays with its glossary table (`SECTION(..., keep=16)` forces the break before the heading); the quoted final-review line now reads "does not" instead of "doesn't" (the replacement is applied in the builder, like the existing Letter/A4 edit). Pages 10 and 11 re-rendered and inspected; the heading now starts page 12 with its table.
  - Note 2 (recorded deviation, accepted by the human): six guide figures are sourced from `evidence/step07.md` (65 Checks rows; 128/78/148/66; 24 tables), a file outside the plan's allowed list. `check_step08.py` now enforces an allowed-source list that includes `evidence/step07.md` (new check, 66 checks in total).
  - Note 5a: the comment in `check_step08.py` now says 0.5 %, as the code does.
- **Baseline token count.** The plan says "the baseline's 55 tokens". The baseline file `verify/baseline_amend2/note_tokens.txt` has 61 (same finding as data quality log 27; log 30 records that no scrub gives 55). The check compares against the 61. Three tokens could not meet the tag-sheet rule and the sentences were reworded; they are the only token changes (log 29): "25" (the FY2024 and FY2025 average sentence, sheet 3.1), "5" and "95" (the percentile band, sheet 4.2, cells p5 and p95). No workbook cell carries these three tokens as a figure of its own.
- **Chart colour check.** `check_step08.py` accepts a colour as dominant when it carries more than 0.5 % of the chart pixels. Anti-aliased edges of lines and text produce a few mixed greys below that share (largest 0.4 %). The Verifier's visual check remains the plan's real test.
- **Helvetica entry.** reportlab lists an unused standard font in the resource dictionary if any table or paragraph style leaves its font at the default. All styles and the table cell font are now set explicitly, so the PDF font set is the six allowed fonts plus DejaVuSans for the arrow.
- **Changes to earlier steps (the Verifier should recheck steps 6 and 7):**
  - `checks/check_step06.py`: the plan's listed edits only (tag drop for doc_map ids, A4 test, tag-sheet match); 17 checks unchanged, 8 added.
  - `checks/check_step07.py`: the line that required `check_step06.py` to pass exactly 17/17 now requires at least 17 with none failing (the same pattern as the existing step-5 floor). Without it, step 7's check would fail on the 8 added step-6 checks. Result 74/74.
  - `py/06_build_note.py` (a step 6 file) is rebuilt as the plan requires; the note text changed only in tags, two register edits ("Our" to "The", "We would treat" to "The shares can be read as") and the 3 rewordings above.
- No definition or number changed. No check was loosened.

<!-- The Verifier appends its section below. -->
