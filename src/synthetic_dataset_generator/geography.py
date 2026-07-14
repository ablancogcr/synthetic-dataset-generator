"""Synthetic US-like geography helpers."""

from __future__ import annotations

import numpy as np

from synthetic_dataset_generator.constants import STATE_CITIES, STATE_REGIONS


def city_for_state(state: str, rng: np.random.Generator) -> str:
    return str(rng.choice(STATE_CITIES[state]))


def zip_prefix(rng: np.random.Generator) -> str:
    return f"{int(rng.integers(501, 99950)):05d}"


def distance_band(seller_state: str, customer_state: str) -> str:
    if seller_state == customer_state:
        return "same_state"
    if STATE_REGIONS[seller_state] == STATE_REGIONS[customer_state]:
        return "same_region"
    if seller_state in {"AK", "HI"} or customer_state in {"AK", "HI"}:
        return "remote"
    return "cross_region"


def shipping_zone(band: str) -> str:
    return {
        "same_state": "zone_1",
        "same_region": "zone_2",
        "cross_region": "zone_3",
        "remote": "zone_4",
    }[band]
