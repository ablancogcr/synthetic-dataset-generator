"""Product dimension generation."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from synthetic_dataset_generator.constants import CATEGORIES, CATEGORY_PROFILES
from synthetic_dataset_generator.random import rng_for
from synthetic_dataset_generator.schemas import columns_for


def generate_products(count: int, start_date: date, seed: int) -> tuple[pd.DataFrame, np.ndarray]:
    rng = rng_for(seed, "products")
    categories = rng.choice(CATEGORIES, size=count)
    rows: list[dict[str, object]] = []
    popularity = rng.lognormal(mean=0, sigma=0.75, size=count)
    for index, category in enumerate(categories, start=1):
        median_price, sigma, median_weight, names = CATEGORY_PROFILES[str(category)]
        price = float(np.clip(rng.lognormal(np.log(median_price), sigma), 4.5, 2500))
        weight = int(np.clip(rng.lognormal(np.log(median_weight), 0.55), 50, 30_000))
        volume_scale = max(4.0, (weight / 18) ** (1 / 3))
        length = float(np.clip(rng.normal(volume_scale * 1.6, volume_scale * 0.25), 4, 180))
        width = float(np.clip(rng.normal(volume_scale * 1.25, volume_scale * 0.20), 3, 120))
        height = float(np.clip(rng.normal(volume_scale, volume_scale * 0.18), 2, 100))
        rows.append(
            {
                "product_id": f"product_{index:06d}",
                "product_category": category,
                "product_name": f"{rng.choice(names)} {index:04d}",
                "product_weight_g": weight,
                "product_length_cm": round(length, 1),
                "product_height_cm": round(height, 1),
                "product_width_cm": round(width, 1),
                "product_price_base_usd": round(price, 2),
                "created_at": pd.Timestamp(start_date),
            }
        )
    frame = pd.DataFrame(rows, columns=columns_for("products"))
    popularity /= popularity.sum()
    return frame, popularity
