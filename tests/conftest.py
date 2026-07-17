from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from synthetic_dataset_generator.config import GeneratorConfig, load_scenarios


@pytest.fixture
def tmp_path():
    """Provide an isolated temp directory without pytest's shared Windows temp root."""
    with TemporaryDirectory(prefix="synthetic_dataset_generator_") as directory:
        yield Path(directory)


@pytest.fixture
def config_factory() -> Callable[..., GeneratorConfig]:
    def factory(
        *,
        orders: int = 240,
        scenario: str = "baseline",
        seed: int = 42,
        customer_count: int | None = 120,
    ) -> GeneratorConfig:
        simulation = {
            "scenario": scenario,
            "seller_count": 35,
            "product_count": 90,
            "min_items_per_order": 1,
            "max_items_per_order": 4,
        }
        if customer_count is not None:
            simulation["customer_count"] = customer_count
        return GeneratorConfig.model_validate(
            {
                "dataset": {
                    "start_date": "2024-01-01",
                    "end_date": "2026-12-31",
                    "number_of_orders": orders,
                    "random_seed": seed,
                },
                "simulation": simulation,
            }
        )

    return factory


@pytest.fixture(scope="session")
def scenarios():
    return load_scenarios(Path("config/scenarios.yaml"))
