"""Step 1a: parse the condensed consolidated statements FY2021-FY2025 from the annual-report text lines.

Purpose
    Build the condensed income statement (IS), balance sheet (BS, YE2020-YE2025) and cash-flow lines (CF) that the
    FCFF and the equity bridge need, plus the totals used for tie-out checks; the non-recurring breakdown by IS line;
    the 3-5 largest one-off adjustments; right-of-use additions (Decision 9); and a restatement log.

Inputs (DuckDB, built by step 0)
    raw_report_lines (doc_id, page, line_no, text), docs AR2021-AR2025 only.

Outputs (DuckDB tables, all CREATE OR REPLACE, no timestamps)
    hist_statements    (fy, statement, line_item, value_eur_m, doc_id, pdf_page)
    hist_other_inputs  (fy, item, value_eur_m, doc_id, pdf_page, note)   FY2020 revenue, right-of-use additions
    hist_nonrec_lines  (fy, is_line, amount_eur_m, doc_id, pdf_page)     IS "of which non-recurring" by line, as printed
    hist_adjustments   (fy, item, amount_eur_m, doc_id, pdf_page, description, note_doc_id, note_page)
    hist_restatements  (fy, statement, line_item, value_used, doc_used, page_used, value_original, doc_original,
                        page_original, diff)   every condensed line whose original-report value differs by > 0.1 m

Brief definitions implemented
    "Fiscal years" (FY2021-FY2025), "Adjusted EBIT" (non-recurring items, listed with source page and amount),
    inputs of "FCFF", "Net working capital" and "Tax rate". Plan step 1 rule: each year from the latest report that
    presents it (FY t from AR(t+1) comparative column, FY2024-25 from AR2025; YE2020 BS from AR2021).

Conventions
    Values are stored as printed, in EUR m = EUR thousand / 1000. Parenthesised numbers are negative; '-' is zero.
    So costs, taxes and capex are negative in hist_statements. "of which non-recurring" keeps the IS sign
    (expense negative); hist_adjustments.amount_eur_m is the add-back, i.e. -(non-recurring), so that
    adjusted EBIT = EBIT + sum(adjustments).
    pdf_page is the 1-based PDF page index (not the printed page number).
"""
import re
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "curiosity.duckdb"

YEARS = [2021, 2022, 2023, 2024, 2025]
REPORT = {y: f"AR{y}" for y in YEARS}            # report whose current column is fiscal year y
# PDF page of each primary statement in each annual report (IS; BS assets; BS equity & liabilities; CF).
# Each page is validated below by finding every expected label on it.
PAGES = {
    "AR2021": {"IS": 75, "BSA": 77, "BSL": 78, "CF": 79},
    "AR2022": {"IS": 83, "BSA": 85, "BSL": 86, "CF": 87},
    "AR2023": {"IS": 90, "BSA": 92, "BSL": 93, "CF": 94},
    "AR2024": {"IS": 137, "BSA": 139, "BSL": 140, "CF": 141},
    "AR2025": {"IS": 144, "BSA": 146, "BSL": 147, "CF": 148},
}
RESTATEMENT_THRESHOLD = 0.1   # EUR m, plan step 1 / feasibility: log differences larger than 0.1 m
N_ITEMISED = 5                # plan: itemise the 3-5 largest non-recurring items (5 = upper end)
RESIDUAL = "other non-recurring (not itemised)"

