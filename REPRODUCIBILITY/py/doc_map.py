"""Registry shared by the workbook, the investment note and the process guide (Amendment 2, R-A and Design).

Purpose
    One list of sheets and guide sections (id, sheet name, guide title, previous/next), the set of sheets that carry a
    readable-label column, and the mapping LABELS = {DuckDB key: readable label}.
Inputs
    none (constants only).
Outputs
    SHEETS, SECTIONS, LABEL_SHEETS, LABEL_KEY_HEADERS, LABELS and small lookup helpers; step 9 adds AUTHOR_NAME,
    AUTHOR_EMAIL, AUTHOR_AFFILIATION, AUTHOR_LINE and TEXT_REWORDS / reword() (plan Amendment 3).
Brief definitions implemented
    none (presentation only). Sheet names supersede brief section 6 (plan Amendment 2, R-A).
"""
# (id, workbook sheet name, guide title). The sheet name starts with the id.
SHEETS = [
    ("0.0", "0.0 Overview", "Overview"),
    ("1.1", "1.1 Statements", "Condensed statements"),
    ("1.2", "1.2 Adjustments & Ratios", "Adjustments and historical ratios"),
    ("2.1", "2.1 WACC", "Cost of capital"),
    ("2.2", "2.2 Bridge Inputs", "Equity bridge inputs"),
    ("3.1", "3.1 FCFF Forecast", "FCFF forecast"),
    ("3.2", "3.2 Valuation", "Valuation"),
    ("3.3", "3.3 Multiples Check", "Exit-multiple cross-check"),
    ("4.1", "4.1 Sensitivity", "Sensitivity grid"),
    ("4.2", "4.2 Monte Carlo", "Monte Carlo"),
    ("5.1", "5.1 Checks", "Reconciliations and checks"),
]
SHEET_NAMES = [s[1] for s in SHEETS]
SHEET_ID = {s[1]: s[0] for s in SHEETS}
NAME_OF_ID = {s[0]: s[1] for s in SHEETS}
TITLE_OF_ID = {s[0]: s[2] for s in SHEETS}

# Old sheet name (HEAD 59ecd69) -> new sheet name. The bridge_inputs block of Valuation moves to 2.2.
OLD_TO_NEW = {"Statements_5Y": "1.1 Statements", "Adjustments_Ratios": "1.2 Adjustments & Ratios", "WACC": "2.1 WACC",
              "Forecast_FCFF": "3.1 FCFF Forecast", "Valuation": "3.2 Valuation", "Multiples_Check": "3.3 Multiples Check",
              "Sensitivity": "4.1 Sensitivity", "MonteCarlo": "4.2 Monte Carlo", "Checks": "5.1 Checks"}
BRIDGE_SHEET = "2.2 Bridge Inputs"
BRIDGE_HEADER = "Bridge input"          # header label that starts the moved block (old Valuation, new 2.2)

# Guide sections in outline order (step 8). (id, title)
SECTIONS = [("0.0", "Question, answer and method"), ("0", "Data and sources"),
            ("1", "Historical statements"), ("1.1", TITLE_OF_ID["1.1"]), ("1.2", TITLE_OF_ID["1.2"]),
            ("2", "Cost of capital and bridge"), ("2.1", TITLE_OF_ID["2.1"]), ("2.2", TITLE_OF_ID["2.2"]),
            ("3", "Forecast and valuation"), ("3.1", TITLE_OF_ID["3.1"]), ("3.2", TITLE_OF_ID["3.2"]),
            ("3.3", TITLE_OF_ID["3.3"]),
            ("4", "Sensitivity and simulation"), ("4.1", TITLE_OF_ID["4.1"]), ("4.2", TITLE_OF_ID["4.2"]),
            ("5", "Checks"), ("5.1", TITLE_OF_ID["5.1"]),
            ("6", "Investment note"),
            ("A", "Appendix"), ("A.1", "Audit trail"), ("A.2", "Glossary"), ("A.3", "Limitations")]

# Sheets whose column A holds DuckDB keys: a column B "Label" is inserted (Decision 3 = B).
LABEL_SHEETS = ["1.2 Adjustments & Ratios", "2.1 WACC", "2.2 Bridge Inputs", "3.1 FCFF Forecast", "3.2 Valuation",
                "4.2 Monte Carlo"]
