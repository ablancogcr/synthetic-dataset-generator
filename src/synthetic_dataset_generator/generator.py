"""Dataset generation orchestration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from synthetic_dataset_generator.calendar import generate_calendar
from synthetic_dataset_generator.config import GeneratorConfig, ScenarioConfig
from synthetic_dataset_generator.customers import generate_customers
from synthetic_dataset_generator.metadata import generate_data_dictionary, generate_metadata
from synthetic_dataset_generator.order_items import generate_order_items
from synthetic_dataset_generator.orders import generate_order_shells
from synthetic_dataset_generator.payments import generate_payments
from synthetic_dataset_generator.products import generate_products
from synthetic_dataset_generator.reviews import generate_reviews
from synthetic_dataset_generator.seller_products import generate_seller_products
from synthetic_dataset_generator.sellers import generate_sellers
from synthetic_dataset_generator.shipping import generate_shipping


@dataclass
class GeneratedDataset:
    config: GeneratorConfig
    tables: dict[str, pd.DataFrame]


class DatasetGenerator:
    """Generate a complete in-memory synthetic ecommerce dataset."""

    def __init__(
        self,
        config: GeneratorConfig,
        scenario: ScenarioConfig,
        *,
        progress: Callable[[str], None] | None = None,
    ) -> None:
        self.config = config
        self.scenario = scenario
        self.progress = progress

    def _report(self, message: str) -> None:
        if self.progress is not None:
            self.progress(message)

    def generate(self) -> GeneratedDataset:
        config = self.config
        seed = config.dataset.random_seed
        self._report("Generating calendar...")
        calendar = generate_calendar(config.dataset.start_date, config.dataset.end_date)
        self._report(f"Generated calendar ({len(calendar):,} rows).")
        self._report("Generating customers...")
        customers, customer_weights = generate_customers(
            config.simulation.customer_count,
            config.dataset.start_date,
            config.dataset.end_date,
            seed,
        )
        self._report(f"Generated customers ({len(customers):,} rows).")
        self._report("Generating sellers...")
        sellers = generate_sellers(
            config.simulation.seller_count,
            config.dataset.start_date,
            config.dataset.end_date,
            seed,
            self.scenario,
        )
        self._report(f"Generated sellers ({len(sellers.frame):,} rows).")
        self._report("Generating products...")
        products, product_weights = generate_products(
            config.simulation.product_count, config.dataset.start_date, seed
        )
        self._report(f"Generated products ({len(products):,} rows).")
        self._report("Generating seller-product catalog...")
        seller_products = generate_seller_products(config, sellers, products)
        self._report(f"Generated seller-product catalog ({len(seller_products):,} rows).")
        self._report("Generating orders...")
        orders = generate_order_shells(config, self.scenario, customers, customer_weights)
        self._report(f"Generated orders ({len(orders):,} rows).")
        self._report("Generating order items...")
        order_items, order_sellers = generate_order_items(
            config,
            self.scenario,
            orders,
            customers,
            sellers,
            products,
            seller_products,
            product_weights,
        )
        self._report(f"Generated order items ({len(order_items):,} rows).")
        self._report("Generating shipping outcomes...")
        shipping, orders = generate_shipping(
            config,
            self.scenario,
            orders,
            order_items,
            order_sellers,
            customers,
            sellers.frame,
        )
        self._report(f"Generated shipping outcomes ({len(shipping):,} rows).")
        self._report("Generating payments...")
        payments = generate_payments(config, order_items)
        self._report(f"Generated payments ({len(payments):,} rows).")
        self._report("Generating reviews...")
        reviews = generate_reviews(
            config,
            self.scenario,
            orders,
            order_items,
            shipping,
            order_sellers,
            sellers.frame,
        )
        self._report(f"Generated reviews ({len(reviews):,} rows).")
        tables = {
            "customers": customers,
            "sellers": sellers.frame,
            "products": products,
            "seller_products": seller_products,
            "orders": orders,
            "order_items": order_items,
            "payments": payments,
            "shipping": shipping,
            "reviews": reviews,
            "calendar": calendar,
        }
        self._report("Generating simulation metadata and data dictionary...")
        tables["simulation_metadata"] = generate_metadata(config, tables)
        tables["data_dictionary"] = generate_data_dictionary(tables)
        self._report(f"Built {len(tables)} dataset tables in memory.")
        return GeneratedDataset(config=config, tables=tables)
