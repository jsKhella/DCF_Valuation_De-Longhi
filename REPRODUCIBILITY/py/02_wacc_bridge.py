"""Step 2: estimate the WACC (base + beta sensitivity) and assemble the sourced equity-bridge inputs.

Purpose
    Build bridge_inputs (every item the EV -> equity -> per-share bridge needs, each with value, unit, as_of, source,
    treatment, note), wacc_inputs (every WACC input with its source) and wacc (two rows: base, beta_sensitivity).

Inputs (DuckDB, built by steps 0-1)
    hist_statements (YE2024/YE2025 balance sheet debt lines, minority interest), raw_report_lines (AR2025 notes 9, 15,
    18, 24, 26, 28, 32, 33 and the NFP table; IR_H1_2026 cash-flow summary and notes 26-28), raw_yahoo_prices (DLG.MI),
    raw_ecb_yield_10y, raw_damodaran_beta_europe, raw_damodaran_beta_global, raw_damodaran_params,
    raw_damodaran_ctryprem, raw_damodaran_taxrates.

Outputs (DuckDB tables, CREATE OR REPLACE, no timestamps)
    bridge_inputs (item, value, unit, as_of, source, treatment, note)   money in EUR m, shares in millions
    wacc_inputs   (input, value, unit, source)                          rates as decimals (0.04362 = 4.362%)
    wacc          (case, rf, beta_u, d_e, tax_marginal, beta_l, erp_mature, country_spread, ke, kd_pre, kd_post,
                   w_e, w_d, wacc)

Brief definitions implemented (by term)
    "Net debt" and "Equity bridge" (inputs; Decision 4A cash-like assets, Decision 1A distributions, minorities at book),
    "Market price" (Decision 2: DLG.MI close 2026-11-06), "Cost of equity" = rf + beta_l x (mature ERP + Italy default
    spread), "Cost of debt" (FY2025 interest on loans and bonds / average gross financial debt excl. leases),
    "WACC" (Decision 5A: D = gross financial debt + leases, E = market cap; beta relevered at that D/E),
    "Diluted shares" (issued - treasury at 30 Jun 2026 + treasury-stock-method options + performance-share rights).

Conventions
    Everything is parsed from raw_report_lines by anchor text (a unique matching line is asserted, never a hard-coded
    page). Where a plan page reference differs from the PDF page found, the PDF page index is stored in `source`.
"""
import re
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "curiosity.duckdb"

VAL_DATE_LIMIT = "2026-11-09"   # Decision 2: only completed sessions strictly before this date
AS_OF_BS = "2025-12-31"
AS_OF_H1 = "2026-06-30"

con = duckdb.connect(str(DB))


# ----------------------------------------------------------------------------------------------------- helpers
def num(s: str) -> float:
    """'(1,234)' -> -1234.0 ; '1,234' -> 1234.0 ; '-' -> 0.0"""
    s = s.strip()
    if s in ("-", ""):
        return 0.0
    neg = s.startswith("(") and s.endswith(")")
    v = float(s.strip("()").replace(",", ""))
    return -v if neg else v


def find(doc, pattern, pages=None):
    """Return (page, line_no, text) of the single line of `doc` matching regex `pattern` (restricted to pages)."""
    q = "SELECT page, line_no, text FROM raw_report_lines WHERE doc_id = ? AND regexp_matches(text, ?)"
    args = [doc, pattern]
    if pages:
        q += " AND page BETWEEN ? AND ?"
        args += list(pages)
    rows = con.execute(q + " ORDER BY page, line_no", args).fetchall()
    assert len(rows) == 1, f"{doc} /{pattern}/ pages={pages}: expected exactly 1 line, got {rows}"
    return rows[0]


def after(doc, page, line_no, k):
    """Text of line `line_no + k` on the same page."""
    return con.execute("SELECT text FROM raw_report_lines WHERE doc_id=? AND page=? AND line_no=?",
                       [doc, page, line_no + k]).fetchall()[0][0]


def nums(text):
    """All numeric tokens (thousand-format) in a text line, as floats. Parentheses = negative."""
    return [num(t) for t in re.findall(r"\(?[\d][\d,]*\.?\d*\)?", text)]


