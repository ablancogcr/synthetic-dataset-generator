# AGENTS.md

## Project Name

Synthetic Dataset Generator

## Project Purpose

Build a synthetic ecommerce dataset generator that creates modern, realistic, portfolio-ready ecommerce datasets for analysts.

The generator should produce downloadable multi-table CSV datasets that can be used for SQL analytics projects, BI dashboards, and data science projects.

This is Stage 1 of a larger analytics portfolio ecosystem:

1. Synthetic ecommerce dataset generator
2. SQL analytics warehouse using the generated dataset
3. Data science project using the generated dataset

This repository should focus only on Stage 1.

## Core Product Goal

Create a tool that generates a fully synthetic, US-like ecommerce marketplace dataset with modern dates, realistic relationships, business scenarios, and documentation.

The generated dataset should feel like a practical ecommerce marketplace database, not a toy flat file.

The output should be useful for analysts who want to build their own portfolio projects without relying on overused public datasets.

## Important Disclaimer

The generated dataset must be fully synthetic.

It must not be presented as real US ecommerce data, real company data, or real customer activity.

The README and generated dataset metadata must clearly state that:

* The dataset is synthetic.
* It does not contain real customers, sellers, orders, or company performance.
* It is designed for education, analytics practice, portfolio projects, SQL modeling, dashboard development, and machine learning experiments.
* It should not be used as real market data or for operational decision making.

## Preferred Technical Stack

Use:

* Python
* pandas
* numpy
* Faker
* pydantic
* pytest
* ruff
* uv for package and environment management

Optional:

* pyarrow for parquet support later

Do not use heavy synthetic data libraries for the MVP unless clearly justified.

Avoid CTGAN, GANs, deep learning, or complex probabilistic frameworks in the first implementation.

The first version should be interpretable, configurable, reproducible, and easy to explain.

## Development Principles

Prioritize:

* Clear structure
* Reproducibility
* Business realism
* Good documentation
* Simple configuration
* Valid relational outputs
* Data quality checks
* Useful generated datasets
* Portfolio-ready presentation

Avoid:

* Overengineering
* Unnecessary web frameworks in the first version
* Hidden magic
* One giant script
* One giant flat file
* Models that are hard to explain
* Claims that the dataset represents real ecommerce behavior exactly

## Expected Repository Structure

Use a structure close to this:

```text
synthetic-dataset-generator/
  README.md
  AGENTS.md
  pyproject.toml
  uv.lock
  config/
    default_config.yaml
    scenarios.yaml
  data/
    sample_output/
      README.md
  docs/
    methodology.md
    data_dictionary.md
    validation_report.md
    user_guide.md
  src/
    synthetic_dataset_generator/
      __init__.py
      cli.py
      config.py
      constants.py
      schemas.py
      generator.py
      exporters.py
      validators.py
      metadata.py
      geography.py
      calendar.py
      pricing.py
      categories.py
      customers.py
      sellers.py
      products.py
      orders.py
      payments.py
      shipping.py
      reviews.py
      scenarios.py
  tests/
    test_config.py
    test_generation.py
    test_relationships.py
    test_validation.py
```

Small deviations are acceptable if they improve clarity.

## MVP Scope

The MVP should generate a zipped dataset package containing CSV files.

The dataset package should include:

```text
customers.csv
sellers.csv
products.csv
orders.csv
order_items.csv
payments.csv
shipping.csv
reviews.csv
calendar.csv
simulation_metadata.csv
data_dictionary.csv
```

The MVP should support:

* Configurable dataset size
* Configurable date range
* Configurable random seed
* Configurable scenario
* US-like states and regions
* Modern dates, defaulting to 2024 through 2026
* Synthetic customers
* Synthetic sellers
* Synthetic products
* Synthetic orders
* Synthetic order items
* Synthetic payments
* Synthetic shipping outcomes
* Synthetic reviews
* Dataset metadata
* Data dictionary
* Basic validation report

## CLI Requirements

Create a simple command line interface.

Example target usage:

```bash
uv run synthetic-dataset-generator generate \
  --config config/default_config.yaml \
  --output data/output \
  --scenario baseline \
  --orders 50000 \
  --seed 42
```

Alternative shorter command names are acceptable if documented clearly.

The CLI should generate the dataset files and a ZIP package.

Example output:

```text
data/output/ecommerce_baseline_50000_seed42/
data/output/ecommerce_baseline_50000_seed42.zip
```

