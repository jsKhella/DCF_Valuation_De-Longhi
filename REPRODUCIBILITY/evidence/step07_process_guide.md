# Extra deliverable: process guide PDF (re-verification after fixes). Verdict: PASS WITH NOTES

## Summary for the human (one page max)
- Scope: regenerated `report/DeLonghi_DCF_process_guide.pdf` (sha256 6d4b155e...ab6ca, 19:57), checked against my five earlier findings, the sources (brief, plan, step01-06 packs, DQ log) and the live DuckDB tables.
- All five findings are resolved ✓
  1. On p.10 (Step 2 case), 305.138 is now labelled "financial assets", with the split 304.744 cash-like (used in the bridge) + 0.394 lease prepayments. The split matches `bridge_inputs` (financial_assets_all 305.138, cash_like 304.744, excluded 0.394). The arithmetic 227.043+212.180+94.370-998.448-305.138 = -769.993 ✓
  2. On p.4, the interest figure (EUR 19.8 m = 19.786) is now "broader than its label in the plan ('interest on loans and bonds'), because it also includes charges on other financing instruments... the label is slightly loose". This matches step02.md finding 1 ✓
  3. On p.5, Gordon now "needs g to be below the WACC". g < rf is correctly attributed to the brief's plausibility rule ✓
  4. In the glossary on p.9, beta is now "sensitivity to market moves, not total volatility" ✓. CAPM now reads rf + beta x (market risk premium + Italy default spread). This matches brief section 2 and the wacc table (0.04362 + 0.4196 x (0.0423+0.01618) = 6.82%), and the BTP = 10y Italian yield claim matches brief/plan Decision 2 ✓
  5. On p.5, the bridge summary now includes cash-like financial assets (EUR 304.7 m = 304.744 rounded) ✓
- No new errors. The merged Step 2 bullet on p.4 (kd_pre 3.84% < rf 4.36%, inside the band; "No SURPRISE: nothing here moves the WACC by more than 0.17 pp") matches step02.md line 8 verbatim in substance. The new text on p.4, p.5, p.9 and p.10 attaches every number to the right quantity. Every other number on the 10 pages is unchanged from the version I verified earlier.
- report/final_review.md was aligned for findings 1 and 2 (git diff checked). The new wording is consistent with the PDF and the sources.
- Rendering: 10 A4 pages (595.3 x 841.9 pt); embedded DejaVu Sans (regular, bold, oblique); 38 euro signs (+1 = the new "EUR 304.7 m"), 0 U+FFFD; all characters within x 56.7-538.6 and y 55.6-809.8. Pages 4, 5, 9 and 10 were rendered to PNG and inspected: no clipping or overlap, and the table cells wrap cleanly. `py/07_verify_guide.py` reproduces "pages: 10 | euro signs in text: 38 | replacement chars: 0; numbers not found verbatim in sources: []".
- Needs your decision: no.

## Findings (notes only, cosmetic, no action required)
| # | Criterion | Location | Note |
|---|---|---|---|
| N1 | wording ambiguity | p.5, Step 3 bullet 4 (py/07_process_guide.py:165) | "plus cash and cash-like financial assets (EUR 304.7 m)": the bracket could be read as the total of cash plus cash-like, which would be 1,303.2. It is the cash-like amount only, as the p.10 trace makes clear. |
| N2 | consistency | p.4 "Why it matters" and interview question; p.9 glossary "Equity bridge" | p.4 still gives CAPM as rf + beta x market risk premium, while the corrected glossary shows the default spread inside the bracket. The glossary bridge entry ("add cash, subtract debt, leases and minorities") omits cash-like assets and the H1 2026 distributions. Both are simplifications, not errors; p.5 and p.10 give the full versions. |

## Verifier details
- Hash/state: `git status` shows only py/07_*, the PDF, the evidence pack, requirements.txt and final_review.md changed; the analysis code and DB are untouched. The new strings were found in py/07_process_guide.py at lines 154, 165, 167, 249 and 279, so the PDF matches its code.
- Text was extracted page by page with pdfplumber (UTF-8). I re-read p.4, p.5, p.9 and p.10 in full against step02.md (finding 1, line 8), the brief section 2 cost-of-equity row and plan Decision 2 (rf = ECB monthly 10-year Italian yield, Sep 2026, 4.362%).
- DuckDB (read-only) `bridge_inputs`: bank 227.043, other fin. payables 212.18, leases 94.37, cash 998.448, cash_like 304.744, financial_assets_all 305.138, excluded 0.394, nfp 769.993, distributions 156.4 (127.9 dividends + 28.5 buybacks), minorities 197.801, diluted shares 149.600349, interest_expense_fy2025 19.786 (source: note 9, financial debt and other financing instruments).
- I did not edit the PDF or its code.

### Previous verification (before fixes): PASS WITH NOTES, 5 findings
Findings 1-5 as listed in the Executor's "Fixes" section below; all are now resolved.

---
(Executor's section follows)

# Extra deliverable: plain-English process guide (PDF)

Outside plan/plan.md. No analysis, no new numbers, no other file changed.

## Files
| File | Purpose |
|---|---|
| py/07_process_guide.py | Generates report/DeLonghi_DCF_process_guide.pdf with reportlab (DejaVu Sans, so the euro sign renders) |
| py/07_verify_guide.py | Re-opens the PDF with pdfplumber and compares every number with the source files |
| report/DeLonghi_DCF_process_guide.pdf | The guide: cover and answer, how the project worked, steps 1-6, restyle, glossary, limitations |
| requirements.txt | `reportlab>=4.0` added |

Not registered in run.py STEPS (the analysis fingerprints are unaffected).

## Verification result
Command: `.venv/Scripts/python.exe py/07_verify_guide.py`
- Pages: 10 (A4, page numbers in the footer).
- Euro signs extracted: 37; replacement characters: 0.
- Sources searched: brief, plan, data_quality_log, final_review, evidence/step01-06.md.
- Numbers not found verbatim in the sources: none. Integers 0-12 and the "Page N" labels are ignored by the script.
- Numbers I deliberately avoided because they would be derived: none are computed. The wording "20 in total" is the Verifier's count in step03.md.

Limit of the check: it matches number tokens, not their meaning. A number could be real but attached to the wrong label, so the human should skim the key-number tables.

## Fixes (Executor, after the Verifier's findings)
Result: 10 pages, 38 euro signs, 0 replacement characters, numbers not found in sources: none.
Changed only `py/07_process_guide.py`; PDF regenerated; `py/07_verify_guide.py` re-run (output below).
1. Step 2 trace case: 305.138 now labelled "financial assets", with the split 304.744 cash-like (used in the bridge) and 0.394 lease prepayments.
2. Interest figure: now says it is broader than the plan's label "interest on loans and bonds", that note 9 has no narrower group figure, and the label is slightly loose.
3. Gordon: now says it needs g below the WACC; g below the risk-free rate is the brief's plausibility rule.
4. Glossary: beta is sensitivity to market moves, not total volatility; CAPM entry includes the Italy default spread and explains the "country risk counted twice" limitation.
5. Step 3 bridge summary now includes cash-like financial assets (304.7 m).
