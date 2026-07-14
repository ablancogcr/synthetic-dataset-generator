"""Order shell and purchase-timing generation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from synthetic_dataset_generator.calendar import holiday_period, promotion_period
from synthetic_dataset_generator.config import GeneratorConfig, ScenarioConfig
from synthetic_dataset_generator.random import rng_for


def _date_weights(dates: pd.DatetimeIndex, scenario: ScenarioConfig) -> np.ndarray:
    weights = np.ones(len(dates), dtype=float)
    months = dates.month
    weights *= np.where(months >= 10, scenario.q4_multiplier, 1.0)
    weights *= np.where(months == 11, scenario.november_multiplier, 1.0)
    weights *= np.where(months == 12, scenario.december_multiplier, 1.0)
    weights *= np.where(dates.dayofweek >= 5, 1.06, 1.0)
    promo = promotion_period(pd.Series(dates)).to_numpy()
    weights *= np.where(promo, 1.20, 1.0)
    return weights / weights.sum()


def generate_order_shells(
    config: GeneratorConfig,
    scenario: ScenarioConfig,
    customers: pd.DataFrame,
    customer_weights: np.ndarray,
) -> pd.DataFrame:
    rng = rng_for(config.dataset.random_seed, "orders")
    count = config.dataset.number_of_orders
    dates = pd.date_range(config.dataset.start_date, config.dataset.end_date, freq="D")
    chosen_dates = rng.choice(dates.to_numpy(), size=count, p=_date_weights(dates, scenario))
    seconds = rng.integers(8 * 3600, 23 * 3600, size=count)
    purchase = pd.to_datetime(chosen_dates) + pd.to_timedelta(seconds, unit="s")

    customer_created = pd.to_datetime(customers["created_at"]).to_numpy()
    uniform_weights = np.full(len(customers), 1 / len(customers))
    repeat_rate = config.simulation.repeat_customer_rate
    selection_weights = (1 - repeat_rate) * uniform_weights + repeat_rate * customer_weights
    selection_weights /= selection_weights.sum()
    customer_indices = rng.choice(len(customers), size=count, p=selection_weights)
    invalid = customer_created[customer_indices] > purchase.to_numpy(dtype="datetime64[ns]")
    while invalid.any():
        customer_indices[invalid] = rng.choice(
            len(customers), size=int(invalid.sum()), p=selection_weights
        )
        invalid = customer_created[customer_indices] > purchase.to_numpy(dtype="datetime64[ns]")

    days_remaining = (pd.Timestamp(config.dataset.end_date) - purchase.normalize()).days
    random_values = rng.random(count)
    status = np.full(count, "delivered", dtype=object)
    recent = days_remaining <= 12
    status[(~recent) & (random_values >= 0.93) & (random_values < 0.95)] = "shipped"
    status[(~recent) & (random_values >= 0.95) & (random_values < 0.98)] = "processing"
    status[(~recent) & (random_values >= 0.98)] = "cancelled"
    status[recent & (random_values >= 0.48) & (random_values < 0.73)] = "shipped"
    status[recent & (random_values >= 0.73) & (random_values < 0.94)] = "processing"
    status[recent & (random_values >= 0.94)] = "cancelled"
    if not config.business_rules.allow_cancelled_orders:
        status[status == "cancelled"] = "processing"

    approval_hours = rng.integers(0, 25, count)
    approved = pd.Series(purchase + pd.to_timedelta(approval_hours, unit="h"))
    end_timestamp = pd.Timestamp(config.dataset.end_date) + pd.Timedelta(hours=23, minutes=59)
    approved = approved.clip(upper=end_timestamp)
    approved.loc[status == "cancelled"] = pd.NaT
    purchase_series = pd.Series(purchase)
    iso_week = purchase_series.dt.isocalendar().week.astype(int)
    return pd.DataFrame(
        {
            "order_id": [f"order_{index:07d}" for index in range(1, count + 1)],
            "customer_id": customers.iloc[customer_indices]["customer_id"].to_numpy(),
            "order_status": status,
            "order_purchase_timestamp": purchase_series,
            "order_approved_at": approved,
            "order_estimated_delivery_date": pd.NaT,
            "order_delivered_carrier_date": pd.NaT,
            "order_delivered_customer_date": pd.NaT,
            "order_year": purchase_series.dt.year,
            "order_quarter": purchase_series.dt.quarter,
            "order_month": purchase_series.dt.month,
            "order_week": iso_week,
            "order_day_of_week": purchase_series.dt.dayofweek,
            "is_weekend": purchase_series.dt.dayofweek >= 5,
            "is_holiday_period": holiday_period(purchase_series).to_numpy(),
            "is_promotion_period": promotion_period(purchase_series).to_numpy(),
            "scenario_name": config.simulation.scenario,
        }
    )
