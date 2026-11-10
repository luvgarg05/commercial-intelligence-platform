# Commercial Intelligence Platform

Sales analytics on **~110K delivered order items (96K orders, 93K customers)** from Olist, a
Brazilian e-commerce marketplace, Jan 2017 – Aug 2018. SQL for the analysis, Python for
cleaning and forecasting, Power BI for the dashboard.

**Business questions**
1. Which regions and product categories drive revenue, and which are growing fastest?
2. How does delivery performance affect customer satisfaction?
3. How well does the business keep customers?
4. What revenue should we expect in the coming weeks?

## Key findings
| # | Finding | Number | So what |
|---|---|---|---|
| 1 | Revenue is concentrated in 3 states | SP, RJ, MG = **62.6%** of revenue; SP alone 37.4% | Logistics and marketing spend should prioritise the South-East |
| 2 | No single category dominates | Top 3 categories (health & beauty, watches & gifts, bed/bath/table) = **25.3%** of revenue | Broad catalogue; growth isn't tied to one category |
| 3 | Fast growth across categories | Watches & gifts revenue grew **308%** from H1 2017 to H1 2018; health & beauty **234%** | Candidates for more seller acquisition |
| 4 | Late deliveries destroy satisfaction | **8.1%** of orders arrive late; their average review is **2.57 vs 4.30** for on-time orders, and **54%** of late orders get 1–2 star reviews (vs 9.2%) | Fixing late deliveries is the biggest lever on ratings |
| 5 | Very low repeat purchase | Only **3.0%** of customers ordered more than once | Retention programmes (loyalty, remarketing) are the main growth gap |
| 6 | Weekly revenue can be forecast with ~83% accuracy | Best model WAPE **16.5%** on a 12-week hold-out, vs 38.4% for the naive baseline | Usable for short-term demand and staffing planning |

Average order value: **R$159.83**. Average review: **4.16 / 5**.
A sharp dip in the week ending 27 May 2018 coincides with the nationwide truck drivers' strike in Brazil in late May 2018, a plausible cause (not tested).

## Forecasting method
- Weekly revenue, complete weeks only (the final week of Aug 2018 is cut short by the data collection end date).
- Last 12 weeks held out; models never see them during fitting.
- Models compared: naive (last week repeats), 4-week moving average, Holt's exponential smoothing with damped trend.
- Metrics: **WAPE** (total absolute error ÷ total actual revenue) and MAPE. Accuracy = 100 − WAPE.
- Also backtested for the top 5 categories: best WAPE 15–22% per category (`outputs/forecast_by_category.csv`).
- The 8-week forward forecast uses Holt (it models trend; the moving average forecasts a flat line).

## Project structure
```
data/raw/            Olist CSVs (download with src/download_data.py)
sql/01_build_fact_sales.sql   joins 5 tables into one clean fact table
sql/02_analysis.sql           business queries (window functions, CTEs, Pareto, growth)
src/build_database.py         CSV -> SQLite + fact table
src/analysis.py               runs queries, saves outputs/*.csv and charts
src/forecast.py               backtest + 8-week forecast
src/export_powerbi.py         tables for Power BI
powerbi/POWERBI_GUIDE.md      step-by-step dashboard build (3 pages, 12 visuals, DAX measures)
outputs/                      results and charts
```

## Run it
```
pip install pandas matplotlib statsmodels
python src/download_data.py
python src/build_database.py
python src/analysis.py
python src/forecast.py
python src/export_powerbi.py
```

## Data
[Brazilian E-Commerce Public Dataset by Olist](https://github.com/olist/work-at-olist-data) (CC BY-NC-SA 4.0).
Revenue = item price + freight, delivered orders only, in Brazilian reais (BRL).