def hist(fy, item):
    r = con.execute("SELECT value_eur_m, pdf_page FROM hist_statements WHERE fy=? AND statement='BS' AND "
                    "line_item=?", [fy, item]).fetchall()[0]
    return r


def src(doc, page, line, what):
    return f"{doc} PDF p.{page} line {line}: {what}"


bridge = []   # dicts


def add(item, value, unit, as_of, source, treatment, note):
    bridge.append(dict(item=item, value=float(value), unit=unit, as_of=as_of, source=source, treatment=treatment,
                       note=note))


# ------------------------------------------------------------------- balance-sheet debt (YE2025) from step 1
bank_lt, p_bs = hist(2025, "bank loans and borrowings (long-term portion)")
bank_st, _ = hist(2025, "bank loans and borrowings (short-term portion)")
ofp_lt, _ = hist(2025, "other financial payables (long-term portion)")
ofp_st, _ = hist(2025, "other financial payables (short-term portion)")
lease_lt, _ = hist(2025, "lease liabilities (long-term portion)")
lease_st, _ = hist(2025, "lease liabilities (short-term portion)")
cash25, p_cash = hist(2025, "cash and cash equivalents")
mino25, _ = hist(2025, "minority interest")
bank24 = hist(2024, "bank loans and borrowings (long-term portion)")[0] + \
    hist(2024, "bank loans and borrowings (short-term portion)")[0]
ofp24 = hist(2024, "other financial payables (long-term portion)")[0] + \
    hist(2024, "other financial payables (short-term portion)")[0]

bank_debt = bank_lt + bank_st
other_fp = ofp_lt + ofp_st
leases = lease_lt + lease_st

# cross-checks against the notes (single source of truth for the parse: the PDF text)
pg, ln, t = find("AR2025", r"^Total banks loans and borrowings ", (170, 180))
assert abs(nums(t)[2] / 1000 - bank_debt) < 1e-9, (t, bank_debt)   # numeric tokens: 35,877 191,166 227,043 ...
pg33, ln33, t = find("AR2025", r"^Total other financial payables ", (170, 180))
assert abs(nums(t)[0] / 1000 - other_fp) < 1e-9 and abs(nums(t)[1] / 1000 - ofp24) < 1e-9, (t, other_fp, ofp24)
pg15, ln15, t = find("AR2025", r"^At 31 December 2025 financial liabilities for leases of", (160, 175))
assert abs(nums(t)[2] / 1000 - leases) < 1e-9, (t, leases)
note32_page = find("AR2025", r"^32\. Bank loans and borrowings", (170, 180))[0]

add("bank_debt", bank_debt, "EUR m", AS_OF_BS,
    f"hist_statements BS FY2025 bank loans and borrowings (long-term {bank_lt} + short-term {bank_st}); "
    f"AR2025 PDF p.{p_bs} (balance sheet), note 32 PDF p.{note32_page}",
    "deduct from EV", "Gross bank loans and overdrafts at 31 Dec 2025; equals note 32 'Total banks loans and "
    "borrowings' 227,043 thousand.")
add("other_financial_payables", other_fp, "EUR m", AS_OF_BS,
    f"hist_statements BS FY2025 other financial payables (long-term {ofp_lt} + short-term {ofp_st}); "
    f"AR2025 PDF p.{p_bs}, note 33 PDF p.{pg33} line {ln33}",
    "deduct from EV", "US private placement bonds 193.177, derivative liabilities 4.312, other short-term financial "
    "payables 14.691 (mainly factoring). Equals note 33 'Total other financial payables' 212,180 thousand.")
add("lease_liabilities", leases, "EUR m", AS_OF_BS,
    f"hist_statements BS FY2025 lease liabilities (long-term {lease_lt} + short-term {lease_st}); "
    f"AR2025 PDF p.{pg15} line {ln15} (note 15: EUR 94,370 thousand)",
    "deduct from EV", "IFRS 16 lease liabilities. Equals the NFP table lease lines (26,739 + 67,631). The plan's "
    "'NFP table 94.0' is the same figure rounded.")
