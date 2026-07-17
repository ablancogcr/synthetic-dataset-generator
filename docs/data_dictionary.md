# Data Dictionary Guide

Every generated package contains `data_dictionary.csv`, built from the same schema registry used by
the code and validators. It lists table, column, logical type, description, example, and nullability.

## Table overview

| Table | Grain | Purpose |
|---|---|---|
| `customers` | One row per synthetic customer | Geography and behavioral segmentation |
| `sellers` | One row per synthetic seller | Origin, quality, capacity, and churn state |
| `products` | One row per synthetic product | Generic category, price, weight, and dimensions |
| `seller_products` | One row per unique seller-product listing | Seller catalog, listing price, availability, and active state |
| `orders` | One row per order | Customer, status, timestamps, and calendar attributes |
| `order_items` | One row per order-item sequence | Listing, product, seller, item price, and allocated shipping |
| `payments` | One row per payment sequence | Payment method, installments, and value |
| `shipping` | One row per order | Route, timing, delay, and total shipping cost |
| `reviews` | Zero or one row per eligible delivered order | Score, sentiment, and satisfaction risk |
| `calendar` | One row per date | Reusable date attributes and business-period flags |
| `simulation_metadata` | One row per run | Configuration, counts, provenance, and disclaimer |
| `data_dictionary` | One row per generated field | Machine-readable field documentation |

CSV timestamps use ISO-style values; nullable values are empty fields. Monetary fields are synthetic
USD-like values rounded to two decimals. Identifiers are generic and carry no real-world meaning.

## Seller-product listing fields

| Field | Meaning |
|---|---|
| `seller_product_id` | Unique synthetic listing identifier and authoritative order-item reference |
| `seller_id` | Seller offering the catalog product |
| `product_id` | Shared catalog product being offered |
| `seller_price_usd` | Seller-specific price used as the center of item-price variation |
| `listing_created_at` | Later of the seller and product creation dates |
| `listing_active_flag` | Whether the listing is active at the end of the simulation period |
| `scenario_name` | Scenario that produced the listing |

`order_items.seller_product_id` joins to this table. The item-level `seller_id` and `product_id` are
retained for convenience and must exactly match the referenced listing.

`simulation_metadata.csv` records both `requested_number_of_orders` and the final
`number_of_orders`, plus `data_quality_mode`. These counts differ when dirty mode removes complete
transaction days.

Metadata also records `number_of_seller_products`; dirty structural defects do not change that count.

The dictionary always describes the intended clean logical schema. In dirty mode, selected exported
values deliberately violate documented nullability, format, type, or range rules; relationship
identifiers remain protected and the dictionary itself is not corrupted.
