"""Run every query in sql/02_analysis.sql, save each result to outputs/<name>.csv,
and draw the key charts into outputs/charts/.

Run:  python src/analysis.py
"""
from pathlib import Path
import re
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "commerce.db"
OUT = ROOT / "outputs"
CHARTS = OUT / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)


def load_queries():
    text = (ROOT / "sql" / "02_analysis.sql").read_text()
    parts = re.split(r"^-- name: (\w+)\s*$", text, flags=re.M)
    # parts = [preamble, name1, sql1, name2, sql2, ...]
    return dict(zip(parts[1::2], parts[2::2]))


def main():
    con = sqlite3.connect(DB)
    results = {}
    for name, sql in load_queries().items():
        df = pd.read_sql_query(sql, con)
        df.to_csv(OUT / f"{name}.csv", index=False)
        results[name] = df
        print(f"\n=== {name} ===")
        print(df.head(10).to_string(index=False))
    con.close()

    # chart 1: monthly revenue
    m = results["monthly_revenue"]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(m["order_month"], m["revenue_brl"] / 1e3, marker="o")
    ax.set_title("Monthly revenue (BRL thousands)")
    ax.tick_params(axis="x", rotation=60)
    fig.tight_layout(); fig.savefig(CHARTS / "monthly_revenue.png", dpi=120); plt.close(fig)

    # chart 2: top 10 states
    s = results["revenue_by_state"].head(10)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(s["state"][::-1], s["revenue_share_pct"][::-1])
    ax.set_title("Revenue share by state, top 10 (%)")
    fig.tight_layout(); fig.savefig(CHARTS / "revenue_by_state.png", dpi=120); plt.close(fig)

    # chart 3: top 10 categories
    c = results["category_performance"].head(10)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(c["category"][::-1], c["revenue_share_pct"][::-1])
    ax.set_title("Revenue share by category, top 10 (%)")
    fig.tight_layout(); fig.savefig(CHARTS / "top_categories.png", dpi=120); plt.close(fig)


if __name__ == "__main__":
    main()
