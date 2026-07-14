# Data Dictionary Guide

Every generated package contains `data_dictionary.csv`, built from the same schema registry used by
the code and validators. It lists table, column, logical type, description, example, and nullability.

## Table overview

| Table | Grain | Purpose |
|---|---|---|
| `customers` | One row per synthetic customer | Geography and behavioral segmentation |
| `sellers` | One row per synthetic seller | Origin, quality, capacity, and churn state |
| `products` | One row per synthetic product | Generic category, price, weight, and dimensions |
| `orders` | One row per order | Customer, status, timestamps, and calendar attributes |
| `order_items` | One row per order-item sequence | Product, seller, item price, and allocated shipping |
| `payments` | One row per payment sequence | Payment method, installments, and value |
| `shipping` | One row per order | Route, timing, delay, and total shipping cost |
| `reviews` | Zero or one row per eligible delivered order | Score, sentiment, and satisfaction risk |
| `calendar` | One row per date | Reusable date attributes and business-period flags |
| `simulation_metadata` | One row per run | Configuration, counts, provenance, and disclaimer |
| `data_dictionary` | One row per generated field | Machine-readable field documentation |

CSV timestamps use ISO-style values; nullable values are empty fields. Monetary fields are synthetic
USD-like values rounded to two decimals. Identifiers are generic and carry no real-world meaning.

