"""Simulation metadata and data-dictionary generation."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from synthetic_dataset_generator.config import GeneratorConfig
from synthetic_dataset_generator.schemas import SCHEMA_REGISTRY, columns_for

DISCLAIMER = (
    "Fully synthetic data for education, analytics practice, portfolio projects, SQL modeling, "
    "dashboard development, and machine learning experiments. It contains no real customers, "
    "sellers, orders, companies, or performance and must not be used as real market data or for "
    "operational decisions."
)


def generate_metadata(config: GeneratorConfig, tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    generated_at = datetime.now(UTC).replace(microsecond=0)
    run_id = (
        f"simulation_run_{generated_at:%Y%m%d_%H%M%S}_"
        f"{config.simulation.scenario}_seed{config.dataset.random_seed}"
    )
    row = {
        "simulation_run_id": run_id,
        "dataset_name": config.dataset.name,
        "domain": config.dataset.domain,
        "scenario_name": config.simulation.scenario,
        "random_seed": config.dataset.random_seed,
        "generated_at": generated_at,
        "start_date": config.dataset.start_date,
        "end_date": config.dataset.end_date,
        "number_of_orders": len(tables["orders"]),
        "number_of_customers": len(tables["customers"]),
        "number_of_sellers": len(tables["sellers"]),
        "number_of_products": len(tables["products"]),
        "currency": config.business_rules.currency,
        "disclaimer": DISCLAIMER,
    }
    return pd.DataFrame([row], columns=columns_for("simulation_metadata"))


def generate_data_dictionary(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for table_name, columns in SCHEMA_REGISTRY.items():
        table = tables.get(table_name)
        for column_name, spec in columns.items():
            example: object = ""
            if table is not None and not table.empty and column_name in table:
                non_null = table[column_name].dropna()
                if not non_null.empty:
                    example = non_null.iloc[0]
            rows.append(
                {
                    "table_name": table_name,
                    "column_name": column_name,
                    "data_type": spec.data_type,
                    "description": spec.description,
                    "example_value": example,
                    "nullable": spec.nullable,
                }
            )
    return pd.DataFrame(rows, columns=columns_for("data_dictionary"))