# (statement, line_item, page key, label (case-insensitive, literal), has note-reference column, n values)
# n values: 2 = [current, prior]; 4 = [current, current non-recurring, prior, prior non-recurring] (EBIT only)
LINES = [
    ("IS", "total consolidated revenues", "IS", "Total consolidated revenues", False, 2),
    ("IS", "amortization", "IS", "Amortization", True, 2),
    ("IS", "ebit", "IS", "EBIT", False, 4),
    ("IS", "net financial income (expenses)", "IS", "Net financial income (expenses)", True, 2),
    ("IS", "profit before taxes", "IS", "Profit (loss) before taxes", False, 2),
    ("IS", "taxes", "IS", "Taxes", True, 2),
    ("IS", "consolidated profit", "IS", "Consolidated profit (loss)", False, 2),
    ("IS", "profit pertaining to minority interests", "IS", "Profit (loss) pertaining to minority", True, 2),
    ("BS", "trade receivables", "BSA", "Trade receivables", True, 2),
    ("BS", "inventories", "BSA", "Inventories", True, 2),
    ("BS", "cash and cash equivalents", "BSA", "Cash and cash equivalents", True, 2),
    ("BS", "total assets", "BSA", "Total assets", False, 2),
    ("BS", "trade payables", "BSL", "Trade payables", True, 2),
    ("BS", "bank loans and borrowings (long-term portion)", "BSL", "- Banks loans and borrowings (long-term portion)", True, 2),
    ("BS", "bank loans and borrowings (short-term portion)", "BSL", "- Banks loans and borrowings (short-term portion)", True, 2),
    ("BS", "other financial payables (long-term portion)", "BSL", "- Other financial payables (long-term portion)", True, 2),
    ("BS", "other financial payables (short-term portion)", "BSL", "- Other financial payables (short-term portion)", True, 2),
    ("BS", "lease liabilities (long-term portion)", "BSL", "- Lease liabilities (long-term portion)", True, 2),
    ("BS", "lease liabilities (short-term portion)", "BSL", "- Lease liabilities (short-term portion)", True, 2),
    ("BS", "minority interest", "BSL", "Minority interest", True, 2),
    ("BS", "total net equity and liabilities", "BSL", "Total net equity and liabilities", False, 2),
    ("CF", "investments in intangible assets", "CF", "Investments in intangible assets", False, 2),
    ("CF", "investments in property, plant and equipment", "CF", "Investments in property, plant and equipment", False, 2),
    ("CF", "cash flow for the period", "CF", "Cash flow for the period", False, 2),
    ("CF", "opening cash and cash equivalents", "CF", "Opening cash and cash equivalents", True, 2),
    ("CF", "translation difference on cash", "CF", "Translation difference effect on cash and cash equivalents", False, 2),
    ("CF", "closing cash and cash equivalents", "CF", "Closing cash and cash equivalents", True, 2),
]
# Optional line: AR2021-AR2023 do not present a separate translation line below "Cash flow for the period"; their FX
# effect on cash sits inside the period cash flow (financing section), so the separate reconciling item is zero.
OPTIONAL = {"translation difference on cash"}

# IS cost lines that carry an "of which non-recurring" column (Materials consumed is a subtotal and is excluded).
NONREC_LINES = [
    "Raw and ancillary materials, consumables and goods",
    "Change in inventories of finished products and work in progress",
    "Change in inventories of raw and ancillary materials, consumables and goods",
    "Payroll costs",
    "Services and other operating expenses",
    "Provisions",
    "Amortization",
]
# Plain-language description of the itemised adjustments, read from the notes (AR note 8 and notes 4-6).
# Keyed by (fy, IS line). The script fails if a selected item has no description.
DESCRIPTIONS = {
    (2021, "Change in inventories of finished products and work in progress"):
        "inventory fair-value step-up released after the Capital Brands and Eversys business combinations, and "
        "valuations of current assets for the geopolitical situation (note 8)",
    (2021, "Payroll costs"):
        "special bonus paid to employees and business partners for the health-crisis period (note 8)",
    (2021, "Provisions"):
        "non-recurring provisions: Ukraine-related asset valuations and purchase-price-allocation effects (notes 6, 8)",
    (2022, "Provisions"):
        "income from the revised valuation of assets in Ukraine (receivables collected) and purchase-price-allocation "
        "effects of Capital Brands and Eversys (note 6)",
    (2025, "Payroll costs"):
        "corporate reorganization (note 4)",
    (2023, "Services and other operating expenses"):
        "services connected to the La Marzocco/Eversys business combination and reorganization (notes 5, 8)",
    (2025, "Provisions"):
        "accounting effects of allocations for past business combinations (note 6)",
}

VAL_RE = re.compile(r"^(\(\d{1,3}(,\d{3})*\)|\d{1,3}(,\d{3})*|-)$")
NOTE_RE = re.compile(r"^\d+(-\d+)*$")


def to_num(tok: str) -> float:
    """Printed EUR thousand token -> EUR thousand (float). '(x)' negative, '-' zero."""
    if tok == "-":
        return 0.0
    neg = tok.startswith("(")
    n = float(tok.strip("()").replace(",", ""))
    return -n if neg else n


