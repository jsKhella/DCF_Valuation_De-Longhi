# Step 01: Build the condensed statements and historical ratios. Verdict: PASS WITH NOTES

## Summary for the human (one page max)
- Headline numbers (all FY2021-25, from `hist_ratios`): 105 of 105 values recomputed independently and identical (|diff| <= 1e-9 relative) ✓. Key ones:
  - FY2025 adjusted EBIT 459.782 m (Executor) = 459.782 m (Verifier) ✓; FY2021 417.692 = 417.692 ✓
  - Adjusted EBIT margin FY2021-25: 12.97% / 8.08% / 10.90% / 12.33% / 12.09%, the same on both sides ✓ (FY2024-25 average 12.21%, the Decision 7 anchor)
  - Effective tax FY2025 24.13%; median FY2021-25 24.13% (Decision 8 input) ✓. D&A 3.32% and capex incl. ROU 4.02% of revenue (5-year averages) ✓. NWC FY2025 2.65% of revenue ✓
  - Method: my own tokenizer over `raw_report_lines` (pages located by anchor lines, not hard-coded), ratios in pandas. The Executor used a hard-coded page map, label parsing and SQL.
- Rows: raw_report_lines → hist_statements 153 (IS 9x5 + BS 13x6 + CF 6x5), hist_ratios 5, hist_adjustments 10 (5 itemised + 5 residual). All differences explained ✓
- Checks: 128/128 pass. All planned checks are present and none is weakened (anchors ±0.0005, tie-outs ±0.002, adjustments ±0.01, identities 1e-9). No earlier-step check files exist (step 0 has none) ✓
- Reproducible: two `run.py --fresh --through 1` rebuilds give identical fingerprints for all 6 step-1 tables ✓
- Notes: 3 minor notes, no SURPRISE and no FRAGILE (see Findings)
- Spot-checks: Executor cases 1-5 traced ✓; 2 random cases (seed 20261109) traced ✓
- Needs your decision: no

## Findings (notes only, nothing blocking)
| # | Level | File:line | Problem | Evidence |
|---|-------|-----------|---------|----------|
| N1 | V4 / doc | plan/plan.md:73; evidence/data_quality_log.md #2 | The plan's expected restatement example ("FY2021 minority profit 0.684 vs 0.651") is a plan error, not a missed restatement. The Executor documented this correctly. | Minority profit FY2021 = 651 in both AR2021 p.75 l.28 and AR2022 p.83 l.25. "684" is the "Minority interest" line on p.76 (AR2021) / p.84 (AR2022), not the IS line. My zero-threshold diff of 72 original-vs-used values (IS/BS/CF condensed lines, FY2021-24) finds 0 differences. The only restatement is the FY2023 CF presentation change, which the Executor logged. |
| N2 | V4 / format | py/01_statements.py:86-88; DQ log #3 | "Cash flow for the period" is not like-for-like across years. FY2021-22 include the FX effect (AR2022/AR2023 present no separate translation line, so translation = 0), while FY2023-25 exclude it. The tie-outs hold and nothing downstream uses the line, but the Statements_5Y sheet (step 5) should footnote it. | AR2022 p.87 l.25 "FX effect on cash ... 26,428 46,112" inside section E; AR2024 p.141 l.48 separate translation line (15,473) for FY2023. |
| N3 | V4 / definition | py/01_statements.py:320-331; evidence step01 "Itemisation unit" | An "itemised adjustment" is one IS line's non-recurring amount in one year, not a single event from note 8. This is a reasonable reading because only FY2021's note 8 itemises amounts, and it is disclosed. Adjusted EBIT uses the full IS non-recurring total, so the numbers are unaffected. | Each of the 5 items' amounts is quoted verbatim on its note page (AR2021 p.94/95/96, AR2022 p.100, AR2025 p.163), all checked. |

## Verifier details
**V1.** `run.py --fresh --through 1` OK (21 s, no manual steps). Fingerprints saved to `verify/fp_step01.txt` for hist_statements (153), hist_other_inputs (6), hist_nonrec_lines (18), hist_adjustments (10), hist_restatements (2) and hist_ratios (5). After a second fresh rebuild, `--compare` gives "PASS fingerprints identical".

