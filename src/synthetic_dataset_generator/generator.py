"""Dataset generation orchestration."""

from __future__ import annotations

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
from synthetic_dataset_generator.sellers import generate_sellers
from synthetic_dataset_generator.shipping import generate_shipping


@dataclass
class GeneratedDataset:
    config: GeneratorConfig
    tables: dict[str, pd.DataFrame]


class DatasetGenerator:
    """Generate a complete in-memory synthetic ecommerce dataset."""

    def __init__(self, config: GeneratorConfig, scenario: ScenarioConfig) -> None:
        self.config = config
        self.scenario = scenario

    def generate(self) -> GeneratedDataset:
        config = self.config
        seed = config.dataset.random_seed
        calendar = generate_calendar(config.dataset.start_date, config.dataset.end_date)
        customers, customer_weights = generate_customers(
            config.simulation.customer_count,
            config.dataset.start_date,
            config.dataset.end_date,
            seed,
        )
        sellers = generate_sellers(
            config.simulation.seller_count,
            config.dataset.start_date,
            config.dataset.end_date,
            seed,
            self.scenario,
        )
        products, product_weights = generate_products(
            config.simulation.product_count, config.dataset.start_date, seed
        )
        orders = generate_order_shells(config, self.scenario, customers, customer_weights)
        order_items, order_sellers = generate_order_items(
            config,
            self.scenario,
            orders,
            customers,
            sellers,
            products,
            product_weights,
        )
        shipping, orders = generate_shipping(
            config,
            self.scenario,
            orders,
            order_items,
            order_sellers,
            customers,
            sellers.frame,
        )
        payments = generate_payments(config, order_items)
        reviews = generate_reviews(
            config,
            self.scenario,
            orders,
            order_items,
            shipping,
            order_sellers,
            sellers.frame,
        )
        tables = {
            "customers": customers,
            "sellers": sellers.frame,
            "products": products,
            "orders": orders,
            "order_items": order_items,
            "payments": payments,
            "shipping": shipping,
            "reviews": reviews,
            "calendar": calendar,
        }
        tables["simulation_metadata"] = generate_metadata(config, tables)
        tables["data_dictionary"] = generate_data_dictionary(tables)
        return GeneratedDataset(config=config, tables=tables)