add("cash", cash25, "EUR m", AS_OF_BS,
    f"hist_statements BS FY2025 cash and cash equivalents; AR2025 PDF p.{p_cash}",
    "add to EV", "Cash only (NFP table line A). Cash pooling is netted under IAS 32; EUR 4 thousand restricted.")

# ---------------------------------------------------------------- NFP table and financial assets (note 18 / 24)
pn, ln_a, t = find("AR2025", r"^A\. Cash [\d,]+ [\d,]+$", (170, 180))
assert abs(nums(t)[0] / 1000 - cash25) < 1e-9
_, ln_c, t_c = find("AR2025", r"^C\. Other current financial assets [\d,]+ [\d,]+$", (pn, pn))
other_cur_fa = nums(t_c)[0] / 1000
_, ln_i1, t_i1 = find("AR2025", r"^I\.1\. Other non-current financial assets [\d,]+ [\d,]+$", (pn, pn))
noncur_fa = nums(t_i1)[-2] / 1000   # last two tokens = 2025, 2024 (label contains "I.1.")
_, ln_nfp, t_nfp = find("AR2025", r"^Total net financial position [\d,]+ [\d,]+$", (pn, pn))
nfp_reported = nums(t_nfp)[0] / 1000
# derivatives line: "2,431 7,076" is the line two lines after "Fair value of derivatives and other financial ..."
_, ln_fvh, _ = find("AR2025", r"^Fair value of derivatives and other financial non-bank assets/$", (pn, pn))
fv_net = nums(after("AR2025", pn, ln_fvh, 2))[0] / 1000

# note 24 (current financial receivables and assets) itemised
p24, l24, _ = find("AR2025", r"^24\. Current financial receivables and assets$", (160, 180))
items24 = {}
for k, key in [(3, "derivatives"), (4, "lease_prepayments"), (5, "fv_other_current"), (6, "other_current"),
               (7, "total")]:
    tx = after("AR2025", p24, l24, k)
    items24[key] = (nums(tx)[0] / 1000, l24 + k, tx)
assert items24["derivatives"][2].startswith("Fair value of derivatives")
assert items24["lease_prepayments"][2].startswith("Advances for leasing")
assert items24["fv_other_current"][2].startswith("Fair value of other current")
assert items24["other_current"][2].startswith("Other current financial assets")
assert items24["total"][2].startswith("Total")
assert abs(sum(v[0] for k, v in items24.items() if k != "total") - items24["total"][0]) < 1e-9
# NFP table line C = note 24 total less derivatives (derivatives sit in the separate "fair value" line)
assert abs(other_cur_fa - (items24["total"][0] - items24["derivatives"][0])) < 1e-9
# derivative net position = derivative assets - derivative liabilities (note 33, 4.312)
_, l_dl, t_dl = find("AR2025", r"^Negative fair value of derivatives 4,312 9,523$", (pg33 - 1, pg33 + 1))
deriv_liab = nums(t_dl)[0] / 1000
assert abs(items24["derivatives"][0] - deriv_liab - fv_net) < 1e-9

# note 18 (other non-current financial assets): total = NFP line I.1; components quoted in the note text
p18, l18, _ = find("AR2025", r"^18\. Other non-current financial assets$", (160, 180))
_, l18b, t18b = find("AR2025", r"^The item mainly includes ", (p18, p18))

fin_assets_all = (other_cur_fa + items24["derivatives"][0]) + noncur_fa
# reconciliation to the reported NFP (done here as an assertion, and again in the check)
nfp_calc = cash25 + other_cur_fa + noncur_fa + fv_net - (bank_debt + other_fp - deriv_liab + leases)
assert abs(nfp_calc - nfp_reported) < 0.0015, (nfp_calc, nfp_reported)

cash_like = items24["derivatives"][0] + items24["fv_other_current"][0] + items24["other_current"][0] + noncur_fa
excluded = items24["lease_prepayments"][0]
assert abs(cash_like + excluded - fin_assets_all) < 1e-9

