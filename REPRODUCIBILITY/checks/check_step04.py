"""Acceptance checks for step 4 (plan/plan.md): WACC x g sensitivity grid, beta sensitivity line, Monte Carlo.

Every check prints PASS/FAIL with actual vs expected; exit code 1 if any check fails.
Smell tests print SURPRISE (not a FAIL).

Order of work in this script:
  1. Determinism: fingerprint mc_runs (checks/fingerprint.py), rerun py/04_sensitivity_mc.py, fingerprint again.
     This happens before the read-only connection is opened (DuckDB allows one writer process).
  2. Table checks with own SQL (quantile_cont, stddev_samp, corr) against the stored outputs.
  3. Same-code-path checks: run 0 and every stored run are recomputed through the step-4 module's run function
     (py/04_sensitivity_mc.py, imported without executing its main()) and py/dcf.py.

Plan constants (Decision 6, plan step 4 grid and tolerances) are typed here on purpose: they are the expected values.
"""
import importlib.util
import math
import subprocess
import sys
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "py"))
from _lib import Checks, DB  # noqa: E402
from fingerprint import fingerprint  # noqa: E402

SEED = 20261109
N_RUNS = 10_000
SD_GROWTH, SD_MARGIN, RHO = 0.015, 0.010, 0.50     # Decision 6
SD_WACC, LO_ABOVE_G, HI_ABOVE_BASE = 0.0075, 0.010, 0.030
WACC_SHIFTS = [-0.010, -0.005, 0.0, 0.005, 0.010]  # plan step 4 grid
G_GRID = [0.010, 0.015, 0.020, 0.025, 0.030]
PRICE = 45.32

# ------------------------------------------------------------------ 1. determinism (run the script twice)
fp_before = fp_after = None
rerun_ok = False
try:
    con = duckdb.connect(str(DB), read_only=True)
    fp_before = fingerprint(con, "mc_runs")
    con.close()
    r = subprocess.run([sys.executable, str(ROOT / "py" / "04_sensitivity_mc.py")], cwd=ROOT,
                       capture_output=True, text=True)
    rerun_ok = r.returncode == 0
    if not rerun_ok:
        print(r.stdout[-2000:], r.stderr[-2000:])
    con = duckdb.connect(str(DB), read_only=True)
    fp_after = fingerprint(con, "mc_runs")
    con.close()
except Exception as e:  # tables missing etc.
    print(f"ERROR during determinism rerun: {e!r}")

c = Checks()
c.equal("py/04_sensitivity_mc.py reruns without error", rerun_ok, True)
c.equal("determinism: mc_runs fingerprint identical across two runs of the script",
        fp_after if fp_after is not None else "missing", fp_before if fp_before is not None else "missing-before")

# step-4 module (functions only; main() is guarded)
spec = importlib.util.spec_from_file_location("step04", ROOT / "py" / "04_sensitivity_mc.py")
m4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m4)
import dcf  # noqa: E402

base_vps = c.scalar("SELECT value FROM valuation WHERE item = 'value_per_share'")
base_wacc = c.scalar("SELECT wacc FROM wacc WHERE \"case\" = 'base'")
base_g = c.scalar("SELECT value FROM forecast_assumptions WHERE driver = 'terminal_g'")
c.equal("base g read from forecast_assumptions = 2.0%", base_g, 0.02)

# ------------------------------------------------------------------ 2a. sensitivity grid
c.equal("sensitivity: exactly 25 rows", c.scalar("SELECT COUNT(*) FROM sensitivity"), 25)
c.equal("sensitivity: (wacc, g) unique", c.scalar("SELECT COUNT(DISTINCT (wacc, g)) FROM sensitivity"), 25)
c.zero("sensitivity: no nulls",
       "SELECT COUNT(*) FROM sensitivity WHERE wacc IS NULL OR g IS NULL OR value_per_share IS NULL")
