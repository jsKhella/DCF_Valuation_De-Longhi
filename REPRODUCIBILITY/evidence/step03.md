# Step 03: Forecast FCFF and value the base case. Verdict: PASS WITH NOTES

## Summary for the human (one page max)
- Headline numbers: value per share EUR 56.4724 (Executor) = 56.4724 (Verifier, method: one DuckDB SQL CTE chain built from `hist_statements` + `hist_other_inputs` + raw guidance lines, not from `hist_ratios` or `py/dcf.py`) ✓; EV 8,032.898 m = 8,032.898 m ✓; upside_pct -19.75% = -19.75% ✓; TV share 79.65% = 79.65% ✓. All 20 compared numbers (FCFF and margin per year, fcff_tv, TV, sum PV, EV, equity, exit values) agree to ≤ 3.2e-16 relative.
- Rows: forecast_fcff 5, valuation 35, multiples_check 2, forecast_assumptions 19. These are derived tables, so no rows are dropped, and the row flow in the Executor's pack is accurate ✓
- Checks: 148/148 pass. Every plan acceptance check for step 3 is present and none is weakened. Steps 1 (128/128) and 2 (78/78) still pass ✓
- Reproducible: two `run.py --fresh --through 3` rebuilds give identical fingerprints for all 4 tables ✓
- Notes: **FRAGILE** (smell-test outcomes only, not the direction of the result), see finding 1. One minor modelling note, finding 2.
- Spot-checks: Executor cases 1-5 all traced ✓, plus Verifier cases FY2027 PV and FY2021 capex % (seed 20261109) ✓
- Needs your decision: no. For the final review, be aware that the "within 30% of price" and "TV ≤ 80%" smell tests pass narrowly.

## Findings (only if FAIL or NOTES)
| # | Level | File:line | Problem | Evidence |
|---|-------|-----------|---------|----------|
| 1 | V6 FRAGILE | py/03_forecast_valuation.py:47-51, 121 (Decision 7/8/9 choices) | Both smell tests pass only narrowly: value/price - 1 = +24.6% (limit 30%) and TV share = 79.6% (limit 80%). Reasonable alternatives flip them. The direction (DCF value above the 45.32 price) holds in every variant. | `verify/verify_step03.py --quiet`: margin held flat (the Decision 7 alternative) gives 59.08, +30.4%, TV 80.1%. Tax B (27.81% throughout) gives 55.89, +23.3%, TV 80.5%. ROU not counted as capex (9B) gives 62.18, +37.2%. g 2.5% gives 62.47, +37.8%, TV 81.6%. g 1.5% gives 51.67, +14.0%, TV 77.7%. |
| 2 | V4 note | py/dcf.py:91-93 | The terminal FCFF keeps the FY2030 ΔNWC computed at 2.6% growth, not at g = 2.0%. The Executor documents this (plan formula kept as written). | ΔNWC at g would be about 2.43 m vs 3.08 m, so fcff_tv is about +0.65 m and value about +EUR 0.08/share. Immaterial. |

## Verifier details
**V1.** `run.py --fresh --through 3` succeeded twice with no manual steps. Fingerprints are saved in `verify/fp_step03.txt`: forecast_assumptions 19 rows / 165131166181891473612, forecast_fcff 5 / 23714476038502305789, valuation 35 / 326047371952931037148, multiples_check 2 / 13893529367532981564. `--compare` reports "PASS fingerprints identical". check_step01 128/128, check_step02 78/78, check_step03 148/148.

**V2.** I compared the checks line by line with plan step 3. They cover 5 rows and the FCFF identity (1e-9); FY2026 ΔNWC from FY2025 actual NWC; revenue 3,991.531 ±0.001; the growth formula (1e-12); guidance bridge 680 ±0.5 with an independent parse of the PDF guidance and the AR2025 625,077 line; the linear margin path (1e-12) and 8-16%; capex/D&A ≥ 0.9 as FRAGILE (actual 1.211); FCFF 250-650; non-empty note and source; tau 0.1506/4.1506 ±0.0001; PV, TV, EV (1e-6); bridge and upside recomputed; exact raw multiples 9.452668 and 10.626402; SURPRISE smell tests; and the hard limits (TV 50-95%, EUR 15-120, implied multiple 5-25x). Nothing is missing or loosened. The pasted output matches my run.

