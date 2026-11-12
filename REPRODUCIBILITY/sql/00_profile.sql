-- Step 0 (Planner): profile every raw_ table. Rerunnable; results land in profile_ tables.
--   profile_columns : one row per (table, column): type, min, max, approx distinct, null %
--   profile_tables  : one row per table: row count
--   profile_keys    : candidate-key uniqueness (COUNT(*) vs COUNT(DISTINCT key))
--   profile_coverage: presence checks for the specific facts the brief needs (statement anchors per report)

CREATE OR REPLACE TABLE profile_columns AS
          SELECT 'raw_documents'                AS table_name, * FROM (SUMMARIZE raw_documents)
UNION ALL SELECT 'raw_report_lines',               * FROM (SUMMARIZE raw_report_lines)
UNION ALL SELECT 'raw_ecb_yield_10y',              * FROM (SUMMARIZE raw_ecb_yield_10y)
UNION ALL SELECT 'raw_yahoo_prices',               * FROM (SUMMARIZE raw_yahoo_prices)
UNION ALL SELECT 'raw_damodaran_beta_europe',      * FROM (SUMMARIZE raw_damodaran_beta_europe)
UNION ALL SELECT 'raw_damodaran_beta_global',      * FROM (SUMMARIZE raw_damodaran_beta_global)
UNION ALL SELECT 'raw_damodaran_wacc_europe',      * FROM (SUMMARIZE raw_damodaran_wacc_europe)
UNION ALL SELECT 'raw_damodaran_vebitda_europe',   * FROM (SUMMARIZE raw_damodaran_vebitda_europe)
UNION ALL SELECT 'raw_damodaran_vebitda_global',   * FROM (SUMMARIZE raw_damodaran_vebitda_global)
UNION ALL SELECT 'raw_damodaran_pe_europe',        * FROM (SUMMARIZE raw_damodaran_pe_europe)
UNION ALL SELECT 'raw_damodaran_pe_global',        * FROM (SUMMARIZE raw_damodaran_pe_global)
UNION ALL SELECT 'raw_damodaran_ctryprem',         * FROM (SUMMARIZE raw_damodaran_ctryprem)
UNION ALL SELECT 'raw_damodaran_taxrates',         * FROM (SUMMARIZE raw_damodaran_taxrates)
UNION ALL SELECT 'raw_damodaran_params',           * FROM (SUMMARIZE raw_damodaran_params)
UNION ALL SELECT 'raw_damodaran_indname',          * FROM (SUMMARIZE raw_damodaran_indname);

CREATE OR REPLACE TABLE profile_tables AS
          SELECT 'raw_documents' AS table_name, COUNT(*) AS n_rows FROM raw_documents
UNION ALL SELECT 'raw_report_lines',             COUNT(*) FROM raw_report_lines
UNION ALL SELECT 'raw_ecb_yield_10y',            COUNT(*) FROM raw_ecb_yield_10y
UNION ALL SELECT 'raw_yahoo_prices',             COUNT(*) FROM raw_yahoo_prices
UNION ALL SELECT 'raw_damodaran_beta_europe',    COUNT(*) FROM raw_damodaran_beta_europe
UNION ALL SELECT 'raw_damodaran_beta_global',    COUNT(*) FROM raw_damodaran_beta_global
UNION ALL SELECT 'raw_damodaran_wacc_europe',    COUNT(*) FROM raw_damodaran_wacc_europe
UNION ALL SELECT 'raw_damodaran_vebitda_europe', COUNT(*) FROM raw_damodaran_vebitda_europe
UNION ALL SELECT 'raw_damodaran_vebitda_global', COUNT(*) FROM raw_damodaran_vebitda_global
UNION ALL SELECT 'raw_damodaran_pe_europe',      COUNT(*) FROM raw_damodaran_pe_europe
UNION ALL SELECT 'raw_damodaran_pe_global',      COUNT(*) FROM raw_damodaran_pe_global
UNION ALL SELECT 'raw_damodaran_ctryprem',       COUNT(*) FROM raw_damodaran_ctryprem
UNION ALL SELECT 'raw_damodaran_taxrates',       COUNT(*) FROM raw_damodaran_taxrates
UNION ALL SELECT 'raw_damodaran_params',         COUNT(*) FROM raw_damodaran_params
UNION ALL SELECT 'raw_damodaran_indname',        COUNT(*) FROM raw_damodaran_indname;

