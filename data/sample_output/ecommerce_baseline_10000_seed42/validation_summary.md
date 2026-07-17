# Validation Summary

Overall status: **PASSED**

Checks passed: 66 of 66
Expected issues: 0
Unexpected failures: 0

| Check | Status | Details |
|---|---|---|
| required_tables | PASS | Missing tables: [] |
| schema_customers | PASS | Columns match the declared schema. |
| required_values_customers | PASS | Missing required values: 0 |
| schema_sellers | PASS | Columns match the declared schema. |
| required_values_sellers | PASS | Missing required values: 0 |
| schema_products | PASS | Columns match the declared schema. |
| required_values_products | PASS | Missing required values: 0 |
| schema_seller_products | PASS | Columns match the declared schema. |
| required_values_seller_products | PASS | Missing required values: 0 |
| schema_orders | PASS | Columns match the declared schema. |
| required_values_orders | PASS | Missing required values: 0 |
| schema_order_items | PASS | Columns match the declared schema. |
| required_values_order_items | PASS | Missing required values: 0 |
| schema_payments | PASS | Columns match the declared schema. |
| required_values_payments | PASS | Missing required values: 0 |
| schema_shipping | PASS | Columns match the declared schema. |
| required_values_shipping | PASS | Missing required values: 0 |
| schema_reviews | PASS | Columns match the declared schema. |
| required_values_reviews | PASS | Missing required values: 0 |
| schema_calendar | PASS | Columns match the declared schema. |
| required_values_calendar | PASS | Missing required values: 0 |
| schema_simulation_metadata | PASS | Columns match the declared schema. |
| required_values_simulation_metadata | PASS | Missing required values: 0 |
| schema_data_dictionary | PASS | Columns match the declared schema. |
| required_values_data_dictionary | PASS | Missing required values: 0 |
| required_files | PASS | Missing files: [] |
| unique_customers | PASS | Duplicate keys: 0 |
| unique_sellers | PASS | Duplicate keys: 0 |
| unique_products | PASS | Duplicate keys: 0 |
| unique_seller_products | PASS | Duplicate keys: 0 |
| unique_orders | PASS | Duplicate keys: 0 |
| unique_reviews | PASS | Duplicate keys: 0 |
| unique_calendar | PASS | Duplicate keys: 0 |
| unique_order_items | PASS | Duplicate keys: 0 |
| unique_payments | PASS | Duplicate keys: 0 |
| unique_shipping | PASS | Duplicate keys: 0 |
| fk_orders_customer_id | PASS | Invalid rows: 0 |
| fk_order_items_order_id | PASS | Invalid rows: 0 |
| fk_seller_products_seller_id | PASS | Invalid rows: 0 |
| fk_seller_products_product_id | PASS | Invalid rows: 0 |
| fk_order_items_seller_product_id | PASS | Invalid rows: 0 |
| fk_order_items_product_id | PASS | Invalid rows: 0 |
| fk_order_items_seller_id | PASS | Invalid rows: 0 |
| fk_payments_order_id | PASS | Invalid rows: 0 |
| fk_shipping_order_id | PASS | Invalid rows: 0 |
| fk_reviews_order_id | PASS | Invalid rows: 0 |
| unique_seller_product_pairs | PASS | Each seller can list a product only once. |
| seller_product_catalog_coverage | PASS | Every seller and product has at least one listing. |
| seller_product_cardinality | PASS | Each product has between 1 and 4 sellers. |
| order_item_listing_consistency | PASS | Order-item seller and product identifiers match the referenced listing. |
| one_seller_per_order | PASS | Every order is fulfilled by one seller. |
| seller_product_active_status | PASS | Listing period-end active flags match their sellers. |
| seller_product_available_at_purchase | PASS | Purchased listings existed when their orders were placed. |
| valid_order_statuses | PASS | Allowed values only. |
| valid_payment_types | PASS | Allowed values only. |
| valid_review_scores | PASS | Scores are between 1 and 5. |
| valid_states | PASS | All geography uses recognized US state abbreviations. |
| non_negative_values | PASS | Prices and shipping values are non-negative. |
| date_sequence | PASS | Delivered-order timestamps are logically ordered. |
| configured_date_range | PASS | All business dates are within the configured period. |
| payment_reconciliation | PASS | Payments match order item totals to the cent. |
| shipping_coverage | PASS | Exactly one shipping row exists per order. |
| shipping_reconciliation | PASS | Order shipping equals item shipping. |
| reviews_for_delivered_orders | PASS | Reviews belong only to delivered orders. |
| scenario_populated | PASS | Scenario names are populated on scenario-bearing tables. |
| seller_churn_cutoff | PASS | Deactivated sellers receive no post-churn orders. |
