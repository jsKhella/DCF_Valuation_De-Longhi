# Step 04: Run the sensitivity grid and the Monte Carlo. Verdict: PASS WITH NOTES

## Summary for the human (one page max)
- Headline numbers (all recomputed with the Verifier's own vectorised numpy DCF, built from the brief/plan definitions and the verified step 1-3 inputs, not importing `py/dcf.py`; percentiles with numpy 'linear'):
  - MC p10 EUR 44.3414 (Executor) = 44.3414 (Verifier) ✓, rel diff 1e-16
  - MC p90 EUR 74.0800 (Executor) = 74.0800 (Verifier) ✓
  - Price percentile 12.03 (Executor) = 12.03 (Verifier; 1,203 of 10,000 runs strictly below EUR 45.32) ✓
  - Also matched: p5/p25/p50/p75/p95, mean 58.1657, sd 12.3948, all 10,000 run values (max rel diff 1.6e-15), all 25 grid cells (max rel diff 6.7e-16), beta line EUR 35.5996, base/run 0 EUR 56.4724.
- Rows: 25 grid cells, 1 beta line, 11 params, 10,000 runs (run_id 1..10000), 1 summary row, 54 histogram bins summing to 10,000 (recounted with pandas.cut: 0 mismatches) ✓
- Draws: reproduced bit-for-bit from the documented generator `random.Random(20261109)` by the Verifier's own loop (0 mismatching runs). sd growth 1.515 pp, sd margin 1.007 pp, corr 0.516, WACC in [3.307%, 9.172%] inside [3.0%, 9.521%]; KS tests vs N(0,1.5pp) p = 0.28, N(0,1.0pp) p = 0.55, truncated N(base,0.75pp) p = 0.08; WACC uncorrelated with shifts (-0.013, -0.014) ✓
- Checks: 66/66 pass; every plan check present and not weakened (several extra checks added); steps 1-3 still pass (128/128, 78/78, 148/148) ✓
- Reproducible: two `run.py --fresh --through 4` rebuilds, identical fingerprints for all 6 tables (`verify/fp_step04.txt`) ✓
- Notes: **FRAGILE** (price inside the 80% MC range, see finding 1). No SURPRISE: the price sits inside [p10, p90].
- Spot-checks: Executor runs 1, 2057, 4062, 4634, 9545, grid corner, beta line; Verifier runs 4746, 7823 (seeded). All traced ✓
- Needs your decision: no (the FRAGILE note goes to the final review)

## Findings (only if FAIL or NOTES)
| # | Level | File:line | Problem | Evidence |
|---|-------|-----------|---------|----------|
| 1 | V6 FRAGILE | py/04_sensitivity_mc.py:47-53 (Decision 6 constants) | The conclusion "the market price is inside the Monte Carlo 10th-90th range" holds only narrowly: the price (45.32) is EUR 0.98 above p10 (44.34), at the 12.0th percentile. It is stable across seeds but flips under reasonable alternative Decision 6 parameters. | Verifier's numpy draws (`verify/sens_step04.py`): seeds 1-5 give percentile 11.5-12.3, always inside. rho = 0: p10 45.37, percentile 9.9, **outside**. WACC sd 0.5 pp: p10 46.07, percentile 8.2, **outside**. Margin sd 0.5 pp: p10 45.99, percentile 8.3, **outside**. rho 0.8, WACC sd 1.0 pp, growth sd 1.0/2.0 pp and margin sd 1.5 pp: still inside (percentile 10.5-15.4). |
| 2 | V4 note (not an error) | py/04_sensitivity_mc.py:95 / py/dcf.py:67 | Grid g also moves the end point of the growth fade (Decision 7 "towards g"). This is a defensible reading and it is documented (DQ log #22). | With the fade held at 2.0%, the grid cells move by at most 1.5% (`verify/verify_step04.py`, reading B). The monotonicity and centre-cell conclusions are unchanged, so it is not FRAGILE. |

## Verifier details
Commands run (venv interpreter):
1. `run.py --fresh --through 4` → OK; `checks/fingerprint.py --save verify/fp_step04.txt sensitivity beta_sensitivity mc_params mc_runs mc_summary mc_histogram`.
2. `run.py --fresh --through 4` again; `--compare` → "PASS fingerprints identical" (mc_runs 10000 / 92558926622417105030481, etc., which equals the Executor's pasted values).
3. `checks/check_step01..04.py` → 128/128, 78/78, 148/148, 66/66. The step-4 output matches the evidence pack line for line.
4. V2 audit vs plan step 4: 25 rows, unique, no nulls, grid values, centre |diff| < 1e-9, strict monotonicity, wacc - g >= 1 pp (min 2.52 pp); beta wacc exact plus the same dcf path; 10,000 rows, run_id 1..10000, seed, rerun determinism; sd ±3%, corr ±0.03, truncation bounds; run 0 exact; percentile ordering, |p50/base - 1| <= 10% (actual 0.19%), price percentile with strict "<", histogram sum; smell test printed. Tolerances are identical to the plan's. Nothing is weakened.
5. `verify/verify_step04.py` (V3, written before reading the Executor's code): independent vectorised DCF (growth fade, linear margin path, D&A/capex as FY2021-25 average % recomputed from `hist_ratios`, NWC at FY2025 %, median effective tax for the forecast and 27.81% for the terminal FCFF, tau = days/365.25 from 2026-11-06, Gordon on fcff_tv, bridge from `bridge_inputs` with shares = issued - treasury + dilutive).

| metric | Executor | Verifier | rel diff |
|---|---|---|---|
| base / run 0 | 56.472437148238 | 56.472437148238 | 2e-16 |
| beta line | 35.599618889791 | 35.599618889791 | 0 |
| p5 | 41.606316423235 | 41.606316423235 | 2e-16 |
| p10 | 44.341405464229 | 44.341405464229 | 1e-16 |
| p50 | 56.364259834952 | 56.364259834952 | 2e-16 |
| p90 | 74.079999119486 | 74.079999119486 | 2e-16 |
| p95 | 81.088446768459 | 81.088446768459 | 2e-16 |
| mean | 58.165706735244 | 58.165706735244 | 0 |
| sd | 12.394766123850 | 12.394766123850 | 2e-16 |
| price percentile | 12.03 | 12.03 | 0 |

6. V4 code review (`py/04_sensitivity_mc.py`, `py/dcf.py`): the Decision 6 construction z_m = rho z_g + sqrt(1 - rho^2) z_2 is correct; truncation is by redraw (a true truncated normal, 0 redraws occurred); g is held at 2.0% in the MC; the shifts apply to every forecast year, including the FY2030 base of the terminal FCFF; the percentile uses strict "<" per plan; there are no joins (no fan-out risk). Headers are present and accurate, DQ log entries #21-22 are added, and the evidence numbers match the code output.
7. V5 smell: value distribution min 28.89, p1 36.63, p50 56.36, p99 97.34, max 161.40 (right skew from convexity in WACC, DQ #21: verified 6 runs with WACC < 4% and 74 runs > EUR 100). The p50 is within 0.2% of base. Price inside [p10, p90], so there is no SURPRISE. The beta line (-37.0%) confirms the plan's "beta dominates" risk.
8. V6: `verify/sens_step04.py`, see finding 1.
9. V7 traced (`verify/spot_step04.py`): run 1 57.638355 ✓; run 2057 45.300201 (< price) ✓; run 4062 45.310969 (< price) ✓; run 4634 45.327976 (not below) ✓; run 9545 161.395600 (max) ✓; grid corner (5.52%, 3.0%) 95.902432 ✓; beta line 35.599619 ✓. Own cases (numpy default_rng(4242)): run 4746 73.302305 ✓; run 7823 63.726184 ✓.
---
(Executor's section follows)

# Step 04: Run the sensitivity grid and the Monte Carlo. Status: AWAITING VERIFICATION

## What was done
- Re-ran the step-3 DCF engine (`py/dcf.py`, unchanged) on a 5 x 5 grid: WACC = base 6.52% -1.0 to +1.0 pp (step 0.5) x g = 1.0-3.0% (step 0.5). Values range from EUR 41.20 (WACC 7.52%, g 1.0%) to EUR 95.90 (WACC 5.52%, g 3.0%). The centre cell equals the base case, EUR 56.4724, exactly.
- Beta sensitivity line: the step-2 'beta_sensitivity' WACC (Global Furn/Home cash-corrected beta_u 0.938, WACC 9.62%) through the same engine gives EUR 35.60 per share, EUR 20.87 (-37.0%) below the base.
- Monte Carlo per Decision 6: 10,000 runs, seed 20261109 (Python stdlib `random.Random`, Mersenne Twister). The growth and margin shifts are correlated through z_m = 0.5 z_g + sqrt(0.75) z_2. WACC ~ N(base, 0.75 pp), with redraws outside [3.0%, 9.52%] (0 redraws were needed). g is held at 2.0%. Each run calls the same `run_value` -> `dcf.value_per_share` path. Run 0 (zero shifts, base WACC) equals the step-3 value exactly.
- Results: p10 EUR 44.34, p50 56.36, p90 74.08 (mean 58.17, sd 12.39). The price of EUR 45.32 sits at the 12.03rd percentile (1,203 of 10,000 runs are below it), inside [p10, p90], so the smell test raises no SURPRISE. The histogram has 54 bins of EUR 2.5.
- Determinism: the check script reruns `py/04_sensitivity_mc.py` and compares the `mc_runs` fingerprints. Separately, two `run.py --fresh --through 4` rebuilds give identical fingerprints for all 6 step-4 tables.

## Files
| File | Purpose |
|------|---------|
| `py/04_sensitivity_mc.py` | Builds sensitivity, beta_sensitivity, mc_params, mc_runs, mc_summary and mc_histogram. `run_value()` and `draw_runs()` are module functions; `main()` is guarded so the check can import them |
| `checks/check_step04.py` | 66 acceptance checks (plan step 4), including the rerun-twice determinism test and recomputation of all 10,000 runs |
| `run.py` | Step 4 registered: `4: ["py/04_sensitivity_mc.py"]` |
| `evidence/data_quality_log.md` | Step 4 section (entries 21-22) |

## Row flow
| Table | Rows in | Rows out | Why the difference |
|-------|---------|----------|--------------------|
| forecast_assumptions, wacc, bridge_inputs -> sensitivity | base params | 25 | 5 WACC x 5 g |
| wacc ('beta_sensitivity' row) -> beta_sensitivity | 1 | 1 | One line |
| (constants of Decision 6) -> mc_params | | 11 | seed, n_runs, 2 shift sds, rho, WACC mean/sd/lower/upper, g, histogram bin width |
| base params + 10,000 draws -> mc_runs | | 10,000 | run_id 1..10000; run 0 is not stored as a row, it is in `mc_summary.run0_value_per_share` |
| mc_runs -> mc_summary | 10,000 | 1 | Percentiles 5-95, mean, sd, price, price percentile, base and run-0 values, n_wacc_redraws |
| mc_runs -> mc_histogram | 10,000 | 54 bins (sum 10,000) | Bins [lo, hi) of EUR 2.5 from 27.5 to 162.5; zero-count bins are kept in the tail |

Fingerprints after `run.py --fresh --through 4` (identical across two fresh rebuilds): sensitivity 25 / 211612140954553477047; beta_sensitivity 1 / 14954831024859884661; mc_params 11 / 54931069627522448737; mc_runs 10000 / 92558926622417105030481; mc_summary 1 / 10622573609439084133; mc_histogram 54 / 536392324687718055623. Checks 01 (128/128), 02 (78/78) and 03 (148/148) still pass.

## Check results
```
PASS  py/04_sensitivity_mc.py reruns without error  (actual=True expected=True)
PASS  determinism: mc_runs fingerprint identical across two runs of the script  (actual='mc_runs\t10000\t92558926622417105030481' expected='mc_runs\t10000\t92558926622417105030481')
PASS  base g read from forecast_assumptions = 2.0%  (actual=0.02 expected=0.02)
PASS  sensitivity: exactly 25 rows  (actual=25 expected=25)
PASS  sensitivity: (wacc, g) unique  (actual=25 expected=25)
PASS  sensitivity: no nulls  (actual=0 expected=0)
PASS  sensitivity: 5 distinct WACC values  (actual=5 expected=5)
PASS  sensitivity: 5 distinct g values  (actual=5 expected=5)
PASS  sensitivity WACC values = base -1.0..+1.0 pp step 0.5 (max abs diff)  (actual=0.0 expected in [0, 1e-12])
PASS  sensitivity g values = 1.0..3.0% step 0.5 (max abs diff)  (actual=0.0 expected in [0, 1e-12])
PASS  sensitivity: exactly one centre cell at base WACC and g = 2.0% (exact match)  (actual=1 expected=1)
PASS  centre cell = step 3 value per share (|diff| < 1e-9)  (actual=0.0 expected in [0, 1e-09])
PASS  sensitivity strictly decreasing in WACC (violations)  (actual=0 expected=0)
PASS  sensitivity strictly increasing in g (violations)  (actual=0 expected=0)
PASS  sensitivity: every cell has wacc - g >= 1.0 pp  (actual=0 expected=0)
PASS  every sensitivity cell = dcf.value_per_share(base, wacc, g) (max abs diff)  (actual=0.0 expected in [0, 1e-09])
PASS  beta_sensitivity: exactly 1 row  (actual=1 expected=1)
PASS  beta_sensitivity wacc = wacc row 'beta_sensitivity' exactly  (actual=0.09622382827576295 expected=0.09622382827576295)
PASS  beta_sensitivity beta_u = wacc row 'beta_sensitivity' beta_u exactly  (actual=0.9383844270287286 expected=0.9383844270287286)
PASS  beta_sensitivity value per share = dcf.value_per_share(base params, wacc=beta wacc) exactly  (actual=35.59961888979088 expected=35.59961888979088)
PASS  diff_vs_base = value_per_share - base value per share  (actual=0.0 expected in [0, 1e-12])
PASS  beta_sensitivity value below base (higher WACC)  (actual=True expected=True)
PASS  mc_params seed = 20261109  (actual=20261109.0 expected=20261109.0)
PASS  mc_params n_runs = 10,000  (actual=10000.0 expected=10000.0)
PASS  mc_params sd_growth_shift = 1.5 pp  (actual=0.015 expected=0.015)
PASS  mc_params sd_margin_shift = 1.0 pp  (actual=0.01 expected=0.01)
PASS  mc_params rho_growth_margin = 0.5  (actual=0.5 expected=0.5)
PASS  mc_params wacc_mean = base WACC  (actual=0.06520792331945185 expected=0.06520792331945185)
PASS  mc_params wacc_sd = 0.75 pp  (actual=0.0075 expected=0.0075)
PASS  mc_params wacc_lower = g + 1.0 pp  (actual=0.0 expected in [0, 1e-15])
PASS  mc_params wacc_upper = base + 3.0 pp  (actual=0.0 expected in [0, 1e-15])
PASS  mc_params terminal_g held at base  (actual=0.02 expected=0.02)
PASS  mc_runs: exactly 10,000 rows  (actual=10000 expected=10000)
PASS  mc_runs: run_id distinct count  (actual=10000 expected=10000)
PASS  mc_runs: run_id min..max = 1..10000  (actual=(1, 10000) expected=(1, 10000))
PASS  mc_runs: no nulls  (actual=0 expected=0)
PASS  sd(growth_shift) = 1.5 pp +/- 3%  (actual=0.015149588626759414 expected in [0.014549999999999999, 0.01545])
PASS  sd(margin_shift) = 1.0 pp +/- 3%  (actual=0.010069523248471181 expected in [0.0097, 0.0103])
PASS  corr(growth_shift, margin_shift) = 0.50 +/- 0.03  (actual=0.5162615678453155 expected in [0.47, 0.53])
PASS  all wacc >= g + 1.0 pp  (actual=True expected=True)
PASS  all wacc <= base + 3.0 pp  (actual=True expected=True)
INFO  draw means: growth_shift +0.00011, margin_shift -0.00001, wacc 0.06532 (base 0.06521); sd(wacc) 0.00742; wacc range 0.03307-0.09172
PASS  mean wacc within 0.05 pp of base (unbiased draw)  (actual=0.00011473585671499531 expected in [0, 0.0005])
PASS  sd(wacc) = 0.75 pp +/- 3%  (actual=0.007423683977776947 expected in [0.007274999999999999, 0.007725])
PASS  run 0 (zero shifts, base WACC) through the MC code path = step 3 value per share exactly  (actual=56.47243714823831 expected=56.47243714823831)
PASS  mc_summary.run0_value_per_share = step 3 value per share exactly  (actual=56.47243714823831 expected=56.47243714823831)
PASS  every mc_runs value_per_share = run_value(shifts, wacc) exactly (mismatches)  (actual=0 expected=0)
PASS  first 200 runs = dcf.value_per_share directly (mismatches)  (actual=0 expected=0)
PASS  mc_summary: exactly 1 row  (actual=1 expected=1)
PASS  p5 < p10 < p25 < p50 < p75 < p90 < p95  (actual=True expected=True)
PASS  p5 recomputed with quantile_cont  (actual=41.60631642323455 expected=41.60631642323455 rel_tol=1e-12)
PASS  p10 recomputed with quantile_cont  (actual=44.34140546422919 expected=44.34140546422918 rel_tol=1e-12)
PASS  p25 recomputed with quantile_cont  (actual=49.71107365850467 expected=49.71107365850466 rel_tol=1e-12)
PASS  p50 recomputed with quantile_cont  (actual=56.36425983495167 expected=56.36425983495167 rel_tol=1e-12)
PASS  p75 recomputed with quantile_cont  (actual=64.56244276377868 expected=64.56244276377868 rel_tol=1e-12)
PASS  p90 recomputed with quantile_cont  (actual=74.07999911948627 expected=74.07999911948627 rel_tol=1e-12)
PASS  p95 recomputed with quantile_cont  (actual=81.08844676845925 expected=81.08844676845925 rel_tol=1e-12)
PASS  mean recomputed  (actual=58.165706735244 expected=58.16570673524419 rel_tol=1e-12)
PASS  sd (sample) recomputed  (actual=12.394766123850177 expected=12.394766123850198 rel_tol=1e-12)
PASS  |p50 / base - 1| <= 10%  (actual=0.0019155772045517105 expected in [0, 0.1])
PASS  mc_summary price = bridge_inputs price = 45.32  (actual=(45.32, 45.32) expected=(45.32, 45.32))
PASS  price_percentile = 100 x share of runs with value < 45.32  (actual=12.03 expected=12.03)
PASS  mc_summary base_value_per_share = valuation value_per_share  (actual=56.47243714823831 expected=56.47243714823831)
PASS  histogram counts sum to 10,000  (actual=10000 expected=10000)
PASS  histogram bins contiguous (bin_hi = next bin_lo)  (actual=True expected=True)
PASS  histogram covers min..max of runs  (actual=True expected=True)
PASS  every histogram count recounted on [bin_lo, bin_hi) (mismatches)  (actual=0 expected=0)
INFO  base 56.4724; p10 44.3414, p50 56.3643, p90 74.0800; price 45.32 at percentile 12.03
INFO  smell: market price inside [p10, p90]

66/66 checks passed
```

## Spot-check cases for the human
The common bridge (step 3) is cash 998.448 + cash-like 304.744 - bank debt 227.043 - other financial payables 212.180 - leases 94.370 - distributions 156.400 - minorities 197.801 = +415.398 m. The divisor is 149.600349 m diluted shares.
1. **Typical: run 1** (`mc_runs` run_id 1). growth_shift -0.015955, margin_shift -0.002246, WACC 0.060382. FY2026E growth = 5.0% - 1.5955 pp = 3.405%; FY2026E margin = 12.818% - 0.225 pp = 12.593%; FY2030E revenue 4,238.630; EV 8,207.320; equity 8,207.320 + 415.398 = 8,622.718; / 149.600349 = **EUR 57.6384** (stored 57.638355). Lower growth and margin are more than offset by the 0.48 pp lower WACC.
2. **Edge: just below the price** (run 2057). growth_shift -0.036673, margin_shift -0.017459, WACC 0.061263, value **EUR 45.3002**. This is < 45.32, so it counts among the 1,203 runs below the price (strict "<", per the plan's definition). Run 4062 (45.3110) is also below; run 4634 (45.3280) is not.
3. **Outlier: the right tail** (run 9545). WACC 0.034893, which is inside the truncation bound [3.0%, 9.52%] but 4.0 sd below the base. Shifts -0.006 / +0.0035; EV 23,729.440; value **EUR 161.3956**, the maximum. It sits in histogram bin 160.0-162.5 (count 1). It does not affect p10/p50/p90; it raises the mean above the median (data quality log #21).
4. **Grid corner** (`sensitivity` wacc_shift -0.01, g 0.03). WACC 5.5208%, g 3.0%: the growth path becomes 5.0/4.6/4.2/3.8/3.4% (the fade goes towards the cell's g, data quality log #22). fcff_tv 374.830; TV 374.830 x 1.03 / (0.055208 - 0.03) = 15,315.630; EV 13,931.639; value **EUR 95.9024**, the grid maximum. wacc - g = 2.52 pp, which is >= 1.0 pp.
5. **Beta line** (`beta_sensitivity`). beta_u 0.938384 relevered at the same D/E gives WACC 9.6224% (step 2, `wacc` case 'beta_sensitivity'). The same forecast discounted at 9.62% gives **EUR 35.5996**, diff_vs_base -20.8728 (-37.0%). On this line the price (45.32) would sit 27% above the value.

## Deviations, disputes, changes to earlier steps
- **No changes to earlier steps.** `py/dcf.py` is reused unchanged; `run.py` only gained the step-4 entry.
- **Extra columns (additive):** `sensitivity.wacc_shift`; `beta_sensitivity.base_value_per_share` and `pct_vs_base`; `mc_summary` adds `n_runs`, `base_value_per_share`, `run0_value_per_share` and `n_wacc_redraws`; `mc_histogram.bin_id`; `mc_params` is a long table (param, value, unit, note).
- **RNG choice:** Python's standard-library `random` (not numpy), so that results do not depend on the numpy version. Draw order per run: z_g, z_2, then WACC (plus redraws, none occurred).
- **Truncation method:** out-of-range WACC draws are redrawn (a truncated normal), not clipped. 0 redraws happened. The minimum WACC drawn is 3.307% (bound 3.0%) and the maximum is 9.172% (bound 9.521%).
- **Grid g:** applied as `terminal_g`, so it also moves the growth-fade end point (Decision 7 defines the fade "towards g"). Logged as data quality log #22. The centre cell is unaffected.
- **Plan constants typed in code:** the grid steps, the Decision 6 parameters and the seed are named constants at the top of `py/04_sensitivity_mc.py`; the histogram bin width (EUR 2.5) is a presentation constant. All other inputs are read from DuckDB.
- **Diagnostics close to tolerance:** corr(growth_shift, margin_shift) = 0.516 (tolerance 0.47-0.53; sampling sd about 0.0075, so this is about 2 sd from 0.5). All other diagnostics are well inside.

<!-- The Verifier appends its section below. -->
