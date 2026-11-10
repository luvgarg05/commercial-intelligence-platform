"""Export clean tables for the Power BI dashboard into powerbi/.

  fact_sales.csv          one row per delivered item line (the main table)
  dim_customer.csv        one row per real customer, with first order month and order count
  order_review.csv        review score per order
  forecast_next_8_weeks.csv  copied from outputs/

Run:  python src/export_powerbi.py
"""
from pathlib import Path
import shutil
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "commerce.db"
PBI = ROOT / "powerbi"
PBI.mkdir(exist_ok=True)

con = sqlite3.connect(DB)
pd.read_sql_query("SELECT * FROM fact_sales", con).to_csv(PBI / "fact_sales.csv", index=False)
pd.read_sql_query("""
    SELECT customer_unique_id,
           MIN(order_month)          AS first_order_month,
           COUNT(DISTINCT order_id)  AS orders,
           ROUND(SUM(revenue), 2)    AS lifetime_revenue
    FROM fact_sales GROUP BY customer_unique_id
""", con).to_csv(PBI / "dim_customer.csv", index=False)
pd.read_sql_query("""
    SELECT r.* FROM order_review r
    WHERE r.order_id IN (SELECT DISTINCT order_id FROM fact_sales)
""", con).to_csv(PBI / "order_review.csv", index=False)
con.close()
shutil.copy(ROOT / "outputs" / "forecast_next_8_weeks.csv", PBI / "forecast_next_8_weeks.csv")
for f in sorted(PBI.glob("*.csv")):
    print(f.name, sum(1 for _ in open(f)) - 1, "rows")
