# Power BI dashboard: step-by-step build guide

You build this yourself in Power BI Desktop (free, Windows). Budget 3–4 hours.
At the end you will have **3 report pages with 12 KPI visuals**. Save it as
`powerbi/Commercial_Intelligence.pbix` and add screenshots to `outputs/charts/`.

## 1. Load the data
1. Home → Get data → Text/CSV → load each file in this folder:
   `fact_sales.csv`, `dim_customer.csv`, `order_review.csv`, `forecast_next_8_weeks.csv`.
2. In Power Query (Transform data), check types: `order_date` = Date, `revenue`, `price`,
   `freight_value`, `delivery_days` = Decimal, `is_late` = Whole number. Close & Apply.

## 2. Build the model (Model view)
- `dim_customer[customer_unique_id]` 1 → * `fact_sales[customer_unique_id]`
- `order_review[order_id]` 1 → * `fact_sales[order_id]`
- Add a date table: Modeling → New table:
  ```
  Calendar = CALENDAR(DATE(2017,1,1), DATE(2018,8,31))
  ```
  Add columns `Month = FORMAT('Calendar'[Date], "YYYY-MM")`, then relate
  `Calendar[Date]` 1 → * `fact_sales[order_date]`. Mark it as a date table.

## 3. DAX measures (Modeling → New measure, on fact_sales)
```
Total Revenue = SUM(fact_sales[revenue])
Orders = DISTINCTCOUNT(fact_sales[order_id])
Customers = DISTINCTCOUNT(fact_sales[customer_unique_id])
Avg Order Value = DIVIDE([Total Revenue], [Orders])
Late Delivery % = DIVIDE(
    CALCULATE(DISTINCTCOUNT(fact_sales[order_id]), fact_sales[is_late] = 1), [Orders])
Avg Review = AVERAGE(order_review[review_score])
Repeat Customer % = DIVIDE(
    COUNTROWS(FILTER(dim_customer, dim_customer[orders] > 1)), COUNTROWS(dim_customer))
Revenue MoM % =
VAR prev = CALCULATE([Total Revenue], DATEADD('Calendar'[Date], -1, MONTH))
RETURN DIVIDE([Total Revenue] - prev, prev)
Avg Delivery Days = AVERAGE(fact_sales[delivery_days])
```
Format the % measures as Percentage, revenue as currency (R$).

## 4. Pages and the 12 visuals

**Page 1 – Executive overview**
1. Card: Total Revenue
2. Card: Orders
3. Card: Avg Order Value
4. Card: Repeat Customer %
5. Line chart: Total Revenue by `Calendar[Month]` (+ Revenue MoM % as tooltip)
6. Slicer: `category` (and a date slicer)

**Page 2 – Regions & categories**
7. Filled map or bar chart: Total Revenue by `state`
8. Bar chart: Top 10 `category` by Total Revenue (Filters pane → Top N = 10)
9. Matrix: category × Month with Total Revenue (conditional formatting: colour scale)

**Page 3 – Customer experience & forecast**
10. Clustered column: Avg Review by `is_late` (rename 0/1 to On time / Late)
11. Card: Late Delivery %, with Avg Delivery Days beside it
12. Line chart: `forecast_next_8_weeks[forecast_revenue_brl]` by `week_ending`

## 5. Things you must be able to explain
- Why a separate Calendar table (time intelligence like DATEADD needs one continuous date column).
- Why DISTINCTCOUNT for orders (fact_sales has one row per *item*, an order can have several).
- Difference between a measure (calculated on the fly, respects filters) and a calculated column (stored per row).
