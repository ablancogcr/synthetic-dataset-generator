from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from synthetic_dataset_generator.config import GeneratorConfig, ScenarioConfig
from synthetic_dataset_generator.generator import DatasetGenerator


def test_keys_relationships_dates_and_money(
    config_factory: Callable[..., GeneratorConfig], scenarios: dict[str, ScenarioConfig]
) -> None:
    tables = DatasetGenerator(config_factory(orders=260), scenarios["baseline"]).generate().tables
    assert tables["orders"]["order_id"].is_unique
    assert not tables["order_items"].duplicated(["order_id", "order_item_id"]).any()
    assert set(tables["orders"]["customer_id"]) <= set(tables["customers"]["customer_id"])
    assert set(tables["order_items"]["product_id"]) <= set(tables["products"]["product_id"])
    assert set(tables["order_items"]["seller_id"]) <= set(tables["sellers"]["seller_id"])

    delivered = tables["orders"].query("order_status == 'delivered'")
    assert (
        pd.to_datetime(delivered["order_purchase_timestamp"])
        <= pd.to_datetime(delivered["order_approved_at"])
    ).all()
    assert (
        pd.to_datetime(delivered["order_approved_at"])
        <= pd.to_datetime(delivered["order_delivered_carrier_date"])
    ).all()
    assert (
        pd.to_datetime(delivered["order_delivered_carrier_date"])
        <= pd.to_datetime(delivered["order_delivered_customer_date"])
    ).all()

    item_totals = tables["order_items"].groupby("order_id")["item_total_usd"].sum().round(2)
    payment_totals = tables["payments"].groupby("order_id")["payment_value_usd"].sum().round(2)
    pd.testing.assert_series_equal(item_totals, payment_totals, check_names=False)


def test_each_order_uses_one_seller(
    config_factory: Callable[..., GeneratorConfig], scenarios: dict[str, ScenarioConfig]
) -> None:
    items = (
        DatasetGenerator(config_factory(orders=200), scenarios["baseline"])
        .generate()
        .tables["order_items"]
    )
    assert items.groupby("order_id")["seller_id"].nunique().max() == 1
