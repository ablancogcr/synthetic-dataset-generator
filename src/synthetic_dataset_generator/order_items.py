"""Order-item generation with one seller per order."""

from __future__ import annotations

import numpy as np
import pandas as pd

from synthetic_dataset_generator.config import GeneratorConfig, ScenarioConfig
from synthetic_dataset_generator.geography import distance_band
from synthetic_dataset_generator.random import rng_for
from synthetic_dataset_generator.schemas import columns_for
from synthetic_dataset_generator.sellers import SellerPopulation

BAND_SURCHARGE = {"same_state": 1.0, "same_region": 2.2, "cross_region": 4.8, "remote": 9.5}


def _seller_indices(
    orders: pd.DataFrame,
    sellers: SellerPopulation,
    rng: np.random.Generator,
) -> np.ndarray:
    count = len(orders)
    indices = np.empty(count, dtype=int)
    if sellers.churn_date is None:
        return rng.choice(len(sellers.frame), size=count, p=sellers.weights)
    before = pd.to_datetime(orders["order_purchase_timestamp"]) < sellers.churn_date
    indices[before.to_numpy()] = rng.choice(
        int(len(sellers.frame)), size=int(before.sum()), p=sellers.weights
    )
    active_weights = sellers.weights * sellers.frame["seller_active_flag"].to_numpy(dtype=float)
    active_weights /= active_weights.sum()
    indices[(~before).to_numpy()] = rng.choice(
        len(sellers.frame), size=int((~before).sum()), p=active_weights
    )
    return indices


def generate_order_items(
    config: GeneratorConfig,
    scenario: ScenarioConfig,
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    sellers: SellerPopulation,
    products: pd.DataFrame,
    seller_products: pd.DataFrame,
    product_weights: np.ndarray,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = rng_for(config.dataset.random_seed, "order_items")
    seller_indices = _seller_indices(orders, sellers, rng)
    seller_ids = sellers.frame.iloc[seller_indices]["seller_id"].to_numpy()
    order_sellers = pd.DataFrame({"order_id": orders["order_id"], "seller_id": seller_ids})
    customer_lookup = customers.set_index("customer_id")
    seller_lookup = sellers.frame.set_index("seller_id")
    product_lookup = products.set_index("product_id")
    product_weight_lookup = dict(zip(products["product_id"], product_weights, strict=True))
    listings_by_seller = {
        str(seller_id): frame.reset_index(drop=True)
        for seller_id, frame in seller_products.groupby("seller_id", sort=False)
    }
    item_counts = np.clip(
        rng.geometric(0.58, len(orders)),
        config.simulation.min_items_per_order,
        config.simulation.max_items_per_order,
    )
    rows: list[dict[str, object]] = []
    for order_position, order in orders.iterrows():
        seller_id = seller_ids[order_position]
        seller = seller_lookup.loc[seller_id]
        customer = customer_lookup.loc[order["customer_id"]]
        band = distance_band(str(seller["seller_state"]), str(customer["customer_state"]))
        listings = listings_by_seller[str(seller_id)]
        product_probabilities = np.array(
            [product_weight_lookup[str(product_id)] for product_id in listings["product_id"]],
            dtype=float,
        )
        if bool(order["is_holiday_period"]):
            categories = listings["product_id"].map(product_lookup["product_category"])
            for category, multiplier in scenario.category_multipliers.items():
                product_probabilities[categories.eq(category).to_numpy()] *= multiplier
        product_probabilities /= product_probabilities.sum()
        selected = rng.choice(
            len(listings), size=int(item_counts[order_position]), p=product_probabilities
        )
        for item_sequence, listing_index in enumerate(selected, start=1):
            listing = listings.iloc[int(listing_index)]
            product = product_lookup.loc[listing["product_id"]]
            price_factor = rng.lognormal(mean=0, sigma=0.10)
            if bool(order["is_promotion_period"]):
                price_factor *= rng.uniform(0.82, 0.96)
            price = max(1.0, float(listing["seller_price_usd"]) * price_factor)
            volumetric_kg = (
                float(product["product_length_cm"])
                * float(product["product_width_cm"])
                * float(product["product_height_cm"])
                / 5000
            )
            billable_kg = max(float(product["product_weight_g"]) / 1000, volumetric_kg)
            shipping = 2.75 + 0.72 * billable_kg + BAND_SURCHARGE[band]
            shipping *= scenario.shipping_cost_multiplier
            if bool(order["is_holiday_period"]):
                shipping *= 1.08
            shipping *= rng.uniform(0.92, 1.08)
            price = round(price, 2)
            shipping = round(max(0.0, shipping), 2)
            rows.append(
                {
                    "order_id": order["order_id"],
                    "order_item_id": item_sequence,
                    "seller_product_id": listing["seller_product_id"],
                    "product_id": listing["product_id"],
                    "seller_id": seller_id,
                    "item_price_usd": price,
                    "shipping_cost_usd": shipping,
                    "item_total_usd": round(price + shipping, 2),
                    "scenario_name": config.simulation.scenario,
                }
            )
    return pd.DataFrame(rows, columns=columns_for("order_items")), order_sellers
