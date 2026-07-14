# Baseline Sample Dataset

This directory contains the complete 10,000-order baseline sample generated with seed 42 and the
default 2024-01-01 through 2026-12-31 date range.

The data is fully synthetic and is provided only for education, analytics practice, portfolio work,
SQL modeling, dashboards, and machine-learning experiments. It is not real market or company data.

The bundled sample data is dedicated to the public domain under
[CC0 1.0 Universal](LICENSE-DATA).

Recreate it from the repository root:

```bash
uv run synthetic-dataset-generator generate --config config/default_config.yaml --output data/sample_output --scenario baseline --orders 10000 --seed 42 --overwrite
```
