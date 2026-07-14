from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from synthetic_dataset_generator.config import GeneratorConfig, ScenarioConfig
from synthetic_dataset_generator.generator import DatasetGenerator


def _generate(config_factory, scenarios, scenario: str):
    config = config_factory(orders=1500, scenario=scenario, seed=91)
    return DatasetGenerator(config, scenarios[scenario]).generate().tables


def test_holiday_spike_has_stronger_q4_share(
    config_factory: Callable[..., GeneratorConfig], scenarios: dict[str, ScenarioConfig]
) -> None:
    baseline = _generate(config_factory, scenarios, "baseline")
    holiday = _generate(config_factory, scenarios, "holiday_spike")
    baseline_share = baseline["orders"]["order_quarter"].eq(4).mean()
    holiday_share = holiday["orders"]["order_quarter"].eq(4).mean()
    assert holiday_share > baseline_share


def test_logistics_improvement_changes_delivery_and_reviews(
    config_factory: Callable[..., GeneratorConfig], scenarios: dict[str, ScenarioConfig]
) -> None:
    baseline = _generate(config_factory, scenarios, "baseline")
    improved = _generate(config_factory, scenarios, "logistics_improvement")
    assert (
        improved["shipping"]["late_delivery_flag"].mean()
        < baseline["shipping"]["late_delivery_flag"].mean()
    )
    assert improved["reviews"]["review_score"].mean() > baseline["reviews"]["review_score"].mean()


def test_seller_churn_blocks_post_deactivation_orders(
    config_factory: Callable[..., GeneratorConfig], scenarios: dict[str, ScenarioConfig]
) -> None:
    tables = _generate(config_factory, scenarios, "seller_churn")
    deactivated = tables["sellers"].dropna(subset=["deactivated_at"])
    assert not deactivated.empty
    joined = tables["order_items"].merge(
        tables["orders"][["order_id", "order_purchase_timestamp"]], on="order_id"
    )
    joined = joined.merge(deactivated[["seller_id", "deactivated_at"]], on="seller_id")
    assert (
        pd.to_datetime(joined["order_purchase_timestamp"])
        < pd.to_datetime(joined["deactivated_at"])
    ).all()