S = c.con.execute("SELECT wacc, g, value_per_share FROM sensitivity ORDER BY wacc, g").fetchall()
waccs = sorted({r[0] for r in S})
gs = sorted({r[1] for r in S})
c.equal("sensitivity: 5 distinct WACC values", len(waccs), 5)
c.equal("sensitivity: 5 distinct g values", len(gs), 5)
if len(waccs) == 5:
    c.between("sensitivity WACC values = base -1.0..+1.0 pp step 0.5 (max abs diff)",
              max(abs(w - (base_wacc + s)) for w, s in zip(waccs, WACC_SHIFTS)), 0, 1e-12)
if len(gs) == 5:
    c.between("sensitivity g values = 1.0..3.0% step 0.5 (max abs diff)",
              max(abs(a - b) for a, b in zip(gs, G_GRID)), 0, 1e-12)
grid = {(w, g): v for w, g, v in S}
centre = [v for (w, g), v in grid.items() if w == base_wacc and g == base_g]
c.equal("sensitivity: exactly one centre cell at base WACC and g = 2.0% (exact match)", len(centre), 1)
if centre:
    c.between("centre cell = step 3 value per share (|diff| < 1e-9)", abs(centre[0] - base_vps), 0, 1e-9)
viol_w = sum(1 for g in gs for a, b in zip(waccs, waccs[1:]) if not grid[(b, g)] < grid[(a, g)])
c.equal("sensitivity strictly decreasing in WACC (violations)", viol_w, 0)
viol_g = sum(1 for w in waccs for a, b in zip(gs, gs[1:]) if not grid[(w, b)] > grid[(w, a)])
c.equal("sensitivity strictly increasing in g (violations)", viol_g, 0)
c.zero("sensitivity: every cell has wacc - g >= 1.0 pp",
       "SELECT COUNT(*) FROM sensitivity WHERE wacc - g < 0.01 - 1e-12")
# every cell through the same dcf.py path
P = dcf.load_base_params(c.con)
maxdiff = 0.0
for (w, g), v in grid.items():
    q = dict(P, wacc=w, terminal_g=g)
    maxdiff = max(maxdiff, abs(dcf.value_per_share(q)["value_per_share"] - v))
c.between("every sensitivity cell = dcf.value_per_share(base, wacc, g) (max abs diff)", maxdiff, 0, 1e-9)

# ------------------------------------------------------------------ 2b. beta sensitivity line
c.equal("beta_sensitivity: exactly 1 row", c.scalar("SELECT COUNT(*) FROM beta_sensitivity"), 1)
B = c.con.execute("SELECT beta_u, wacc, value_per_share, diff_vs_base FROM beta_sensitivity").fetchall()
W = c.con.execute("SELECT beta_u, wacc FROM wacc WHERE \"case\" = 'beta_sensitivity'").fetchall()[0]
if B:
    b_u, b_w, b_v, b_d = B[0]
    c.equal("beta_sensitivity wacc = wacc row 'beta_sensitivity' exactly", b_w, W[1])
    c.equal("beta_sensitivity beta_u = wacc row 'beta_sensitivity' beta_u exactly", b_u, W[0])
    c.equal("beta_sensitivity value per share = dcf.value_per_share(base params, wacc=beta wacc) exactly",
            b_v, dcf.value_per_share(dict(P, wacc=W[1]))["value_per_share"])
    c.between("diff_vs_base = value_per_share - base value per share", abs(b_d - (b_v - base_vps)), 0, 1e-12)
    c.equal("beta_sensitivity value below base (higher WACC)", b_v < base_vps, True)

# ------------------------------------------------------------------ 2c. mc_params
MP = dict(c.con.execute("SELECT param, value FROM mc_params").fetchall())
c.equal("mc_params seed = 20261109", MP.get("seed"), float(SEED))
c.equal("mc_params n_runs = 10,000", MP.get("n_runs"), float(N_RUNS))
c.equal("mc_params sd_growth_shift = 1.5 pp", MP.get("sd_growth_shift"), SD_GROWTH)
c.equal("mc_params sd_margin_shift = 1.0 pp", MP.get("sd_margin_shift"), SD_MARGIN)
c.equal("mc_params rho_growth_margin = 0.5", MP.get("rho_growth_margin"), RHO)
c.equal("mc_params wacc_mean = base WACC", MP.get("wacc_mean"), base_wacc)
c.equal("mc_params wacc_sd = 0.75 pp", MP.get("wacc_sd"), SD_WACC)
c.between("mc_params wacc_lower = g + 1.0 pp", abs((MP.get("wacc_lower") or 0) - (base_g + LO_ABOVE_G)), 0, 1e-15)
c.between("mc_params wacc_upper = base + 3.0 pp", abs((MP.get("wacc_upper") or 0) - (base_wacc + HI_ABOVE_BASE)), 0, 1e-15)
c.equal("mc_params terminal_g held at base", MP.get("terminal_g"), base_g)

