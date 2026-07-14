"""Payment generation and exact order-total reconciliation."""

from __future__ import annotations

import pandas as pd

from synthetic_dataset_generator.config import GeneratorConfig
from synthetic_dataset_generator.constants import PAYMENT_TYPES
from synthetic_dataset_generator.random import rng_for
from synthetic_dataset_generator.schemas import columns_for


def generate_payments(config: GeneratorConfig, order_items: pd.DataFrame) -> pd.DataFrame:
    rng = rng_for(config.dataset.random_seed, "payments")
    totals = order_items.groupby("order_id")["item_total_usd"].sum().round(2)
    rows: list[dict[str, object]] = []
    probabilities = [0.48, 0.13, 0.27, 0.08, 0.04]
    for order_id, total in totals.items():
        payment_count = 2 if rng.random() < 0.08 and total >= 20 else 1
        if payment_count == 1:
            values = [float(total)]
        else:
            first = round(float(total) * float(rng.uniform(0.2, 0.75)), 2)
            values = [first, round(float(total) - first, 2)]
        methods = rng.choice(PAYMENT_TYPES, size=payment_count, p=probabilities, replace=False)
        for sequence, (method, value) in enumerate(zip(methods, values, strict=True), start=1):
            installments = (
                int(rng.integers(1, min(12, max(2, round(value / 40))) + 1))
                if method == "credit_card"
                else 1
            )
            rows.append(
                {
                    "order_id": order_id,
                    "payment_sequential": sequence,
                    "payment_type": method,
                    "payment_installments": installments,
                    "payment_value_usd": value,
                    "scenario_name": config.simulation.scenario,
                }
            )
    return pd.DataFrame(rows, columns=columns_for("payments"))