def page_lines(con, doc, page):
    return con.execute("SELECT line_no, text FROM raw_report_lines WHERE doc_id=? AND page=? ORDER BY line_no",
                       [doc, page]).fetchall()


def find_values(lines, label, has_note, doc, page, required=True):
    """Return the list of numeric values (EUR thousand) printed after `label` on the page.
    Lines must be exactly `label` + optional note ref + numeric tokens. Repeated lines must agree."""
    found = []
    lab = label.lower()
    for _, text in lines:
        t = text.strip()
        if not t.lower().startswith(lab + " "):
            continue
        toks = t[len(label):].split()
        if toks and re.match(r"^\([A-E+]+\)$", toks[0]):   # e.g. "Cash flow for the period (A+B+C+D+E)"
            toks = toks[1:]
        if has_note and toks and NOTE_RE.match(toks[0]) and len(toks) > 1 and "," not in toks[0]:
            # note reference present only if the remaining tokens are all values
            if all(VAL_RE.match(x) for x in toks[1:]):
                toks = toks[1:]
        if not toks or not all(VAL_RE.match(x) for x in toks):
            continue
        found.append([to_num(x) for x in toks])
    if not found:
        if required:
            raise ValueError(f"label '{label}' not found on {doc} p.{page}")
        return None
    if any(f != found[0] for f in found[1:]):
        raise ValueError(f"label '{label}' appears with different values on {doc} p.{page}: {found}")
    return found[0]


def parse_report(con, doc):
    """Parse every condensed line of one report: {line_item: dict(cur, prior, cur_nr, prior_nr, page)}."""
    out = {}
    for st, item, pkey, label, has_note, n in LINES:
        page = PAGES[doc][pkey]
        vals = find_values(page_lines(con, doc, page), label, has_note, doc, page, required=item not in OPTIONAL)
        if vals is None:
            out[item] = None
            continue
        if len(vals) != n:
            raise ValueError(f"{doc} p.{page} '{label}': expected {n} values, got {vals}")
        if n == 2:
            out[item] = {"cur": vals[0], "prior": vals[1], "page": page}
        else:
            out[item] = {"cur": vals[0], "cur_nr": vals[1], "prior": vals[2], "prior_nr": vals[3], "page": page}
    return out


def parse_nonrec(con, doc, prev_doc):
    """IS cost lines of `doc` split into gross and non-recurring for current and prior year.
    With 3 values the layout is either [cur, cur_nr, prior] or [cur, prior, prior_nr]; it is resolved by matching the
    prior gross value against the previous report's current gross value of the same line."""
    page = PAGES[doc]["IS"]
    lines = page_lines(con, doc, page)
    prev_lines = page_lines(con, prev_doc, PAGES[prev_doc]["IS"])
    res = {}
    for label in NONREC_LINES:
        v = find_values(lines, label, True, doc, page)
        if len(v) == 2:
            cur_nr, prior_nr = 0.0, 0.0
        elif len(v) == 4:
            cur_nr, prior_nr = v[1], v[3]
        elif len(v) == 3:
            prev_cur = find_values(prev_lines, label, True, prev_doc, PAGES[prev_doc]["IS"])[0]
            if v[1] == prev_cur and v[2] != prev_cur:
                cur_nr, prior_nr = 0.0, v[2]
            elif v[2] == prev_cur and v[1] != prev_cur:
                cur_nr, prior_nr = v[1], 0.0
            else:
                raise ValueError(f"cannot resolve 3-value layout for '{label}' on {doc} p.{page}: {v}, prev {prev_cur}")
        else:
            raise ValueError(f"unexpected values for '{label}' on {doc} p.{page}: {v}")
        res[label] = {"cur_nr": cur_nr, "prior_nr": prior_nr, "page": page}
    return res


