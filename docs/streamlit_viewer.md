# Local Streamlit Dataset App

The Streamlit app is a local utility for generating and inspecting Synthetic Dataset Generator CSV
packages. Its Generate dataset page uses the same Python workflow as the CLI. Analytical pages do
not write back to generated datasets, use a database, upload files, or include deployment
configuration.

## Run locally

Install the optional viewer and development dependencies:

```bash
uv sync --extra dev --extra viewer
```

Start the app from the repository root:

```bash
uv run streamlit run streamlit_app/app.py
```

The default discovery root is `data/output/`. The sidebar also accepts the exact path to another
local generated dataset folder. That folder is inspected directly; the viewer does not recursively
search unrelated filesystem locations.

## Generation

Generate dataset exposes only the current CLI command options:

- Config YAML path (`--config`)
- Scenarios YAML path (`--scenarios`)
- Output directory (`--output`)
- Scenario (`--scenario`)
- Order count (`--orders`)
- Random seed (`--seed`)
- Dirty-data mode (`--dirty`)
- Overwrite (`--overwrite`)

The form defaults to the documented CLI values. It does not edit or persist YAML values such as
entity counts, date ranges, business rules, or dirty-data rates. The shared generation workflow
emits the CLI progress and validation messages into the page, creates the same folder and ZIP
package, and makes the ZIP available for download when one exists.

Packages written outside `data/output/` are retained as the app's generated dataset selection for
the browser session. The sidebar can still be used to choose another local package or enter a
different exact folder manually.

## Configuration

**Configuration** displays the repository's two generator YAML files: `config/default_config.yaml`
and `config/scenarios.yaml`. It renders controls only for parameters already present in each file;
the page has no way to add or remove parameters or scenarios.

Before writing, the page validates the full candidate file with the same Pydantic schemas used by
the generator, including cross-field constraints such as date ranges and item/seller limits. An
invalid edit is shown as an error and leaves the source YAML file unchanged. Successful writes are
atomic, so an interrupted write does not leave a partial configuration file.

## Architecture

`streamlit_app/app.py` configures navigation, discovers datasets, and owns shared selection state.
Direct page scripts live in `streamlit_app/app_pages/`. The CLI and Generate dataset page share the
generation workflow in `synthetic_dataset_generator.workflow`, while reusable filesystem, loading,
calculation, validation, and chart logic lives in `streamlit_app/utils/` so it can be tested without
browser UI automation.

CSV loading uses `st.cache_data` with the resolved file path and nanosecond modification time as
cache inputs. Regenerating a file therefore creates a fresh cache entry. Reusable aggregations and
CSV download serialization are also cached with bounded entry counts.

## Dataset discovery

A selectable dataset directory must contain:

- `orders.csv`
- `order_items.csv`
- `seller_products.csv`
- `customers.csv`
- `products.csv`

Discovery checks directories immediately below `data/output/` based on their contents, not their
names. Directories that contain generator artifacts but lack a core table are listed as incomplete.
ZIP files are not opened; select their extracted dataset directory instead.

`simulation_metadata.csv`, when present, supplies the sidebar scenario, configured order count,
date range, random seed, and data-quality mode. The viewer does not infer these values from a directory name when
metadata exists.

## Pages

- **Generate dataset** runs the CLI-equivalent local generator, shows its progress and validation
  output, and downloads the generated ZIP package.
- **Configuration** views and edits only existing keys in the local default and scenario YAML files,
  validates the complete candidate configuration, and saves only valid values.
- **Overview** shows entity counts, revenue KPIs, delivery/review KPIs, monthly trends, and order
  statuses.
- **Data explorer** previews any available CSV, shows columns and pandas data types, applies a
  simple text search and sorting, limits rendered rows, and downloads the full selected table.
- **Marketplace analysis** summarizes monthly performance, categories, seller concentration,
  customer geography, and payment records.
- **Shipping and reviews** compares delivery performance across distance bands and shows observed
  review/delivery relationships without making causal claims.
- **Data quality** renders the generator's existing JSON and Markdown validation summaries,
  distinguishes expected dirty issues from unexpected failures, and displays counts from the dirty
  manifest. It does not create a separate validation engine.
- **Schema** reports table dimensions, pandas data types, documented primary keys, foreign-key
  relationships, including the seller-product listing bridge, and `data_dictionary.csv` content.

## Metric definitions

- **Product revenue:** sum of `item_price_usd` in `order_items.csv`.
- **Shipping revenue:** sum of `shipping_cost_usd` in `order_items.csv`.
- **Total order value:** sum of `item_total_usd` in `order_items.csv`.
- **Average order value:** total order value divided by distinct `order_id` values in `orders.csv`.
- **Monthly order count:** distinct orders grouped by parsed `order_purchase_timestamp` month.
- **Category order count:** distinct orders containing at least one item in a category. One order may
  appear in more than one category, so category counts are not additive.
- **Seller revenue concentration:** top seller product revenue divided by total item-level product
  revenue. Revenue is aggregated before seller attributes are joined.
- **Late delivery rate:** mean of `late_delivery_flag` in `shipping.csv`.
- **Satisfaction risk rate:** mean of `satisfaction_risk_flag` among available reviews.
- **Shipping cost by distance band:** average order-level `shipping_cost_usd` from `shipping.csv`.

Payment summaries show payment rows, distinct orders, and payment value separately because an order
can contain multiple payment records. Shipping revenue is never added from both `order_items.csv`
and `shipping.csv` in the same metric.

## Expected and optional files

The viewer can list every CSV it finds. Full coverage uses the generator's standard output:
`customers.csv`, `sellers.csv`, `products.csv`, `seller_products.csv`, `orders.csv`,
`order_items.csv`, `payments.csv`,
`shipping.csv`, `reviews.csv`, `calendar.csv`, `simulation_metadata.csv`, and
`data_dictionary.csv`, plus `validation_summary.json` and `validation_summary.md`.
Dirty packages additionally include `dirty_data_manifest.json`.

Missing optional files disable only the affected metadata, chart, validation, or dictionary view.
Missing core files make a directory incomplete and prevent selection. CSV parsing and validation
JSON errors are reported in the UI with the failing filename.

Dirty packages display a warning on every page. The viewer never writes back to a source CSV. Some
analytical metrics defensively coerce invalid numeric or date cells and may exclude them from a chart;
use Data explorer to inspect the unchanged raw values.

## Adding a view

Add a direct page script under `streamlit_app/app_pages/`, register it with `st.Page` in
`streamlit_app/app.py`, and keep the page focused on rendering. Put calculations used by more than
one page in `streamlit_app/utils/metrics.py`, file access in the loading helpers, and repeated Plotly
formatting in `streamlit_app/utils/charts.py`. Add non-UI tests for new discovery, loading, or metric
logic in `tests/`.
