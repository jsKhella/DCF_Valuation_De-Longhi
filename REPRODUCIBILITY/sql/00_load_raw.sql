-- Step 0 (Planner): load the tabular raw sources (CSV / JSON) into raw_ tables.
-- Paths are relative to the project root (run.py chdirs there).
-- PDFs and Damodaran .xls files are loaded by py/00_load_raw.py (DuckDB cannot read them natively).

-- ECB "long-term interest rate for convergence purposes" (10-year government bond yield, monthly average, % p.a.)
CREATE OR REPLACE TABLE raw_ecb_yield_10y AS
SELECT REF_AREA                       AS country,
       TIME_PERIOD                    AS period,         -- 'YYYY-MM'
       CAST(OBS_VALUE AS DOUBLE)      AS yield_pct,
       OBS_STATUS                     AS obs_status,
       KEY                            AS series_key,
       filename                       AS source_file
FROM read_csv(['data/raw/market/ecb_irs_italy_10y_monthly.csv',
               'data/raw/market/ecb_irs_germany_10y_monthly.csv'],
              header = true, all_varchar = true, filename = true);

-- Yahoo Finance v8 chart JSON (5y daily). One row per ticker per trading day.
-- close = unadjusted close; adjclose = dividend/split adjusted close. Timestamps are exchange-open UTC epoch seconds.
CREATE OR REPLACE TABLE raw_yahoo_prices AS
WITH j AS (
    SELECT filename, unnest(chart.result) AS r
    FROM read_json('data/raw/market/yahoo_chart_*.json', filename = true, maximum_object_size = 50000000)
), z AS (
    SELECT filename,
           r.meta.symbol                          AS ticker,
           r.meta.currency                        AS currency,
           r.meta.exchangeTimezoneName            AS exchange_tz,
           r.timestamp                            AS ts,
           r.indicators.quote[1]."close"          AS close,
           r.indicators.quote[1].volume           AS volume,
           r.indicators.adjclose[1].adjclose      AS adjclose
    FROM j
)
SELECT ticker, currency,
       CAST(timezone(exchange_tz, to_timestamp(ts[i])) AS DATE) AS trade_date,
       CAST(close[i] AS DOUBLE)    AS close,
       CAST(adjclose[i] AS DOUBLE) AS adjclose,
       CAST(volume[i] AS BIGINT)   AS volume,
       filename                    AS source_file
FROM z, range(1, len(ts) + 1) t(i);