def rou_additions(con, fy):
    """Right-of-use 'Additions' (Total column = last value) from note 15 of the year's own report."""
    doc = REPORT[fy]
    hit = con.execute("SELECT page, line_no FROM raw_report_lines WHERE doc_id=? AND text ILIKE ? ORDER BY page, line_no",
                      [doc, f"Movements in the leased right of use assets in {fy}%"]).fetchall()
    if len(hit) != 1:
        raise ValueError(f"{doc}: expected one note-15 movement table, found {hit}")
    page, ln = hit[0]
    rows = con.execute("SELECT text FROM raw_report_lines WHERE doc_id=? AND page=? AND line_no BETWEEN ? AND ? "
                       "AND text LIKE 'Additions %' ORDER BY line_no", [doc, page, ln, ln + 20]).fetchall()
    if len(rows) != 1:
        raise ValueError(f"{doc} p.{page}: expected one 'Additions' row, found {rows}")
    toks = rows[0][0].split()[1:]
    assert toks and all(VAL_RE.match(x) for x in toks), rows
    return to_num(toks[-1]), doc, page


def note_location(con, fy, amount_thousand):
    """First note line in the year's own report quoting the amount ('x,xxx thousand') near a 'non-recurring' mention."""
    doc = REPORT[fy]
    s = f"{abs(amount_thousand):,.0f} thousand"
    hits = con.execute("SELECT page, line_no FROM raw_report_lines WHERE doc_id=? AND page > ? AND page < ? "
                       "AND text LIKE ? ORDER BY page, line_no",
                       [doc, PAGES[doc]["IS"], PAGES[doc]["IS"] + 40, f"%{s}%"]).fetchall()
    for page, ln in hits:
        near = con.execute("SELECT COUNT(*) FROM raw_report_lines WHERE doc_id=? AND page=? AND line_no BETWEEN ? AND ? "
                           "AND text ILIKE '%non-recurring%'", [doc, page, ln - 2, ln + 2]).fetchone()[0]
        if near:
            return doc, page
    raise ValueError(f"no note line quoting '{s}' near 'non-recurring' in {doc}")


