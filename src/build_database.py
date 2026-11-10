"""Load the raw Olist CSVs into a SQLite database and build one clean sales fact table.

Why SQLite: it is a real SQL database in a single file, so the same SQL works in
MySQL/PostgreSQL with small changes, and nothing needs installing.

Cleaning decisions (be ready to explain these in an interview):
  * Only orders with status 'delivered' count as revenue (cancelled/unavailable are excluded).
  * Revenue = item price + freight for each item line (what the customer paid for that line).
  * Product categories are translated from Portuguese to English; missing ones become 'unknown'.
  * Analysis window = Jan 2017 to Aug 2018. Months before 2017 and after Aug 2018 have very
    few orders (the platform was starting up / data collection stopped), so they would distort trends.

Run:  python src/build_database.py
"""
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "commerce.db"

TABLES = {
    "orders": "olist_orders_dataset",
    "order_items": "olist_order_items_dataset",
    "customers": "olist_customers_dataset",
    "products": "olist_products_dataset",
    "payments": "olist_order_payments_dataset",
    "reviews": "olist_order_reviews_dataset",
    "sellers": "olist_sellers_dataset",
    "category_translation": "product_category_name_translation",
}


def main():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)

    # 1) raw tables, one per CSV
    for table, file in TABLES.items():
        df = pd.read_csv(RAW / f"{file}.csv")
        df.to_sql(table, con, index=False)
        print(f"{table:22s} {len(df):>8,} rows")

    # 2) clean fact table: one row per delivered item line
    con.executescript((ROOT / "sql" / "01_build_fact_sales.sql").read_text())
    n = con.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    print(f"{'fact_sales':22s} {n:>8,} rows (clean, delivered, Jan 2017 - Aug 2018)")
    con.close()


if __name__ == "__main__":
    main()