LABEL_HEADER = "Label"
# Header words in column A of the tables whose column A holds keys: their column-B header cell reads "Label".
LABEL_KEY_HEADERS = {"Ratio", "Input", "Item", "Beta sensitivity line", "Line item", "Driver", "Headline numbers",
                     "Bridge input", "Statistic", "Parameter"}


def prev_next(name):
    i = SHEET_NAMES.index(name)
    return (SHEET_NAMES[i - 1] if i > 0 else None, SHEET_NAMES[i + 1] if i + 1 < len(SHEET_NAMES) else None)


YEARS_FC = ["2026", "2027", "2028", "2029", "2030"]
LABELS = {
    # historical ratios (1.2)
    "revenue": "Revenue", "growth": "Revenue growth", "ebit_reported": "EBIT as reported",
    "nonrec": "Non-recurring items in EBIT", "adj_ebit": "Adjusted EBIT", "adj_ebit_margin": "Adjusted EBIT margin",
    "da": "Depreciation and amortisation", "da_pct": "D&A, % of revenue", "capex_intangible": "Capex, intangibles",
    "capex_ppe": "Capex, property, plant and equipment", "capex_rou": "Right-of-use additions",
    "capex_total": "Capex, total", "capex_pct": "Capex, % of revenue",
    "capex_excl_rou_pct": "Capex excl. right-of-use, % of revenue", "trade_receivables": "Trade receivables",
    "inventories": "Inventories", "trade_payables": "Trade payables", "nwc": "Net working capital",
    "nwc_pct": "Net working capital, % of revenue", "delta_nwc": "Change in net working capital",
    "pbt": "Profit before tax", "taxes": "Income taxes", "eff_tax_rate": "Effective tax rate",
    "tax_included": "Year used for the tax-rate median", "fcff_hist": "Free cash flow to the firm, historical",
    # WACC inputs, cases and beta line (2.1)
    "rf": "Risk-free rate", "erp_mature": "Mature-market equity risk premium", "country_spread": "Italy default spread",
    "tax_marginal": "Marginal tax rate", "beta_u_base": "Unlevered beta, base", "beta_u_sensitivity": "Unlevered beta, sensitivity",
    "price": "Share price", "diluted_shares": "Diluted shares", "market_cap_E": "Market capitalisation (E)",
    "debt_D": "Debt for the WACC weights (D)", "d_e": "Debt to equity", "w_e": "Equity weight", "w_d": "Debt weight",
    "interest_expense_fy2025": "Interest expense FY2025",
    "gross_financial_debt_excl_leases_ye2025": "Gross financial debt excl. leases, YE2025",
    "gross_financial_debt_excl_leases_ye2024": "Gross financial debt excl. leases, YE2024",
    "kd_pre": "Cost of debt, pre-tax", "kd_post": "Cost of debt, after tax",
    "terminal_g_reference": "Terminal growth, reference", "beta_u": "Unlevered beta", "beta_l": "Relevered beta",
    "ke": "Cost of equity", "wacc": "WACC", "value_per_share": "Value per share",
    "base_value_per_share": "Base-case value per share", "diff_vs_base": "Difference vs base case",
    "pct_vs_base": "Difference vs base case, %",
    # forecast lines and drivers (3.1)
    "tax_rate": "Tax rate", "nopat": "NOPAT", "capex": "Capex", "fcff": "Free cash flow to the firm",
    "share_based_cost": "Share-based cost", "adj_ebitda_mgmt": "Adjusted EBITDA, management definition",
    "nopat_tv": "NOPAT, terminal year", "fcff_tv": "FCFF, terminal year",
    "revenue_fy2025": "Revenue FY2025", "nwc_fy2025": "Net working capital FY2025",
    "growth_fy2026": "Revenue growth FY2026E", "terminal_g": "Terminal growth rate",
    "growth_fade_years": "Years of growth fade", "guidance_adj_ebitda_fy2026": "Guidance, adjusted EBITDA FY2026",
    "adj_ebitda_fy2025_mgmt": "Adjusted EBITDA FY2025, management", "share_based_cost_fy2025": "Share-based cost FY2025",
    "share_based_pct": "Share-based cost, % of revenue", "adj_ebit_margin_fy2026": "Adjusted EBIT margin FY2026E",
    "adj_ebit_margin_target_fy2030": "Adjusted EBIT margin target FY2030E", "tax_rate_forecast": "Tax rate, forecast years",
    "tax_rate_terminal": "Tax rate, terminal value", "revenue_growth": "Revenue growth, forecast path",
    # headline and valuation lines (3.2)
    "g": "Terminal growth rate", "mc_p10": "Monte Carlo 10th percentile", "mc_p90": "Monte Carlo 90th percentile",
    "price_percentile": "Price percentile in the simulation", "price_percentile_ordinal": "Price percentile, rounded",
    "sum_pv_fcff": "Sum of present values of FCFF", "tv_gordon": "Terminal value (Gordon growth)",
    "pv_tv": "Present value of terminal value", "ev": "Enterprise value", "tv_share_of_ev": "Terminal value, % of EV",
    "cash": "Cash and cash equivalents", "cash_like_financial_assets": "Cash-like financial assets",
    "bank_debt": "Bank debt", "other_financial_payables": "Other financial payables",
    "lease_liabilities": "Lease liabilities", "distributions_2026": "Distributions paid in 2026",
    "minority_book": "Minorities at book value", "equity_value": "Equity value", "upside_pct": "Price vs value per share, %",
    # bridge inputs (2.2)
    "financial_assets_all": "Financial assets, all", "financial_assets_excluded": "Financial assets, excluded",
    "nfp_reported": "Net financial position as reported", "shares_issued": "Shares issued",
    "treasury_shares": "Treasury shares", "dilutive_shares": "Dilutive shares", "price_date": "Price date",
    "market_cap": "Market capitalisation",
    # Monte Carlo statistics and parameters (4.2)
    "p5": "5th percentile", "p10": "10th percentile", "p25": "25th percentile", "p50": "Median",
    "p75": "75th percentile", "p90": "90th percentile", "p95": "95th percentile", "mean": "Mean",
    "sd": "Standard deviation", "run0_value_per_share": "Run 0 value per share", "n_runs": "Number of runs",
    "n_wacc_redraws": "WACC redraws", "seed": "Random seed", "sd_growth_shift": "Growth shift, standard deviation",
    "sd_margin_shift": "Margin shift, standard deviation", "rho_growth_margin": "Correlation, growth and margin",
    "wacc_mean": "WACC, mean", "wacc_sd": "WACC, standard deviation", "wacc_lower": "WACC, lower bound",
    "wacc_upper": "WACC, upper bound", "hist_bin_width": "Histogram bin width",
}
LABELS.update({f"tau_{y}": f"Year fraction to FY{y}" for y in YEARS_FC})
LABELS.update({f"discount_factor_{y}": f"Discount factor FY{y}" for y in YEARS_FC})
LABELS.update({f"pv_fcff_{y}": f"Present value of FCFF FY{y}" for y in YEARS_FC})

