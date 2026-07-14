"""Customer dimension generation."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from synthetic_dataset_generator.constants import (
    CUSTOMER_LIFECYCLE_STAGES,
    CUSTOMER_SEGMENTS,
    CUSTOMER_STATE_WEIGHTS,
    STATE_REGIONS,
    state_probabilities,
)
from synthetic_dataset_generator.geography import city_for_state, zip_prefix
from synthetic_dataset_generator.random import rng_for
from synthetic_dataset_generator.schemas import columns_for

SEGMENT_PROPENSITY = {
    "one_time_buyer": 0.35,
    "occasional_buyer": 0.85,
    "high_value_buyer": 2.30,
    "discount_sensitive": 1.15,
    "category_loyal": 1.45,
}


def generate_customers(
    count: int, start_date: date, end_date: date, seed: int
) -> tuple[pd.DataFrame, np.ndarray]:
    rng = rng_for(seed, "customers")
    states, probabilities = state_probabilities(CUSTOMER_STATE_WEIGHTS)
    selected_states = rng.choice(states, size=count, p=probabilities)
    segments = rng.choice(CUSTOMER_SEGMENTS, size=count, p=[0.38, 0.28, 0.10, 0.14, 0.10])
    lifecycle = rng.choice(CUSTOMER_LIFECYCLE_STAGES, size=count, p=[0.20, 0.40, 0.28, 0.12])
    period_days = (end_date - start_date).days
    creation_window = max(1, min(180, period_days // 4))
    created_offsets = np.where(
        rng.random(count) < 0.78, 0, rng.integers(0, creation_window + 1, count)
    )
    created = pd.Timestamp(start_date) + pd.to_timedelta(created_offsets, unit="D")
    frame = pd.DataFrame(
        {
            "customer_id": [f"customer_{index:06d}" for index in range(1, count + 1)],
            "customer_unique_id": [f"customer_unique_{index:06d}" for index in range(1, count + 1)],
            "customer_state": selected_states,
            "customer_city": [city_for_state(state, rng) for state in selected_states],
            "customer_region": [STATE_REGIONS[state] for state in selected_states],
            "customer_zip_prefix": [zip_prefix(rng) for _ in range(count)],
            "customer_segment": segments,
            "customer_lifecycle_stage": lifecycle,
            "created_at": created,
        }
    )
    propensities = np.array([SEGMENT_PROPENSITY[str(segment)] for segment in segments])
    propensities *= rng.lognormal(mean=0, sigma=0.35, size=count)
    propensities /= propensities.sum()
    return frame[columns_for("customers")], propensities