**V3.** `verify/verify_step03.py` (SQL from `hist_statements`/`hist_other_inputs`, with revenue compounded via exp(sum(ln(1+g))) and `date_diff` for tau):

| item | Verifier | Executor | rel diff |
|---|---|---|---|
| FCFF 2026 / 2030 | 355.1541718754 / 389.1550618517 | same | ≤3.2e-16 |
| fcff_tv 2030 | 368.5726026299 | 368.5726026299 | 0 |
| sum PV FCFF | 1,634.9608117033 | same | 0 |
| TV Gordon | 8,315.8886115158 | same | 0 |
| EV | 8,032.8982839771 | same | 1.1e-16 |
| equity value | 8,448.2962839771 | same | 0 |
| value per share | 56.4724371482 | same | 0 |
| upside_pct | -0.1974846086 | same | 0 |
| exit vps Europe / Global | 48.2803 / 52.5734 | same | ≤2.7e-16 |
| implied Gordon EV/EBITDA | 11.6924x | 11.6924x | n/a |

**V4.** `dcf.py` and `03_forecast_valuation.py` implement the brief's definitions of FCFF (capex includes ROU, 9A), tax (8A), Gordon TV, year-end discounting at (31 Dec − 2026-11-06)/365.25, and the equity bridge (all 7 items with the correct signs, divided by diluted shares). There are no joins, so no fan-out and no silent drops. No NULLs feed the arithmetic (fcff_tv is NULL by design except in FY2030). Integer division is not an issue. Header comments are present and true. Data quality log entries 18-20 were added. I traced these documentation claims to raw lines: guidance €670-690 m (PR_H1_2026 p.6 l.8, raised from 640-660); H1 revenue +5.8% (p.1 l.10); AR2025 p.187 l.41 "625,077"; p.23 l.26 bucket (35.9); p.163 l.23 30,271 stock-option cost. Every evidence-pack number is reproduced by code.

**V5.** WACC 6.52% and g 2.0% sit in the expected bands. FCFF of 355-389 m vs FY2025 operating cash after capex of 457.8 m is plausible given the higher capex (ROU) and tax. The FY2026E margin of 12.82% is inside the FY2021-25 range of 8.1-13.0%. Implied exit multiple 11.7x vs Damodaran 9.5x/10.6x. Value/price +24.6% and TV share 79.6% raise no SURPRISE, but see finding 1. The low-beta risk flagged in the plan is the main reason the value sits above the price.

**V6.** See finding 1 for the table. g, margin path, tax and ROU are the judgment calls. The base vs price ordering never flips.

**V7.** Executor cases: (1) FY2026 FCFF 355.154 ✓; (2) guidance bridge 680.000, with sbc 34.250 = 625.077 − 459.782 − 131.045 ✓ (raw lines confirmed); (3) tau 55/365.25 = 0.150582 ✓; (4) fcff_tv 368.573, TV 8,315.889 ✓; (5) bridge 8,448.296 / 149.600349 = 56.4724 ✓. Verifier cases (`verify/spot_step03.py`, seed 20261109): **FY2027 PV** recomputed by hand from the row and WACC = 340.909556, which matches `valuation.pv_fcff_2027` with diff 0 ✓. **FY2021 capex %** traced to raw PDF lines: AR2022 p.87 l.17 intangibles (16,723) and l.19 PP&E (88,373) in the comparative column, plus AR2021 p.101 l.40 ROU additions 30,018, over revenue = 0.0419401990, equal to `hist_ratios.capex_pct` ✓.

Commands run: `run.py --fresh --through 3` (x2), `checks/fingerprint.py --save/--compare`, `checks/check_step01..03.py`, `verify/verify_step03.py` (plus `--quiet` variants), `verify/spot_step03.py`.

