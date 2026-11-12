# Step 02: Estimate the WACC and assemble the equity bridge. Verdict: PASS WITH NOTES

## Summary for the human (one page max)
- Headline numbers: base WACC **6.5208%** (Executor) = 6.5208% (Verifier, method: DuckDB SQL + regexp straight from `raw_report_lines` / `raw_damodaran_*` / `raw_ecb_yield_10y` / `raw_yahoo_prices`; debt from the balance-sheet face, not `hist_statements`; rel. diff 0) ✓. Market price **45.32** on **2026-11-06** = 45.32 ✓. Diluted shares **149.600349 m** = 149.600349 m ✓. Also identical: every one of the 16 bridge values and all 13 x 2 `wacc` columns (42/42 exact, 0 mismatches). Beta-sensitivity WACC 9.6224% ✓.
- Rows: `bridge_inputs` 18 (13 required + 5 sourced helper rows), `wacc_inputs` 19, `wacc` 2. No joins, no drops ✓.
- Checks: 78/78 pass, all plan checks present, none weakened (several tighter than the plan); step 1 still 128/128 ✓.
- Reproducible: two `run.py --fresh --through 2` rebuilds, identical fingerprints for all 3 tables ✓.
- Notes: two minor items (cost-of-debt numerator wording; kd_pre below rf). No SURPRISE: WACC 6.52% is inside 6-10%, though only 0.52 pp above the floor. Not FRAGILE: none of this step's own judgement calls moves WACC by more than 0.17 pp.
- Spot-checks: Executor 1-5 traced ✓; Verifier random picks (seed 20261109) `distributions_2026` and `cash` traced ✓.
- Needs your decision: no.

## Findings (NOTES only, nothing to fix for a PASS)
| # | Level | File:line | Problem | Evidence |
|---|-------|-----------|---------|----------|
| 1 | V4 doc | py/02_wacc_bridge.py:300-309, 368 | The plan defines kd_pre's numerator as "FY2025 interest on loans and bonds". The figure used (19.786 m) is note 9's "interest expenses relating to the Group's financial debt ... and financial charges relating to other financing instruments", which is broader (it likely includes factoring charges). The `wacc_inputs` source text still says "interest on loans and bonds". Note 9 has no narrower group-level figure, so the choice is reasonable. The label is slightly loose. | AR2025 p.164 lines 66-69. Alternative: cash interest paid on loans 11.748 (CF p.148 line 43) gives kd_pre 2.28% and WACC 6.44% (-0.08 pp). |
| 2 | V5 note | wacc.kd_pre | kd_pre 3.84% is below rf 4.36%. That's an embedded book cost of legacy fixed-rate debt (private placements at 1.65% / 1.18%), not a marginal cost. It is inside the plan's [rf-1pp, rf+3pp] band, so the rule correctly keeps it. With the plan's fallback (rf + spread = 5.98%), WACC would be 6.63% (+0.11 pp). For the final review only. | AR2025 p.177 lines 14-21. |

## Verifier details
**V1 Reproduce.** `run.py --fresh --through 2` ran twice with no intervention (about 24 s each). Fingerprints (`verify/fp_step02.txt`): bridge_inputs 18 / 193314225145580952589; wacc_inputs 19 / 150340380625399664412; wacc 2 / 27037920684730890735. `--compare`: identical. `check_step01.py` 128/128, `check_step02.py` 78/78.

**V2 Check audit** (plan vs `checks/check_step02.py`):