# ------------------------------------------------------------------ 2d. mc_runs shape
c.equal("mc_runs: exactly 10,000 rows", c.scalar("SELECT COUNT(*) FROM mc_runs"), N_RUNS)
c.equal("mc_runs: run_id distinct count", c.scalar("SELECT COUNT(DISTINCT run_id) FROM mc_runs"), N_RUNS)
c.equal("mc_runs: run_id min..max = 1..10000",
        c.con.execute("SELECT MIN(run_id), MAX(run_id) FROM mc_runs").fetchone(), (1, N_RUNS))
c.zero("mc_runs: no nulls", "SELECT COUNT(*) FROM mc_runs WHERE growth_shift IS NULL OR margin_shift IS NULL "
                            "OR wacc IS NULL OR value_per_share IS NULL OR NOT isfinite(value_per_share)")

# ------------------------------------------------------------------ 2e. draw diagnostics
sd_g, sd_m, rho, w_min, w_max = c.con.execute(
    "SELECT stddev_samp(growth_shift), stddev_samp(margin_shift), corr(growth_shift, margin_shift), MIN(wacc), "
    "MAX(wacc) FROM mc_runs").fetchone()
c.between("sd(growth_shift) = 1.5 pp +/- 3%", sd_g, SD_GROWTH * 0.97, SD_GROWTH * 1.03)
c.between("sd(margin_shift) = 1.0 pp +/- 3%", sd_m, SD_MARGIN * 0.97, SD_MARGIN * 1.03)
c.between("corr(growth_shift, margin_shift) = 0.50 +/- 0.03", rho, RHO - 0.03, RHO + 0.03)
c.equal("all wacc >= g + 1.0 pp", w_min >= base_g + LO_ABOVE_G, True)
c.equal("all wacc <= base + 3.0 pp", w_max <= base_wacc + HI_ABOVE_BASE, True)
mean_g, mean_m, mean_w, sd_w = c.con.execute(
    "SELECT AVG(growth_shift), AVG(margin_shift), AVG(wacc), stddev_samp(wacc) FROM mc_runs").fetchone()
print(f"INFO  draw means: growth_shift {mean_g:+.5f}, margin_shift {mean_m:+.5f}, wacc {mean_w:.5f} "
      f"(base {base_wacc:.5f}); sd(wacc) {sd_w:.5f}; wacc range {w_min:.5f}-{w_max:.5f}")
c.between("mean wacc within 0.05 pp of base (unbiased draw)", abs(mean_w - base_wacc), 0, 0.0005)
c.between("sd(wacc) = 0.75 pp +/- 3%", sd_w, SD_WACC * 0.97, SD_WACC * 1.03)

# ------------------------------------------------------------------ 3. same code path: run 0 and every run
run0 = m4.run_value(P, 0.0, 0.0, base_wacc)
c.equal("run 0 (zero shifts, base WACC) through the MC code path = step 3 value per share exactly", run0, base_vps)
c.equal("mc_summary.run0_value_per_share = step 3 value per share exactly",
        c.scalar("SELECT run0_value_per_share FROM mc_summary"), base_vps)
runs = c.con.execute("SELECT run_id, growth_shift, margin_shift, wacc, value_per_share FROM mc_runs ORDER BY run_id").fetchall()
mism = sum(1 for _, gsft, msft, w, v in runs if m4.run_value(P, gsft, msft, w) != v)
c.equal("every mc_runs value_per_share = run_value(shifts, wacc) exactly (mismatches)", mism, 0)
mism2 = 0
for _, gsft, msft, w, v in runs[:200]:
    mism2 += dcf.value_per_share(dict(P, growth_shift=gsft, margin_shift=msft, wacc=w))["value_per_share"] != v