add("cash_like_financial_assets", cash_like, "EUR m", AS_OF_BS,
    f"AR2025 PDF p.{p24} lines {l24+3}, {l24+5}, {l24+6} (note 24: derivatives {items24['derivatives'][0]:.3f} + "
    f"fair value of other current financial assets {items24['fv_other_current'][0]:.3f} + other current financial "
    f"assets {items24['other_current'][0]:.3f}) and PDF p.{pn} line {ln_i1} (NFP line I.1 / note 18 PDF p.{p18}: "
    f"{noncur_fa:.3f})",
    "add to EV (Decision 4A)",
    f"Itemised: derivative fair values {items24['derivatives'][0]:.3f}; fair value of other current financial assets "
    f"{items24['fv_other_current'][0]:.3f}; other current financial assets (liquidity investments held to maturity) "
    f"{items24['other_current'][0]:.3f}; non-current liquidity investments (bond 9.994 + floating rate note 50.348 "
    f"+ other, note 18) {noncur_fa:.3f}. Excluded as not liquid: lease prepayments {excluded:.3f}. "
    "Guarantee deposits (note 17 'non-current receivables' 4.999) and operating receivables are not in this line.")
add("financial_assets_all", fin_assets_all, "EUR m", AS_OF_BS,
    f"AR2025 PDF p.{p24} (note 24 total {items24['total'][0]:.3f}) + PDF p.{pn} line {ln_i1} (NFP line I.1)",
    "reconciliation only", "All financial receivables and assets in the company's NFP incl. derivative assets "
    "(Decision 4 B-view). Used only for the NFP reconciliation.")
add("financial_assets_excluded", excluded, "EUR m", AS_OF_BS,
    f"AR2025 PDF p.{p24} line {l24+4} (note 24 'Advances for leasing contracts')",
    "reconciliation only", "Financial assets not treated as cash-like under Decision 4A (lease prepayments).")
add("nfp_reported", nfp_reported, "EUR m", AS_OF_BS,
    f"AR2025 PDF p.{pn} line {ln_nfp}: Total net financial position (EUR 769,993 thousand)",
    "reconciliation only",
    f"Company NFP (positive = net cash). Reconciles to the bridge items: cash + other current financial assets "
    f"{other_cur_fa:.3f} + non-current financial assets {noncur_fa:.3f} + net derivatives {fv_net:.3f} - gross "
    f"financial debt incl. leases and net of derivative liabilities = {nfp_calc:.3f}.")

# ------------------------------------------------------------------------- distributions since 31 Dec 2025
pcf, lcf, tcf = find("IR_H1_2026", r"^Dividends paid \([\d.]+\) \([\d.]+\) \([\d.]+\)$", (15, 25))
div_h1 = -nums(tcf)[0]
_, lbb, tbb = find("IR_H1_2026", r"^Cash flow by treasury shares purchase \([\d.]+\)", (pcf, pcf))
bb_h1 = -nums(tbb)[0]
assert (div_h1, bb_h1) == (127.9, 28.5), (div_h1, bb_h1)
add("distributions_2026", div_h1 + bb_h1, "EUR m", AS_OF_H1,
    f"IR_H1_2026 PDF p.{pcf} lines {lcf} and {lbb} (condensed cash flow, 6 months to 30 Jun 2026): dividends paid "
    f"{div_h1} + treasury share purchases {bb_h1}. (The plan cites 'p.18'; the figures are on PDF p.{pcf}, printed "
    f"page {pcf-1}.)",
    "deduct from equity value (Decision 1A)",
    "Cash already paid to shareholders between the 31 Dec 2025 balance sheet and the valuation date. The 127.9 "
    "dividends include EUR 1.026 m paid to minority shareholders (interim p.30). H2 2026 cash moves until 6 Nov are "
    "not captured (Q3 report not published).")

add("minority_book", mino25, "EUR m", AS_OF_BS,
    f"hist_statements BS FY2025 minority interest; AR2025 PDF p.{p_bs}",
    "deduct from equity value at book (simplification)",
    "SIMPLIFICATION: minorities at book value (La Marzocco / Eversys); likely understates their share of value "
    "(7.35% of FY2025 profit; H1 2026 minority profit 27.6 m). Book 30 Jun 2026 = 227.6 m, not used.")