| Plan check | In check | Status |
|---|---|---|
| 13 items exactly once, every row sourced | l.18-30 | present, plus null checks |
| NFP recon = -770.0 +/-0.1 | l.38-41 | present. Uses the Executor's `financial_assets_all` row; Verifier independently confirmed 305.138 = note 24 total 244.795 + BS other NC fin. assets 60.343 |
| minority 197.8 +/-0.1; leases 94.370 (94.0 +/-0.5); shares x1.5 = SC +/-0.01; 0<=dilutive<=1.3 | l.49-57 | present; share capital re-read from raw |
| price 45.32, date 2026-11-06, < 2026-11-09, mcap 6.0-7.5 bn | l.64-75 | present, plus raw close tie |
| wacc 2 rows; 4 identities <1e-12 | l.79-100 | present, plus kd_post, d_e, w_e |
| inputs = raw cells (rf, ERP, spread, tax, both betas) | l.103-126 | present, exact equality |
| kd_pre rule and band | l.130-137 | present (fallback not triggered) |
| smell 6-10% SURPRISE; hard 4-12%, g < rf | l.146-153 | present |

Pasted output in the Executor section matches my run line for line (78/78).

**V3 Blind recompute** (`verify/verify_step02.py`, written before reading the Executor's code). My sources: BS p.146/147 face lines (2025 and 2024 columns), note 24 p.171, note 9 p.164, IR_H1_2026 p.60 shares issued, IR p.57 treasury, IR p.58 options 30,000, AR2025 p.174 rights 861,473 (IR p.60 confirms "unchanged"), strike 16.982, Damodaran / ECB / Yahoo raw rows. Result: 0 mismatches out of 42 values (the max rel. diff is 1.3e-16, on dilutive_shares). The first run of my script showed DIFFs from my own wrong token index on three text lines; after the fix everything matches.

**V4 Code review.** No joins (no fan-out risk). Every brief definition matches: net debt items (bank + other fin. payables + IFRS 16 leases - cash), Decision 4A cash-like (all NFP financial assets except the 0.394 lease prepayment), Decision 1A distributions 127.9 + 28.5, minorities at book with the simplification flagged, diluted shares = issued - treasury (30 Jun 2026, consistent with the deducted H1 buyback) + TSM options + rights, Decision 5A D = gross debt incl. leases, Hamada relevering at the marginal tax rate, ke = rf + beta_l x (ERP + default spread). Derivative liabilities 4.312 sit in other_financial_payables and derivative assets 6.743 in cash-like, with no double count (NFP reconciles to 769.993 exactly). Every number hand-typed in the note strings was traced to a raw line: 193.177 = 21.415+21.399+150.363; 1.026 minority dividends (IR p.30); 39,333 = 149,399,562 - 149,360,229 (IR p.62); 27.6 and 227.648 minorities (IR p.11, p.29); 7.35% = 25.095/341.420; EUR 4 thousand restricted cash (AR2025 p.171 l.72-73). The data quality log has entries 12-17, all accurate. run.py diff: one line, the step-2 registration.

**V5 Smell.** WACC 6.52% (6-10% smell range, 4-12% hard), ke 6.82%, kd_post 2.77%, w_d 7.3%, mcap EUR 6.78 bn: all plausible. The plan expected WACC "near or below 6%", but it landed 0.52 pp inside, mainly because rf is 4.362% (Sep 2026). Not a SURPRISE under the pre-registered tests.

**V6 Sensitivity** (base WACC 6.521%):

| Alternative | WACC |
|---|---|
| kd fallback rf + spread | 6.634% |
| kd = CF interest paid / avg debt | 6.439% |
| D = 0 (Decision 5B) | 6.684% |
| Treasury shares at YE2025 | 6.522% |
| No dilution | 6.520% |
| (Gate 1 decision, not this step) raw Europe beta 0.345 | 6.222% |
| (Gate 1 decision) Europe Household beta 0.711 | 8.320% |
| (Gate 1 decision) rf = DE 10y 3.473% | 5.697% (would leave 6-10%) |

None of this step's judgement calls flips the smell test. Only a different rf source (a Gate 1 decision) would.

**V7 Spot-checks.** Executor 1 (cash-like 304.744) ✓ against note 24 p.171 l.50-54 and BS p.146 l.27. Executor 2 (NFP -769.993) ✓, recomputed from the BS face. Executor 3 (price) ✓: Yahoo 2026-11-06 close 45.3199997, 2026-11-09 bar excluded. Executor 4 (treasury 2,574,620) ✓: IR p.57 l.10. Executor 5 (WACC arithmetic) ✓ to 1e-12. Verifier random (seed 20261109, `random.sample` of 2 over the sorted bridge items): `distributions_2026` = IR_H1_2026 p.20 l.12-13 (127.9) + (28.5), also in PR_H1_2026 p.13 ✓. `cash` 998.448 = BS p.146 l.36 = CF closing cash p.148 l.51 = NFP line A p.177 l.33 ✓.

---
(Executor's section follows)

# Step 02: Estimate the WACC and assemble the equity bridge. Status: AWAITING VERIFICATION

## What was done
- Parsed the YE2025 bridge items from the AR2025 text by anchor lines (not hard-coded pages): bank debt 227.043, other financial payables 212.180, leases 94.370, cash 998.448, minority interest 197.801. Each is cross-checked against its note (32, 33, 15) inside the script.
- Itemised the cash-like financial assets under Decision 4A (note 24 items 6.743 + 72.541 + 165.117, note 18 / NFP line I.1 60.343 = 304.744; lease prepayments 0.394 excluded) and reconciled the whole bridge to the company's NFP of 769.993 (asserted in the script and in the check).
- Took distributions since the balance sheet from IR_H1_2026 (dividends 127.9 + buybacks 28.5 = 156.4), the share count at 30 Jun 2026 (151.295 m issued, 2.575 m treasury, 0.880 m dilutive by the treasury stock method) and the 6 Nov 2026 close (45.32). Market cap 6,779.9 m.
- Built the WACC: rf 4.362% (ECB IT, Sep 2026), ERP 4.23% + Italy default spread 1.618%, tax 27.81%, Europe Furn/Home cash-corrected unlevered beta 0.397 relevered at D/E 7.87% (Decision 5A, D = 533.6 m gross debt incl. leases). Cost of debt 3.84% = FY2025 interest 19.786 / average gross debt excl. leases 515.3. Base WACC 6.52% (ke 6.82%); beta sensitivity (Global 0.938) WACC 9.62% (ke 10.16%).

## Files
| File | Purpose |
|------|---------|
| `py/02_wacc_bridge.py` | Parses notes, builds `bridge_inputs` (18 rows), `wacc_inputs` (19 rows), `wacc` (2 rows) |
| `checks/check_step02.py` | 78 acceptance checks (plan step 2) |
| `run.py` | Step 2 registered: `2: ["py/02_wacc_bridge.py"]` |
| `evidence/data_quality_log.md` | Step 2 section (entries 12-17) |

`bridge_inputs` holds the 13 required items plus 5 sourced helper rows (`financial_assets_all`, `financial_assets_excluded`, `nfp_reported`, `market_cap`, `interest_expense_fy2025`) used by the NFP reconciliation, the market cap and the cost of debt.

## Row flow
| Table | Rows in | Rows out | Why the difference |
|-------|---------|----------|--------------------|
| raw_report_lines (AR2025, IR_H1_2026), hist_statements -> bridge_inputs | 79,876 lines + 153 | 18 | 13 required items + 5 helper rows |
| raw_damodaran_*, raw_ecb_yield_10y, bridge_inputs -> wacc_inputs | | 19 | one row per WACC input / derived weight |
| wacc_inputs -> wacc | | 2 | base and beta_sensitivity (same D/E, rf, kd; different beta_u) |

Determinism: two `run.py --fresh --through 2` rebuilds give identical fingerprints for the three tables (`checks/fingerprint.py --compare`: PASS).

## Check results
```
PASS  bridge_inputs 'bank_debt' exactly once  (actual=1 expected=1)
PASS  bridge_inputs 'other_financial_payables' exactly once  (actual=1 expected=1)
PASS  bridge_inputs 'lease_liabilities' exactly once  (actual=1 expected=1)
PASS  bridge_inputs 'cash' exactly once  (actual=1 expected=1)
PASS  bridge_inputs 'cash_like_financial_assets' exactly once  (actual=1 expected=1)
PASS  bridge_inputs 'distributions_2026' exactly once  (actual=1 expected=1)
PASS  bridge_inputs 'minority_book' exactly once  (actual=1 expected=1)
PASS  bridge_inputs 'shares_issued' exactly once  (actual=1 expected=1)
PASS  bridge_inputs 'treasury_shares' exactly once  (actual=1 expected=1)
PASS  bridge_inputs 'dilutive_shares' exactly once  (actual=1 expected=1)
PASS  bridge_inputs 'diluted_shares' exactly once  (actual=1 expected=1)
PASS  bridge_inputs 'price' exactly once  (actual=1 expected=1)
PASS  bridge_inputs 'price_date' exactly once  (actual=1 expected=1)
PASS  bridge_inputs: item unique  (actual=0 expected=0)
PASS  bridge_inputs: every row has a source  (actual=0 expected=0)
PASS  bridge_inputs: no null value / unit / as_of / treatment / note  (actual=0 expected=0)
PASS  NFP reconciliation: debt + other fin. payables + leases - cash - all financial assets = -770.0 (+/-0.1)  (actual=-769.9929999999999 expected in [-770.1, -769.9])
PASS  reported NFP row (AR2025 NFP table) = 770.0 (+/-0.1)  (actual=769.993 expected in [769.9, 770.1])
PASS  cash-like + excluded financial assets = all financial assets (+/-0.0005)  (actual=305.138 expected in [305.1375, 305.13849999999996])
PASS  cash_like_financial_assets plausible (about 305 m, Decision 4A)  (actual=304.74399999999997 expected in [290, 306])
PASS  minority_book = 197.8 (+/-0.1)  (actual=197.801 expected in [197.7, 197.9])
PASS  lease_liabilities = 94.370 (+/-0.0005)  (actual=94.37 expected in [94.3695, 94.3705])
PASS  lease_liabilities vs NFP table 94.0 (+/-0.5)  (actual=94.37 expected in [93.5, 94.5])
PASS  shares_issued x 1.5 = BS share capital (+/-0.01 m)  (actual=226.9421055 expected in [226.93200000000002, 226.952])
PASS  0 <= dilutive_shares <= 1.3 m  (actual=0.8802316054721977 expected in [0.0, 1.3])
PASS  treasury_shares plausible (0 to 5 m)  (actual=2.57462 expected in [0.0, 5.0])
PASS  diluted_shares = issued - treasury + dilutive (1e-9)  (actual=0.0 expected in [-1e-09, 1e-09])
PASS  distributions_2026 = 127.9 + 28.5 (IR_H1_2026)  (actual=156.4 expected in [156.39, 156.41])
PASS  price = 45.32  (actual=45.32 expected=45.32)
PASS  price_date (as_of) = 2026-11-06  (actual='2026-11-06' expected='2026-11-06')
PASS  price_date value = 20261106  (actual=20261106.0 expected=20261106.0)
PASS  price_date < 2026-11-09 (intraday bar excluded)  (actual=0 expected=0)
PASS  price equals raw DLG.MI close of 2026-11-06 (rounded to 0.01)  (actual=45.32 expected in [45.314999694824216, 45.32499969482422])
PASS  market cap = price x diluted shares between 6.0 and 7.5 bn (EUR m)  (actual=6779.8877987999995 expected in [6000, 7500])
PASS  market_cap row = price x diluted shares (1e-6)  (actual=0.0 expected in [-1e-06, 1e-06])
PASS  wacc has exactly 2 rows  (actual=2 expected=2)
PASS  wacc cases  (actual=['base', 'beta_sensitivity'] expected=['base', 'beta_sensitivity'])
PASS  [base] w_e + w_d = 1  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  [base] beta_l = beta_u x (1 + (1 - t) x D/E)  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  [base] ke = rf + beta_l x (ERP + country spread)  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  [base] wacc = w_e x ke + w_d x kd_post  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  [base] kd_post = kd_pre x (1 - t)  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  [base] d_e = D / market cap (Decision 5A)  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  [base] w_e = E / (D + E)  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  [beta_sensitivity] w_e + w_d = 1  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  [beta_sensitivity] beta_l = beta_u x (1 + (1 - t) x D/E)  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  [beta_sensitivity] ke = rf + beta_l x (ERP + country spread)  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  [beta_sensitivity] wacc = w_e x ke + w_d x kd_post  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  [beta_sensitivity] kd_post = kd_pre x (1 - t)  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  [beta_sensitivity] d_e = D / market cap (Decision 5A)  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  [beta_sensitivity] w_e = E / (D + E)  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  last ECB IT observation is 2026-09  (actual='2026-09' expected='2026-09')
PASS  raw rf = 4.362%  (actual=0.04362 expected=0.04362)
PASS  raw ERP = 4.23%  (actual=0.0423 expected=0.0423)
PASS  raw Italy default spread = 1.618%  (actual=0.016180901401917473 expected in [0.01617, 0.01619])
PASS  raw Italy tax = 27.81%  (actual=0.2781 expected=0.2781)
PASS  [base] rf equals raw cell  (actual=0.04362 expected=0.04362)
PASS  [base] erp_mature equals raw cell  (actual=0.0423 expected=0.0423)
PASS  [base] country_spread equals raw cell  (actual=0.016180901401917473 expected=0.016180901401917473)
PASS  [base] tax_marginal equals raw cell  (actual=0.2781 expected=0.2781)
PASS  [beta_sensitivity] rf equals raw cell  (actual=0.04362 expected=0.04362)
PASS  [beta_sensitivity] erp_mature equals raw cell  (actual=0.0423 expected=0.0423)
PASS  [beta_sensitivity] country_spread equals raw cell  (actual=0.016180901401917473 expected=0.016180901401917473)
PASS  [beta_sensitivity] tax_marginal equals raw cell  (actual=0.2781 expected=0.2781)
PASS  base beta_u = Europe Furn/Home cash-corrected (0.397...)  (actual=0.3970408846882334 expected=0.3970408846882334)
PASS  sensitivity beta_u = Global Furn/Home cash-corrected (0.938...)  (actual=0.9383844270287286 expected=0.9383844270287286)
PASS  base beta_u about 0.397  (actual=0.3970408846882334 expected in [0.397, 0.3971])
PASS  sensitivity beta_u about 0.938  (actual=0.9383844270287286 expected in [0.9383, 0.9385])
PASS  kd_pre = interest / average gross financial debt excl. leases  (actual=0.0 expected in [-1e-12, 1e-12])
PASS  kd_pre same in both cases  (actual=0.0383950012370774 expected=0.0383950012370774)
PASS  kd_pre inside [rf - 1 pp, rf + 3 pp]  (actual=0.0383950012370774 expected in [0.03362, 0.07361999999999999])
PASS  YE2024 gross financial debt excl. leases = 591.432 (bank 322.234 + other 269.198)  (actual=591.432 expected in [591.431, 591.433])
PASS  wacc_inputs: every row has a source  (actual=0 expected=0)
PASS  wacc_inputs: input unique  (actual=0 expected=0)
PASS  HARD: base WACC inside 4%-12%  (actual=0.06520792331945185 expected in [0.04, 0.12])
PASS  HARD: g (2.0%) < rf  (actual=0.02 expected in [0.0, 0.043619999999])
PASS  HARD: base WACC - g >= 1.0 pp (needed by the step-4 grid)  (actual=0.04520792331945185 expected in [0.01, 1.0])
INFO  smell test base WACC 6.5208% inside 6-10%
INFO  sensitivity WACC 9.6224%, base ke 6.8159%, sensitivity ke 10.1615%
PASS  sensitivity WACC > base WACC (higher beta)  (actual=0.031015904956311097 expected in [0.0, 1.0])

78/78 checks passed
```
No SURPRISE: base WACC 6.52% is inside the 6-10% smell range (the plan expected it near or below 6%). It is only 0.52 pp above the lower edge; the beta sensitivity (9.62%) shows how much the beta choice matters.

## Spot-check cases for the human
1. **Typical: cash-like assets (Decision 4A).** AR2025 PDF p.171 note 24: derivatives 6,743; fair value of other current financial assets 72,541; other current financial assets 165,117; lease advances 394; total 244,795. Plus PDF p.177 NFP line I.1 (note 18) 60,343. `cash_like_financial_assets` = 6.743 + 72.541 + 165.117 + 60.343 = 304.744; `financial_assets_excluded` = 0.394; sum 305.138 = note 24 total + I.1. Correct under Decision 4A: all liquid financial assets in, only the lease prepayment out.
2. **NFP reconciliation.** Bridge items: 227.043 + 212.180 + 94.370 - 998.448 - 305.138 = -769.993, i.e. NFP +769.993 (AR2025 PDF p.177 line 55: 769,993). Derivative liabilities (4.312) sit inside `other_financial_payables` and derivative assets inside the 305.138, so no item is double counted.
3. **Edge: price date.** `raw_yahoo_prices` has DLG.MI bars for 2026-11-06 (close 45.31999969, volume 171,917) and 2026-11-09 (45.98, volume 65,761, intraday). `price` = 45.32, `price_date` = 2026-11-06. Correct: Decision 2 requires the last completed session.
4. **Edge: share count date.** Treasury shares 1,771,513 at 31 Dec 2025 (AR2025 p.172 line 51) vs 2,574,620 at 30 Jun 2026 (IR_H1_2026 PDF p.57 line 10). The bridge uses 2.574620 m because Decision 1A deducts the H1 2026 buyback cash (28.5 m, 818,107 shares). Diluted shares = 151.294737 - 2.574620 + 0.880232 = 149.600349 m; market cap 45.32 x 149.600349 = 6,779.9 m.
5. **WACC arithmetic (base).** D = 227.043 + 212.180 + 94.370 = 533.593; E = 6,779.888; D/E = 7.870%; beta_l = 0.39704 x (1 + 0.7219 x 0.07870) = 0.41960; ke = 4.362% + 0.41960 x (4.23% + 1.618%) = 6.816%; kd_pre = 19.786 / ((439.223 + 591.432)/2) = 3.840%, kd_post = 2.772%; WACC = 0.92704 x 6.816% + 0.07296 x 2.772% = 6.521%.

## Deviations, disputes, changes to earlier steps
- No deviations from definitions or decisions; no check edited. Points for the Verifier and the human, logged in `evidence/data_quality_log.md` (12-17): the plan's "IR_H1_2026 p.18" for distributions is PDF p.20 in the file; the 127.9 dividend figure includes 1.026 m of minority dividends; "lease liabilities 94.0 (NFP table)" is 94.370 exactly; the treasury-share count is taken at 30 Jun 2026 to match the H1 buyback deduction (a judgement call, impact on share count 0.80 m = 0.5%); `bridge_inputs` has 5 extra helper rows beyond the 13 listed items.
- `price_date` is stored as the number 20261106 (unit yyyymmdd) with `as_of` = '2026-11-06' so that the `value` column stays numeric.
- Cost-of-debt fallback (rf + spread) is not implemented because it was not triggered (kd_pre 3.84% is inside [3.36%, 7.36%]); the script stops with `BLOCKED` text if it ever is.
- Changes to earlier steps: none (`run.py` only gained the step-2 entry).

<!-- The Verifier appends its section below. -->
