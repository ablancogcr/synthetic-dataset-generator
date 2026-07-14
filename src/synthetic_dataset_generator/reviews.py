"""Review generation driven by fulfillment experience."""

from __future__ import annotations

import numpy as np
import pandas as pd

from synthetic_dataset_generator.config import GeneratorConfig, ScenarioConfig
from synthetic_dataset_generator.random import rng_for
from synthetic_dataset_generator.schemas import columns_for


def generate_reviews(
    config: GeneratorConfig,
    scenario: ScenarioConfig,
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    shipping: pd.DataFrame,
    order_sellers: pd.DataFrame,
    sellers: pd.DataFrame,
) -> pd.DataFrame:
    rng = rng_for(config.dataset.random_seed, "reviews")
    delivered = orders.loc[orders["order_status"] == "delivered"].copy()
    if delivered.empty:
        return pd.DataFrame(columns=columns_for("reviews"))
    response_rate = 0.72 if config.business_rules.allow_missing_reviews else 1.0
    delivered = delivered.loc[rng.random(len(delivered)) < response_rate]
    shipping_lookup = shipping.set_index("order_id")
    seller_by_order = order_sellers.set_index("order_id")["seller_id"]
    quality = sellers.set_index("seller_id")["seller_quality_score"]
    order_totals = order_items.groupby("order_id")["item_total_usd"].sum()
    shipping_totals = order_items.groupby("order_id")["shipping_cost_usd"].sum()
    rows: list[dict[str, object]] = []
    end_date = pd.Timestamp(config.dataset.end_date)
    end_timestamp = end_date + pd.Timedelta(hours=23, minutes=59)
    for _, order in delivered.iterrows():
        order_id = str(order["order_id"])
        delivered_at = pd.Timestamp(order["order_delivered_customer_date"])
        review_date = delivered_at.normalize() + pd.Timedelta(days=int(rng.integers(1, 8)))
        if review_date > end_date:
            continue
        shipment = shipping_lookup.loc[order_id]
        seller_quality = float(quality.loc[seller_by_order.loc[order_id]])
        shipping_ratio = float(shipping_totals.loc[order_id] / order_totals.loc[order_id])
        latent = (
            4.15
            + 1.35 * (seller_quality - 0.75)
            - 0.42 * float(shipment["delivery_delay_days"] or 0)
            - 1.15 * max(0, shipping_ratio - 0.15)
            + scenario.review_score_shift
            + rng.normal(0, 0.65)
        )
        score = int(np.clip(round(latent), 1, 5))
        sentiment = "negative" if score <= 2 else "neutral" if score == 3 else "positive"
        answer_timestamp = min(
            review_date + pd.Timedelta(hours=int(rng.integers(8, 73))), end_timestamp
        )
        rows.append(
            {
                "review_id": f"review_{len(rows) + 1:07d}",
                "order_id": order_id,
                "review_score": score,
                "review_creation_date": review_date,
                "review_answer_timestamp": answer_timestamp,
                "review_sentiment_label": sentiment,
                "satisfaction_risk_flag": score <= 2,
                "scenario_name": config.simulation.scenario,
            }
        )
    return pd.DataFrame(rows, columns=columns_for("reviews"))
