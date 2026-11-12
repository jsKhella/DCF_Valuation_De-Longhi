"""Acceptance checks for step 2 (plan/plan.md): WACC and equity-bridge inputs.

Every check prints PASS/FAIL with actual vs expected; exit code 1 if any check fails.
Raw cells are re-read here from the raw_ tables with their own queries (not from the step-2 script).
Smell tests (WACC 6-10%) print SURPRISE instead of failing; the hard limits (4-12%, g < rf) FAIL.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import Checks  # noqa: E402

c = Checks()
G = 0.02  # terminal growth, Decision 7 (used only for the g < rf hard check)

# ---------------- bridge_inputs: items present exactly once, sourced
ITEMS = ["bank_debt", "other_financial_payables", "lease_liabilities", "cash", "cash_like_financial_assets",
         "distributions_2026", "minority_book", "shares_issued", "treasury_shares", "dilutive_shares",
         "diluted_shares", "price", "price_date"]
for it in ITEMS:
    c.equal(f"bridge_inputs '{it}' exactly once",
            c.scalar(f"SELECT COUNT(*) FROM bridge_inputs WHERE item='{it}'"), 1)
c.zero("bridge_inputs: item unique",
       "SELECT COUNT(*) FROM (SELECT item FROM bridge_inputs GROUP BY item HAVING COUNT(*) > 1)")
c.zero("bridge_inputs: every row has a source",
       "SELECT COUNT(*) FROM bridge_inputs WHERE source IS NULL OR trim(source) = ''")
c.zero("bridge_inputs: no null value / unit / as_of / treatment / note",
       "SELECT COUNT(*) FROM bridge_inputs WHERE value IS NULL OR unit IS NULL OR as_of IS NULL "
       "OR treatment IS NULL OR note IS NULL")


def b(item):
    return c.scalar(f"SELECT value FROM bridge_inputs WHERE item='{item}'")


# ---------------- NFP reconciliation (independent of Decision 4)
nfp_calc = (b("bank_debt") + b("other_financial_payables") + b("lease_liabilities") - b("cash")
            - b("financial_assets_all"))
c.between("NFP reconciliation: debt + other fin. payables + leases - cash - all financial assets = -770.0 (+/-0.1)",
          nfp_calc, -770.1, -769.9)
c.between("reported NFP row (AR2025 NFP table) = 770.0 (+/-0.1)", b("nfp_reported"), 769.9, 770.1)
c.between("cash-like + excluded financial assets = all financial assets (+/-0.0005)",
          b("cash_like_financial_assets") + b("financial_assets_excluded"), b("financial_assets_all") - 0.0005,
          b("financial_assets_all") + 0.0005)
c.between("cash_like_financial_assets plausible (about 305 m, Decision 4A)", b("cash_like_financial_assets"), 290, 306)

# ---------------- point checks
c.between("minority_book = 197.8 (+/-0.1)", b("minority_book"), 197.7, 197.9)
c.between("lease_liabilities = 94.370 (+/-0.0005)", b("lease_liabilities"), 94.3695, 94.3705)
c.between("lease_liabilities vs NFP table 94.0 (+/-0.5)", b("lease_liabilities"), 93.5, 94.5)
# share capital read independently from the AR2025 balance-sheet text line "- Share Capital 28 226,942 226,820"
sc_line = c.scalar("SELECT text FROM raw_report_lines WHERE doc_id='AR2025' AND page=147 AND text LIKE '- Share Capital%'")
share_capital = int(re.findall(r"[\d,]+", sc_line)[1].replace(",", "")) / 1000  # [note no, 2025, 2024]
c.between("shares_issued x 1.5 = BS share capital (+/-0.01 m)", b("shares_issued") * 1.5,
          share_capital - 0.01, share_capital + 0.01)
c.between("0 <= dilutive_shares <= 1.3 m", b("dilutive_shares"), 0.0, 1.3)
c.between("treasury_shares plausible (0 to 5 m)", b("treasury_shares"), 0.0, 5.0)
c.between("diluted_shares = issued - treasury + dilutive (1e-9)",
          b("diluted_shares") - (b("shares_issued") - b("treasury_shares") + b("dilutive_shares")), -1e-9, 1e-9)
c.between("distributions_2026 = 127.9 + 28.5 (IR_H1_2026)", b("distributions_2026"), 156.39, 156.41)

# ---------------- price and market cap
c.equal("price = 45.32", b("price"), 45.32)
c.equal("price_date (as_of) = 2026-11-06",
        c.scalar("SELECT as_of FROM bridge_inputs WHERE item='price_date'"), "2026-11-06")
c.equal("price_date value = 20261106", b("price_date"), 20261106.0)
c.scalar("SELECT 1")  # connection sanity
c.zero("price_date < 2026-11-09 (intraday bar excluded)",
       "SELECT COUNT(*) FROM bridge_inputs WHERE item IN ('price','price_date') AND as_of >= '2026-11-09'")
raw_close = c.scalar("SELECT close FROM raw_yahoo_prices WHERE ticker='DLG.MI' AND trade_date=DATE '2026-11-06'")
c.between("price equals raw DLG.MI close of 2026-11-06 (rounded to 0.01)", b("price"), raw_close - 0.005,
          raw_close + 0.005)
mcap = b("price") * b("diluted_shares")
c.between("market cap = price x diluted shares between 6.0 and 7.5 bn (EUR m)", mcap, 6000, 7500)
c.between("market_cap row = price x diluted shares (1e-6)", b("market_cap") - mcap, -1e-6, 1e-6)

# ---------------- wacc table
c.equal("wacc has exactly 2 rows", c.scalar("SELECT COUNT(*) FROM wacc"), 2)
c.equal("wacc cases", sorted(r[0] for r in c.con.execute("SELECT \"case\" FROM wacc").fetchall()),
        ["base", "beta_sensitivity"])
COLS = ["rf", "beta_u", "d_e", "tax_marginal", "beta_l", "erp_mature", "country_spread", "ke", "kd_pre", "kd_post",
        "w_e", "w_d", "wacc"]
rows = c.con.execute(f'SELECT "case", {", ".join(COLS)} FROM wacc').fetchall()
W = {r[0]: dict(zip(COLS, r[1:])) for r in rows}
for case, w in W.items():
    c.between(f"[{case}] w_e + w_d = 1", w["w_e"] + w["w_d"] - 1.0, -1e-12, 1e-12)
    c.between(f"[{case}] beta_l = beta_u x (1 + (1 - t) x D/E)",
              w["beta_l"] - w["beta_u"] * (1 + (1 - w["tax_marginal"]) * w["d_e"]), -1e-12, 1e-12)
    c.between(f"[{case}] ke = rf + beta_l x (ERP + country spread)",
              w["ke"] - (w["rf"] + w["beta_l"] * (w["erp_mature"] + w["country_spread"])), -1e-12, 1e-12)
    c.between(f"[{case}] wacc = w_e x ke + w_d x kd_post",
              w["wacc"] - (w["w_e"] * w["ke"] + w["w_d"] * w["kd_post"]), -1e-12, 1e-12)
    c.between(f"[{case}] kd_post = kd_pre x (1 - t)", w["kd_post"] - w["kd_pre"] * (1 - w["tax_marginal"]),
              -1e-12, 1e-12)
    c.between(f"[{case}] d_e = D / market cap (Decision 5A)",
              w["d_e"] - (b("bank_debt") + b("other_financial_payables") + b("lease_liabilities")) / mcap,
              -1e-12, 1e-12)
    c.between(f"[{case}] w_e = E / (D + E)", w["w_e"] - mcap / (mcap + b("bank_debt") + b("other_financial_payables")
                                                              + b("lease_liabilities")), -1e-12, 1e-12)

# ---------------- inputs equal raw cells exactly
rf_raw = c.scalar("SELECT yield_pct FROM raw_ecb_yield_10y WHERE country='IT' AND period='2026-09'") / 100
erp_raw = float(c.scalar("SELECT value FROM raw_damodaran_params WHERE param='mature_market_erp'"))
spr_raw = c.scalar("SELECT rating_based_default_spread FROM raw_damodaran_ctryprem WHERE country='Italy'")
tax_raw = c.scalar("SELECT corporate_tax_rate FROM raw_damodaran_taxrates WHERE country='Italy'")
bu_eu = c.scalar("SELECT unlevered_beta_corrected_for_cash FROM raw_damodaran_beta_europe "
                 "WHERE industry_name='Furn/Home Furnishings'")
bu_gl = c.scalar("SELECT unlevered_beta_corrected_for_cash FROM raw_damodaran_beta_global "
                 "WHERE industry_name='Furn/Home Furnishings'")
c.equal("last ECB IT observation is 2026-09",
        c.scalar("SELECT MAX(period) FROM raw_ecb_yield_10y WHERE country='IT'"), "2026-09")
c.equal("raw rf = 4.362%", round(rf_raw, 6), 0.04362)
c.equal("raw ERP = 4.23%", erp_raw, 0.0423)
c.between("raw Italy default spread = 1.618%", spr_raw, 0.01617, 0.01619)
c.equal("raw Italy tax = 27.81%", tax_raw, 0.2781)
for case in ("base", "beta_sensitivity"):
    w = W[case]
    c.equal(f"[{case}] rf equals raw cell", w["rf"], rf_raw)
    c.equal(f"[{case}] erp_mature equals raw cell", w["erp_mature"], erp_raw)
    c.equal(f"[{case}] country_spread equals raw cell", w["country_spread"], spr_raw)
    c.equal(f"[{case}] tax_marginal equals raw cell", w["tax_marginal"], tax_raw)
c.equal("base beta_u = Europe Furn/Home cash-corrected (0.397...)", W["base"]["beta_u"], bu_eu)
c.equal("sensitivity beta_u = Global Furn/Home cash-corrected (0.938...)", W["beta_sensitivity"]["beta_u"], bu_gl)
c.between("base beta_u about 0.397", W["base"]["beta_u"], 0.3970, 0.3971)
c.between("sensitivity beta_u about 0.938", W["beta_sensitivity"]["beta_u"], 0.9383, 0.9385)

# ---------------- cost of debt
# kd_pre = FY2025 interest on loans and bonds / average gross financial debt excl. leases (YE2024, YE2025)
interest = b("interest_expense_fy2025")
debt25 = b("bank_debt") + b("other_financial_payables")
debt24 = c.scalar("SELECT value FROM wacc_inputs WHERE input='gross_financial_debt_excl_leases_ye2024'")
c.between("kd_pre = interest / average gross financial debt excl. leases",
          W["base"]["kd_pre"] - interest / ((debt25 + debt24) / 2), -1e-12, 1e-12)
c.equal("kd_pre same in both cases", W["base"]["kd_pre"], W["beta_sensitivity"]["kd_pre"])
c.between("kd_pre inside [rf - 1 pp, rf + 3 pp]", W["base"]["kd_pre"], W["base"]["rf"] - 0.01, W["base"]["rf"] + 0.03)
c.between("YE2024 gross financial debt excl. leases = 591.432 (bank 322.234 + other 269.198)", debt24, 591.431, 591.433)

# ---------------- wacc_inputs: sourced
c.zero("wacc_inputs: every row has a source",
       "SELECT COUNT(*) FROM wacc_inputs WHERE source IS NULL OR trim(source) = '' OR value IS NULL OR unit IS NULL")
c.zero("wacc_inputs: input unique",
       "SELECT COUNT(*) FROM (SELECT input FROM wacc_inputs GROUP BY input HAVING COUNT(*) > 1)")

# ---------------- smell tests and hard limits
wb = W["base"]["wacc"]
c.between("HARD: base WACC inside 4%-12%", wb, 0.04, 0.12)
c.between("HARD: g (2.0%) < rf", G, 0.0, W["base"]["rf"] - 1e-12)
c.between("HARD: base WACC - g >= 1.0 pp (needed by the step-4 grid)", wb - G, 0.01, 1.0)
if 0.06 <= wb <= 0.10:
    print(f"INFO  smell test base WACC {wb:.4%} inside 6-10%")
else:
    print(f"SURPRISE  smell test: base WACC {wb:.4%} outside 6-10% (not a FAIL; goes to the final review)")
ws = W["beta_sensitivity"]["wacc"]
print(f"INFO  sensitivity WACC {ws:.4%}, base ke {W['base']['ke']:.4%}, sensitivity ke {W['beta_sensitivity']['ke']:.4%}")
c.between("sensitivity WACC > base WACC (higher beta)", ws - wb, 0.0, 1.0)

c.done()