The ZIP should contain all generated CSVs, the data dictionary, metadata, and validation summary.

## Configuration Requirements

Use YAML config.

The default config should include:

```yaml
dataset:
  name: "Synthetic Ecommerce Dataset"
  domain: "ecommerce_marketplace"
  country_context: "US-like synthetic marketplace"
  start_date: "2024-01-01"
  end_date: "2026-12-31"
  number_of_orders: 50000
  random_seed: 42

output:
  format: "csv"
  create_zip: true
  include_data_dictionary: true
  include_validation_report: true

simulation:
  scenario: "baseline"
  customer_count: 20000
  seller_count: 1200
  product_count: 8000
  min_items_per_order: 1
  max_items_per_order: 5
  repeat_customer_rate: 0.18

business_rules:
  currency: "USD"
  allow_cancelled_orders: true
  allow_late_deliveries: true
  allow_missing_reviews: true
```

Do not hardcode all parameters into Python modules. The config should control the main generation behavior.

## Supported Scenarios

Implement these scenarios in the MVP:

### baseline

Normal synthetic ecommerce marketplace behavior.

### holiday_spike

Increased Q4 demand, especially in November and December.

Expected behavior:

* Higher order volume in Q4
* Increased demand for Electronics, Toys & Games, Watches & Gifts, and Home Goods
* Slightly higher shipping delays
* Slightly higher shipping costs
* Slightly more negative reviews caused by delivery pressure

### logistics_improvement

Improved delivery performance.

Expected behavior:

* Lower delivery delay rate
* Lower average actual delivery days
* Higher review score distribution
* Similar product demand and order values

### seller_churn

A small group of important sellers exits or becomes inactive during the period.

Expected behavior:

* Some top sellers become inactive after a chosen date
* Revenue shifts to other sellers
* Category-level AOV can change
* Seller concentration should be visible in metadata

Each row in the relevant tables should include a `scenario_name` field where appropriate.

## Data Model

### customers.csv

Required fields:

```text
customer_id
customer_unique_id
customer_state
customer_city
customer_region
customer_zip_prefix
customer_segment
customer_lifecycle_stage
created_at
```

Suggested customer segments:

```text
one_time_buyer
occasional_buyer
high_value_buyer
discount_sensitive
category_loyal
```

Suggested lifecycle stages:

```text
new
active
returning
at_risk
```

### sellers.csv

Required fields:

```text
seller_id
seller_state
seller_city
seller_region
seller_zip_prefix
seller_segment
seller_quality_score
seller_fulfillment_capacity
seller_active_flag
created_at
deactivated_at
```

Suggested seller segments:

```text
long_tail
growth_seller
high_volume
premium
at_risk
```

### products.csv

Required fields:

```text
product_id
product_category
product_name
product_weight_g
product_length_cm
product_height_cm
product_width_cm
product_price_base_usd
created_at
```

Use English product categories.

Recommended initial categories:

```text
Health & Beauty
Home & Bedding
Sports & Outdoors
Electronics & Accessories
Furniture & Decor
Watches & Gifts
Home Goods
Mobile & Telecom
Automotive
Toys & Games
Office Supplies
Pet Supplies
Garden & Outdoor
Baby Products
Fashion
Books & Media
```

### orders.csv

Required fields:

```text
order_id
customer_id
order_status
order_purchase_timestamp
order_approved_at
order_estimated_delivery_date
order_delivered_carrier_date
order_delivered_customer_date
order_year
order_quarter
order_month
order_week
order_day_of_week
is_weekend
is_holiday_period
is_promotion_period
scenario_name
```

Order statuses should include:

```text
delivered
shipped
cancelled
processing
```

Most orders should be delivered.

All dates must respect logical order where applicable:

```text
order_purchase_timestamp <= order_approved_at
order_approved_at <= order_delivered_carrier_date
order_delivered_carrier_date <= order_delivered_customer_date
```

Cancelled or processing orders may have missing delivery timestamps.

### order_items.csv

Required fields:

```text
order_id
order_item_id
product_id
seller_id
item_price_usd
shipping_cost_usd
item_total_usd
```

An order may have one or more items.

The combination of `order_id` and `order_item_id` should be unique.

### payments.csv

Required fields:

```text
order_id
payment_sequential
payment_type
payment_installments
payment_value_usd
```

Payment types:

```text
credit_card
debit_card
digital_wallet
bank_transfer
gift_card
```

