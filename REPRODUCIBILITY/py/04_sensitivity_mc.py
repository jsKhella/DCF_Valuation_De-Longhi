"""Step 4: WACC x g sensitivity grid, beta sensitivity line and the 10,000-run Monte Carlo.

Purpose
    Re-run the shared DCF engine (py/dcf.py, value_per_share) on (a) a 5 x 5 grid of WACC and terminal g around the
    base case, (b) the beta-sensitivity WACC from step 2, and (c) 10,000 Monte Carlo draws of a revenue-growth shift,
    an EBIT-margin shift and the WACC (Decision 6). Summarise the distribution and place the market price in it.

Inputs (DuckDB, built by steps 2-3)
    forecast_assumptions, wacc, bridge_inputs (via dcf.load_base_params), wacc (case = 'beta_sensitivity'),
    valuation (base value per share, for the run-0 assertion).

Outputs (DuckDB tables, CREATE OR REPLACE, no timestamps)
    sensitivity       (wacc_shift, wacc, g, value_per_share)                        25 rows
    beta_sensitivity  (beta_u, wacc, value_per_share, base_value_per_share, diff_vs_base, pct_vs_base)   1 row
    mc_params         (param, value, unit, note)
    mc_runs           (run_id, growth_shift, margin_shift, wacc, value_per_share)   10,000 rows
    mc_summary        (p5, p10, p25, p50, p75, p90, p95, mean, sd, price, price_percentile, n_runs,
                       base_value_per_share, run0_value_per_share, n_wacc_redraws)  1 row
    mc_histogram      (bin_id, bin_lo, bin_hi, count)    bins are [bin_lo, bin_hi)

Brief definitions implemented (by term)
    "Monte Carlo" (10,000 runs, fixed seed; growth, EBIT margin and WACC drawn per Decision 6; output 10th-90th
    percentile range, median and the market price's percentile = 100 x share of runs with value < price).
    "Terminal value" g held at the base 2.0% in the Monte Carlo (Decision 6). Sensitivity table WACC x g
    (brief section 5); g in the grid is passed as terminal_g to dcf.py, so it moves both the Gordon growth and the
    end point of the Decision 7 growth fade (the fade is defined "towards g").
    Decision 6: growth_shift ~ N(0, 1.5 pp) and margin_shift ~ N(0, 1.0 pp), one draw per run added to every forecast
    year, correlation +0.5 (z_m = rho z_g + sqrt(1 - rho^2) z_2); WACC ~ N(base, 0.75 pp) truncated to
    [g + 1.0 pp, base + 3.0 pp] by redrawing out-of-range values; WACC independent of the shifts.

Randomness: Python's standard-library random.Random(20261109) (Mersenne Twister, normalvariate), draws taken in a
fixed order per run: z_g, z_2, then WACC (plus any redraws). No numpy RNG, so results do not depend on its version.
"""
import math
import random
import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "curiosity.duckdb"
sys.path.insert(0, str(ROOT / "py"))
import dcf  # noqa: E402

# ------------------------------------------------------------------ approved constants (plan step 4, Decision 6)
GRID_WACC_SHIFTS = (-0.010, -0.005, 0.0, 0.005, 0.010)   # base WACC -1.0 .. +1.0 pp, step 0.5 pp
GRID_G = (0.010, 0.015, 0.020, 0.025, 0.030)             # g 1.0 .. 3.0 %, step 0.5 pp
MC_SEED = 20261109
MC_RUNS = 10_000
MC_SD_GROWTH = 0.015          # 1.5 pp
MC_SD_MARGIN = 0.010          # 1.0 pp
MC_RHO = 0.5                  # growth / margin shift correlation
MC_SD_WACC = 0.0075           # 0.75 pp
MC_WACC_LO_ABOVE_G = 0.010    # truncation lower bound = g + 1.0 pp
MC_WACC_HI_ABOVE_BASE = 0.030  # truncation upper bound = base + 3.0 pp
HIST_BIN_WIDTH = 2.5          # EUR per share, histogram presentation only
PERCENTILES = (5, 10, 25, 50, 75, 90, 95)


def run_value(p: dict, growth_shift: float, margin_shift: float, wacc: float) -> float:
    """One Monte Carlo evaluation: base params with the two shifts and the drawn WACC, through dcf.value_per_share."""
    return dcf.value_per_share(dict(p, growth_shift=growth_shift, margin_shift=margin_shift,
                                    wacc=wacc))["value_per_share"]


