-- Star schema for the online retailer (DuckDB). Run from the project root.
CREATE OR REPLACE TABLE staging AS
SELECT CAST("Invoice" AS VARCHAR) AS invoice, CAST("StockCode" AS VARCHAR) AS stock_code,
       upper(trim("Description")) AS description, "Quantity" AS qty,
       CAST("InvoiceDate" AS TIMESTAMP) AS ts, "Price" AS unit_price,
       CAST("Customer ID" AS INTEGER) AS customer_id, "Country" AS country
FROM read_csv_auto('data/retail.csv');

CREATE OR REPLACE TABLE dim_product AS
SELECT stock_code, arg_max(description, cnt) AS description          -- most common label
FROM (SELECT stock_code, description, count(*) cnt FROM staging
      WHERE description IS NOT NULL GROUP BY ALL)
GROUP BY stock_code;

CREATE OR REPLACE TABLE dim_customer AS
SELECT customer_id, arg_max(country, ts) AS country, min(ts) AS first_purchase
FROM staging WHERE customer_id IS NOT NULL GROUP BY customer_id;

CREATE OR REPLACE TABLE dim_date AS
SELECT DISTINCT CAST(ts AS DATE) AS date_key, year(ts) AS year, month(ts) AS month,
       quarter(ts) AS quarter, dayname(ts) AS weekday, date_trunc('week', ts)::DATE AS week_start
FROM staging;

CREATE OR REPLACE TABLE fact_sales AS
SELECT invoice, s.stock_code, customer_id, CAST(ts AS DATE) AS date_key, qty, unit_price,
       qty * unit_price AS revenue,
       invoice LIKE 'C%' AS is_cancellation
FROM staging s
WHERE unit_price > 0 AND regexp_matches(s.stock_code, '^[0-9]{5}');
