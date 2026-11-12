"""Acceptance checks for step 3 (plan/plan.md): forecast FCFF and base-case valuation.

Every check prints PASS/FAIL with actual vs expected; exit code 1 if any check fails.
Recomputations here use their own SQL on hist_ratios / wacc / bridge_inputs / raw_ tables, not the step-3 code
(except the last block, which confirms py/dcf.py reproduces the stored value per share, as step 4 will rely on it).
Smell tests print SURPRISE (not a FAIL); FRAGILE flags print FRAGILE (not a FAIL); hard limits FAIL.

Plan constants (Decision 7 and the plan's stated anchors) are typed here on purpose: they are the expected values.
"""
import datetime as dt
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import Checks  # noqa: E402

c = Checks()
YEARS = [2026, 2027, 2028, 2029, 2030]
G26, G = 0.05, 0.02                      # Decision 7: FY2026E growth, terminal g
VAL_DATE = dt.date(2026, 11, 6)          # Decision 2 price date

# ------------------------------------------------------------------ forecast_fcff shape
fy = [r[0] for r in c.con.execute("SELECT fy FROM forecast_fcff ORDER BY fy").fetchall()]
c.equal("forecast_fcff has exactly fy 2026-2030", fy, YEARS)
c.zero("forecast_fcff: no nulls in core columns",
       "SELECT COUNT(*) FROM forecast_fcff WHERE revenue IS NULL OR growth IS NULL OR adj_ebit_margin IS NULL "
       "OR adj_ebit IS NULL OR tax_rate IS NULL OR nopat IS NULL OR da IS NULL OR capex IS NULL OR nwc IS NULL "
       "OR delta_nwc IS NULL OR fcff IS NULL")
F = {r[0]: dict(zip([d[0] for d in c.con.description], r))
     for r in c.con.execute("SELECT * FROM forecast_fcff ORDER BY fy").fetchall()}

# FCFF identity per row
for y in YEARS:
    f = F.get(y, {})
    if not f:
        c.equal(f"row fy {y} present", False, True)
        continue
    c.between(f"FCFF identity FY{y}: fcff = adj_ebit x (1 - t) + da - capex - delta_nwc",
              f["fcff"] - (f["adj_ebit"] * (1 - f["tax_rate"]) + f["da"] - f["capex"] - f["delta_nwc"]), -1e-9, 1e-9)
    c.between(f"nopat = adj_ebit x (1 - t) FY{y}", f["nopat"] - f["adj_ebit"] * (1 - f["tax_rate"]), -1e-9, 1e-9)
    c.between(f"adj_ebit = margin x revenue FY{y}", f["adj_ebit"] - f["adj_ebit_margin"] * f["revenue"], -1e-9, 1e-9)

# history anchors from step 1 (own queries)
H = {r[0]: dict(zip([d[0] for d in c.con.description], r))
     for r in c.con.execute("SELECT * FROM hist_ratios ORDER BY fy").fetchall()}
