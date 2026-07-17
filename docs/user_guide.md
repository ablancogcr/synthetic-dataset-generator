# Analyst User Guide

## Load the files

Generate a package, unzip it if necessary, and load dimension tables before fact tables. In a SQL
database, use strings for identifiers and state/category fields, dates or timestamps for temporal
fields, decimals for USD fields, integers for counts/scores, and booleans for flags. The generated
`data_dictionary.csv` provides the intended logical type for every field.

Useful relationships include:

- `orders.customer_id` to `customers.customer_id`
- `order_items.order_id` to `orders.order_id`
- `order_items.product_id` to `products.product_id`
- `order_items.seller_id` to `sellers.seller_id`
- payments, shipping, and reviews to orders through `order_id`

## Suggested analysis questions

- Which categories, states, and customer segments drive gross merchandise value?
- How concentrated is seller revenue, and how does seller churn redistribute it?
- How do delivery delay, seller quality, and shipping burden affect review scores?
- What are repeat-purchase and cohort patterns by customer segment?
- How do holiday and logistics scenarios change operational KPIs?

## Dashboard ideas

Build an executive overview with orders, item value, shipping value, average review, and late-delivery
rate. Add category and regional drill-downs, a seller concentration view, a delivery-performance page,
and a scenario comparison page.

## Data science ideas

Predict late delivery from route, capacity, season, and shipping attributes; model satisfaction risk;
or segment customers and sellers. Because the business drivers are documented, the dataset is also
useful for checking whether a model recovers expected relationships.

Always label portfolio outputs as synthetic. Do not describe results as real US ecommerce findings or
use them for operational decisions.

## Data-cleaning exercises

Generate with `--dirty` to practice profiling and remediation. Start by loading
`data_dictionary.csv` as the intended contract, then identify missing values, time-series gaps,
malformed dates, type-conversion failures, invalid negative values, and order headers without items.
Use `validation_summary.json` to distinguish expected training issues from unexpected generator
failures.

`dirty_data_manifest.json` reveals only aggregate counts by defect, table, and column. It does not
identify the affected rows or removed dates, so it can support grading and completeness checks without
turning the exercise into a cell-by-cell answer key. Keep transformations in a separate cleaned layer
instead of overwriting the generated source files.