# ----------------------------------------------------------------------------------------------- share count
p28, l28, t28 = find("AR2025", r"^.*therefore, the share capital comprises$", (170, 180))
sh25_txt = after("AR2025", p28, l28, 1)
shares_issued = nums(sh25_txt)[0] / 1e6
sc_pg, sc_ln, sc_txt = find("AR2025", r"^- Share Capital \d+ [\d,]+ [\d,]+$", (140, 150))
share_capital = nums(sc_txt)[1] / 1000    # [note number, 2025, 2024]
assert abs(shares_issued * 1.5 - share_capital) < 0.01, (shares_issued, share_capital)
pi, li, ti = find("IR_H1_2026", r"^At 30 June 2026 the share capital comprises [\d,]+ ordinary shares", (55, 65))
assert float(re.search(r"comprises ([\d,]+) ordinary", ti).group(1).replace(",", "")) / 1e6 == shares_issued
add("shares_issued", shares_issued, "million shares", AS_OF_H1,
    f"AR2025 PDF p.{p28} line {l28+1} (note 28: {sh25_txt.split()[0]} ordinary shares, EUR 226,942 thousand = x 1.5 "
    f"par); unchanged at 30 Jun 2026 (IR_H1_2026 PDF p.{pi} line {li})",
    "gross share count", "Issued ordinary shares, par value EUR 1.5. No shares were issued in H1 2026.")

pt, lt, tt = find("IR_H1_2026", r"^As of 30 June 2026, the treasury shares held in the portfolio amounted to [\d,]+ for", (55, 60))
treasury = float(re.search(r"amounted to ([\d,]+) for", tt).group(1).replace(",", "")) / 1e6
add("treasury_shares", treasury, "million shares", AS_OF_H1,
    f"IR_H1_2026 PDF p.{pt} line {lt} (note 26: 2,574,620 treasury shares at 30 Jun 2026)",
    "deduct from share count",
    "30 Jun 2026 (not 31 Dec 2025: 1,771,513) so the share count is consistent with the H1 2026 buybacks "
    "(818,107 shares, EUR 28.5 m) deducted in distributions_2026.")

# dilution: treasury stock method for options, rights at zero exercise price counted in full
po, lo, to_ = find("IR_H1_2026", r"^amounted to [\d,]+; during the first half of 2026", (55, 65))
options = float(re.search(r"decreased to ([\d,]+) following", to_).group(1).replace(",", ""))
pe, le, te = find("AR2025", r"^Exercise price \(Euro\) 16\.982 ", (170, 180))
strike = float(te.split()[3])
pr, lr, tr = find("IR_H1_2026", r"^At 30 June 2026, based on the available information", (55, 65))
rights_line = after("IR_H1_2026", pr, lr, 1)
rights = float(re.search(r"estimated at ([\d,]+)", rights_line).group(1).replace(",", ""))

# price (needed for the treasury stock method)
px = con.execute("SELECT trade_date, close FROM raw_yahoo_prices WHERE ticker='DLG.MI' AND trade_date < CAST(? AS DATE) "
                 "ORDER BY trade_date DESC LIMIT 1", [VAL_DATE_LIMIT]).fetchall()[0]
price_date, price_raw = px
price = round(price_raw, 2)   # Yahoo returns a float32 artefact (45.31999969...); EUR quotes have 2 decimals
assert str(price_date) == "2026-11-06" and price == 45.32, (price_date, price)

dil_options = options * max(0.0, 1.0 - strike / price) / 1e6
dil_rights = rights / 1e6
dilutive = dil_options + dil_rights
add("dilutive_shares", dilutive, "million shares", AS_OF_H1,
    f"IR_H1_2026 PDF p.{po} line {lo} ({options:,.0f} options, exercise price EUR {strike} from AR2025 PDF p.{pe} "
    f"line {le}) and PDF p.{pr} line {lr+1} ({rights:,.0f} Performance Shares Plan rights)",
    "add to share count",
    f"Treasury stock method at the 6 Nov 2026 price: options {options:,.0f} x (1 - {strike}/{price}) = "
    f"{dil_options*1e6:,.0f} shares; performance-share rights {rights:,.0f} (zero exercise price, assumed to vest in "
    "full, the plan's estimate). Reported weighted diluted shares at 30 Jun 2026 differ from basic by only 39,333.")