# Per-sheet label overrides: the same DuckDB key can mean different things on two sheets.
# pct_vs_base is price/value - 1 on 3.2 Valuation, and the beta-sensitivity value vs base on 2.1 WACC.
LABEL_OVERRIDES = {("3.2 Valuation", "pct_vs_base"): "Price vs value, %"}


def label_for(sheet, key):
    return LABEL_OVERRIDES.get((sheet, key), LABELS[key])


# ---- Amendment 3 (step 9): author line and rewording rules for source text copied into the workbook ----
AUTHOR_NAME = "Mina Khella"
AUTHOR_EMAIL = "mina.khellas@gmail.com"
AUTHOR_AFFILIATION = "Undergraduate in Statistics and Economics, Università degli studi di Milano Bicocca"
AUTHOR_LINE = " · ".join([AUTHOR_NAME, AUTHOR_EMAIL, AUTHOR_AFFILIATION])

# Ordered (old substring, new substring) rules applied to text cells at workbook build time (DuckDB is untouched).
# No digit and no banned word in either side.
TEXT_REWORDS = [
    ("The plan's 'NFP table", "The figure quoted as 'NFP table"),
    ("(The plan cites", "(An earlier reference cites"),
    ("Performance Shares Plan rights", "performance-share rights"),
    ("the plan's estimate", "an assumption fixed in advance"),
    (", plan/plan.md", ", fixed in advance"),
    ("incentive plans", "incentive schemes"),
]


def reword(text):
    """Apply TEXT_REWORDS in order to a text cell."""
    for old, new in TEXT_REWORDS:
        text = text.replace(old, new)
    return text
