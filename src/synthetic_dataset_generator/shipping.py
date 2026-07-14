"""Shipping outcomes and fulfillment timestamps."""

from __future__ import annotations

import pandas as pd

from synthetic_dataset_generator.config import GeneratorConfig, ScenarioConfig
from synthetic_dataset_generator.geography import distance_band, shipping_zone
from synthetic_dataset_generator.random import rng_for
from synthetic_dataset_generator.schemas import columns_for

BASE_DAYS = {"same_state": 3, "same_region": 5, "cross_region": 7, "remote": 10}
BASE_DELAY_PROBABILITY = {
    "same_state": 0.08,
    "same_region": 0.11,
    "cross_region": 0.15,
    "remote": 0.22,
}


def generate_shipping(
    config: GeneratorConfig,
    scenario: ScenarioConfig,
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    order_sellers: pd.DataFrame,
    customers: pd.DataFrame,
    sellers: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = rng_for(config.dataset.random_seed, "shipping")
    customer_lookup = customers.set_index("customer_id")
    seller_lookup = sellers.set_index("seller_id")
    seller_by_order = order_sellers.set_index("order_id")["seller_id"]
    shipping_totals = order_items.groupby("order_id")["shipping_cost_usd"].sum()
    updated = orders.copy()
    rows: list[dict[str, object]] = []
    end_timestamp = pd.Timestamp(config.dataset.end_date) + pd.Timedelta(hours=23, minutes=59)
    for index, order in updated.iterrows():
        seller = seller_lookup.loc[seller_by_order.loc[order["order_id"]]]
        customer = customer_lookup.loc[order["customer_id"]]
        band = distance_band(str(seller["seller_state"]), str(customer["customer_state"]))
        capacity_penalty = round((1 - float(seller["seller_fulfillment_capacity"])) * 3)
        holiday_penalty = 1 if bool(order["is_holiday_period"]) else 0
        estimated_days = max(
            1,
            round(
                (BASE_DAYS[band] + capacity_penalty + holiday_penalty)
                * scenario.transit_days_multiplier
            ),
        )
        delay_probability = BASE_DELAY_PROBABILITY[band] * scenario.delay_probability_multiplier
        if bool(order["is_holiday_period"]):
            delay_probability *= 1.35
        if not config.business_rules.allow_late_deliveries:
            delay_probability = 0
        delayed = rng.random() < min(0.85, delay_probability)
        delay_days = int(rng.integers(1, 6)) if delayed else int(rng.choice([-1, 0, 0, 0]))
        actual_days = max(1, estimated_days + delay_days)
        purchase = pd.Timestamp(order["order_purchase_timestamp"])
        approved = order["order_approved_at"]
        estimated_date = min(
            purchase.normalize() + pd.Timedelta(days=estimated_days), end_timestamp.normalize()
        )
        status = str(order["order_status"])
        delivered_at = purchase + pd.Timedelta(days=actual_days, hours=int(rng.integers(8, 18)))
        if status == "delivered" and delivered_at > end_timestamp:
            status = "shipped"
            updated.at[index, "order_status"] = status
        carrier_at = pd.NaT
        actual_value: int | None = None
        delay_value: int | None = None
        late = False
        if status in {"delivered", "shipped"}:
            approval_value = pd.Timestamp(approved) if pd.notna(approved) else purchase
            carrier_at = min(
                approval_value + pd.Timedelta(days=int(rng.integers(1, 4))),
                end_timestamp,
            )
        if status == "delivered":
            carrier_at = min(carrier_at, delivered_at - pd.Timedelta(hours=1))
            actual_value = actual_days
            delay_value = max(0, actual_days - estimated_days)
            late = delay_value > 0
            updated.at[index, "order_delivered_customer_date"] = delivered_at
        updated.at[index, "order_estimated_delivery_date"] = estimated_date
        updated.at[index, "order_delivered_carrier_date"] = carrier_at
        rows.append(
            {
                "order_id": order["order_id"],
                "seller_state": seller["seller_state"],
                "customer_state": customer["customer_state"],
                "seller_region": seller["seller_region"],
                "customer_region": customer["customer_region"],
                "shipping_distance_band": band,
                "shipping_zone": shipping_zone(band),
                "estimated_delivery_days": estimated_days,
                "actual_delivery_days": actual_value,
                "delivery_delay_days": delay_value,
                "late_delivery_flag": late,
                "shipping_cost_usd": round(float(shipping_totals.loc[order["order_id"]]), 2),
                "scenario_name": config.simulation.scenario,
            }
        )
    return pd.DataFrame(rows, columns=columns_for("shipping")), updated