**V2.** I compared `checks/check_step01.py` with plan step 1 line by line. Coverage, uniqueness, nulls, doc/page, the 25 anchors, 6 BS balances, 5x5 CF/IS tie-outs, adjustment sums and the 3-5 item count, the ratio identities (adj_ebit, growth base 2,351.257, NWC, FCFF, capex_rou per Decision 9), the expected ranges, the 0-40% tax rule and the 8 DQ-log keywords are all present. Some checks are stricter than the plan: every line is required in every year, delta_nwc is checked explicitly, and ratio items are checked against the BS. The output I got matches the pasted output (128/128).

**V3.** `verify/verify_step01.py`, written before I read the Executor's code. It compares 19 hist_ratios columns x 5 years plus nonrec and taxes: 105/105 match, 0 diffs. Parsed independently: FY2020 revenue 2,351.257; ROU additions 30.018 / 28.139 / 41.037 / 26.047 / 16.845; historical FCFF 331.456 / 52.435 / 455.907 / 290.698 / 357.912.

**V4.** `sql/01_ratios.sql`: the `lag()` window runs after `WHERE fy BETWEEN 2021 AND 2025`, so FY2021 falls through to coalesce(FY2020 revenue), which is correct. The inner joins nwc p (fy-1) and hist_other_inputs (ROU) drop no rows (YE2020 present, 5 ROU rows). There is no integer division, and signs are documented. The Executor's 3-value layout resolution was traced on AR2024 p.137 l.27 vs AR2023 p.90 l.12 and is correct. ROU additions exclude acquired ROU (FY2021 0.344; FY2024 11.749 change in consolidation), which is consistent with CF capex excluding acquisitions, and this is logged. Euro-sign claim confirmed: U+20AC appears in 2,011 lines and U+FFFD in 0. The reclassification is confirmed at AR2025 p.23 l.38-39 (management view only). Headers are present and accurate, and the evidence numbers are all reproduced by the code.

**V5.** The ranges look plausible. Margins run 8.1-13.0% (FY2022 trough). NWC swings from 9.1% (FY2022 inventory build) to 2.0% (FY2023 release), which explains the FCFF pattern of 52 m in FY2022 and 456 m in FY2023. Taxes are 22.1-24.5%. Nothing contradicts the brief's pre-registered expectations; none apply to this step.

**V6.** I tested 2 judgment calls. (a) Excluding FY2021's non-operating Eversys re-measurement gain (+25.329, below EBIT) from PBT raises the FY2021 tax rate from 22.11% to 23.60%, but the FY2021-25 median stays 24.13%. (b) Counting acquired ROU as capex changes the 5-year average capex % by +0.07 pp. Neither flips anything, so nothing is FRAGILE.

**V7.** I traced the Executor's cases against raw lines: (1) AR2025 p.144 l.25/34 ✓; (2) AR2023 p.94 l.33 479,951 and l.25 FX (15,473) vs AR2024 p.141 l.45/48 495,424 and (15,473) ✓; (3) AR2022 p.87 l.25/33, 662.947 + 363.134 = 1,026.081 ✓; (4) AR2024 p.137 l.27 "83,484 (23,588) 753" and AR2023 p.90 l.12 "(23,588) 753 ..." ✓; (5) AR2021 p.96 l.7 "€14,978 thousand in change in inventories" ✓. Random cases (seed 20261109, `verify/verify_step01_extra.py`): YE2025 BS other financial payables (long-term) 171.762, from AR2025 p.147 l.27 "171,762 193,581" ✓; YE2020 BS cash 662.947, from AR2021 p.77 l.29 "1,026,081 662,947" ✓.

