# Final review: De'Longhi DCF valuation
Date: 2026-11-09 · Status: **Gate 2 passed. Approved by human: yes, 2026-11-09**

All six steps passed independent verification (all PASS WITH NOTES). Every number below comes from a verified evidence pack in `evidence/`.

## 1. Headline answer
> De'Longhi is worth **€56.47 per share** (DCF base case, WACC 6.52%, g 2.00%); the 80% Monte Carlo range is **€44.34 to €74.08**; the market price of **€45.32** (close of 6 Nov 2026) sits at the **12th percentile**, i.e. **19.7% below** the base-case value.

Supporting figures: enterprise value €8,032.9 m; terminal value 79.6% of EV; implied exit multiple 11.7x EV/EBITDA against Damodaran Furn/Home Furnishings 9.45x (Europe) and 10.63x (Global). Monte Carlo median €56.36 (10,000 runs, seed 20261109).

**How robust is "the stock looks cheap"?** Only moderately, and it depends on beta. With the Global Furn/Home beta (0.938), WACC is 9.62% and the same forecast gives **€35.60 per share, 37.0% below the base case and below the €45.32 price**. The sign of the conclusion therefore depends on the beta choice. The note says this explicitly.

## 2. Definitions, assumptions and decisions recap
- **Scope:** FY2021–FY2025 history, FY2026E–FY2030E forecast, EUR, condensed statements (resized by the human's Amendment).
- **FCFF** = adjusted EBIT × (1 − tax) + D&A − capex − increase in NWC. IFRS 16 leases are treated as debt, and right-of-use additions count as capex (Decision 9).
- **Valuation date and bridge (Decision 1A):** net debt at 31 Dec 2025 with the full FY2026E FCFF, minus the H1 2026 dividends and buybacks (€156.4 m). Cash-like financial assets (€304.7 m) count as cash (Decision 4A), which reconciles to the reported net financial position of €770.0 m. Minorities are deducted at book value (€197.8 m).
- **Market data (Decision 2):** price €45.32 (6 Nov 2026), risk-free rate 4.362% (ECB monthly average for Sep 2026).
- **WACC (Decisions 3 and 5):** unlevered beta 0.397 relevered to 0.420, cost of equity 6.82%, after-tax cost of debt 2.77%, debt weight 7.3%. The global-beta sensitivity gives 9.62%.
- **Forecast (Decisions 7 and 8):** growth 5.0% in FY2026E fading towards g = 2.0%. The margin is anchored on the €680 m EBITDA guidance midpoint and fades to the FY2024–25 average. Tax is the effective rate for the explicit years (24.1%) and the Italian marginal rate (27.81%) for the terminal value.
- **Monte Carlo (Decision 6):** growth shift N(0, 1.5 pp), margin shift N(0, 1.0 pp), correlation 0.5, WACC N(base, 0.75 pp) truncated, seed 20261109.
- **Deviations agreed by you:** the .docx note is step 6, after the Excel report (the template has the Excel report last). The Peers sheet is replaced by Multiples_Check.
- **Accepted by the human (2026-11-09):** adjustment amounts show 1 decimal instead of the brief's "no decimals" (step 5 note 1), because otherwise small items would show as 0. The Excel restyle was also reviewed by the human and accepted.

## 3. SURPRISE and FRAGILE notes
No SURPRISE was raised in any step. These are the FRAGILE and borderline items:

| Step | Flag | Explanation |
|---|---|---|
| 3 | **FRAGILE** (smell tests) | Value vs price (+24.6%, limit 30%) and TV share (79.6%, limit 80%) pass only narrowly. Margin held flat gives €59.08 (+30.4%, TV 80.1%). Tax at 27.81% throughout gives €55.89 (TV 80.5%). Not counting right-of-use additions as capex gives €62.18 (+37.2%). g of 2.5% gives €62.47 (+37.8%, TV 81.6%). The DCF value stays above the price in every variant. |
| 4 | **FRAGILE** | The price is inside the 80% range by only €0.98 above p10. Changing the seed doesn't move it outside. But zero growth–margin correlation, a WACC spread of 0.5 pp, or a margin spread of 0.5 pp would put it outside. "Price inside the range" depends on how wide the distributions were set. |
| 4 | Note | The distribution is right-skewed (convexity in WACC, a few very high values up to €161.40), so the mean is €58.17 against a median of €56.36. See data quality log #21. |
| 6 | **FRAGILE** (carried) | The conclusion flips with the Global beta: €35.60 against the price of €45.32. The note states this. |
| 2 | Minor | The pre-tax cost of debt (3.84%) is below the risk-free rate (4.36%), reflecting old fixed-rate bonds. It is inside the plan's allowed band. WACC is only 0.52 pp above the 6% lower edge of the smell test. |
| 2 | Minor | The interest figure (€19.8 m, from note 9) is broader than its label "interest on loans and bonds" (the plan's wording). The Verifier called the label slightly loose; note 9 has no narrower group figure, so the choice itself is reasonable. |
| 3 | Minor | The terminal FCFF uses the FY2030 working-capital increase at 2.6% growth, not 2.0% (worth about €0.08 per share). |
| 1 | Minor | The plan's expected FY2021 restatement example (minority profit 0.684 vs 0.651) was a plan error. The only real restatement on the condensed lines is the FY2023 cash-flow presentation. |
| 1 | Minor | "Cash flow for the period" includes the FX effect in FY2021–22 but not in FY2023–25. Tie-outs hold and nothing downstream uses this line. |
| 1 | Minor | Each itemised adjustment is one income-statement line's non-recurring amount in one year. Adjusted EBIT uses the full non-recurring total. |
| 5 | Minor | The round-trip check matches cells against a pool of source values rather than each cell's own source, and the determinism rows cover step 1–4 tables only. The Verifier's full read-back found no problems. |
| 6 | Minor | The note says the forecast tax rate is 24.1% without adding that the terminal value uses 27.81%. The comparison wording in the note is typed text that no check tests (all true today). The page size is US Letter, not A4. |

**Known limitations (disclosed in the note):** minorities at book value; Italy's country risk is counted twice in the cost of equity (via the BTP yield and the default spread, as the brief specified); the workbook holds values only, with no live formulas.

## 4. Five spot-check cases (about 10 minutes)
1. **Step 1, source tie-out (check against the PDF).** AR2025 p.144: total consolidated revenues 3,801,458 and EBIT 458,145, with non-recurring (1,637). Adjusted EBIT = 458.145 + 1.637 = 459.782, margin 12.09%. Find the same figures on the `Statements_5Y` and `Adjustments_Ratios` sheets.
2. **Step 2, net financial position.** Bank debt 227.043 + other financial payables 212.180 + leases 94.370 − cash 998.448 − financial assets 305.138 (of which 304.744 is the cash-like amount used in the bridge, and 0.394 is lease prepayments) = −769.993, i.e. net cash of €770.0 m, which matches AR2025 PDF p.177 (769,993). Cash-like assets are the sum of derivatives, fair-value financial assets and other current financial assets from note 24 (AR2025 p.171) plus 60.343 from the net financial position line (p.177).
3. **Step 3, the FY2026E FCFF row (`Forecast_FCFF` sheet).** Revenue 3,991.531; adjusted EBIT 511.627; NOPAT 388.172 at 24.13% tax; D&A 132.410; capex 160.387; change in NWC 5.041; FCFF = **355.154**. The guidance check: 511.627 + 132.410 + 35.963 = 680.000, the midpoint of the €670–690 m guidance (H1 2026 press release, p.6).
4. **Step 3, the bridge to value per share (`Valuation` sheet).** EV 8,032.898 + cash 998.448 + cash-like 304.744 − bank debt 227.043 − other financial payables 212.180 − leases 94.370 − distributions 156.400 − minorities 197.801 = 8,448.296, divided by 149.600349 m diluted shares = **€56.47**. Check that net cash is added, treasury shares are excluded and minorities are deducted.
5. **Step 4, Monte Carlo (`MonteCarlo` sheet).** Run 2057 (growth shift −3.67 pp, margin shift −1.75 pp, WACC 6.13%) gives €45.30, which is just below the price. In total 1,203 of 10,000 runs fall below €45.32, so the percentile is 12.0, and the headline in `Valuation!A1` says "12th". The Global-beta line gives €35.60, 37.0% below the base case.

## 5. Links
- Workbook: [report/DeLonghi_DCF_Valuation.xlsx](DeLonghi_DCF_Valuation.xlsx)
- Investment note: [report/DeLonghi_DCF_Valuation_note.docx](DeLonghi_DCF_Valuation_note.docx)
- Evidence packs: [step01](../evidence/step01.md) · [step02](../evidence/step02.md) · [step03](../evidence/step03.md) · [step04](../evidence/step04.md) · [step05](../evidence/step05.md) · [step06](../evidence/step06.md)
- [Data quality log](../evidence/data_quality_log.md) · [Brief](../brief/research_brief.md) · [Plan](../plan/plan.md)
- Rebuild: `python run.py --fresh` (using `.venv`) reproduces everything from `data/raw/`.

**Gate 2:** approved by the human on 2026-11-09. The project is done.

---

## Addendum 2026-11-10: presentation restructure (Amendment 2, steps 7 and 8)

Scope: presentation only. Every number in the three deliverables is unchanged. The headline sentence in section 1 stands as written; it now sits on sheet `3.2 Valuation` (cell A3) and on `0.0 Overview`.

### A1. What changed
- **One numbering scheme across the three documents.** Workbook sheet *x.y* = guide section §*x.y* = note tag [*x.y*]. Every sheet opens with a `GUIDE ▸ §x.y` band and links to `0.0 Overview` and to the previous and next sheet. Every guide section opens with `WORKBOOK ▸ <sheet>`, and the guide has a clickable contents page and PDF bookmarks.
- **"Ledger" identity, defined once in `py/ledger_style.py`.** Ivory paper, near-black ink, one vermilion accent, Garamond headings and Gill Sans MT body; fonts are embedded in the PDF. The note is now A4.
- **Readable labels** (decision 3 = B) in column B of six sheets; the database key stays in column A.
- **Coaching content removed** from the guide: the reader profile, "Questions you could be asked", "check yourself", "open point for the human" and the restyle section. The register is formal throughout.

### A2. Old to new sheet names (the evidence packs for steps 1–6 and sections 1–4 above use the old names)
| Old | New |
|---|---|
| — | 0.0 Overview (new) |
| Statements_5Y | 1.1 Statements |
| Adjustments_Ratios | 1.2 Adjustments & Ratios |
| WACC | 2.1 WACC |
| Valuation (bridge-input block) | 2.2 Bridge Inputs (new sheet) |
| Forecast_FCFF | 3.1 FCFF Forecast |
| Valuation | 3.2 Valuation (headline moved from A1 to A3) |
| Multiples_Check | 3.3 Multiples Check |
| Sensitivity | 4.1 Sensitivity |
| MonteCarlo | 4.2 Monte Carlo |
| Checks | 5.1 Checks |

Mapping rule, verified: old cell (r, c) → (r+2, c); on the six label sheets, columns from B onward shift right by one. 2,691 of 2,691 baseline cells match, and there are still 1,237 numeric cells and 0 formulas.

### A3. Decisions and deviations
- Gate 1 (Amendment 2, lean version), 2026-11-10: decisions 1 = A (Gill Sans MT), 2 = A (keep "▸"), 3 = B (readable labels), 4 = A (no PDF copy of the note). Full visual inspection.
- After verification: guide §6 sentence about the note reworded (a); six guide figures sourced from `evidence/step07.md` accepted as a deviation and enforced by the source check (b); polish pass (c).
- One approved label override: on 3.2, `pct_vs_base` reads "Price vs value, %" (on 2.1 the same key keeps "Difference vs base case, %").
- The 1-decimal display of adjustment amounts (accepted at Gate 2 on 2026-11-09) is stated in guide §1.2 as a decision, not an open point.
- `checks/check_step05.py`, `check_step06.py` and `check_step07.py` received sheet-reference edits only; the Verifier judged none of them a weakening. Step 6's check count rose from 17 to 25 because the plan added checks; `check_step07` therefore requires step 6 at "at least 17".

### A4. Notes from steps 7 and 8 (no SURPRISE, no FRAGILE)
1. **3.2 Valuation has a gap of about 20 empty rows** where the bridge block used to be. A link line at the top of the gap points to 2.2. It exists because every other cell keeps its verified position.
2. **Excel itself is untested.** No Excel is installed here; all renders are from LibreOffice. Two items depend on Excel: the "▸" glyph relies on Office font fallback, and the chart's axis text carries an empty text run that LibreOffice ignores. **Open the workbook once in Excel before sending it.**
3. **Guide §6, last bullet** ("Every number in the note was checked by script against the cells of the sheets named by its tags") slightly overstates the check: dates and year labels are exempt, and the "80" of "80% range" matches only the headline text cell. The substance is correct.
4. The render check "band on every sheet" is vacuous: every sheet maps to page 1 of the render because the Overview lists every id. The Verifier confirmed the bands by eye.
5. The workbook's bytes differ between rebuilds only in the save timestamp (`docProps/core.xml`); contents are identical. The guide PDF and note are byte-identical across rebuilds.
6. Page 11 of the guide ends with about 40% blank space, so that the §A.2 Glossary heading starts page 12 with its table.

### A5. Five spot-check cases (about 10 minutes, new locations)
1. **Source tie-out.** Revenue FY2025 3,801.458 and EBIT 458.145 on `1.1 Statements`; adjusted EBIT 459.782 and margin 12.09% on `1.2 Adjustments & Ratios`; the same figures in guide §1.1–§1.2.
2. **Net cash.** `2.2 Bridge Inputs`: cash 998.448, cash-like 304.744, bank debt 227.043, other financial payables 212.180, leases 94.370; guide §2.2 shows the same table.
3. **FY2026E FCFF 355.154** on `3.1 FCFF Forecast`, and guide §3.1.
4. **Bridge to EUR 56.47** on `3.2 Valuation` (EV 8,032.898 → equity 8,448.296 ÷ 149.600349 m shares). In the note, the Thesis figures carry the tag [3.2].
5. **Monte Carlo.** `4.2 Monte Carlo`: p10 44.34, p90 74.08, price percentile 12; the note's chart shows the same distribution, with the price line at 45.32.

### A6. Links
- [Workbook](DeLonghi_DCF_Valuation.xlsx) · [Process guide](DeLonghi_DCF_process_guide.pdf) · [Investment note](DeLonghi_DCF_Valuation_note.docx)
- Evidence packs: [step07](../evidence/step07.md) · [step08](../evidence/step08.md) · [Data quality log](../evidence/data_quality_log.md) · [Plan, Amendment 2](../plan/plan.md)
- Rebuild: `.venv/Scripts/python.exe run.py --fresh` rebuilds all three documents (the guide is step 7 in `run.py`).


## Addendum 2 (2026-11-10): final polish (Amendment 3, step 9)
This file is an internal review document and still uses process terms; it is not one of the three deliverables. Step 9 changed presentation only; no figure changed (same 24 table fingerprints; 8 workbook text cells reworded, no digits changed).
- Author line (name, e-mail, programme, university) added to the guide cover, `0.0 Overview` and the note; file properties now carry the author name.
- The empty rows on `3.2 Valuation` are closed: the simplification flag moved from row 79 to row 61 (every baseline cell still compared, 0 mismatches).
- All three documents no longer name the process roles, and no longer use the words surprise or fragile; the guide's section 5 is a short account of the reconciliations and checks per stage; its limitations appendix gains four plain sensitivity items.
- Guide §6 wording on the note's figures now states exactly what is matched (display precision of the cell; dates and year labels exempt).
- Decision during the step: a sixth wording rule ("incentive plans" to "incentive schemes", workbook only, cell `3.1 G30`), approved by the human after a disputed check.
- Verifier verdict for step 9: PASS WITH NOTES (the notes concerned documentation only and are closed).

**Gate 2 (Amendments 2 and 3):** approved by the human on 2026-11-10. The project is done.