diluted = shares_issued - treasury + dilutive
add("diluted_shares", diluted, "million shares", AS_OF_H1,
    "computed: shares_issued - treasury_shares + dilutive_shares", "divisor for value per share",
    "Used for market cap and value per share.")

add("price", price, "EUR per share", str(price_date),
    f"raw_yahoo_prices DLG.MI close of {price_date} (raw {price_raw!r}); the 2026-11-09 bar is intraday and excluded",
    "market price (Decision 2)", "Rounded to 0.01 (float32 artefact in the Yahoo JSON).")
add("price_date", int(str(price_date).replace("-", "")), "yyyymmdd", str(price_date),
    "raw_yahoo_prices DLG.MI latest trade_date < 2026-11-09", "valuation date (Decision 2)",
    "Last completed Milan session before the data download; 7-8 Nov 2026 is a weekend.")
mcap = price * diluted
add("market_cap", mcap, "EUR m", str(price_date), "computed: price x diluted_shares", "WACC equity weight",
    "Market capitalisation on diluted shares.")

# ------------------------------------------------------------------------------------------- cost of debt data
pint, lint, tint = find("AR2025", r"^nancing instruments for an amount of .[\d,]+ thousand", (160, 170))
interest = float(re.search(r"amount of .([\d,]+) thousand", tint).group(1).replace(",", "")) / 1000
prev_line = after("AR2025", pint, lint, -2)
assert "net of interest expenses relating to the Group" in prev_line, prev_line
debt24 = bank24 + ofp24
debt25 = bank_debt + other_fp
add("interest_expense_fy2025", interest, "EUR m", "FY2025",
    f"AR2025 PDF p.{pint} lines {lint-2}-{lint} (note 9: interest expenses on the Group's financial debt and other "
    "financing instruments)", "cost of debt numerator",
    "Excludes interest on leases (2.871) and interest income (23.601). FY2024: 25.456.")

# ------------------------------------------------------------------------------------------------ WACC inputs
rf_row = con.execute("SELECT yield_pct, period FROM raw_ecb_yield_10y WHERE country='IT' ORDER BY period DESC "
                     "LIMIT 1").fetchall()[0]
assert rf_row[1] == "2026-09"
rf = rf_row[0] / 100
erp = float(con.execute("SELECT value FROM raw_damodaran_params WHERE param='mature_market_erp'").fetchall()[0][0])
spread = con.execute("SELECT rating_based_default_spread FROM raw_damodaran_ctryprem WHERE country='Italy'").fetchall()[0][0]
tax = con.execute("SELECT corporate_tax_rate FROM raw_damodaran_taxrates WHERE country='Italy'").fetchall()[0][0]
bu_base = con.execute("SELECT unlevered_beta_corrected_for_cash FROM raw_damodaran_beta_europe "
                      "WHERE industry_name='Furn/Home Furnishings'").fetchall()[0][0]
bu_sens = con.execute("SELECT unlevered_beta_corrected_for_cash FROM raw_damodaran_beta_global "
                      "WHERE industry_name='Furn/Home Furnishings'").fetchall()[0][0]

D = bank_debt + other_fp + leases          # Decision 5A
E = mcap
d_e = D / E
w_e = E / (D + E)
w_d = D / (D + E)

kd_pre = interest / ((debt25 + debt24) / 2)
if not (rf - 0.01 <= kd_pre <= rf + 0.03):
    raise SystemExit(f"BLOCKED: kd_pre {kd_pre:.4%} outside [rf-1pp, rf+3pp]; plan rule needs a documented fallback")
kd_post = kd_pre * (1 - tax)

wrows = []
for case, bu in [("base", bu_base), ("beta_sensitivity", bu_sens)]:
    beta_l = bu * (1 + (1 - tax) * d_e)
    ke = rf + beta_l * (erp + spread)
    wacc = w_e * ke + w_d * kd_post
    wrows.append(dict(case=case, rf=rf, beta_u=bu, d_e=d_e, tax_marginal=tax, beta_l=beta_l, erp_mature=erp,
                      country_spread=spread, ke=ke, kd_pre=kd_pre, kd_post=kd_post, w_e=w_e, w_d=w_d, wacc=wacc))

