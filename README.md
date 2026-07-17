# Synthetic Dataset Generator

Generate reproducible, relational ecommerce datasets for SQL practice, BI dashboards, data
science experiments, and analytics portfolio case studies.

> **Synthetic-data disclaimer:** Every customer, seller, product, order, payment, shipment, and
> review produced by this project is synthetic. The output does not represent a real company,
> marketplace, customer, or market. Use it for education and experimentation only—not as market
> data or for operational decisions.

## Why this project exists

Common public ecommerce datasets are useful but overused. This generator creates configurable,
modern, internally consistent data with known business rules and scenario effects, giving analysts
a fresh foundation for original portfolio work.

This repository is Stage 1 of a larger portfolio ecosystem. It produces files only; SQL warehouses,
dashboards, machine-learning models, applications, APIs, databases, and deployment belong in later
projects.

## Installation

Install [uv](https://docs.astral.sh/uv/), clone the repository, and run:

```bash
uv sync --extra dev
```

On a Windows machine where the default uv cache is unavailable, use a local cache:

```powershell
$env:UV_CACHE_DIR='.uv-cache'
uv sync --extra dev
```

## Generate a dataset

```bash
uv run synthetic-dataset-generator generate \
  --config config/default_config.yaml \
  --output data/output \
  --scenario baseline \
  --orders 50000 \
  --seed 42
```

PowerShell accepts the same arguments on one line. Add `--overwrite` to replace an existing package
with the same scenario, order count, and seed. Use `--scenarios` to select a different scenario YAML
file.

Add `--dirty` to create a reproducible data-cleaning exercise using the defect rates under
`data_quality` in `config/default_config.yaml`:

```bash
uv run synthetic-dataset-generator generate \
  --config config/default_config.yaml \
  --output data/output \
  --scenario baseline \
  --orders 50000 \
  --seed 42 \
  --dirty
```

Dirty packages use an `_dirty` filename suffix. The same seed, configuration, and generator version
produce the same missing days, empty orders, nulls, invalid date formats and types, and negative
values.

The command creates:

```text
data/output/ecommerce_baseline_50000_seed42/
data/output/ecommerce_baseline_50000_seed42.zip
```

The folder and ZIP contain:

```text
customers.csv                 payments.csv
sellers.csv                   shipping.csv
products.csv                  reviews.csv
seller_products.csv           calendar.csv
orders.csv                    simulation_metadata.csv
order_items.csv               data_dictionary.csv
validation_summary.json       validation_summary.md
```

`seller_products.csv` is the authoritative marketplace catalog. It connects sellers and products
through seller-specific listings, while `order_items.csv` retains `seller_product_id`, `seller_id`,
and `product_id` for convenient analysis. Every order item must resolve to one exact listing.

Dirty packages also include `dirty_data_manifest.json`. It reports requested settings and applied
counts by defect, table, and column, but deliberately omits row IDs, cell locations, and removed
dates.

Clean ZIPs are created only when every validation check passes. Dirty ZIPs are created when the
clean source passes and all configured defects survive CSV serialization; their validation status
is `expected_issues`. Unexpected generator or audit failures retain the folder for diagnosis, omit
the ZIP, and return a nonzero exit code.

## Local Streamlit Data Viewer

The optional Streamlit viewer explores datasets that the CLI has already generated. It is a
local-only project utility: it does not generate data, upload files, connect to a database, or add
anything to a public website.

Install the viewer dependencies alongside the development tools:

```bash
uv sync --extra dev --extra viewer
```

Generate a dataset first using the normal CLI command above. Generated dataset folders are detected
under `data/output/` when they contain at least `orders.csv`, `order_items.csv`, `customers.csv`,
`products.csv`, and `seller_products.csv`. Then launch the viewer from the repository root:

```bash
uv run streamlit run streamlit_app/app.py
```

The app provides overview KPIs and monthly trends, a table explorer with CSV downloads, marketplace
analysis, shipping and review relationship views, generator validation results, and a schema/data
dictionary reference. An exact alternative local dataset folder can also be entered in the sidebar.
Missing optional files produce page-level messages rather than stopping the whole app.

The viewer is not required for dataset generation. `uv sync --extra dev` and the existing CLI flow
continue to work without the optional `viewer` extra. See
[the local viewer guide](docs/streamlit_viewer.md) for architecture and metric definitions.

## Scenarios

- `baseline` — normal seasonality, seller concentration, delivery, and review behavior.
- `holiday_spike` — stronger Q4 category demand with higher shipping pressure and lower satisfaction.
- `logistics_improvement` — faster delivery, fewer late shipments, and better review outcomes.
- `seller_churn` — the highest-volume sellers deactivate during the period and demand redistributes.

Scenario parameters are visible in `config/scenarios.yaml`. The general dataset shape is controlled
by `config/default_config.yaml`, and CLI options override scenario, order count, and seed.

Catalog breadth is controlled by `simulation.min_sellers_per_product` and
`simulation.max_sellers_per_product`, defaulting to one through four sellers per product. Every
product and seller receives at least one listing; invalid combinations that cannot provide complete
coverage are rejected during configuration validation.

## Dirty-data training mode

Dirty mode is intended for data-quality profiling, ingestion hardening, SQL cleaning exercises, and
portfolio demonstrations. The default preset introduces null text attributes, missing transaction
days, inconsistent or malformed dates, text tokens in numeric and boolean fields, negative monetary
values and review scores, and order headers with no item rows. Primary keys, foreign keys, scenario
fields, metadata, and the data dictionary are protected.

Seller listings participate in dirty mode without breaking their relationships: listing prices can
be negative, listing dates can use malformed formats, and listing active flags can contain invalid
types. Listing identifiers and seller/product foreign keys remain protected.

Cell-level rates are applied independently to non-overlapping field groups. Any positive rate affects
at least one eligible value without exceeding the available population. Missing days remove the
orders and dependent facts for selected active dates while retaining the matching calendar rows.
Empty orders retain their headers, payments, and shipping records but lose every order-item row.

`data_dictionary.csv` continues to describe the intended clean schema. Dirty values violate that
schema by design and are not silently repaired by the generator or local viewer.

## Portfolio uses

- Build a dimensional SQL model and analyze revenue, retention, seller concentration, catalog
  breadth, listing-price dispersion, and cohorts.
- Create a BI dashboard comparing regions, categories, fulfillment outcomes, and scenarios.
- Model late-delivery risk or customer satisfaction using transparent synthetic drivers.
- Practice data-quality checks, data dictionaries, ingestion, and stakeholder documentation.

See [the user guide](docs/user_guide.md), [methodology](docs/methodology.md), and
[data dictionary](docs/data_dictionary.md) for details.

## Development

```bash
uv run pytest
uv run ruff check .
```

Generation is deterministic for analytical tables when configuration and seed are unchanged.
`generated_at` and the corresponding run identifier intentionally reflect the actual run time.

## License

The Python source code and project documentation are available under the
[MIT License](LICENSE).

The bundled synthetic sample dataset is dedicated to the public domain under
[CC0 1.0 Universal](data/sample_output/LICENSE-DATA). It may be copied, modified,
redistributed, and used commercially without requesting permission.

The project does not impose a license on datasets you generate yourself. You are
responsible for choosing appropriate terms for your generated outputs and for any
third-party material you add.

## Roadmap

Stage 1 focuses on robust local CSV generation and validation. Possible later improvements include
Parquet export, additional documented scenarios, and larger performance profiles. SQL analytics,
BI, and machine learning will remain separate projects.