rev25 = H[2025]["revenue"]
nwc25 = H[2025]["nwc"]
da_pct = sum(H[y]["da_pct"] for y in range(2021, 2026)) / 5
capex_pct = sum(H[y]["capex_pct"] for y in range(2021, 2026)) / 5
nwc_pct = H[2025]["nwc_pct"]
tax_hist = sorted(H[y]["eff_tax_rate"] for y in range(2021, 2026) if H[y]["tax_included"])
tax_median = tax_hist[len(tax_hist) // 2] if len(tax_hist) % 2 else (tax_hist[len(tax_hist) // 2 - 1] + tax_hist[len(tax_hist) // 2]) / 2
tax_marg = c.scalar("SELECT tax_marginal FROM wacc WHERE \"case\" = 'base'")
margin_target = (H[2024]["adj_ebit_margin"] + H[2025]["adj_ebit_margin"]) / 2

if all(y in F for y in YEARS):
    # FY2026 delta NWC from FY2025 actual NWC; later years from the prior forecast year
    c.between("FY2026 delta_nwc = nwc_2026 - FY2025 actual NWC", F[2026]["delta_nwc"] - (F[2026]["nwc"] - nwc25), -1e-9, 1e-9)
    for y in YEARS[1:]:
        c.between(f"delta_nwc FY{y} = nwc - prior nwc", F[y]["delta_nwc"] - (F[y]["nwc"] - F[y - 1]["nwc"]), -1e-9, 1e-9)

    # revenue and growth path (Decision 7)
    c.between("FY2026E revenue = 3,801.458 x 1.05 = 3,991.531 (+/-0.001)", F[2026]["revenue"], 3991.530, 3991.532)
    c.between("FY2025 revenue base = 3,801.458", rev25, 3801.4575, 3801.4585)
    for y in YEARS:
        exp_g = G26 - (G26 - G) * (y - 2026) / 5
        c.between(f"growth FY{y} = 5.0% - (5.0% - g) x (t - 2026)/5 = {exp_g:.4%}", F[y]["growth"] - exp_g, -1e-12, 1e-12)
        prev = rev25 if y == 2026 else F[y - 1]["revenue"]
        c.between(f"revenue FY{y} = prior x (1 + growth)", F[y]["revenue"] - prev * (1 + F[y]["growth"]), -1e-9, 1e-9)

    # drivers equal their historical anchors (Decision 7, 8, 9)
    for y in YEARS:
        c.between(f"da FY{y} = FY2021-25 average D&A % x revenue", F[y]["da"] - da_pct * F[y]["revenue"], -1e-9, 1e-9)
        c.between(f"capex FY{y} = FY2021-25 average capex % (incl. ROU, Decision 9) x revenue",
                  F[y]["capex"] - capex_pct * F[y]["revenue"], -1e-9, 1e-9)
        c.between(f"nwc FY{y} = FY2025 NWC % x revenue", F[y]["nwc"] - nwc_pct * F[y]["revenue"], -1e-9, 1e-9)
        c.between(f"tax_rate FY{y} = median FY2021-25 effective rate (Decision 8A)", F[y]["tax_rate"] - tax_median, -1e-12, 1e-12)

    # guidance bridge: adj EBIT + D&A + share-based cost = guidance midpoint
    pr = c.scalar("SELECT string_agg(text, ' ' ORDER BY line_no) FROM raw_report_lines WHERE doc_id='PR_H1_2026' AND page=6")
    m = re.search(r"€\s*([\d,.]+)\s*-\s*€\s*([\d,.]+)\s*million", pr)
    c.equal("guidance range found in PR_H1_2026 p.6", bool(m), True)
    mid = (float(m.group(1)) + float(m.group(2))) / 2 if m else None
    c.between("guidance midpoint = 680", mid, 679.999, 680.001)
    bridge26 = F[2026]["adj_ebit"] + F[2026]["da"] + F[2026]["share_based_cost"]
    c.between("guidance bridge FY2026E: adj_ebit + da + share-based cost = 680 (+/-0.5)", bridge26, 679.5, 680.5)
    # share-based cost at its FY2025 % of revenue (adj EBITDA 625,077 in AR2025 segment note, own parse)
    seg = c.scalar("SELECT text FROM raw_report_lines WHERE doc_id='AR2025' AND regexp_matches(text, '^EBITDA adjusted \\(\\*\\*\\*\\) .*625,077$')")
    adj_ebitda25 = float(seg.split()[-1].replace(",", "")) / 1000
    sbc25 = adj_ebitda25 - (H[2025]["ebit_reported"] + H[2025]["da"]) + H[2025]["nonrec"]
    c.between("FY2025 share-based cost = adj EBITDA 625.077 - EBIT - D&A - non-recurring (about 34.25)", sbc25, 34.0, 34.5)
    for y in YEARS:
        c.between(f"share_based_cost FY{y} = FY2025 % x revenue",
                  F[y]["share_based_cost"] - sbc25 / rev25 * F[y]["revenue"], -1e-9, 1e-9)

    # margin path: linear from FY2026E to the FY2024-25 average by FY2030E
    m26 = F[2026]["adj_ebit_margin"]
    for y in YEARS:
        exp_m = m26 + (margin_target - m26) * (y - 2026) / 4
        c.between(f"margin FY{y} on the linear path to FY2024-25 average {margin_target:.4%}",
                  F[y]["adj_ebit_margin"] - exp_m, -1e-12, 1e-12)
        c.between(f"margin FY{y} within 8-16%", F[y]["adj_ebit_margin"], 0.08, 0.16)

    # capex / D&A and FCFF range
    ratio = F[2030]["capex"] / F[2030]["da"]
    if ratio >= 0.9:
        print(f"INFO  FY2030E capex / D&A = {ratio:.3f} (>= 0.9)")
    else:
        print(f"FRAGILE  FY2030E capex / D&A = {ratio:.3f} < 0.9 (not a FAIL; goes to the final review)")
    for y in YEARS:
        c.between(f"FCFF FY{y} between 250 and 650 m", F[y]["fcff"], 250, 650)

    # terminal-year FCFF (Decision 8A: marginal tax)
    f30 = F[2030]
    fcff_tv_exp = f30["adj_ebit"] * (1 - tax_marg) + f30["da"] - f30["capex"] - f30["delta_nwc"]
    c.between("fcff_tv = FY2030 FCFF at marginal tax 27.81%", f30["fcff_tv"] - fcff_tv_exp, -1e-9, 1e-9)
    c.between("marginal tax = 27.81%", tax_marg, 0.27809999, 0.27810001)
    c.zero("fcff_tv only on FY2030", "SELECT COUNT(*) FROM forecast_fcff WHERE (fy < 2030 AND fcff_tv IS NOT NULL) OR (fy = 2030 AND fcff_tv IS NULL)")

# ------------------------------------------------------------------ forecast_assumptions
c.zero("forecast_assumptions: every driver has a non-empty note, source and rule",
       "SELECT COUNT(*) FROM forecast_assumptions WHERE note IS NULL OR trim(note)='' OR source IS NULL "
       "OR trim(source)='' OR rule IS NULL OR trim(rule)=''")
c.zero("forecast_assumptions: driver unique",
       "SELECT COUNT(*) FROM (SELECT driver FROM forecast_assumptions GROUP BY driver HAVING COUNT(*) > 1)")
c.equal("forecast_assumptions: terminal_g = 2.0%",
        c.scalar("SELECT value FROM forecast_assumptions WHERE driver='terminal_g'"), G)
for d in ["revenue_growth", "adj_ebit_margin", "da_pct", "capex_pct", "nwc_pct", "tax_rate_forecast",
          "tax_rate_terminal", "share_based_pct", "terminal_g"]:
    c.equal(f"forecast_assumptions has driver '{d}'",
            c.scalar(f"SELECT COUNT(*) FROM forecast_assumptions WHERE driver='{d}'"), 1)

# ------------------------------------------------------------------ valuation: discounting
V = dict(c.con.execute("SELECT item, value FROM valuation").fetchall())
c.zero("valuation: item unique", "SELECT COUNT(*) FROM (SELECT item FROM valuation GROUP BY item HAVING COUNT(*) > 1)")
c.zero("valuation: no null values", "SELECT COUNT(*) FROM valuation WHERE value IS NULL")
wacc = c.scalar("SELECT wacc FROM wacc WHERE \"case\" = 'base'")
c.equal("valuation wacc = wacc table base row", V.get("wacc"), wacc)
c.equal("valuation terminal_g = 2.0%", V.get("terminal_g"), G)

tau = {y: (dt.date(y, 12, 31) - VAL_DATE).days / 365.25 for y in YEARS}
c.between("tau_2026 = 0.1506 (+/-0.0001)", V.get("tau_2026"), 0.1505, 0.1507)
c.between("tau_2030 = 4.1506 (+/-0.0001)", V.get("tau_2030"), 4.1505, 4.1507)
sum_pv = 0.0
for y in YEARS:
    c.between(f"tau_{y} = (31 Dec {y} - 2026-11-06)/365.25", V.get(f"tau_{y}", math.nan) - tau[y], -1e-12, 1e-12)
    pv = F[y]["fcff"] / (1 + wacc) ** tau[y] if y in F else math.nan
    sum_pv += pv
    c.between(f"pv_fcff_{y} recomputed", V.get(f"pv_fcff_{y}", math.nan) - pv, -1e-6, 1e-6)
c.between("sum_pv_fcff recomputed", V.get("sum_pv_fcff", math.nan) - sum_pv, -1e-6, 1e-6)
tv = F[2030]["fcff_tv"] * (1 + G) / (wacc - G) if 2030 in F else math.nan
c.between("tv_gordon = fcff_tv x (1 + g)/(wacc - g)", V.get("tv_gordon", math.nan) - tv, -1e-6, 1e-6)
pv_tv = tv / (1 + wacc) ** tau[2030]
c.between("pv_tv discounted at tau_2030", V.get("pv_tv", math.nan) - pv_tv, -1e-6, 1e-6)
ev = sum_pv + pv_tv
c.between("ev = sum PV + PV TV", V.get("ev", math.nan) - ev, -1e-6, 1e-6)
c.between("tv_share_of_ev = pv_tv / ev", V.get("tv_share_of_ev", math.nan) - pv_tv / ev, -1e-12, 1e-12)

# ------------------------------------------------------------------ valuation: equity bridge
B = dict(c.con.execute("SELECT item, value FROM bridge_inputs").fetchall())
for it in ["bank_debt", "other_financial_payables", "lease_liabilities", "cash", "cash_like_financial_assets",
           "distributions_2026", "minority_book", "diluted_shares", "price"]:
    c.equal(f"valuation {it} = bridge_inputs {it}", V.get(it), B[it])
equity = (ev + B["cash"] + B["cash_like_financial_assets"] - B["bank_debt"] - B["other_financial_payables"]
          - B["lease_liabilities"] - B["distributions_2026"] - B["minority_book"])
c.between("equity_value = EV + cash + cash-like - debt - other fin. payables - leases - distributions - minorities",
          V.get("equity_value", math.nan) - equity, -1e-6, 1e-6)
vps = equity / B["diluted_shares"]
c.between("value_per_share = equity / diluted shares", V.get("value_per_share", math.nan) - vps, -1e-8, 1e-8)
c.between("upside_pct = price / value - 1", V.get("upside_pct", math.nan) - (B["price"] / vps - 1), -1e-10, 1e-10)
note_min = c.scalar("SELECT note FROM valuation WHERE item='minority_book'") or ""
c.equal("minorities at book flagged as a simplification in the note column", "simplification" in note_min.lower(), True)

# ------------------------------------------------------------------ multiples_check
raw_eu = c.scalar("SELECT ev_ebitda FROM raw_damodaran_vebitda_europe WHERE industry_name='Furn/Home Furnishings'")
raw_gl = c.scalar("SELECT ev_ebitda FROM raw_damodaran_vebitda_global WHERE industry_name='Furn/Home Furnishings'")
c.equal("multiples_check has 2 rows", c.scalar("SELECT COUNT(*) FROM multiples_check"), 2)
mc_eu = c.scalar("SELECT ev_ebitda FROM multiples_check WHERE region='Europe' AND industry='Furn/Home Furnishings'")
mc_gl = c.scalar("SELECT ev_ebitda FROM multiples_check WHERE region='Global' AND industry='Furn/Home Furnishings'")
c.equal("Europe Furn/Home ev_ebitda equals the raw cell exactly", mc_eu, raw_eu)
c.equal("Global Furn/Home ev_ebitda equals the raw cell exactly", mc_gl, raw_gl)
c.between("Europe Furn/Home ev_ebitda = 9.452668", raw_eu, 9.4526675, 9.4526685)
c.between("Global Furn/Home ev_ebitda = 10.626402", raw_gl, 10.6264015, 10.6264025)
ebitda30 = F[2030]["adj_ebit"] + F[2030]["da"]
for region, mult in [("Europe", raw_eu), ("Global", raw_gl)]:
    r = dict(zip(["n", "e", "tv", "ev", "vps", "pct", "impl"], c.con.execute(
        "SELECT n_firms, fy2030_ebitda, tv_exit, ev_exit, value_per_share_exit, pct_vs_gordon, implied_gordon_ev_ebitda "
        f"FROM multiples_check WHERE region='{region}'").fetchone()))
    c.between(f"[{region}] fy2030_ebitda = adj_ebit + da FY2030", r["e"] - ebitda30, -1e-9, 1e-9)
    c.between(f"[{region}] tv_exit = multiple x FY2030 EBITDA", r["tv"] - mult * ebitda30, -1e-9, 1e-9)
    ev_x = sum_pv + mult * ebitda30 / (1 + wacc) ** tau[2030]
    c.between(f"[{region}] ev_exit = sum PV + PV(exit TV)", r["ev"] - ev_x, -1e-6, 1e-6)
    vps_x = (ev_x + equity - ev) / B["diluted_shares"]
    c.between(f"[{region}] value_per_share_exit via the same bridge", r["vps"] - vps_x, -1e-8, 1e-8)
    c.between(f"[{region}] pct_vs_gordon = exit / Gordon - 1", r["pct"] - (vps_x / vps - 1), -1e-10, 1e-10)
    c.between(f"[{region}] implied_gordon_ev_ebitda = TV Gordon / FY2030 EBITDA", r["impl"] - tv / ebitda30, -1e-10, 1e-10)
    print(f"INFO  [{region}] exit {mult:.2f}x -> EUR {vps_x:.2f}/share, {vps_x / vps - 1:+.1%} vs Gordon")

# ------------------------------------------------------------------ smell tests and hard limits
tv_share = pv_tv / ev
c.between("HARD: TV share of EV within 50-95%", tv_share, 0.50, 0.95)
c.between("HARD: value per share within EUR 15-120", vps, 15, 120)
c.between("HARD: implied Gordon EV/EBITDA within 5x-25x", tv / ebitda30, 5, 25)
if tv_share <= 0.80:
    print(f"INFO  smell: TV share of EV {tv_share:.1%} <= 80%")
else:
    print(f"SURPRISE  smell: TV share of EV {tv_share:.1%} > 80% (not a FAIL; goes to the final review)")
gap = vps / B["price"] - 1
if abs(gap) <= 0.30:
    print(f"INFO  smell: value / price - 1 = {gap:+.1%} (within +/-30%)")
else:
    print(f"SURPRISE  smell: value / price - 1 = {gap:+.1%} (outside +/-30%; not a FAIL)")

# ------------------------------------------------------------------ dcf.py reproduces the stored value (step 4 reuse)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))
try:
    import dcf  # noqa: E402
    params = dcf.load_base_params(c.con)
    out = dcf.value_per_share(params)
    c.equal("py/dcf.py value_per_share(load_base_params) == valuation value_per_share", out["value_per_share"],
            V.get("value_per_share"))
except Exception as e:  # noqa: BLE001
    c.equal(f"py/dcf.py importable and runnable ({type(e).__name__}: {e})", False, True)

c.done()
