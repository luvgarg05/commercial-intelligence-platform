-- Business analysis queries. Each block starts with "-- name: <name>" so
-- src/analysis.py can run them one by one and save each result to outputs/<name>.csv.

-- name: kpi_summary
-- Headline KPIs for the whole period.
WITH orders AS (
    SELECT order_id, customer_unique_id, SUM(revenue) AS order_value, MAX(is_late) AS is_late
    FROM fact_sales
    GROUP BY order_id, customer_unique_id
),
cust AS (
    SELECT customer_unique_id, COUNT(*) AS n_orders FROM orders GROUP BY customer_unique_id
)
SELECT
    ROUND(SUM(o.order_value), 0)                                   AS total_revenue_brl,
    COUNT(*)                                                       AS orders,
    (SELECT COUNT(*) FROM cust)                                    AS customers,
    ROUND(AVG(o.order_value), 2)                                   AS avg_order_value_brl,
    ROUND(100.0 * (SELECT SUM(n_orders > 1) FROM cust) / (SELECT COUNT(*) FROM cust), 2) AS repeat_customer_pct,
    ROUND(100.0 * AVG(o.is_late), 2)                               AS late_delivery_pct,
    (SELECT ROUND(AVG(r.review_score), 2) FROM order_review r
       WHERE r.order_id IN (SELECT order_id FROM orders))          AS avg_review_score
FROM orders o;

-- name: monthly_revenue
-- Revenue, orders and month-over-month growth (window function LAG).
WITH m AS (
    SELECT order_month,
           SUM(revenue)              AS revenue,
           COUNT(DISTINCT order_id)  AS orders,
           COUNT(DISTINCT customer_unique_id) AS customers
    FROM fact_sales
    GROUP BY order_month
)
SELECT order_month,
       ROUND(revenue, 0) AS revenue_brl,
       orders,
       customers,
       ROUND(revenue / orders, 2) AS avg_order_value_brl,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY order_month))
             / LAG(revenue) OVER (ORDER BY order_month), 1) AS mom_growth_pct
FROM m
ORDER BY order_month;

-- name: revenue_by_state
-- Which regions drive revenue: share and cumulative share (Pareto view).
WITH s AS (
    SELECT state, SUM(revenue) AS revenue, COUNT(DISTINCT order_id) AS orders
    FROM fact_sales GROUP BY state
)
SELECT state,
       ROUND(revenue, 0) AS revenue_brl,
       orders,
       ROUND(100.0 * revenue / SUM(revenue) OVER (), 2) AS revenue_share_pct,
       ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC) / SUM(revenue) OVER (), 2) AS cumulative_share_pct
FROM s
ORDER BY revenue DESC;

-- name: category_performance
-- Revenue by category, share, and growth from H1 2017 to H1 2018 (Jan-Jun each year).
WITH c AS (
    SELECT category,
           SUM(revenue) AS revenue,
           SUM(CASE WHEN order_month BETWEEN '2017-01' AND '2017-06' THEN revenue ELSE 0 END) AS h1_2017,
           SUM(CASE WHEN order_month BETWEEN '2018-01' AND '2018-06' THEN revenue ELSE 0 END) AS h1_2018,
           COUNT(DISTINCT order_id) AS orders
    FROM fact_sales GROUP BY category
)
SELECT category,
       ROUND(revenue, 0) AS revenue_brl,
       orders,
       ROUND(100.0 * revenue / SUM(revenue) OVER (), 2) AS revenue_share_pct,
       ROUND(h1_2017, 0) AS h1_2017_brl,
       ROUND(h1_2018, 0) AS h1_2018_brl,
       CASE WHEN h1_2017 > 0 THEN ROUND(100.0 * (h1_2018 - h1_2017) / h1_2017, 1) END AS h1_growth_pct
FROM c
ORDER BY revenue DESC;

-- name: delivery_vs_review
-- Does late delivery hurt customer satisfaction?
WITH o AS (
    SELECT order_id, MAX(is_late) AS is_late, AVG(delivery_days) AS delivery_days
    FROM fact_sales GROUP BY order_id
)
SELECT CASE WHEN o.is_late = 1 THEN 'Late' ELSE 'On time' END AS delivery,
       COUNT(*)                          AS orders,
       ROUND(AVG(o.delivery_days), 1)    AS avg_delivery_days,
       ROUND(AVG(r.review_score), 2)     AS avg_review_score,
       ROUND(100.0 * AVG(r.review_score <= 2), 1) AS pct_bad_reviews_1_2_stars
FROM o JOIN order_review r ON r.order_id = o.order_id
GROUP BY delivery;

-- name: new_vs_returning
-- Customer acquisition and retention by month: first-time vs returning buyers.
WITH first_order AS (
    SELECT customer_unique_id, MIN(order_month) AS first_month
    FROM fact_sales GROUP BY customer_unique_id
),
m AS (
    SELECT DISTINCT f.order_month, f.customer_unique_id,
           CASE WHEN f.order_month = fo.first_month THEN 'new' ELSE 'returning' END AS type
    FROM fact_sales f JOIN first_order fo USING (customer_unique_id)
)
SELECT order_month,
       SUM(type = 'new')       AS new_customers,
       SUM(type = 'returning') AS returning_customers,
       ROUND(100.0 * SUM(type = 'returning') / COUNT(*), 2) AS returning_pct
FROM m
GROUP BY order_month
ORDER BY order_month;
