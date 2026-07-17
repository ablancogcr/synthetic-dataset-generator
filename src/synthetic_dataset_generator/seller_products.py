"""Seller-product marketplace catalog generation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from synthetic_dataset_generator.config import GeneratorConfig
from synthetic_dataset_generator.random import rng_for
from synthetic_dataset_generator.schemas import columns_for
from synthetic_dataset_generator.sellers import SellerPopulation


def _listing_counts(config: GeneratorConfig, rng: np.random.Generator) -> np.ndarray:
    simulation = config.simulation
    minimum = simulation.min_sellers_per_product
    maximum = simulation.max_sellers_per_product
    span = maximum - minimum
    extras = np.minimum(rng.geometric(0.55, simulation.product_count) - 1, span)
    counts = minimum + extras

    shortfall = simulation.seller_count - int(counts.sum())
    while shortfall > 0:
        candidates = np.flatnonzero(counts < maximum)
        for product_index in rng.permutation(candidates):
            counts[int(product_index)] += 1
            shortfall -= 1
            if shortfall == 0:
                break
    return counts.astype(int)


def generate_seller_products(
    config: GeneratorConfig,
    sellers: SellerPopulation,
    products: pd.DataFrame,
) -> pd.DataFrame:
    """Generate a deterministic many-to-many seller catalog."""
    rng = rng_for(config.dataset.random_seed, "seller_products")
    counts = _listing_counts(config, rng)
    product_slots = np.repeat(np.arange(len(products)), counts)
    coverage_slots = rng.choice(
        len(product_slots), size=len(sellers.frame), replace=False
    )
    shuffled_sellers = rng.permutation(len(sellers.frame))

    assignments: list[set[int]] = [set() for _ in range(len(products))]
    for slot, seller_index in zip(coverage_slots, shuffled_sellers, strict=True):
        assignments[int(product_slots[int(slot)])].add(int(seller_index))

    for product_index, target_count in enumerate(counts):
        assigned = assignments[product_index]
        needed = int(target_count) - len(assigned)
        if needed <= 0:
            continue
        probabilities = sellers.weights.copy()
        if assigned:
            probabilities[np.fromiter(assigned, dtype=int)] = 0
        probabilities /= probabilities.sum()
        selected = rng.choice(
            len(sellers.frame), size=needed, replace=False, p=probabilities
        )
        assigned.update(int(index) for index in np.atleast_1d(selected))

    rows: list[dict[str, object]] = []
    for product_index, seller_indices in enumerate(assignments):
        product = products.iloc[product_index]
        for seller_index in sorted(seller_indices):
            seller = sellers.frame.iloc[seller_index]
            price = max(
                1.0,
                float(product["product_price_base_usd"])
                * float(rng.lognormal(0, 0.08))
                * (0.95 + 0.10 * float(seller["seller_quality_score"])),
            )
            created_at = max(
                pd.Timestamp(product["created_at"]), pd.Timestamp(seller["created_at"])
            )
            rows.append(
                {
                    "seller_product_id": f"seller_product_{len(rows) + 1:07d}",
                    "seller_id": seller["seller_id"],
                    "product_id": product["product_id"],
                    "seller_price_usd": round(price, 2),
                    "listing_created_at": created_at,
                    "listing_active_flag": bool(seller["seller_active_flag"]),
                    "scenario_name": config.simulation.scenario,
                }
            )
    return pd.DataFrame(rows, columns=columns_for("seller_products"))
