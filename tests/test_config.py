from __future__ import annotations

import pytest
from pydantic import ValidationError

from synthetic_dataset_generator.config import GeneratorConfig, apply_overrides, load_config


def test_default_config_loads() -> None:
    config = load_config("config/default_config.yaml")
    assert config.dataset.number_of_orders == 50_000
    assert config.simulation.scenario == "baseline"
    assert config.dataset.start_date.isoformat() == "2024-01-01"
    assert config.data_quality.mode == "clean"
    assert config.data_quality.null_rate == 0.01
    assert config.simulation.min_sellers_per_product == 1
    assert config.simulation.max_sellers_per_product == 4


def test_cli_overrides_take_precedence() -> None:
    config = apply_overrides(
        load_config("config/default_config.yaml"), scenario="seller_churn", orders=75, seed=7
    )
    assert config.simulation.scenario == "seller_churn"
    assert config.dataset.number_of_orders == 75
    assert config.dataset.random_seed == 7

    dirty = apply_overrides(config, dirty=True)
    assert dirty.data_quality.mode == "dirty"


@pytest.mark.parametrize(
    "values",
    [
        {"dataset": {"start_date": "2025-01-01", "end_date": "2024-01-01"}},
        {"dataset": {"number_of_orders": 0}},
        {"simulation": {"min_items_per_order": 5, "max_items_per_order": 2}},
        {"simulation": {"min_sellers_per_product": 4, "max_sellers_per_product": 2}},
        {"simulation": {"seller_count": 3, "max_sellers_per_product": 4}},
        {
            "simulation": {
                "seller_count": 10,
                "product_count": 2,
                "min_sellers_per_product": 1,
                "max_sellers_per_product": 4,
            }
        },
        {"simulation": {"scenario": "unknown"}},
        {"data_quality": {"null_rate": -0.1}},
        {"data_quality": {"empty_order_rate": 1.1}},
    ],
)
def test_invalid_config_is_rejected(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        GeneratorConfig.model_validate(values)