win = [
    ("rf", rf, "decimal", f"ECB Data Portal IRS.M.IT.L.L40.CI.0000.EUR.N.Z, Italy 10y yield monthly average "
                          f"{rf_row[1]} (Decision 2); raw_ecb_yield_10y"),
    ("erp_mature", erp, "decimal", "Damodaran ctryprem.xls 'ERPs by country' E3 mature market ERP, update 2026-01-01"),
    ("country_spread", spread, "decimal", "Damodaran ctryprem.xls Italy (Moody's Baa2) rating-based default spread "
                                          "(not the country risk premium 2.46%); note: Italy risk is also in the "
                                          "BTP rf, so there is partial double counting (limitation stated in the brief)"),
    ("tax_marginal", tax, "decimal", "Damodaran countrytaxrates.xls Italy corporate tax rate (IRES 24% + IRAP 3.9%)"),
    ("beta_u_base", bu_base, "ratio", "Damodaran betaEurope.xls 'Furn/Home Furnishings' (53 firms) unlevered beta "
                                      "corrected for cash (Decision 3 base)"),
    ("beta_u_sensitivity", bu_sens, "ratio", "Damodaran betaGlobal.xls 'Furn/Home Furnishings' (383 firms) unlevered "
                                             "beta corrected for cash (Decision 3 sensitivity line)"),
    ("price", price, "EUR per share", f"raw_yahoo_prices DLG.MI close {price_date} (bridge_inputs)"),
    ("diluted_shares", diluted, "million shares", "bridge_inputs diluted_shares"),
    ("market_cap_E", E, "EUR m", "price x diluted shares (bridge_inputs market_cap)"),
    ("debt_D", D, "EUR m", "Decision 5A: bank debt + other financial payables + lease liabilities at 31 Dec 2025 "
                           "(bridge_inputs), gross, not net of cash"),
    ("d_e", d_e, "ratio", "D / E; beta relevered at this ratio (Hamada, marginal tax)"),
    ("w_e", w_e, "decimal", "E / (D + E)"),
    ("w_d", w_d, "decimal", "D / (D + E)"),
    ("interest_expense_fy2025", interest, "EUR m", f"AR2025 PDF p.{pint} (note 9), bridge_inputs"),
    ("gross_financial_debt_excl_leases_ye2025", debt25, "EUR m", "bank loans + other financial payables, YE2025 "
                                                                 "(hist_statements)"),
    ("gross_financial_debt_excl_leases_ye2024", debt24, "EUR m", "bank loans + other financial payables, YE2024 "
                                                                 "(hist_statements)"),
    ("kd_pre", kd_pre, "decimal", "FY2025 interest on loans and bonds / average gross financial debt excl. leases "
                                  "(YE2024, YE2025); inside [rf - 1 pp, rf + 3 pp], so no fallback to rf + spread"),
    ("kd_post", kd_post, "decimal", "kd_pre x (1 - marginal tax)"),
    ("terminal_g_reference", 0.02, "decimal", "Decision 7 (ECB inflation target); used only for the g < rf check"),
]
wacc_inputs = pd.DataFrame(win, columns=["input", "value", "unit", "source"])

# ------------------------------------------------------------------------------------------------ write tables
bdf = pd.DataFrame(bridge, columns=["item", "value", "unit", "as_of", "source", "treatment", "note"])
wdf = pd.DataFrame(wrows)
for name, df in [("bridge_inputs", bdf), ("wacc_inputs", wacc_inputs), ("wacc", wdf)]:
    con.register("_df", df)
    con.execute(f'CREATE OR REPLACE TABLE {name} AS SELECT * FROM _df')
    con.unregister("_df")
    print(f"{name}: {con.execute(f'SELECT COUNT(*) FROM {name}').fetchall()[0][0]} rows")
print(wdf[["case", "beta_u", "beta_l", "ke", "kd_pre", "kd_post", "w_e", "w_d", "wacc"]].to_string())
con.close()
