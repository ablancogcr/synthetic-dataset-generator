"""Seller dimension generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from synthetic_dataset_generator.config import ScenarioConfig
from synthetic_dataset_generator.constants import (
    SELLER_STATE_WEIGHTS,
    STATE_REGIONS,
    state_probabilities,
)
from synthetic_dataset_generator.geography import city_for_state, zip_prefix
from synthetic_dataset_generator.random import rng_for
from synthetic_dataset_generator.schemas import columns_for


@dataclass
class SellerPopulation:
    frame: pd.DataFrame
    weights: np.ndarray
    churn_date: pd.Timestamp | None


def generate_sellers(
    count: int,
    start_date: date,
    end_date: date,
    seed: int,
    scenario: ScenarioConfig,
) -> SellerPopulation:
    rng = rng_for(seed, "sellers")
    states, probabilities = state_probabilities(SELLER_STATE_WEIGHTS)
    selected_states = rng.choice(states, size=count, p=probabilities)
    raw_weights = rng.pareto(1.8, count) + 0.15
    order = np.argsort(raw_weights)[::-1]
    rank = np.empty(count, dtype=int)
    rank[order] = np.arange(count)
    percentile = rank / max(1, count - 1)
    segments = np.select(
        [percentile < 0.05, percentile < 0.18, percentile < 0.45, percentile > 0.90],
        ["high_volume", "growth_seller", "premium", "at_risk"],
        default="long_tail",
    )
    quality = np.clip(rng.beta(8, 2.2, count), 0.45, 0.99)
    capacity = np.clip(
        0.35 + 0.55 * (raw_weights / raw_weights.max()) + rng.normal(0, 0.09, count), 0.2, 1.0
    )
    churn_date: pd.Timestamp | None = None
    churn_mask = np.zeros(count, dtype=bool)
    if scenario.seller_churn_fraction > 0:
        period_days = (end_date - start_date).days
        churn_date = pd.Timestamp(
            start_date + timedelta(days=round(period_days * scenario.seller_churn_at_fraction))
        )
        churn_count = max(1, round(count * scenario.seller_churn_fraction))
        churn_mask[order[:churn_count]] = True
    frame = pd.DataFrame(
        {
            "seller_id": [f"seller_{index:06d}" for index in range(1, count + 1)],
            "seller_state": selected_states,
            "seller_city": [city_for_state(state, rng) for state in selected_states],
            "seller_region": [STATE_REGIONS[state] for state in selected_states],
            "seller_zip_prefix": [zip_prefix(rng) for _ in range(count)],
            "seller_segment": segments,
            "seller_quality_score": np.round(quality, 4),
            "seller_fulfillment_capacity": np.round(capacity, 4),
            "seller_active_flag": ~churn_mask,
            "created_at": pd.Timestamp(start_date),
            "deactivated_at": [churn_date if flag else pd.NaT for flag in churn_mask],
        }
    )
    weights = raw_weights / raw_weights.sum()
    return SellerPopulation(frame[columns_for("sellers")], weights, churn_date)