---
(Executor's section follows)

# Step 01: Build the condensed statements and historical ratios. Status: AWAITING VERIFICATION

## What was done
- Parsed the condensed IS (9 lines incl. "EBIT of which non-recurring"), BS (13 lines, YE2020-YE2025) and CF (6 lines) from the statement pages of AR2021-AR2025 in `raw_report_lines`. Each year comes from the latest report that presents it (FY t from the AR t+1 comparative column, FY2025 from AR2025, YE2020 from AR2021). Every row has doc_id and PDF page.
- Parsed the IS "of which non-recurring" column line by line for every year (`hist_nonrec_lines`). The 5 largest items by absolute amount are itemised in `hist_adjustments`, with the statement page as the amount source and the note page that explains each one. A residual row per year makes the add-backs sum to -(IS non-recurring).
- Parsed right-of-use additions from note 15 of each year's report (capex per Decision 9) and the FY2020 revenue (growth base) into `hist_other_inputs`.
- Compared every condensed line in its original report with the latest presenter and logged differences > 0.1 m in `hist_restatements`. There are 2 rows, both from the FY2023 cash-flow presentation change.
- Computed `hist_ratios` (one row per FY2021-25: growth, adjusted EBIT and margin, D&A %, capex incl./excl. ROU, NWC and its change, effective tax, historical FCFF) in SQL. Wrote 11 entries to `evidence/data_quality_log.md`.

## Files
| File | Purpose |
|------|---------|
| `py/01_statements.py` | PDF-text line parsing -> `hist_statements`, `hist_other_inputs`, `hist_nonrec_lines`, `hist_adjustments`, `hist_restatements` |
| `sql/01_ratios.sql` | `hist_ratios` from the tables above |
| `checks/check_step01.py` | 128 acceptance checks (plan step 1) |
| `run.py` | Step 1 registered: `1: ["py/01_statements.py", "sql/01_ratios.sql"]` |
| `evidence/data_quality_log.md` | Created; step 1 section (11 issues) |

## Row flow
| Table | Rows in | Rows out | Why the difference |
|-------|---------|----------|--------------------|
| raw_report_lines (AR2021-25, 20 statement pages) -> hist_statements | 79,876 (all docs) | 153 | IS 9 lines x 5 FY = 45; BS 13 lines x 6 YE = 78; CF 6 lines x 5 FY = 30 |
| raw_report_lines -> hist_other_inputs | | 6 | FY2020 revenue + 5 years of ROU additions |
| raw_report_lines -> hist_nonrec_lines | | 18 | Non-zero non-recurring amounts by IS cost line, FY2021-25 (zero entries are not stored) |
| hist_nonrec_lines -> hist_adjustments | 18 | 10 | 5 itemised (largest absolute amounts) + 5 residual rows (one per year) |
| (parsed original vs used) -> hist_restatements | 112 compared values (28 condensed lines x FY2021-24) | 2 | Only FY2023 CF "cash flow for the period" and "translation difference on cash" differ by > 0.1 m |
| hist_statements -> hist_ratios | 153 | 5 | One row per FY2021-25 (YE2020 used only for the FY2021 delta NWC) |

`python run.py --fresh --through 1` rebuilds from scratch. Two fresh rebuilds give identical fingerprints for all 6 step-1 tables (`checks/fingerprint.py --compare`: "PASS fingerprints identical").

## Check results
```
PASS  coverage IS fiscal years  (actual=[2021, 2022, 2023, 2024, 2025] expected=[2021, 2022, 2023, 2024, 2025])
PASS  coverage CF fiscal years  (actual=[2021, 2022, 2023, 2024, 2025] expected=[2021, 2022, 2023, 2024, 2025])
PASS  coverage BS fiscal years  (actual=[2020, 2021, 2022, 2023, 2024, 2025] expected=[2020, 2021, 2022, 2023, 2024, 2025])
PASS  statement only in IS/BS/CF  (actual=0 expected=0)
PASS  (fy, statement, line_item) unique  (actual=0 expected=0)
PASS  no null values / keys / sources in hist_statements  (actual=0 expected=0)
PASS  every (statement, line_item) present in every year of its statement  (actual=0 expected=0)
PASS  anchor IS total consolidated revenues FY2021  (actual=3221.587 expected in [3221.5865, 3221.5875])
PASS  anchor IS total consolidated revenues FY2022  (actual=3158.433 expected in [3158.4325, 3158.4335])
PASS  anchor IS total consolidated revenues FY2023  (actual=3075.904 expected in [3075.9035, 3075.9045])
PASS  anchor IS total consolidated revenues FY2024  (actual=3497.555 expected in [3497.5544999999997, 3497.5555])
PASS  anchor IS total consolidated revenues FY2025  (actual=3801.458 expected in [3801.4575, 3801.4585])
PASS  anchor IS ebit FY2021  (actual=386.93 expected in [386.9295, 386.9305])
PASS  anchor IS ebit FY2022  (actual=263.538 expected in [263.5375, 263.5385])
PASS  anchor IS ebit FY2023  (actual=329.628 expected in [329.6275, 329.6285])
PASS  anchor IS ebit FY2024  (actual=430.801 expected in [430.8005, 430.8015])
PASS  anchor IS ebit FY2025  (actual=458.145 expected in [458.1445, 458.14549999999997])
PASS  anchor IS ebit of which non-recurring FY2021  (actual=-30.762 expected in [-30.7625, -30.7615])
PASS  anchor IS ebit of which non-recurring FY2022  (actual=8.25 expected in [8.2495, 8.2505])
PASS  anchor IS ebit of which non-recurring FY2023  (actual=-5.502 expected in [-5.5024999999999995, -5.5015])
PASS  anchor IS ebit of which non-recurring FY2024  (actual=-0.39 expected in [-0.3905, -0.3895])
PASS  anchor IS ebit of which non-recurring FY2025  (actual=-1.637 expected in [-1.6375, -1.6365])
PASS  anchor BS total assets FY2021  (actual=3930.901 expected in [3930.9004999999997, 3930.9015])
PASS  anchor BS total assets FY2022  (actual=3553.706 expected in [3553.7055, 3553.7065000000002])
PASS  anchor BS total assets FY2023  (actual=3812.428 expected in [3812.4275, 3812.4285])
PASS  anchor BS total assets FY2024  (actual=4336.126 expected in [4336.1255, 4336.1265])
PASS  anchor BS total assets FY2025  (actual=4160.508 expected in [4160.5075, 4160.5085])
PASS  anchor CF closing cash and cash equivalents FY2021  (actual=1026.081 expected in [1026.0804999999998, 1026.0815])
PASS  anchor CF closing cash and cash equivalents FY2022  (actual=770.247 expected in [770.2465, 770.2475])
PASS  anchor CF closing cash and cash equivalents FY2023  (actual=1250.198 expected in [1250.1975, 1250.1985000000002])
PASS  anchor CF closing cash and cash equivalents FY2024  (actual=1019.711 expected in [1019.7105, 1019.7115])
PASS  anchor CF closing cash and cash equivalents FY2025  (actual=998.448 expected in [998.4475, 998.4485])
PASS  BS balances YE2020  (actual=2945.569 expected in [2945.567, 2945.571])
PASS  BS balances YE2021  (actual=3930.901 expected in [3930.899, 3930.903])
PASS  BS balances YE2022  (actual=3553.706 expected in [3553.704, 3553.708])
PASS  BS balances YE2023  (actual=3812.428 expected in [3812.426, 3812.43])
PASS  BS balances YE2024  (actual=4336.126 expected in [4336.124, 4336.128000000001])
PASS  BS balances YE2025  (actual=4160.508 expected in [4160.505999999999, 4160.51])
PASS  CF opening + flow + translation = closing FY2021  (actual=1026.0810000000001 expected in [1026.079, 1026.0829999999999])
PASS  CF closing cash = BS cash FY2021  (actual=1026.081 expected in [1026.079, 1026.0829999999999])
PASS  opening cash FY2021 = closing cash FY2020  (actual=662.947 expected in [662.945, 662.949])
PASS  EBIT + net financial = PBT FY2021  (actual=400.25100000000003 expected in [400.24899999999997, 400.253])
PASS  PBT + taxes = profit FY2021  (actual=311.74899999999997 expected in [311.747, 311.75100000000003])
PASS  CF opening + flow + translation = closing FY2022  (actual=770.2469999999998 expected in [770.245, 770.2489999999999])
PASS  CF closing cash = BS cash FY2022  (actual=770.247 expected in [770.245, 770.2489999999999])
PASS  opening cash FY2022 = closing cash FY2021  (actual=1026.081 expected in [1026.079, 1026.0829999999999])
PASS  EBIT + net financial = PBT FY2022  (actual=238.197 expected in [238.195, 238.199])
PASS  PBT + taxes = profit FY2022  (actual=179.84300000000002 expected in [179.84099999999998, 179.845])
PASS  CF opening + flow + translation = closing FY2023  (actual=1250.1979999999999 expected in [1250.1960000000001, 1250.2])
PASS  CF closing cash = BS cash FY2023  (actual=1250.198 expected in [1250.1960000000001, 1250.2])
PASS  opening cash FY2023 = closing cash FY2022  (actual=770.247 expected in [770.245, 770.2489999999999])
PASS  EBIT + net financial = PBT FY2023  (actual=327.298 expected in [327.296, 327.3])
PASS  PBT + taxes = profit FY2023  (actual=250.412 expected in [250.41, 250.41400000000002])
PASS  CF opening + flow + translation = closing FY2024  (actual=1019.7110000000001 expected in [1019.7090000000001, 1019.713])
PASS  CF closing cash = BS cash FY2024  (actual=1019.711 expected in [1019.7090000000001, 1019.713])
PASS  opening cash FY2024 = closing cash FY2023  (actual=1250.198 expected in [1250.1960000000001, 1250.2])
PASS  EBIT + net financial = PBT FY2024  (actual=429.37399999999997 expected in [429.372, 429.37600000000003])
PASS  PBT + taxes = profit FY2024  (actual=324.95000000000005 expected in [324.948, 324.952])
PASS  CF opening + flow + translation = closing FY2025  (actual=998.448 expected in [998.446, 998.4499999999999])
PASS  CF closing cash = BS cash FY2025  (actual=998.448 expected in [998.446, 998.4499999999999])
PASS  opening cash FY2025 = closing cash FY2024  (actual=1019.711 expected in [1019.7090000000001, 1019.713])
PASS  EBIT + net financial = PBT FY2025  (actual=450.006 expected in [450.00399999999996, 450.008])
PASS  PBT + taxes = profit FY2025  (actual=341.41999999999996 expected in [341.418, 341.422])
PASS  adjustments sum = -(IS non-recurring) FY2021  (actual=30.762 expected in [30.752, 30.772000000000002])
PASS  exactly one residual row FY2021  (actual=1 expected=1)
PASS  adjustments sum = -(IS non-recurring) FY2022  (actual=-8.25 expected in [-8.26, -8.24])
PASS  exactly one residual row FY2022  (actual=1 expected=1)
PASS  adjustments sum = -(IS non-recurring) FY2023  (actual=5.502 expected in [5.492, 5.512])
PASS  exactly one residual row FY2023  (actual=1 expected=1)
PASS  adjustments sum = -(IS non-recurring) FY2024  (actual=0.39 expected in [0.38, 0.4])
PASS  exactly one residual row FY2024  (actual=1 expected=1)
PASS  adjustments sum = -(IS non-recurring) FY2025  (actual=1.637 expected in [1.627, 1.647])
PASS  exactly one residual row FY2025  (actual=1 expected=1)
PASS  itemised (non-residual) item names in total  (actual=5 expected in [3, 5])
PASS  every adjustment has doc_id and pdf_page  (actual=0 expected=0)
PASS  hist_ratios one row per fy 2021-2025  (actual=[2021, 2022, 2023, 2024, 2025] expected=[2021, 2022, 2023, 2024, 2025])
PASS  adj_ebit = ebit_reported - nonrec  (actual=0 expected=0)
PASS  adj_ebit FY2021  (actual=417.692 expected in [417.6915, 417.6925])
PASS  adj_ebit FY2025  (actual=459.782 expected in [459.7815, 459.78249999999997])
PASS  FY2020 revenue used for FY2021 growth  (actual=2351.257 expected in [2351.2565, 2351.2575])
PASS  FY2021 growth 37.0% +/- 0.1 pp  (actual=0.37015519783673145 expected in [0.369, 0.371])
PASS  FY2021 growth = revenue / FY2020 revenue - 1  (actual=0 expected=0)
PASS  nwc = trade receivables + inventories - trade payables  (actual=0 expected=0)
PASS  ratio NWC items equal hist_statements BS lines  (actual=0 expected=0)
PASS  delta_nwc = nwc - prior year-end nwc (FY2021 uses YE2020)  (actual=0 expected=0)
PASS  capex_total = intangible + ppe + rou  (actual=0 expected=0)
PASS  capex_rou (Decision 9) = note 15 right-of-use additions, positive  (actual=0 expected=0)
PASS  FCFF identity fcff_hist = adj_ebit*(1-t) + da - capex_total - delta_nwc  (actual=0 expected=0)
PASS  no nulls in hist_ratios  (actual=0 expected=0)
PASS  adj EBIT margin 7-15% FY2021  (actual=0.12965411146742273 expected in [0.07, 0.15])
PASS  D&A 2.5-4.5% of revenue FY2021  (actual=0.029078525583819403 expected in [0.025, 0.045])
PASS  capex excl. ROU 1.5-5% of revenue FY2021  (actual=0.03262243111857603 expected in [0.015, 0.05])
PASS  NWC -5% to +15% of revenue FY2021  (actual=0.06198559902309018 expected in [-0.05, 0.15])
PASS  effective tax 18-30% FY2021  (actual=0.22111624955340525 expected in [0.18, 0.3])
PASS  tax_included consistent with 0-40% rule FY2021  (actual=True expected=True)
PASS  adj EBIT margin 7-15% FY2022  (actual=0.08082742296575549 expected in [0.07, 0.15])
PASS  D&A 2.5-4.5% of revenue FY2022  (actual=0.03350965494598112 expected in [0.025, 0.045])
PASS  capex excl. ROU 1.5-5% of revenue FY2022  (actual=0.04081770928811851 expected in [0.015, 0.05])
PASS  NWC -5% to +15% of revenue FY2022  (actual=0.09143236535332554 expected in [-0.05, 0.15])
PASS  effective tax 18-30% FY2022  (actual=0.2449820946527454 expected in [0.18, 0.3])
PASS  tax_included consistent with 0-40% rule FY2022  (actual=True expected=True)
PASS  adj EBIT margin 7-15% FY2023  (actual=0.10895333534466616 expected in [0.07, 0.15])
PASS  D&A 2.5-4.5% of revenue FY2023  (actual=0.03517372453756684 expected in [0.025, 0.045])
PASS  capex excl. ROU 1.5-5% of revenue FY2023  (actual=0.030983411705957014 expected in [0.015, 0.05])
PASS  NWC -5% to +15% of revenue FY2023  (actual=0.01987448242858033 expected in [-0.05, 0.15])
PASS  effective tax 18-30% FY2023  (actual=0.23491130407151892 expected in [0.18, 0.3])
PASS  tax_included consistent with 0-40% rule FY2023  (actual=True expected=True)
PASS  adj EBIT margin 7-15% FY2024  (actual=0.1232835509377265 expected in [0.07, 0.15])
PASS  D&A 2.5-4.5% of revenue FY2024  (actual=0.03362977851670667 expected in [0.025, 0.045])
PASS  capex excl. ROU 1.5-5% of revenue FY2024  (actual=0.029585810659160473 expected in [0.015, 0.05])
PASS  NWC -5% to +15% of revenue FY2024  (actual=0.02426151983314058 expected in [-0.05, 0.15])
PASS  effective tax 18-30% FY2024  (actual=0.24320056640597706 expected in [0.18, 0.3])
PASS  tax_included consistent with 0-40% rule FY2024  (actual=True expected=True)
PASS  adj EBIT margin 7-15% FY2025  (actual=0.120948856991186 expected in [0.07, 0.15])
PASS  D&A 2.5-4.5% of revenue FY2025  (actual=0.034472299838640856 expected in [0.025, 0.045])
PASS  capex excl. ROU 1.5-5% of revenue FY2025  (actual=0.023452843619474424 expected in [0.015, 0.05])
PASS  NWC -5% to +15% of revenue FY2025  (actual=0.026522981445540113 expected in [-0.05, 0.15])
PASS  effective tax 18-30% FY2025  (actual=0.24129900490215686 expected in [0.18, 0.3])
PASS  tax_included consistent with 0-40% rule FY2025  (actual=True expected=True)
PASS  FY2025 effective tax 24.1%  (actual=0.24129900490215686 expected in [0.2405, 0.2415])
PASS  data quality log mentions restatements on condensed lines  (actual=True expected=True)
PASS  data quality log mentions FY2021 minority 0.684  (actual=True expected=True)
PASS  data quality log mentions FY2021 minority 0.651  (actual=True expected=True)
PASS  data quality log mentions La Marzocco consolidation 2024  (actual=True expected=True)
PASS  data quality log mentions Capital Brands 2021  (actual=True expected=True)
PASS  data quality log mentions FY2025 cost reclassification  (actual=True expected=True)
PASS  data quality log mentions euro-sign encoding  (actual=True expected=True)
PASS  data quality log mentions intraday Yahoo bar  (actual=True expected=True)

128/128 checks passed
```

## Spot-check cases for the human (3 to 5)
1. **Typical: FY2025 revenue and adjusted EBIT.** AR2025 p.144, line 25: "Total consolidated revenues 3,801,458 3,497,555"; line 34: "EBIT 458,145 (1,637) 430,801 (390)". Output: `hist_statements` revenue FY2025 = 3801.458, ebit = 458.145, ebit of which non-recurring = -1.637; `hist_ratios` adj_ebit = 458.145 - (-1.637) = 459.782, margin 12.09%. Correct under "Adjusted EBIT" (reported EBIT minus the non-recurring items). The non-recurring cost is added back.
2. **Edge, restatement: FY2023 cash flow for the period.** AR2023 p.94 (original) shows 479,951 with the FX effect (-15,473) inside it. AR2024 p.141 (comparative) shows 495,424 and a separate line "Translation difference effect on cash and cash equivalents ... (15,473)". Output: FY2023 cash flow for the period = 495.424 and translation = -15.473 (from AR2024, the latest presenter). Opening 770.247 + 495.424 - 15.473 = 1,250.198 = BS cash. Both differences are in `hist_restatements`.
3. **Edge, missing line: FY2021 translation difference = 0.** AR2022 p.87 has no translation line below the cash flow; line 25 "FX effect on cash and cash equivalents 26,428 46,112" sits inside section E, and line 33 "Cash flow for the period (A+B+C+D+E) (255,834) 363,134". Output: FY2021 cash flow for the period = 363.134 and translation = 0.000; 662.947 + 363.134 = 1,026.081 (closing cash). The script asserts this identity before writing the 0. Data quality log #3.
4. **Edge, ambiguous column layout: FY2023 non-recurring in change in inventories.** AR2024 p.137 line 27: "Change in inventories of finished products and work in progress 3-8 83,484 (23,588) 753" (3 numbers, so 2 layouts are possible). AR2023 p.90 line 12 shows FY2023 current gross = (23,588), which matches the 2nd number, so the layout is [current, prior, prior non-recurring]. Output: `hist_nonrec_lines` FY2023 = +0.753. The FY2023 line amounts (+0.753 - 1.036 - 4.727 - 0.492) sum to -5.502 = EBIT non-recurring (asserted).
5. **Largest one-off item: FY2021 change in inventories, -14.978.** AR2022 p.83 line 13: "... 254,836 (14,978)" (FY2021 comparative with its non-recurring column). Note 8 in AR2021 p.96 lines 6-7 explains it ("expenses of 14,978 thousand in change in inventories"), as the release of the Capital Brands/Eversys inventory step-up and current-asset valuations. Output: `hist_adjustments` "FY2021 change in inventories of finished products and work in progress (non-recurring)" = +14.978 (add-back), doc AR2022 p.83, note AR2021 p.96. FY2021 add-backs: 14.978 + 10.667 + 5.406 - 0.289 (residual, services income) = 30.762.

## Deviations, disputes, changes to earlier steps
- **No changes to earlier steps.** `run.py` only gained the step-1 entry in STEPS.
- **Plan's expected restatement example does not exist (not a dispute).** The plan expects "at least FY2021 minority profit 0.684 vs 0.651". FY2021 minority profit is 0.651 in both AR2021 p.75 and AR2022 p.83. The 0.684 is comprehensive income attributable to minorities (AR2021 p.76, AR2022 p.84). The log records this (entry #2), and the only real restatement on the condensed lines (FY2023 CF presentation) is logged as entry #1. The check tests that the log mentions both figures, and the log explains them.
- **Euro-sign profile note corrected.** The feasibility profile says the euro sign is stored as U+FFFD. It is stored correctly as U+20AC; the replacement character appears only in a non-UTF-8 console (log #7). Parsing is unaffected.
- **Extra column and tables (additive, not a definition change).** `hist_ratios.capex_excl_rou_pct` exists because the plan's range check is on capex excluding ROU, while `capex_pct` = capex_total / revenue (incl. ROU, Decision 9). In `hist_ratios`, `taxes` is the positive tax expense; `hist_statements` keeps the printed sign. The extra tables are `hist_other_inputs`, `hist_nonrec_lines` and `hist_restatements`, and `hist_adjustments` has description/note columns.
- **Debt lines are stored as long-term and short-term portions** (bank loans, other financial payables, lease liabilities), as printed. Step 2 sums them.
- **Itemisation unit:** a "non-recurring item" is one IS line's non-recurring amount in one year, because the notes give amounts by IS line (note 8 is narrative except in FY2021). Top 5 by absolute amount: FY2021 inventories 14.978, FY2021 payroll 10.667, FY2022 provisions 7.258, FY2025 payroll 5.570, FY2021 provisions 5.406. The next one is FY2023 services 4.727.

<!-- The Verifier appends its section below. -->