def main():
    con = duckdb.connect(str(DB))
    parsed = {REPORT[y]: parse_report(con, REPORT[y]) for y in YEARS}

    # ---- Source rule: FY t from AR(t+1) prior column (t <= 2024); FY2025 from AR2025 current column.
    def source(fy):
        return (REPORT[fy + 1], "prior") if fy < 2025 else (REPORT[2025], "cur")

    rows, restated = [], []
    for st, item, pkey, label, has_note, n in LINES:
        fys = [2020] + YEARS if st == "BS" else YEARS
        for fy in fys:
            if fy == 2020:
                doc, col = "AR2021", "prior"
            else:
                doc, col = source(fy)
            rec = parsed[doc][item]
            val = 0.0 if rec is None else rec[col]
            page = PAGES[doc][pkey]
            rows.append((fy, st, item, val / 1000, doc, page))
            if n == 4:
                nr = 0.0 if rec is None else rec[col + "_nr"]
                rows.append((fy, st, "ebit of which non-recurring", nr / 1000, doc, page))
            # restatement log: original report (current column of AR fy) vs value used
            if 2021 <= fy < 2025:
                odoc = REPORT[fy]
                orec = parsed[odoc][item]
                oval = 0.0 if orec is None else orec["cur"]
                pairs = [(item, val, oval)]
                if n == 4:
                    pairs.append(("ebit of which non-recurring", rec[col + "_nr"], orec["cur_nr"]))
                for it, used, orig in pairs:
                    if abs(used - orig) / 1000 > RESTATEMENT_THRESHOLD:
                        restated.append((fy, st, it, used / 1000, doc, page, orig / 1000, odoc,
                                         PAGES[odoc][pkey], (used - orig) / 1000))

    # Years with no separate translation line: the period cash flow must already reconcile opening to closing.
    for fy in YEARS:
        doc, col = source(fy)
        if parsed[doc]["translation difference on cash"] is None:
            p = parsed[doc]
            assert p["opening cash and cash equivalents"][col] + p["cash flow for the period"][col] == \
                p["closing cash and cash equivalents"][col], f"FY{fy}: FX not inside period cash flow?"

    hs = pd.DataFrame(rows, columns=["fy", "statement", "line_item", "value_eur_m", "doc_id", "pdf_page"])
    con.execute("CREATE OR REPLACE TABLE hist_statements AS SELECT * FROM hs ORDER BY statement, line_item, fy")

    # ---- Other inputs: FY2020 revenue (growth base) and right-of-use additions (Decision 9)
    other = [(2020, "total consolidated revenues", parsed["AR2021"]["total consolidated revenues"]["prior"] / 1000,
              "AR2021", PAGES["AR2021"]["IS"], "comparative column of AR2021 income statement; growth base for FY2021")]
    for fy in YEARS:
        val, doc, page = rou_additions(con, fy)
        other.append((fy, "right-of-use additions", val / 1000, doc, page,
                      "note 15 Leases, 'Additions' row, Total column; counted as capex per plan Decision 9"))
    oi = pd.DataFrame(other, columns=["fy", "item", "value_eur_m", "doc_id", "pdf_page", "note"])
    con.execute("CREATE OR REPLACE TABLE hist_other_inputs AS SELECT * FROM oi ORDER BY item, fy")

    # ---- Non-recurring breakdown by IS line (latest presenter of each year)
    nr_rows = []
    nr_by_report = {}
    for fy in YEARS:
        doc, col = source(fy)
        if doc not in nr_by_report:
            prev = f"AR{int(doc[2:]) - 1}"
            nr_by_report[doc] = parse_nonrec(con, doc, prev)
        for label, rec in nr_by_report[doc].items():
            amt = rec[col + "_nr"]
            if amt != 0:
                nr_rows.append((fy, label, amt / 1000, doc, rec["page"]))
        total = sum(r[2] for r in nr_rows if r[0] == fy)
        ebit_nr = hs.query("fy == @fy and line_item == 'ebit of which non-recurring'")["value_eur_m"].iloc[0]
        assert abs(total - ebit_nr) < 1e-9, f"FY{fy}: non-recurring lines {total} != EBIT non-recurring {ebit_nr}"
    nr = pd.DataFrame(nr_rows, columns=["fy", "is_line", "amount_eur_m", "doc_id", "pdf_page"])
    con.execute("CREATE OR REPLACE TABLE hist_nonrec_lines AS SELECT * FROM nr ORDER BY fy, is_line")

    # ---- Adjustments: the N largest items by absolute amount across FY2021-25, plus one residual row per year
    ranked = nr.assign(absamt=nr["amount_eur_m"].abs()).sort_values(["absamt", "fy", "is_line"],
                                                                     ascending=[False, True, True])
    top = ranked.head(N_ITEMISED)
    adj = []
    for _, r in top.iterrows():
        key = (int(r["fy"]), r["is_line"])
        if key not in DESCRIPTIONS:
            raise ValueError(f"no description for selected item {key}")
        ndoc, npage = note_location(con, key[0], r["amount_eur_m"] * 1000)
        adj.append((key[0], f"FY{key[0]} {r['is_line'].lower()} (non-recurring)", -r["amount_eur_m"],
                    r["doc_id"], int(r["pdf_page"]), DESCRIPTIONS[key], ndoc, npage))
    for fy in YEARS:
        ebit_row = hs.query("fy == @fy and line_item == 'ebit of which non-recurring'").iloc[0]
        itemised = sum(a[2] for a in adj if a[0] == fy)
        adj.append((fy, RESIDUAL, -ebit_row["value_eur_m"] - itemised, ebit_row["doc_id"], int(ebit_row["pdf_page"]),
                    "IS 'of which non-recurring' total for the year less the itemised items above", ebit_row["doc_id"],
                    int(ebit_row["pdf_page"])))
    ad = pd.DataFrame(adj, columns=["fy", "item", "amount_eur_m", "doc_id", "pdf_page", "description",
                                    "note_doc_id", "note_page"])
    con.execute("CREATE OR REPLACE TABLE hist_adjustments AS SELECT * FROM ad ORDER BY fy, item")

    rs = pd.DataFrame(restated, columns=["fy", "statement", "line_item", "value_used", "doc_used", "page_used",
                                         "value_original", "doc_original", "page_original", "diff"])
    con.execute("CREATE OR REPLACE TABLE hist_restatements AS SELECT * FROM rs ORDER BY fy, statement, line_item")

    for t in ["hist_statements", "hist_other_inputs", "hist_nonrec_lines", "hist_adjustments", "hist_restatements"]:
        print(f"  {t}: {con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]} rows")
    con.close()


if __name__ == "__main__":
    main()
