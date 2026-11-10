"""Weekly revenue forecasting with an honest backtest.

Approach
  * Aggregate delivered revenue to weekly totals (weeks start Monday).
  * Keep the last 12 weeks as a hold-out test set the models never see while fitting.
  * Compare simple baselines with Holt's exponential smoothing (level + trend).
  * Score with MAPE (mean absolute percentage error) and WAPE (total absolute error / total actual).
    Forecast accuracy is reported as 100 - WAPE. Lower error is better.
  * Repeat for the 5 biggest product categories ("business units").
  * Refit the best model on all data and forecast the next 8 weeks.

Run:  python src/forecast.py
"""
from pathlib import Path
import sqlite3
import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "commerce.db"
OUT = ROOT / "outputs"
TEST_WEEKS = 12
HORIZON = 8


def weekly_series(con, category=None):
    sql = "SELECT order_date, revenue FROM fact_sales"
    params = ()
    if category:
        sql += " WHERE category = ?"
        params = (category,)
    df = pd.read_sql_query(sql, con, params=params, parse_dates=["order_date"])
    s = df.set_index("order_date")["revenue"].resample("W-SUN").sum()
    # keep complete weeks only: data collection stops in late Aug 2018, so the week ending
    # 26 Aug 2018 is cut short and would look like a fake collapse in sales
    s = s[(s.index >= "2017-01-08") & (s.index <= "2018-08-19")]
    return s


def mape(actual, pred):
    return float(np.mean(np.abs((actual - pred) / actual)) * 100)


def wape(actual, pred):
    return float(np.sum(np.abs(actual - pred)) / np.sum(actual) * 100)


def forecasts(train, h):
    """Return a dict of model name -> forecast array of length h."""
    return {
        "naive (last week repeats)": np.repeat(train.iloc[-1], h),
        "4-week moving average": np.repeat(train.iloc[-4:].mean(), h),
        "holt (damped trend)": ExponentialSmoothing(
            train, trend="add", damped_trend=True, initialization_method="estimated"
        ).fit().forecast(h).values,
    }


def backtest(series):
    train, test = series.iloc[:-TEST_WEEKS], series.iloc[-TEST_WEEKS:]
    rows, preds = [], {}
    for name, pred in forecasts(train, TEST_WEEKS).items():
        rows.append({"model": name, "mape_pct": round(mape(test.values, pred), 2),
                     "wape_pct": round(wape(test.values, pred), 2),
                     "accuracy_pct (100-WAPE)": round(100 - wape(test.values, pred), 2)})
        preds[name] = pred
    return pd.DataFrame(rows).sort_values("wape_pct"), train, test, preds


def main():
    con = sqlite3.connect(DB)

    # ---- 1) total revenue
    total = weekly_series(con)
    scores, train, test, preds = backtest(total)
    scores.to_csv(OUT / "forecast_model_comparison.csv", index=False)
    print("Total weekly revenue - backtest on last 12 weeks")
    print(scores.to_string(index=False))

    best = scores.iloc[0]["model"]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(total.index, total.values / 1e3, label="actual")
    ax.plot(test.index, preds[best] / 1e3, label=f"forecast: {best}", linestyle="--")
    ax.set_title("Weekly revenue (BRL thousands): backtest on last 12 weeks")
    ax.legend(); fig.tight_layout()
    fig.savefig(OUT / "charts" / "forecast_backtest.png", dpi=120); plt.close(fig)

    # ---- 2) top 5 categories ("business units")
    top5 = pd.read_sql_query(
        "SELECT category FROM fact_sales GROUP BY category ORDER BY SUM(revenue) DESC LIMIT 5", con
    )["category"]
    unit_rows = []
    for cat in top5:
        sc, *_ = backtest(weekly_series(con, cat))
        holt = sc[sc["model"].str.startswith("holt")].iloc[0]
        naive = sc[sc["model"].str.startswith("naive")].iloc[0]
        unit_rows.append({"category": cat, "holt_wape_pct": holt["wape_pct"],
                          "naive_wape_pct": naive["wape_pct"], "best_model": sc.iloc[0]["model"],
                          "best_wape_pct": sc.iloc[0]["wape_pct"]})
    units = pd.DataFrame(unit_rows)
    units.to_csv(OUT / "forecast_by_category.csv", index=False)
    print("\nTop 5 categories - backtest WAPE (%)")
    print(units.to_string(index=False))

    # ---- 3) final 8-week forecast from the model, refit on all data
    model = ExponentialSmoothing(total, trend="add", damped_trend=True,
                                 initialization_method="estimated").fit()
    future = model.forecast(HORIZON)
    pd.DataFrame({"week_ending": future.index.date, "forecast_revenue_brl": future.round(0).values}) \
        .to_csv(OUT / "forecast_next_8_weeks.csv", index=False)
    print("\nNext 8 weeks forecast saved to outputs/forecast_next_8_weeks.csv")

    # ---- 4) monthly planning forecast, rolling one-step-ahead backtest
    monthly_backtest(con)
    con.close()


def monthly_backtest(con, test_months=6):
    """How the forecast is used in practice: at the start of each month, forecast that month
    using only the history available then. Roll forward month by month over the last 6 months
    (Mar - Aug 2018), which the models only see after they have forecast them."""
    df = pd.read_sql_query("SELECT order_date, revenue FROM fact_sales", con, parse_dates=["order_date"])
    m = df.set_index("order_date")["revenue"].resample("MS").sum()
    m = m[(m.index >= "2017-01-01") & (m.index <= "2018-08-01")]
    first_test = len(m) - test_months

    models = {
        "simple exponential smoothing": lambda h: ExponentialSmoothing(h, initialization_method="estimated").fit().forecast(1).values[0],
        "3-month moving average": lambda h: h.iloc[-3:].mean(),
        "naive (next month = this month)": lambda h: h.iloc[-1],
    }
    rows, detail = [], {"month": m.index[first_test:].strftime("%Y-%m"), "actual_brl": m.iloc[first_test:].round(0).values}
    for name, fn in models.items():
        preds = np.array([fn(m.iloc[:i]) for i in range(first_test, len(m))])
        actual = m.iloc[first_test:].values
        rows.append({"model": name, "mape_pct": round(mape(actual, preds), 2), "wape_pct": round(wape(actual, preds), 2),
                     "accuracy_pct (100-WAPE)": round(100 - wape(actual, preds), 2)})
        detail[name] = preds.round(0)
    res = pd.DataFrame(rows).sort_values("wape_pct")
    res.to_csv(OUT / "forecast_monthly_comparison.csv", index=False)
    pd.DataFrame(detail).to_csv(OUT / "forecast_monthly_backtest_detail.csv", index=False)
    print(f"\nMonthly revenue - rolling one-step-ahead backtest, last {test_months} months")
    print(res.to_string(index=False))


if __name__ == "__main__":
    main()
