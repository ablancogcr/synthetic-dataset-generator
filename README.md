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
orders.csv                    calendar.csv
order_items.csv               simulation_metadata.csv
data_dictionary.csv           validation_summary.json
validation_summary.md
```

The ZIP is created only after every validation check passes. A failed run retains its folder and
validation reports for diagnosis and returns a nonzero exit code.

## Scenarios

- `baseline` — normal seasonality, seller concentration, delivery, and review behavior.
- `holiday_spike` — stronger Q4 category demand with higher shipping pressure and lower satisfaction.
- `logistics_improvement` — faster delivery, fewer late shipments, and better review outcomes.
- `seller_churn` — the highest-volume sellers deactivate during the period and demand redistributes.

Scenario parameters are visible in `config/scenarios.yaml`. The general dataset shape is controlled
by `config/default_config.yaml`, and CLI options override scenario, order count, and seed.

## Portfolio uses

- Build a dimensional SQL model and analyze revenue, retention, seller concentration, and cohorts.
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