def draw_runs(base_wacc: float, g: float):
    """Correlated growth/margin shifts and truncated-normal WACC, fixed seed. Returns (rows, n_redraws)."""
    rng = random.Random(MC_SEED)
    lo, hi = g + MC_WACC_LO_ABOVE_G, base_wacc + MC_WACC_HI_ABOVE_BASE
    rows, redraws = [], 0
    k = math.sqrt(1 - MC_RHO ** 2)
    for run_id in range(1, MC_RUNS + 1):
        z_g = rng.normalvariate(0.0, 1.0)
        z_2 = rng.normalvariate(0.0, 1.0)
        gs = MC_SD_GROWTH * z_g
        ms = MC_SD_MARGIN * (MC_RHO * z_g + k * z_2)
        w = rng.normalvariate(base_wacc, MC_SD_WACC)
        while not (lo <= w <= hi):
            redraws += 1
            w = rng.normalvariate(base_wacc, MC_SD_WACC)
        rows.append((run_id, gs, ms, w))
    return rows, redraws, lo, hi


def write(con, name, df, select="*", order=""):
    con.register("tmp_df", df)
    con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT {select} FROM tmp_df {order}")
    con.unregister("tmp_df")


def main():
    con = duckdb.connect(str(DB))
    P = dcf.load_base_params(con)
    base_wacc, base_g = P["wacc"], P["terminal_g"]
    base_vps = con.execute("SELECT value FROM valuation WHERE item = 'value_per_share'").fetchall()[0][0]
    assert base_g in GRID_G and 0.0 in GRID_WACC_SHIFTS

    # -------------------------------------------------------------- sensitivity grid (WACC rows x g columns)
    S = []
    for s in GRID_WACC_SHIFTS:
        w = base_wacc + s
        for g in GRID_G:
            assert w - g >= 0.01, (w, g)
            S.append((s, w, g, dcf.value_per_share(dict(P, wacc=w, terminal_g=g))["value_per_share"]))
    sens = pd.DataFrame(S, columns=["wacc_shift", "wacc", "g", "value_per_share"])
    centre = sens.loc[(sens.wacc_shift == 0.0) & (sens.g == base_g), "value_per_share"].iloc[0]
    assert abs(centre - base_vps) < 1e-9, (centre, base_vps)
    write(con, "sensitivity", sens, "wacc_shift::DOUBLE AS wacc_shift, wacc::DOUBLE AS wacc, g::DOUBLE AS g, "
                                    "value_per_share::DOUBLE AS value_per_share", "ORDER BY wacc, g")

    # -------------------------------------------------------------- beta sensitivity line (step 2 WACC row)
    bu, bw = con.execute("SELECT beta_u, wacc FROM wacc WHERE \"case\" = 'beta_sensitivity'").fetchall()[0]
    bv = dcf.value_per_share(dict(P, wacc=bw))["value_per_share"]
    beta = pd.DataFrame([(bu, bw, bv, base_vps, bv - base_vps, bv / base_vps - 1)],
                        columns=["beta_u", "wacc", "value_per_share", "base_value_per_share", "diff_vs_base",
                                 "pct_vs_base"])
    write(con, "beta_sensitivity", beta)

    # -------------------------------------------------------------- Monte Carlo
    run0 = run_value(P, 0.0, 0.0, base_wacc)
    assert run0 == base_vps, (run0, base_vps)
    draws, redraws, lo, hi = draw_runs(base_wacc, base_g)
    runs = pd.DataFrame([(rid, gs, ms, w, run_value(P, gs, ms, w)) for rid, gs, ms, w in draws],
                        columns=["run_id", "growth_shift", "margin_shift", "wacc", "value_per_share"])
    write(con, "mc_runs", runs, "run_id::INTEGER AS run_id, growth_shift::DOUBLE AS growth_shift, "
                                "margin_shift::DOUBLE AS margin_shift, wacc::DOUBLE AS wacc, "
                                "value_per_share::DOUBLE AS value_per_share", "ORDER BY run_id")

    params = pd.DataFrame([
        ("seed", MC_SEED, "integer", "random.Random(seed), Python standard library (Mersenne Twister)"),
        ("n_runs", MC_RUNS, "runs", "Brief: 10,000 runs"),
        ("sd_growth_shift", MC_SD_GROWTH, "decimal", "Decision 6: Normal(0, 1.5 pp), one draw per run added to every "
                                                    "forecast year's growth (guidance width 4-6%)"),
        ("sd_margin_shift", MC_SD_MARGIN, "decimal", "Decision 6: Normal(0, 1.0 pp), one draw per run added to every "
                                                    "forecast year's adjusted EBIT margin (FY2021-25 range about 8-13%)"),
        ("rho_growth_margin", MC_RHO, "correlation", "Decision 6: operating leverage; margin z = rho z_g + "
                                                     "sqrt(1 - rho^2) z_2"),
        ("wacc_mean", base_wacc, "decimal", "Decision 6: base WACC (wacc case='base')"),
        ("wacc_sd", MC_SD_WACC, "decimal", "Decision 6: Normal(base, 0.75 pp), independent of the shifts"),
        ("wacc_lower", lo, "decimal", "Decision 6: truncation lower bound g + 1.0 pp (out-of-range draws redrawn)"),
        ("wacc_upper", hi, "decimal", "Decision 6: truncation upper bound base + 3.0 pp (out-of-range draws redrawn)"),
        ("terminal_g", base_g, "decimal", "Decision 6: g held at the base case"),
        ("hist_bin_width", HIST_BIN_WIDTH, "EUR per share", "Histogram presentation only"),
    ], columns=["param", "value", "unit", "note"])
    write(con, "mc_params", params, "param::VARCHAR AS param, value::DOUBLE AS value, unit::VARCHAR AS unit, "
                                    "note::VARCHAR AS note")

    v = runs["value_per_share"]
    price = P["price"]
    summ = {f"p{q}": float(v.quantile(q / 100, interpolation="linear")) for q in PERCENTILES}
    summ.update(mean=float(v.mean()), sd=float(v.std(ddof=1)), price=price,
                price_percentile=100 * int((v < price).sum()) / MC_RUNS, n_runs=MC_RUNS,
                base_value_per_share=base_vps, run0_value_per_share=run0, n_wacc_redraws=redraws)
    write(con, "mc_summary", pd.DataFrame([summ]),
          "* EXCLUDE (n_runs, n_wacc_redraws), n_runs::INTEGER AS n_runs, n_wacc_redraws::INTEGER AS n_wacc_redraws")

    # -------------------------------------------------------------- histogram, bins [lo, hi) of HIST_BIN_WIDTH
    start = math.floor(v.min() / HIST_BIN_WIDTH) * HIST_BIN_WIDTH
    n_bins = math.floor((v.max() - start) / HIST_BIN_WIDTH) + 1
    edges = [start + k * HIST_BIN_WIDTH for k in range(n_bins + 1)]
    assert edges[0] <= v.min() and v.max() < edges[-1]
    hist = pd.DataFrame([(k + 1, edges[k], edges[k + 1], int(((v >= edges[k]) & (v < edges[k + 1])).sum()))
                         for k in range(n_bins)], columns=["bin_id", "bin_lo", "bin_hi", "count"])
    assert hist["count"].sum() == MC_RUNS
    write(con, "mc_histogram", hist, "bin_id::INTEGER AS bin_id, bin_lo::DOUBLE AS bin_lo, bin_hi::DOUBLE AS bin_hi, "
                                     "count::INTEGER AS count", "ORDER BY bin_lo")

    for t in ("sensitivity", "beta_sensitivity", "mc_params", "mc_runs", "mc_summary", "mc_histogram"):
        print(f"  {t}: {con.execute(f'SELECT COUNT(*) FROM {t}').fetchall()[0][0]} rows")
    print(f"  beta line: WACC {bw:.4%} -> {bv:.4f} ({bv - base_vps:+.4f} vs base {base_vps:.4f})")
    print(f"  MC: p10 {summ['p10']:.4f}, p50 {summ['p50']:.4f}, p90 {summ['p90']:.4f}, mean {summ['mean']:.4f}, "
          f"sd {summ['sd']:.4f}; price {price} at percentile {summ['price_percentile']:.2f}; "
          f"WACC redraws {redraws}; {n_bins} histogram bins")
    con.close()


if __name__ == "__main__":
    main()
