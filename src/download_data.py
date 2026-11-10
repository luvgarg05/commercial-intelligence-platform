"""Download the Olist Brazilian e-commerce dataset (public, ~100K orders, 2016-2018).

Source: https://github.com/olist/work-at-olist-data (also on Kaggle: "Brazilian E-Commerce Public Dataset by Olist").
Run:  python src/download_data.py
"""
from pathlib import Path
import urllib.request

BASE = "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets"
FILES = [
    "olist_orders_dataset",
    "olist_order_items_dataset",
    "olist_customers_dataset",
    "olist_products_dataset",
    "olist_order_payments_dataset",
    "olist_order_reviews_dataset",
    "olist_sellers_dataset",
    "product_category_name_translation",
]

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

for name in FILES:
    target = RAW / f"{name}.csv"
    if target.exists():
        print(f"already have {target.name}")
        continue
    print(f"downloading {name} ...")
    urllib.request.urlretrieve(f"{BASE}/{name}.csv", target)
print("done")
