-- Q1: row counts per table
SELECT 'fact_sales' AS tbl, count(*) AS n FROM fact_sales UNION ALL
SELECT 'dim_product', count(*) FROM dim_product UNION ALL
SELECT 'dim_customer', count(*) FROM dim_customer UNION ALL
SELECT 'dim_date', count(*) FROM dim_date;

-- Q2: gross vs cancelled revenue by year
SELECT d.year, round(sum(revenue) FILTER (WHERE NOT is_cancellation)) AS gross,
       round(-sum(revenue) FILTER (WHERE is_cancellation)) AS cancelled,
       round(100 * -sum(revenue) FILTER (WHERE is_cancellation) /
             sum(revenue) FILTER (WHERE NOT is_cancellation), 2) AS cancel_pct
FROM fact_sales f JOIN dim_date d USING (date_key) GROUP BY d.year ORDER BY d.year;

-- Q3: top countries by net revenue, with running share (Pareto)
SELECT country, round(net) AS net_revenue,
       round(100 * sum(net) OVER (ORDER BY net DESC) / sum(net) OVER (), 1) AS cumulative_pct
FROM (SELECT c.country, sum(f.revenue) AS net FROM fact_sales f
      JOIN dim_customer c USING (customer_id) GROUP BY c.country)
ORDER BY net DESC LIMIT 8;

-- Q4: customer cohorts — revenue by first-purchase quarter
SELECT strftime(date_trunc('quarter', first_purchase), '%Y-Q') || quarter(first_purchase) AS cohort,
       count(DISTINCT c.customer_id) AS customers, round(sum(f.revenue)) AS lifetime_revenue,
       round(sum(f.revenue) / count(DISTINCT c.customer_id)) AS revenue_per_customer
FROM dim_customer c JOIN fact_sales f USING (customer_id)
GROUP BY 1 ORDER BY 1;

-- Q5: weekly net revenue + 4-week rolling average (series used for forecasting)
CREATE OR REPLACE TABLE weekly AS
SELECT d.week_start, sum(f.revenue) AS revenue
FROM fact_sales f JOIN dim_date d USING (date_key)
GROUP BY d.week_start;
SELECT week_start, round(revenue) AS revenue,
       round(avg(revenue) OVER (ORDER BY week_start ROWS 3 PRECEDING)) AS rolling_4wk
FROM weekly ORDER BY week_start DESC LIMIT 6;
