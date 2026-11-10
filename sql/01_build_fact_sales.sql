-- Clean sales fact table: one row per delivered order item.
-- Joins 5 raw tables so every analysis query can start from one place.

DROP TABLE IF EXISTS fact_sales;

CREATE TABLE fact_sales AS
SELECT
    oi.order_id,
    oi.order_item_id,
    o.customer_id,
    c.customer_unique_id,                      -- the real person (customer_id changes per order)
    c.customer_state                            AS state,
    c.customer_city                             AS city,
    oi.seller_id,
    oi.product_id,
    COALESCE(t.product_category_name_english, 'unknown') AS category,
    DATE(o.order_purchase_timestamp)            AS order_date,
    STRFTIME('%Y-%m', o.order_purchase_timestamp) AS order_month,
    oi.price,
    oi.freight_value,
    oi.price + oi.freight_value                 AS revenue,
    -- delivery days and whether the order arrived after the promised date
    JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp) AS delivery_days,
    CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END AS is_late
FROM order_items oi
JOIN orders o           ON o.order_id = oi.order_id
JOIN customers c        ON c.customer_id = o.customer_id
LEFT JOIN products p    ON p.product_id = oi.product_id
LEFT JOIN category_translation t ON t.product_category_name = p.product_category_name
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp <  '2018-09-01';

-- one review score per order (some orders have more than one review; keep the average)
DROP TABLE IF EXISTS order_review;
CREATE TABLE order_review AS
SELECT order_id, AVG(review_score) AS review_score
FROM reviews
GROUP BY order_id;

CREATE INDEX idx_fact_month    ON fact_sales(order_month);
CREATE INDEX idx_fact_customer ON fact_sales(customer_unique_id);
CREATE INDEX idx_fact_order    ON fact_sales(order_id);