Most payments should be `credit_card` or `digital_wallet`.

Some orders can have multiple payment rows.

### shipping.csv

Required fields:

```text
order_id
seller_state
customer_state
seller_region
customer_region
shipping_distance_band
shipping_zone
estimated_delivery_days
actual_delivery_days
delivery_delay_days
late_delivery_flag
shipping_cost_usd
```

Distance bands:

```text
same_state
same_region
cross_region
remote
```

Shipping behavior should depend on:

* Distance band
* Product size and weight
* Seller fulfillment capacity
* Holiday period
* Scenario

### reviews.csv

Required fields:

```text
review_id
order_id
review_score
review_creation_date
review_answer_timestamp
review_sentiment_label
satisfaction_risk_flag
```

Review scores should be 1 through 5.

Review score behavior should depend on:

* Late delivery flag
* Delivery delay days
* Seller quality score
* Shipping cost relative to order value
* Holiday pressure
* Scenario

Suggested sentiment labels:

```text
negative
neutral
positive
```

`satisfaction_risk_flag` should be 1 when `review_score` is 1 or 2.

### calendar.csv

Required fields:

```text
date
year
quarter
month
month_name
week
day_of_week
day_name
is_weekend
is_holiday_period
is_promotion_period
season
```

### simulation_metadata.csv

Required fields:

```text
simulation_run_id
dataset_name
domain
scenario_name
random_seed
generated_at
start_date
end_date
number_of_orders
number_of_customers
number_of_sellers
number_of_products
currency
disclaimer
```

### data_dictionary.csv

Required fields:

```text
table_name
column_name
data_type
description
example_value
nullable
```

## Geography Rules

Use US-like synthetic geography.

Use US states and regions.

Recommended regions:

```text
Northeast
South
Midwest
West
```

Customer state distribution should be weighted toward larger states such as:

```text
CA
TX
FL
NY
PA
IL
OH
GA
NC
MI
```

Seller state distribution should be weighted toward commerce and logistics hubs such as:

```text
CA
TX
FL
NJ
IL
GA
NY
PA
OH
WA
```

Do not use real street addresses.

Cities can be generated using Faker, but state-region consistency should be maintained as much as practical.

## Date Rules

Default generated dates should be between 2024-01-01 and 2026-12-31.

The generator should preserve ecommerce-like seasonality.

Expected behavior:

* Normal baseline variation across months
* Higher activity in Q4
* Higher activity around promotion or holiday periods
* Optional weekend effects

Do not generate impossible date sequences.

## Pricing Rules

Use USD-like synthetic prices.

Prices should vary by category.

Suggested behavior:

* Electronics & Accessories: higher average price
* Furniture & Decor: higher price and higher shipping cost
* Health & Beauty: lower to medium price
* Home Goods: medium price
* Toys & Games: medium price with Q4 seasonality
* Books & Media: lower price
* Fashion: medium price with moderate variance

Use realistic distributions, not uniform random values everywhere.

## Shipping Rules

Shipping cost should depend on:

* Product weight
* Product dimensions
* Seller region
* Customer region
* Distance band
* Holiday period
* Scenario

Delivery days should depend on:

* Distance band
* Seller fulfillment capacity
* Holiday period
* Scenario

Late delivery should affect review score probability.

## Review Rules

Review scores should not be random noise.

They should be influenced by:

* Delivery delay
* Seller quality score
* Shipping cost
* Scenario
* Holiday pressure
* Order value, lightly

Example behavior:

* Late deliveries increase probability of 1 or 2 star reviews.
* Early or on-time deliveries increase probability of 4 or 5 star reviews.
* High seller quality improves review score distribution.
* Holiday spike scenario slightly increases low reviews because of delivery pressure.
* Logistics improvement scenario improves review score distribution.

## Validation Requirements

Create validation logic that checks the generated dataset.

At minimum, validate:

* Primary key uniqueness
* Foreign key relationships
* No negative prices
* No negative shipping costs
* Valid review scores
* Valid order statuses
* Valid payment types
* Valid state values
* Date sequence logic
* Payment totals approximately match order totals
* Shipping records match orders
* Reviews only belong to valid orders
* Scenario name is populated
* Required files are generated

Create a validation summary file in the output folder.

Suggested file:

```text
validation_summary.json
```

Also generate a human-readable markdown summary:

```text
validation_summary.md
```

## Testing Requirements

Add pytest tests.

Tests should cover:

