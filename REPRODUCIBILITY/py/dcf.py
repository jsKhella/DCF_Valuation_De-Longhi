"""DCF engine: one pure function, value_per_share(params) -> dict, shared by step 3 (base case) and step 4
(WACC x g grid, beta line, Monte Carlo). No I/O inside value_per_share; load_base_params(con) reads the inputs.

Purpose
    Turn the forecast drivers into FY2026E-30E FCFF, discount them to the price date, add the Gordon terminal value,
    and walk from EV to equity value and value per share.

Inputs of load_base_params (DuckDB, built by steps 1-3)
    forecast_assumptions (scalar drivers, written by py/03_forecast_valuation.py), wacc (case = 'base'),
    bridge_inputs (bridge items, diluted shares, price, price_date).

Output of value_per_share
    dict with per-year lists (years, revenue, growth, adj_ebit_margin, adj_ebit, tax_rate, nopat, da, capex, nwc,
    delta_nwc, share_based_cost, adj_ebitda_mgmt, fcff, tau, discount_factor, pv_fcff) and scalars (fcff_tv,
    nopat_tv, sum_pv_fcff, tv_gordon, pv_tv, ev, tv_share_of_ev, equity_value, value_per_share, upside_pct,
    ebitda_2030, ...). Money in EUR m, rates as decimals.

Brief definitions implemented (by term)
    "FCFF" = adjusted EBIT x (1 - tax rate) + D&A - capex - increase in NWC (capex incl. right-of-use additions,
    Decision 9A). "Tax rate" (Decision 8A: normalised effective rate in FY2026E-30E, marginal rate in the terminal
    FCFF). "Terminal value" = Gordon growth on the FY2030E terminal FCFF: TV = fcff_tv x (1 + g) / (wacc - g).
    "Discounting" = year-end convention, year fraction tau_t = (31 Dec t - price date) / 365.25. "Equity bridge" =
    EV + cash + cash-like financial assets (Decision 4A) - bank debt - other financial payables - lease liabilities
    - distributions paid in 2026 (Decision 1A) - minorities at book; / diluted shares.
    Forecast drivers (Decision 7): growth_t = g26 - (g26 - g) x (t - 2026) / fade_years + growth_shift;
    margin_t = m26 + (m_target - m26) x (t - 2026) / (2030 - 2026) + margin_shift; D&A, capex, NWC and share-based
    cost as fixed % of revenue. growth_shift / margin_shift are 0 in the base case (step 4 Monte Carlo, Decision 6).
"""
import datetime as dt
import math

YEARS = (2026, 2027, 2028, 2029, 2030)

BRIDGE_ITEMS = ("bank_debt", "other_financial_payables", "lease_liabilities", "cash", "cash_like_financial_assets",
                "distributions_2026", "minority_book", "diluted_shares", "price")

# forecast_assumptions drivers that value_per_share needs (scalar `value` column)
SCALAR_DRIVERS = ("revenue_fy2025", "nwc_fy2025", "growth_fy2026", "terminal_g", "growth_fade_years",
                  "adj_ebit_margin_fy2026", "adj_ebit_margin_target_fy2030", "da_pct", "capex_pct", "nwc_pct",
                  "share_based_pct", "tax_rate_forecast", "tax_rate_terminal")


def year_fraction(year: int, valuation_date: dt.date) -> float:
    """tau_t = (31 Dec t - valuation date) / 365.25 (year-end convention)."""
    return (dt.date(year, 12, 31) - valuation_date).days / 365.25