---
(Executor's section follows)

# Step 03: Forecast FCFF and value the base case. Status: AWAITING VERIFICATION

## What was done
- Built every forecast driver from step-1 history, the H1 2026 guidance and Decisions 7-9, each with its rule, source and note, in `forecast_assumptions`. Revenue growth is 5.0% in FY2026E, fading by (5.0% - g) x (t - 2026)/5 to 2.6% in FY2030E. D&A is 3.317% and capex 4.018% of revenue (FY2021-25 averages, capex including ROU additions per Decision 9A), and NWC is 2.652% of revenue (FY2025). Tax is 24.13% (FY2021-25 median) and 27.81% in the terminal FCFF (Decision 8A).
- Bridged the FY2026 guidance (adjusted EBITDA EUR 670-690 m, midpoint 680 parsed from PR_H1_2026 p.6) to the brief's adjusted EBIT. I subtracted forecast D&A and share-based cost. The share-based cost is FY2025's 34.250 m (0.90% of revenue), derived from the AR2025 segment note's adjusted EBITDA of 625.077. The FY2026E margin comes out at 12.82%, fading linearly to the FY2024-25 average of 12.21% by FY2030E.
- Wrote one pure DCF engine, `py/dcf.py` (`value_per_share(params)`, plus `load_base_params(con)` and `exit_multiple_value`), which step 4 will reuse. It discounts year-end FCFF to 2026-11-06 with year fractions, adds the Gordon TV, and walks EV to equity with the step-2 bridge.
- Base case: EV 8,032.9 m, equity 8,448.3 m, **EUR 56.47 per share** against a price of 45.32 (upside_pct = price/value - 1 = -19.7%). TV is 79.6% of EV. The Damodaran Furn/Home EV/EBITDA exit cross-check gives EUR 48.28 on the Europe multiple of 9.45x (-14.5%) and EUR 52.57 on the Global multiple of 10.63x (-6.9%). The implied Gordon multiple is 11.69x.

## Files
| File | Purpose |
|------|---------|
| `py/dcf.py` | Shared DCF engine: `value_per_share(params) -> dict` (pure), `bridge_equity`, `exit_multiple_value`, `load_base_params(con)` |
| `py/03_forecast_valuation.py` | Derives the drivers (history, guidance parse, share-based cost) -> `forecast_assumptions`, runs `dcf.value_per_share` once -> `forecast_fcff`, `valuation`, `multiples_check` |
| `checks/check_step03.py` | 148 acceptance checks (plan step 3), with independent recomputation |
| `run.py` | Step 3 registered: `3: ["py/03_forecast_valuation.py"]` |
| `evidence/data_quality_log.md` | Step 3 section (entries 18-20) |

## Row flow
| Table | Rows in | Rows out | Why the difference |
|-------|---------|----------|--------------------|
| hist_ratios, wacc, raw_report_lines -> forecast_assumptions | 5 + 2 + 2 parsed lines | 19 | 16 scalar drivers + 2 path drivers (growth, margin; `value_by_year` text) + wacc |
| forecast_assumptions, bridge_inputs, wacc -> forecast_fcff | | 5 | One row per FY2026E-30E; `fcff_tv` / `nopat_tv` only on FY2030 |
| forecast_fcff, bridge_inputs -> valuation | 5 + 9 bridge items | 35 | 2 rates + 5 tau + 5 discount factors + 5 PV + 6 EV lines + 7 bridge items + equity + 4 per-share lines |
| raw_damodaran_vebitda_europe / _global -> multiples_check | 1 row each (Furn/Home Furnishings) | 2 | Europe and Global |

`python run.py --fresh --through 3` rebuilds from scratch. Two fresh rebuilds give identical fingerprints for all 4 step-3 tables (`checks/fingerprint.py --compare`: "PASS fingerprints identical"). Checks 1 (128/128) and 2 (78/78) still pass.

## Check results
```
PASS  forecast_fcff has exactly fy 2026-2030  (actual=[2026, 2027, 2028, 2029, 2030] expected=[2026, 2027, 2028, 2029, 2030])
PASS  forecast_fcff: no nulls in core columns  (actual=0 expected=0)
PASS  FCFF identity FY2026: fcff = adj_ebit x (1 - t) + da - capex - delta_nwc  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  nopat = adj_ebit x (1 - t) FY2026  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  adj_ebit = margin x revenue FY2026  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  FCFF identity FY2027: fcff = adj_ebit x (1 - t) + da - capex - delta_nwc  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  nopat = adj_ebit x (1 - t) FY2027  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  adj_ebit = margin x revenue FY2027  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  FCFF identity FY2028: fcff = adj_ebit x (1 - t) + da - capex - delta_nwc  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  nopat = adj_ebit x (1 - t) FY2028  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  adj_ebit = margin x revenue FY2028  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  FCFF identity FY2029: fcff = adj_ebit x (1 - t) + da - capex - delta_nwc  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  nopat = adj_ebit x (1 - t) FY2029  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  adj_ebit = margin x revenue FY2029  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  FCFF identity FY2030: fcff = adj_ebit x (1 - t) + da - capex - delta_nwc  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  nopat = adj_ebit x (1 - t) FY2030  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  adj_ebit = margin x revenue FY2030  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  FY2026 delta_nwc = nwc_2026 - FY2025 actual NWC  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  delta_nwc FY2027 = nwc - prior nwc  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  delta_nwc FY2028 = nwc - prior nwc  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  delta_nwc FY2029 = nwc - prior nwc  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  delta_nwc FY2030 = nwc - prior nwc  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  FY2026E revenue = 3,801.458 x 1.05 = 3,991.531 (+/-0.001)  (actual=3991.5309 expected in [3991.53, 3991.532])
PASS  FY2025 revenue base = 3,801.458  (actual=3801.458 expected in [3801.4575, 3801.4585])
PASS  growth FY2026 = 5.0% - (5.0% - g) x (t - 2026)/5 = 5.0000%  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  revenue FY2026 = prior x (1 + growth)  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  growth FY2027 = 5.0% - (5.0% - g) x (t - 2026)/5 = 4.4000%  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  revenue FY2027 = prior x (1 + growth)  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  growth FY2028 = 5.0% - (5.0% - g) x (t - 2026)/5 = 3.8000%  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  revenue FY2028 = prior x (1 + growth)  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  growth FY2029 = 5.0% - (5.0% - g) x (t - 2026)/5 = 3.2000%  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  revenue FY2029 = prior x (1 + growth)  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  growth FY2030 = 5.0% - (5.0% - g) x (t - 2026)/5 = 2.6000%  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  revenue FY2030 = prior x (1 + growth)  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  da FY2026 = FY2021-25 average D&A % x revenue  (actual=2.842170943040401e-14 expected in [-1e-09, 1e-09])
PASS  capex FY2026 = FY2021-25 average capex % (incl. ROU, Decision 9) x revenue  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  nwc FY2026 = FY2025 NWC % x revenue  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  tax_rate FY2026 = median FY2021-25 effective rate (Decision 8A)  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  da FY2027 = FY2021-25 average D&A % x revenue  (actual=2.842170943040401e-14 expected in [-1e-09, 1e-09])
PASS  capex FY2027 = FY2021-25 average capex % (incl. ROU, Decision 9) x revenue  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  nwc FY2027 = FY2025 NWC % x revenue  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  tax_rate FY2027 = median FY2021-25 effective rate (Decision 8A)  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  da FY2028 = FY2021-25 average D&A % x revenue  (actual=2.842170943040401e-14 expected in [-1e-09, 1e-09])
PASS  capex FY2028 = FY2021-25 average capex % (incl. ROU, Decision 9) x revenue  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  nwc FY2028 = FY2025 NWC % x revenue  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  tax_rate FY2028 = median FY2021-25 effective rate (Decision 8A)  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  da FY2029 = FY2021-25 average D&A % x revenue  (actual=2.842170943040401e-14 expected in [-1e-09, 1e-09])
PASS  capex FY2029 = FY2021-25 average capex % (incl. ROU, Decision 9) x revenue  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  nwc FY2029 = FY2025 NWC % x revenue  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  tax_rate FY2029 = median FY2021-25 effective rate (Decision 8A)  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  da FY2030 = FY2021-25 average D&A % x revenue  (actual=2.842170943040401e-14 expected in [-1e-09, 1e-09])
PASS  capex FY2030 = FY2021-25 average capex % (incl. ROU, Decision 9) x revenue  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  nwc FY2030 = FY2025 NWC % x revenue  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  tax_rate FY2030 = median FY2021-25 effective rate (Decision 8A)  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  guidance range found in PR_H1_2026 p.6  (actual=True expected=True)
PASS  guidance midpoint = 680  (actual=680.0 expected in [679.999, 680.001])
PASS  guidance bridge FY2026E: adj_ebit + da + share-based cost = 680 (+/-0.5)  (actual=679.9999999999999 expected in [679.5, 680.5])
PASS  FY2025 share-based cost = adj EBITDA 625.077 - EBIT - D&A - non-recurring (about 34.25)  (actual=34.25000000000006 expected in [34.0, 34.5])
PASS  share_based_cost FY2026 = FY2025 % x revenue  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  share_based_cost FY2027 = FY2025 % x revenue  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  share_based_cost FY2028 = FY2025 % x revenue  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  share_based_cost FY2029 = FY2025 % x revenue  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  share_based_cost FY2030 = FY2025 % x revenue  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  margin FY2026 on the linear path to FY2024-25 average 12.2116%  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  margin FY2026 within 8-16%  (actual=0.12817820275279065 expected in [0.08, 0.16])
PASS  margin FY2027 on the linear path to FY2024-25 average 12.2116%  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  margin FY2027 within 8-16%  (actual=0.12666270305570704 expected in [0.08, 0.16])
PASS  margin FY2028 on the linear path to FY2024-25 average 12.2116%  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  margin FY2028 within 8-16%  (actual=0.12514720335862345 expected in [0.08, 0.16])
PASS  margin FY2029 on the linear path to FY2024-25 average 12.2116%  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  margin FY2029 within 8-16%  (actual=0.12363170366153985 expected in [0.08, 0.16])
PASS  margin FY2030 on the linear path to FY2024-25 average 12.2116%  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  margin FY2030 within 8-16%  (actual=0.12211620396445624 expected in [0.08, 0.16])
INFO  FY2030E capex / D&A = 1.211 (>= 0.9)
PASS  FCFF FY2026 between 250 and 650 m  (actual=355.1541718754005 expected in [250, 650])
PASS  FCFF FY2027 between 250 and 650 m  (actual=366.59446649786025 expected in [250, 650])
PASS  FCFF FY2028 between 250 and 650 m  (actual=376.18674017699885 expected in [250, 650])
PASS  FCFF FY2029 between 250 and 650 m  (actual=383.75519614695395 expected in [250, 650])
PASS  FCFF FY2030 between 250 and 650 m  (actual=389.1550618516636 expected in [250, 650])
PASS  fcff_tv = FY2030 FCFF at marginal tax 27.81%  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  marginal tax = 27.81%  (actual=0.2781 expected in [0.27809999, 0.27810001])
PASS  fcff_tv only on FY2030  (actual=0 expected=0)
PASS  forecast_assumptions: every driver has a non-empty note, source and rule  (actual=0 expected=0)
PASS  forecast_assumptions: driver unique  (actual=0 expected=0)
PASS  forecast_assumptions: terminal_g = 2.0%  (actual=0.02 expected=0.02)
PASS  forecast_assumptions has driver 'revenue_growth'  (actual=1 expected=1)
PASS  forecast_assumptions has driver 'adj_ebit_margin'  (actual=1 expected=1)
PASS  forecast_assumptions has driver 'da_pct'  (actual=1 expected=1)
PASS  forecast_assumptions has driver 'capex_pct'  (actual=1 expected=1)
PASS  forecast_assumptions has driver 'nwc_pct'  (actual=1 expected=1)
PASS  forecast_assumptions has driver 'tax_rate_forecast'  (actual=1 expected=1)
PASS  forecast_assumptions has driver 'tax_rate_terminal'  (actual=1 expected=1)
PASS  forecast_assumptions has driver 'share_based_pct'  (actual=1 expected=1)
PASS  forecast_assumptions has driver 'terminal_g'  (actual=1 expected=1)
PASS  valuation: item unique  (actual=0 expected=0)
PASS  valuation: no null values  (actual=0 expected=0)
PASS  valuation wacc = wacc table base row  (actual=0.06520792331945185 expected=0.06520792331945185)
PASS  valuation terminal_g = 2.0%  (actual=0.02 expected=0.02)
PASS  tau_2026 = 0.1506 (+/-0.0001)  (actual=0.15058179329226556 expected in [0.1505, 0.1507])
PASS  tau_2030 = 4.1506 (+/-0.0001)  (actual=4.1505817932922655 expected in [4.1505, 4.1507])
PASS  tau_2026 = (31 Dec 2026 - 2026-11-06)/365.25  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  pv_fcff_2026 recomputed  (actual=0.0 expected in [-1e-06, 1e-06])
PASS  tau_2027 = (31 Dec 2027 - 2026-11-06)/365.25  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  pv_fcff_2027 recomputed  (actual=0.0 expected in [-1e-06, 1e-06])
PASS  tau_2028 = (31 Dec 2028 - 2026-11-06)/365.25  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  pv_fcff_2028 recomputed  (actual=0.0 expected in [-1e-06, 1e-06])
PASS  tau_2029 = (31 Dec 2029 - 2026-11-06)/365.25  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  pv_fcff_2029 recomputed  (actual=0.0 expected in [-1e-06, 1e-06])
PASS  tau_2030 = (31 Dec 2030 - 2026-11-06)/365.25  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  pv_fcff_2030 recomputed  (actual=0.0 expected in [-1e-06, 1e-06])
PASS  sum_pv_fcff recomputed  (actual=2.2737367544323206e-13 expected in [-1e-06, 1e-06])
PASS  tv_gordon = fcff_tv x (1 + g)/(wacc - g)  (actual=0.0 expected in [-1e-06, 1e-06])
PASS  pv_tv discounted at tau_2030  (actual=9.094947017729282e-13 expected in [-1e-06, 1e-06])
PASS  ev = sum PV + PV TV  (actual=9.094947017729282e-13 expected in [-1e-06, 1e-06])
PASS  tv_share_of_ev = pv_tv / ev  (actual=1.1102230246251565e-16 expected in [-1e-12, 1e-12])
PASS  valuation bank_debt = bridge_inputs bank_debt  (actual=227.043 expected=227.043)
PASS  valuation other_financial_payables = bridge_inputs other_financial_payables  (actual=212.18 expected=212.18)
PASS  valuation lease_liabilities = bridge_inputs lease_liabilities  (actual=94.37 expected=94.37)
PASS  valuation cash = bridge_inputs cash  (actual=998.448 expected=998.448)
PASS  valuation cash_like_financial_assets = bridge_inputs cash_like_financial_assets  (actual=304.74399999999997 expected=304.74399999999997)
PASS  valuation distributions_2026 = bridge_inputs distributions_2026  (actual=156.4 expected=156.4)
PASS  valuation minority_book = bridge_inputs minority_book  (actual=197.801 expected=197.801)
PASS  valuation diluted_shares = bridge_inputs diluted_shares  (actual=149.6003486054722 expected=149.6003486054722)
PASS  valuation price = bridge_inputs price  (actual=45.32 expected=45.32)
PASS  equity_value = EV + cash + cash-like - debt - other fin. payables - leases - distributions - minorities  (actual=0.0 expected in [-1e-06, 1e-06])
PASS  value_per_share = equity / diluted shares  (actual=0.0 expected in [-1e-08, 1e-08])
PASS  upside_pct = price / value - 1  (actual=0.0 expected in [-1e-10, 1e-10])
PASS  minorities at book flagged as a simplification in the note column  (actual=True expected=True)
PASS  multiples_check has 2 rows  (actual=2 expected=2)
PASS  Europe Furn/Home ev_ebitda equals the raw cell exactly  (actual=9.45266833743719 expected=9.45266833743719)
PASS  Global Furn/Home ev_ebitda equals the raw cell exactly  (actual=10.626401957357944 expected=10.626401957357944)
PASS  Europe Furn/Home ev_ebitda = 9.452668  (actual=9.45266833743719 expected in [9.4526675, 9.4526685])
PASS  Global Furn/Home ev_ebitda = 10.626402  (actual=10.626401957357944 expected in [10.6264015, 10.6264025])
PASS  [Europe] fy2030_ebitda = adj_ebit + da FY2030  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  [Europe] tv_exit = multiple x FY2030 EBITDA  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  [Europe] ev_exit = sum PV + PV(exit TV)  (actual=0.0 expected in [-1e-06, 1e-06])
PASS  [Europe] value_per_share_exit via the same bridge  (actual=0.0 expected in [-1e-08, 1e-08])
PASS  [Europe] pct_vs_gordon = exit / Gordon - 1  (actual=0.0 expected in [-1e-10, 1e-10])
PASS  [Europe] implied_gordon_ev_ebitda = TV Gordon / FY2030 EBITDA  (actual=0.0 expected in [-1e-10, 1e-10])
INFO  [Europe] exit 9.45x -> EUR 48.28/share, -14.5% vs Gordon
PASS  [Global] fy2030_ebitda = adj_ebit + da FY2030  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  [Global] tv_exit = multiple x FY2030 EBITDA  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  [Global] ev_exit = sum PV + PV(exit TV)  (actual=0.0 expected in [-1e-06, 1e-06])
PASS  [Global] value_per_share_exit via the same bridge  (actual=-1.4210854715202004e-14 expected in [-1e-08, 1e-08])
PASS  [Global] pct_vs_gordon = exit / Gordon - 1  (actual=-2.220446049250313e-16 expected in [-1e-10, 1e-10])
PASS  [Global] implied_gordon_ev_ebitda = TV Gordon / FY2030 EBITDA  (actual=0.0 expected in [-1e-10, 1e-10])
INFO  [Global] exit 10.63x -> EUR 52.57/share, -6.9% vs Gordon
PASS  HARD: TV share of EV within 50-95%  (actual=0.7964668848148498 expected in [0.5, 0.95])
PASS  HARD: value per share within EUR 15-120  (actual=56.47243714823831 expected in [15, 120])
PASS  HARD: implied Gordon EV/EBITDA within 5x-25x  (actual=11.692397259392434 expected in [5, 25])
INFO  smell: TV share of EV 79.6% <= 80%
INFO  smell: value / price - 1 = +24.6% (within +/-30%)
PASS  py/dcf.py value_per_share(load_base_params) == valuation value_per_share  (actual=56.47243714823831 expected=56.47243714823831)

148/148 checks passed
```
No SURPRISE and no FRAGILE flag was raised. Two things sit close to their thresholds and are worth a look in the final review: TV share is 79.6% (smell limit 80%), and value/price - 1 is +24.6% (smell limit +/-30%).

## Spot-check cases for the human
1. **Typical: the FY2026E FCFF row.** Revenue 3,801.458 x 1.05 = 3,991.531. Adjusted EBIT 12.818% x 3,991.531 = 511.627; NOPAT at 24.130% = 388.172. D&A 3.317% = 132.410; capex 4.018% = 160.387. NWC 2.652% x revenue = 105.867, minus FY2025 actual NWC 100.826 = delta 5.041. FCFF = 388.172 + 132.410 - 160.387 - 5.041 = **355.154** (`forecast_fcff` fy 2026). This is correct under the brief's FCFF definition, with capex including ROU additions (Decision 9A).
2. **Guidance bridge (Decision 7).** PR_H1_2026 PDF p.6 lines 7-8: "...bringing the range to €670 - €690 million"; midpoint 680. FY2025 share-based cost = 625.077 (AR2025 p.187 line 41, "EBITDA adjusted (***) ... 625,077") - 458.145 (EBIT) - 131.045 (amortization) - 1.637 (IS non-recurring add-back) = 34.250, which is 0.901% of FY2025 revenue. Cross-check: 35.9 bucket (AR2025 p.23 line 26) - 1.637 = 34.263. FY2026E: 511.627 + 132.410 + 35.963 = **680.000** (`forecast_fcff.adj_ebitda_mgmt`).
3. **Edge: the stub year.** tau_2026 = (2026-12-31 - 2026-11-06) / 365.25 = 55 / 365.25 = **0.150582**. Discount factor 1/1.065208^0.150582 = 0.990533, so PV of FY2026E = 351.792. Under Decision 1A the full FY2026E FCFF is counted because net debt is taken at 31 Dec 2025, and the 156.4 m H1 2026 distributions are deducted separately in the bridge.
4. **Edge: the terminal FCFF (Decision 8A).** FY2030E FCFF at 24.13% tax = 389.155. The same year at the marginal 27.81% gives `fcff_tv` = 559.291 x 0.7219 + 151.931 - 184.032 - 3.078 = **368.573**. TV = 368.573 x 1.02 / (0.065208 - 0.02) = 8,315.889; PV at tau 4.150582 = 6,397.937. Implied EV/EBITDA = 8,315.889 / 711.222 = 11.69x, against Damodaran Furn/Home 9.45x (Europe) and 10.63x (Global).
5. **Bridge to value per share.** EV 8,032.898 + cash 998.448 + cash-like 304.744 - bank debt 227.043 - other financial payables 212.180 - leases 94.370 - distributions 156.400 - minorities at book 197.801 (flagged SIMPLIFICATION) = 8,448.296. Divided by 149.600349 m diluted shares = **EUR 56.4724**. upside_pct = 45.32 / 56.4724 - 1 = **-19.75%**, so the price is below the base-case value.

## Deviations, disputes, changes to earlier steps
- **No changes to earlier steps.** `run.py` only gained the step-3 entry.
- **Extra columns and rows (additive, no definition change):**
  - `forecast_assumptions` has a numeric `value` column for scalar drivers. `value_by_year` is text and is only filled for the two path drivers.
  - `forecast_fcff` adds `share_based_cost` and `adj_ebitda_mgmt` (for the guidance-bridge check) and `nopat_tv`.
  - `valuation` has the columns line_no, section, item, fy, value, unit, treatment and note. Bridge items are stored as positive magnitudes, with `treatment` = add/deduct. It also carries `wacc` and `terminal_g` rows.
  - `multiples_check` adds `pv_tv_exit`, `equity_value_exit` and `source`.
- **"upside_pct" sign:** as the plan defines it, upside_pct = price / value - 1. A negative value means the market price sits below the DCF value. Step 5's headline wording must follow this sign ("price ... 19.7% below the base-case value").
- **Growth fade:** the plan's formula divides by 5, so FY2030E growth is 2.6%, not g. The FY2030E delta NWC in the terminal FCFF (3.078) therefore reflects 2.6% growth rather than 2.0%. I kept the plan's formula and terminal-FCFF definition as written and did not normalise them.
- **Damodaran row choice:** I used the `ev_ebitda` column per the plan (data quality log #20).
- **Plan constants typed in code:** 0.05, 0.02 and the /5 fade (Decision 7) are named `DECISION_*` constants in `py/03_forecast_valuation.py`. Every other number is read from DuckDB.

<!-- The Verifier appends its section below. -->