* Config loading
* Dataset generation runs successfully
* Required files are created
* Row counts are reasonable
* Primary keys are unique
* Foreign keys are valid
* Date logic is valid
* Scenario selection works
* Random seed produces reproducible outputs

Do not skip testing just because the code seems simple. That is how small projects become haunted houses.

## Documentation Requirements

Create the following documentation files:

```text
README.md
docs/methodology.md
docs/data_dictionary.md
docs/user_guide.md
docs/validation_report.md
```

### README.md should include:

* Project overview
* Why the project exists
* What the generator creates
* How to install
* How to run
* Example CLI commands
* Output files
* Supported scenarios
* Dataset disclaimer
* Example use cases
* Roadmap

### methodology.md should explain:

* Synthetic generation approach
* Customer generation logic
* Seller generation logic
* Product generation logic
* Order generation logic
* Payment logic
* Shipping logic
* Review score logic
* Scenario logic
* Validation logic
* Limitations

### user_guide.md should explain:

* How analysts can use the generated files
* How to load the data into SQL tools
* Suggested analysis questions
* Suggested dashboard ideas
* Suggested data science use cases

### data_dictionary.md should document:

* Each table
* Each field
* Data type
* Meaning
* Nullable status
* Example value

## Portfolio Page Support

The generated outputs should support a future portfolio page where users can download a sample dataset.

Create at least one sample dataset with a small number of orders.

Recommended sample:

```text
10,000 orders
baseline scenario
seed 42
date range 2024-01-01 to 2026-12-31
```

Place sample output documentation under:

```text
data/sample_output/
```

Do not commit very large generated datasets unless explicitly requested.

For GitHub, keep sample files small enough to be practical.

## Generic Naming Requirements

Do not introduce fictional brand names, marketplace names, or company names into the project.

Use generic names such as:

```text
Synthetic Ecommerce Dataset
Synthetic Marketplace Dataset
Synthetic Dataset Generator
Ecommerce Baseline Dataset
Ecommerce Holiday Spike Dataset
```

Generated IDs should also be generic.

Acceptable examples:

```text
customer_000001
seller_000001
product_000001
order_000001
review_000001
simulation_run_20260101_000001
```

Avoid names that imply a real company, platform, or brand.

## Non-Goals for Stage 1

Do not build the SQL warehouse in this repository.

Do not build the BI dashboard in this repository.

Do not build the machine learning model in this repository.

Do not build a full web app unless explicitly requested later.

Do not add authentication.

Do not add a database backend.

Do not add cloud deployment.

Do not create unnecessary APIs.

This stage should produce a strong local generator and downloadable dataset package.

## Quality Bar

The project should be good enough that another analyst can:

1. Clone the repository
2. Install dependencies
3. Run one command
4. Generate a synthetic ecommerce dataset
5. Read the documentation
6. Load the CSV files into a SQL database
7. Start building a portfolio project

## Coding Style

Use clear, readable Python.

Prefer small modules with clear responsibilities.

Use type hints.

Use pydantic models for config validation.

Use deterministic random generation when a seed is provided.

Avoid overly clever code.

Use constants for repeated values such as states, regions, categories, payment types, and order statuses.

Format code with ruff.

## Suggested Implementation Order

Build in this order:

1. Project structure and pyproject.toml
2. Config loading and validation
3. Constants for geography, categories, statuses, payment types
4. Calendar generation
5. Customer generation
6. Seller generation
7. Product generation
8. Order generation
9. Order item generation
10. Payment generation
11. Shipping generation
12. Review generation
13. Scenario adjustments
14. Exporters
15. Validation checks
16. CLI
17. Documentation
18. Tests
19. Sample dataset

## Acceptance Criteria

The implementation is complete when:

* The CLI can generate a dataset from config.
* The output includes all required CSV files.
* The output includes metadata, data dictionary, and validation summary.
* The generated records have valid relationships.
* The generated records follow realistic business rules.
* At least four scenarios are supported.
* Tests pass.
* Documentation explains how to use the generator.
* A small sample dataset can be generated reproducibly.
* The README clearly states that the dataset is synthetic.
* The project contains no fictional brand or marketplace name.

## Final Reminder

This project should be positioned as a synthetic dataset generator for analytics portfolios.

It should not merely generate random ecommerce rows.

The generated data should preserve believable marketplace behavior across customers, sellers, products, orders, payments, shipping, and reviews.

The main value is not randomness. The main value is controlled, documented, reusable synthetic business data.
