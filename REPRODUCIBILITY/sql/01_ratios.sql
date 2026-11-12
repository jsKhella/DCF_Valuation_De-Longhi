-- Step 1b: historical ratios FY2021-FY2025, one row per fiscal year.
--
-- Purpose : turn the condensed statements into the drivers the forecast needs, plus a historical FCFF.
-- Inputs  : hist_statements, hist_other_inputs (FY2020 revenue, right-of-use additions)  [py/01_statements.py]
-- Output  : hist_ratios (fy, revenue, growth, ebit_reported, nonrec, adj_ebit, adj_ebit_margin, da, da_pct,
--           capex_intangible, capex_ppe, capex_rou, capex_total, capex_pct, capex_excl_rou_pct,
--           trade_receivables, inventories, trade_payables, nwc, nwc_pct, delta_nwc, pbt, taxes, eff_tax_rate,
--           tax_included, fcff_hist)
-- Brief definitions implemented:
--   Adjusted EBIT     = reported EBIT minus the IS "of which non-recurring" amount (expense negative, so adding back).
--   Net working capital = trade receivables + inventories - trade payables (year-end BS); % of revenue.
--   Tax rate (historical) = income tax / pre-tax profit; years with rate < 0 or > 40% get tax_included = false.
--   FCFF (historical) = adj_ebit x (1 - eff_tax_rate) + D&A - capex - increase in NWC.
--     D&A = IS "Amortization" (includes right-of-use depreciation: IFRS 16 leases treated as debt).
--     capex = CF investments in intangibles + CF investments in PP&E + note-15 right-of-use additions (Decision 9).
-- Sign conventions: hist_statements holds values as printed (costs, taxes, capex negative). In this table da, capex_*
-- and taxes are positive amounts (expense / outflow). capex_pct = capex_total / revenue (incl. ROU);
-- capex_excl_rou_pct = (capex_intangible + capex_ppe) / revenue.

CREATE OR REPLACE TABLE hist_ratios AS
WITH s AS (
    SELECT fy,
           max(value_eur_m) FILTER (WHERE statement = 'IS' AND line_item = 'total consolidated revenues')  AS revenue,
           max(value_eur_m) FILTER (WHERE statement = 'IS' AND line_item = 'ebit')                         AS ebit_reported,
           max(value_eur_m) FILTER (WHERE statement = 'IS' AND line_item = 'ebit of which non-recurring')  AS nonrec,
           max(value_eur_m) FILTER (WHERE statement = 'IS' AND line_item = 'amortization')                 AS amortization,
           max(value_eur_m) FILTER (WHERE statement = 'IS' AND line_item = 'profit before taxes')          AS pbt,
           max(value_eur_m) FILTER (WHERE statement = 'IS' AND line_item = 'taxes')                        AS taxes_printed,
           max(value_eur_m) FILTER (WHERE statement = 'CF' AND line_item = 'investments in intangible assets') AS inv_intangible,
           max(value_eur_m) FILTER (WHERE statement = 'CF' AND line_item = 'investments in property, plant and equipment') AS inv_ppe,
           max(value_eur_m) FILTER (WHERE statement = 'BS' AND line_item = 'trade receivables')            AS trade_receivables,
           max(value_eur_m) FILTER (WHERE statement = 'BS' AND line_item = 'inventories')                  AS inventories,
           max(value_eur_m) FILTER (WHERE statement = 'BS' AND line_item = 'trade payables')               AS trade_payables
    FROM hist_statements
    GROUP BY fy
), nwc AS (
    SELECT fy, trade_receivables + inventories - trade_payables AS nwc FROM s
), base AS (
    SELECT s.fy,
           s.revenue,
           s.revenue / coalesce(lag(s.revenue) OVER (ORDER BY s.fy),
                                (SELECT value_eur_m FROM hist_other_inputs
                                 WHERE fy = 2020 AND item = 'total consolidated revenues')) - 1   AS growth,
           s.ebit_reported,
           s.nonrec,
           s.ebit_reported - s.nonrec                                                             AS adj_ebit,
           -s.amortization                                                                        AS da,
           -s.inv_intangible                                                                      AS capex_intangible,
           -s.inv_ppe                                                                             AS capex_ppe,
           o.value_eur_m                                                                          AS capex_rou,
           s.trade_receivables, s.inventories, s.trade_payables,
           n.nwc,
           n.nwc - p.nwc                                                                          AS delta_nwc,
           s.pbt,
           -s.taxes_printed                                                                       AS taxes
    FROM s
    JOIN nwc n ON n.fy = s.fy
    JOIN nwc p ON p.fy = s.fy - 1
    JOIN hist_other_inputs o ON o.fy = s.fy AND o.item = 'right-of-use additions'
    WHERE s.fy BETWEEN 2021 AND 2025
), r AS (
    SELECT *,
           adj_ebit / revenue                                    AS adj_ebit_margin,
           da / revenue                                          AS da_pct,
           capex_intangible + capex_ppe + capex_rou              AS capex_total,
           nwc / revenue                                         AS nwc_pct,
           taxes / pbt                                           AS eff_tax_rate
    FROM base
)
SELECT fy, revenue, growth, ebit_reported, nonrec, adj_ebit, adj_ebit_margin, da, da_pct,
       capex_intangible, capex_ppe, capex_rou, capex_total,
       capex_total / revenue                                     AS capex_pct,
       (capex_intangible + capex_ppe) / revenue                  AS capex_excl_rou_pct,
       trade_receivables, inventories, trade_payables, nwc, nwc_pct, delta_nwc,
       pbt, taxes, eff_tax_rate,
       (eff_tax_rate >= 0 AND eff_tax_rate <= 0.40)              AS tax_included,
       adj_ebit * (1 - eff_tax_rate) + da - capex_total - delta_nwc AS fcff_hist
FROM r
ORDER BY fy;