def value_per_share(p: dict) -> dict:
    """Pure DCF. `p` holds the scalar drivers (SCALAR_DRIVERS), 'wacc', 'valuation_date' (datetime.date), the
    BRIDGE_ITEMS, and optional 'growth_shift' / 'margin_shift' (default 0). Returns a dict (see module docstring)."""
    years = list(p.get("years", YEARS))
    g = p["terminal_g"]
    wacc = p["wacc"]
    if wacc - g <= 0:
        raise ValueError(f"wacc ({wacc}) must exceed g ({g})")
    gs = p.get("growth_shift", 0.0)
    ms = p.get("margin_shift", 0.0)
    first, last = years[0], years[-1]
    vdate = p["valuation_date"]

    out = {k: [] for k in ("years", "revenue", "growth", "adj_ebit_margin", "adj_ebit", "tax_rate", "nopat", "da",
                           "capex", "nwc", "delta_nwc", "share_based_cost", "adj_ebitda_mgmt", "fcff", "tau",
                           "discount_factor", "pv_fcff")}
    rev_prev, nwc_prev = p["revenue_fy2025"], p["nwc_fy2025"]
    for t in years:
        growth = p["growth_fy2026"] - (p["growth_fy2026"] - g) * (t - first) / p["growth_fade_years"] + gs
        margin = (p["adj_ebit_margin_fy2026"]
                  + (p["adj_ebit_margin_target_fy2030"] - p["adj_ebit_margin_fy2026"]) * (t - first) / (last - first)
                  + ms)
        revenue = rev_prev * (1 + growth)
        adj_ebit = margin * revenue
        tax = p["tax_rate_forecast"]
        nopat = adj_ebit * (1 - tax)
        da = p["da_pct"] * revenue
        capex = p["capex_pct"] * revenue
        nwc = p["nwc_pct"] * revenue
        dnwc = nwc - nwc_prev
        sbc = p["share_based_pct"] * revenue
        fcff = nopat + da - capex - dnwc
        tau = year_fraction(t, vdate)
        df = 1 / (1 + wacc) ** tau
        for k, v in (("years", t), ("revenue", revenue), ("growth", growth), ("adj_ebit_margin", margin),
                     ("adj_ebit", adj_ebit), ("tax_rate", tax), ("nopat", nopat), ("da", da), ("capex", capex),
                     ("nwc", nwc), ("delta_nwc", dnwc), ("share_based_cost", sbc),
                     ("adj_ebitda_mgmt", adj_ebit + da + sbc), ("fcff", fcff), ("tau", tau),
                     ("discount_factor", df), ("pv_fcff", fcff * df)):
            out[k].append(v)
        rev_prev, nwc_prev = revenue, nwc

    # terminal FCFF: last forecast year re-taxed at the marginal rate (Decision 8A)
    nopat_tv = out["adj_ebit"][-1] * (1 - p["tax_rate_terminal"])
    fcff_tv = nopat_tv + out["da"][-1] - out["capex"][-1] - out["delta_nwc"][-1]
    tv = fcff_tv * (1 + g) / (wacc - g)
    pv_tv = tv * out["discount_factor"][-1]
    sum_pv = sum(out["pv_fcff"])
    ev = sum_pv + pv_tv
    equity = bridge_equity(ev, p)
    vps = equity / p["diluted_shares"]
    ebitda_last = out["adj_ebit"][-1] + out["da"][-1]
    out.update(nopat_tv=nopat_tv, fcff_tv=fcff_tv, tv_gordon=tv, pv_tv=pv_tv, sum_pv_fcff=sum_pv, ev=ev,
               tv_share_of_ev=pv_tv / ev, equity_value=equity, value_per_share=vps,
               upside_pct=p["price"] / vps - 1, ebitda_2030=ebitda_last,
               implied_gordon_ev_ebitda=tv / ebitda_last, wacc=wacc, terminal_g=g)
    return out


def bridge_equity(ev: float, p: dict) -> float:
    """Equity value = EV + cash + cash-like - bank debt - other financial payables - leases - distributions - minorities."""
    return (ev + p["cash"] + p["cash_like_financial_assets"] - p["bank_debt"] - p["other_financial_payables"]
            - p["lease_liabilities"] - p["distributions_2026"] - p["minority_book"])


def exit_multiple_value(res: dict, p: dict, ev_ebitda: float) -> dict:
    """Exit-multiple cross-check: TV = multiple x FY2030E EBITDA (adj. EBIT + D&A), discounted at tau_2030, same bridge."""
    tv_exit = ev_ebitda * res["ebitda_2030"]
    pv_tv_exit = tv_exit * res["discount_factor"][-1]
    ev_exit = res["sum_pv_fcff"] + pv_tv_exit
    equity_exit = bridge_equity(ev_exit, p)
    vps_exit = equity_exit / p["diluted_shares"]
    return dict(tv_exit=tv_exit, pv_tv_exit=pv_tv_exit, ev_exit=ev_exit, equity_value_exit=equity_exit,
                value_per_share_exit=vps_exit, pct_vs_gordon=vps_exit / res["value_per_share"] - 1)


def load_base_params(con) -> dict:
    """Base-case params from DuckDB: forecast_assumptions scalars, wacc base row, bridge_inputs."""
    fa = dict(con.execute("SELECT driver, value FROM forecast_assumptions WHERE value IS NOT NULL").fetchall())
    p = {k: fa[k] for k in SCALAR_DRIVERS}
    p["wacc"] = con.execute("SELECT wacc FROM wacc WHERE \"case\" = 'base'").fetchall()[0][0]
    bi = dict(con.execute("SELECT item, value FROM bridge_inputs").fetchall())
    p.update({k: bi[k] for k in BRIDGE_ITEMS})
    as_of = con.execute("SELECT as_of FROM bridge_inputs WHERE item = 'price_date'").fetchall()[0][0]
    p["valuation_date"] = dt.date.fromisoformat(str(as_of))
    p["years"] = YEARS
    p["growth_shift"] = 0.0
    p["margin_shift"] = 0.0
    assert all(isinstance(v, (int, float)) and math.isfinite(v) for k, v in p.items()
               if k not in ("valuation_date", "years")), "non-finite parameter"
    return p