c.equal("first 200 runs = dcf.value_per_share directly (mismatches)", mism2, 0)

# ------------------------------------------------------------------ 2f. mc_summary
c.equal("mc_summary: exactly 1 row", c.scalar("SELECT COUNT(*) FROM mc_summary"), 1)
MS = dict(zip([d[0] for d in c.con.execute("SELECT * FROM mc_summary").description],
              c.con.execute("SELECT * FROM mc_summary").fetchone()))
pcts = [MS["p5"], MS["p10"], MS["p25"], MS["p50"], MS["p75"], MS["p90"], MS["p95"]]
c.equal("p5 < p10 < p25 < p50 < p75 < p90 < p95", all(a < b for a, b in zip(pcts, pcts[1:])), True)
for name, q in [("p5", 0.05), ("p10", 0.10), ("p25", 0.25), ("p50", 0.50), ("p75", 0.75), ("p90", 0.90),
                ("p95", 0.95)]:
    c.near(f"{name} recomputed with quantile_cont", MS[name],
           c.scalar(f"SELECT quantile_cont(value_per_share, {q}) FROM mc_runs"), rel=1e-12)
c.near("mean recomputed", MS["mean"], c.scalar("SELECT AVG(value_per_share) FROM mc_runs"), rel=1e-12)
c.near("sd (sample) recomputed", MS["sd"], c.scalar("SELECT stddev_samp(value_per_share) FROM mc_runs"), rel=1e-12)
c.between("|p50 / base - 1| <= 10%", abs(MS["p50"] / base_vps - 1), 0, 0.10)
c.equal("mc_summary price = bridge_inputs price = 45.32",
        (MS["price"], c.scalar("SELECT value FROM bridge_inputs WHERE item = 'price'")), (PRICE, PRICE))
n_below = c.scalar(f"SELECT COUNT(*) FROM mc_runs WHERE value_per_share < {PRICE}")
c.equal("price_percentile = 100 x share of runs with value < 45.32", MS["price_percentile"], 100 * n_below / N_RUNS)
c.equal("mc_summary base_value_per_share = valuation value_per_share", MS["base_value_per_share"], base_vps)

# ------------------------------------------------------------------ 2g. histogram
c.equal("histogram counts sum to 10,000", c.scalar("SELECT SUM(count) FROM mc_histogram"), N_RUNS)
Hb = c.con.execute("SELECT bin_lo, bin_hi, count FROM mc_histogram ORDER BY bin_lo").fetchall()
c.equal("histogram bins contiguous (bin_hi = next bin_lo)", all(a[1] == b[0] for a, b in zip(Hb, Hb[1:])), True)
vmin, vmax = c.con.execute("SELECT MIN(value_per_share), MAX(value_per_share) FROM mc_runs").fetchone()
c.equal("histogram covers min..max of runs", Hb[0][0] <= vmin and vmax < Hb[-1][1], True)
recount = c.con.execute("SELECT h.bin_lo, h.count, (SELECT COUNT(*) FROM mc_runs r WHERE r.value_per_share >= h.bin_lo "
                        "AND r.value_per_share < h.bin_hi) FROM mc_histogram h").fetchall()
c.equal("every histogram count recounted on [bin_lo, bin_hi) (mismatches)", sum(1 for _, a, b in recount if a != b), 0)

# ------------------------------------------------------------------ smell test
print(f"INFO  base {base_vps:.4f}; p10 {MS['p10']:.4f}, p50 {MS['p50']:.4f}, p90 {MS['p90']:.4f}; "
      f"price {PRICE} at percentile {MS['price_percentile']:.2f}")
if MS["p10"] <= PRICE <= MS["p90"]:
    print("INFO  smell: market price inside [p10, p90]")
else:
    print("SURPRISE  smell: market price outside the Monte Carlo [p10, p90] range (not a FAIL; goes to the final review)")

c.done()