CREATE OR REPLACE TABLE profile_keys AS
          SELECT 'raw_documents' AS table_name, 'doc_id' AS key_cols, COUNT(*) AS n_rows, COUNT(DISTINCT doc_id) AS n_distinct FROM raw_documents
UNION ALL SELECT 'raw_report_lines', 'doc_id,page,line_no', COUNT(*), COUNT(DISTINCT (doc_id, page, line_no)) FROM raw_report_lines
UNION ALL SELECT 'raw_ecb_yield_10y', 'country,period', COUNT(*), COUNT(DISTINCT (country, period)) FROM raw_ecb_yield_10y
UNION ALL SELECT 'raw_yahoo_prices', 'ticker,trade_date', COUNT(*), COUNT(DISTINCT (ticker, trade_date)) FROM raw_yahoo_prices
UNION ALL SELECT 'raw_damodaran_beta_europe', 'industry_name', COUNT(*), COUNT(DISTINCT industry_name) FROM raw_damodaran_beta_europe
UNION ALL SELECT 'raw_damodaran_beta_global', 'industry_name', COUNT(*), COUNT(DISTINCT industry_name) FROM raw_damodaran_beta_global
UNION ALL SELECT 'raw_damodaran_vebitda_europe', 'industry_name', COUNT(*), COUNT(DISTINCT industry_name) FROM raw_damodaran_vebitda_europe
UNION ALL SELECT 'raw_damodaran_vebitda_global', 'industry_name', COUNT(*), COUNT(DISTINCT industry_name) FROM raw_damodaran_vebitda_global
UNION ALL SELECT 'raw_damodaran_pe_europe', 'industry_name', COUNT(*), COUNT(DISTINCT industry_name) FROM raw_damodaran_pe_europe
UNION ALL SELECT 'raw_damodaran_ctryprem', 'country', COUNT(*), COUNT(DISTINCT country) FROM raw_damodaran_ctryprem
UNION ALL SELECT 'raw_damodaran_taxrates', 'country', COUNT(*), COUNT(DISTINCT country) FROM raw_damodaran_taxrates
UNION ALL SELECT 'raw_damodaran_indname', 'exchange_ticker', COUNT(*), COUNT(DISTINCT exchange_ticker) FROM raw_damodaran_indname;

-- Where the consolidated primary statements sit in each annual report (first page of each anchor).
CREATE OR REPLACE TABLE profile_coverage AS
WITH anchors(anchor, pattern) AS (
    VALUES ('IS_total_revenues', 'Total consolidated revenues %'),
           ('IS_EBIT',           'EBIT %'),
           ('IS_taxes',          'Taxes 10 %'),
           ('BS_total_assets',   'TOTAL ASSETS %'),
           ('BS_trade_payables', 'TRADE PAYABLES %'),
           ('CF_closing_cash',   'Closing cash and cash equivalents%'),
           ('CF_capex_ppe',      'Investments in property, plant and equipment%'),
           ('EPS_diluted',       '- diluted%'),
           ('share_capital_shares', '%ordinary shares with a par value%')
)
SELECT d.doc_id, a.anchor,
       MIN(l.page)  AS first_page,
       COUNT(l.text) AS n_hits,
       arg_min(l.text, l.page * 10000 + l.line_no) AS first_text
FROM raw_documents d CROSS JOIN anchors a
LEFT JOIN raw_report_lines l ON l.doc_id = d.doc_id AND l.text ILIKE a.pattern
WHERE d.doc_id LIKE 'AR%' OR d.doc_id = 'IR_H1_2026'
GROUP BY ALL
ORDER BY d.doc_id, a.anchor;
