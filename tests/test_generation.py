from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from synthetic_dataset_generator.config import GeneratorConfig, ScenarioConfig
from synthetic_dataset_generator.generator import DatasetGenerator
from synthetic_dataset_generator.schemas import SCHEMA_REGISTRY


def test_generation_produces_declared_tables(
    config_factory: Callable[..., GeneratorConfig], scenarios: dict[str, ScenarioConfig]
) -> None:
    config = config_factory(orders=180)
    dataset = DatasetGenerator(config, scenarios["baseline"]).generate()
    assert set(dataset.tables) == set(SCHEMA_REGISTRY)
    for name, schema in SCHEMA_REGISTRY.items():
        assert list(dataset.tables[name].columns) == list(schema)
    assert len(dataset.tables["orders"]) == 180
    assert len(dataset.tables["shipping"]) == 180
    assert len(dataset.tables["order_items"]) >= 180
    assert len(dataset.tables["calendar"]) == 1096


def test_fixed_seed_reproduces_analytical_tables(
    config_factory: Callable[..., GeneratorConfig], scenarios: dict[str, ScenarioConfig]
) -> None:
    config = config_factory(orders=120, seed=13)
    first = DatasetGenerator(config, scenarios["baseline"]).generate()
    second = DatasetGenerator(config, scenarios["baseline"]).generate()
    for table in (
        "customers",
        "sellers",
        "products",
        "orders",
        "order_items",
        "payments",
        "shipping",
        "reviews",
        "calendar",
    ):
        pd.testing.assert_frame_equal(first.tables[table], second.tables[table])
