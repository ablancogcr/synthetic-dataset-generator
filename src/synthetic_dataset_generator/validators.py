"""Data-quality validation for generated datasets."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from synthetic_dataset_generator.config import GeneratorConfig
from synthetic_dataset_generator.constants import ORDER_STATUSES, PAYMENT_TYPES, STATE_REGIONS
from synthetic_dataset_generator.schemas import REQUIRED_FILES, SCHEMA_REGISTRY


@dataclass(frozen=True)
class ValidationCheck:
    name: str
    passed: bool
    details: str
    expected: bool = False

    @property
    def status(self) -> str:
        if self.passed:
            return "passed"
        return "expected_issue" if self.expected else "failed"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["status"] = self.status
        return payload


@dataclass
class ValidationResult:
    checks: list[ValidationCheck]
    source_integrity_status: str | None = None

    @property
    def expected_issues(self) -> list[ValidationCheck]:
        return [check for check in self.checks if not check.passed and check.expected]

    @property
    def unexpected_failures(self) -> list[ValidationCheck]:
        return [check for check in self.checks if not check.passed and not check.expected]

    @property
    def passed(self) -> bool:
        return not self.unexpected_failures

    @property
    def overall_status(self) -> str:
        if self.unexpected_failures:
            return "failed"
        if self.expected_issues:
            return "expected_issues"
        return "passed"

    def to_dict(self) -> dict[str, object]:
        return {
            "overall_status": self.overall_status,
            "source_integrity_status": self.source_integrity_status
            or ("passed" if self.passed else "failed"),
            "checks_passed": sum(check.passed for check in self.checks),
            "checks_expected_issues": len(self.expected_issues),
            "checks_failed": len(self.unexpected_failures),
            "checks_total": len(self.checks),
            "checks": [check.to_dict() for check in self.checks],
        }


def _check(
    name: str, passed: bool, details: str, *, expected: bool = False
) -> ValidationCheck:
    return ValidationCheck(name=name, passed=bool(passed), details=details, expected=expected)


def validate_dataset(
    tables: dict[str, pd.DataFrame],
    output_dir: Path | None = None,
    *,
    config: GeneratorConfig | None = None,
) -> ValidationResult:
    checks: list[ValidationCheck] = []
    missing_tables = set(SCHEMA_REGISTRY).difference(tables)
    checks.append(
        _check("required_tables", not missing_tables, f"Missing tables: {sorted(missing_tables)}")
    )
    for name, schema in SCHEMA_REGISTRY.items():
        if name in tables:
            checks.append(
                _check(
                    f"schema_{name}",
                    list(tables[name].columns) == list(schema),
                    "Columns match the declared schema.",
                )
            )
            required_columns = [column for column, spec in schema.items() if not spec.nullable]
            missing_values = int(tables[name][required_columns].isna().sum().sum())
            checks.append(
                _check(
                    f"required_values_{name}",
                    missing_values == 0,
                    f"Missing required values: {missing_values}",
                )
            )
    if output_dir is not None:
        missing_files = [name for name in REQUIRED_FILES if not (output_dir / name).is_file()]
        checks.append(
            _check("required_files", not missing_files, f"Missing files: {missing_files}")
        )

    primary_keys = {
        "customers": ["customer_id"],
        "sellers": ["seller_id"],
        "products": ["product_id"],
        "seller_products": ["seller_product_id"],
        "orders": ["order_id"],
        "reviews": ["review_id"],
        "calendar": ["date"],
        "order_items": ["order_id", "order_item_id"],
        "payments": ["order_id", "payment_sequential"],
        "shipping": ["order_id"],
    }
    for table_name, key in primary_keys.items():
        duplicated = tables[table_name].duplicated(key).sum()
        checks.append(
            _check(f"unique_{table_name}", duplicated == 0, f"Duplicate keys: {duplicated}")
        )

    fk_rules = [
        ("orders", "customer_id", "customers", "customer_id"),
        ("order_items", "order_id", "orders", "order_id"),
        ("seller_products", "seller_id", "sellers", "seller_id"),
        ("seller_products", "product_id", "products", "product_id"),
        (
            "order_items",
            "seller_product_id",
            "seller_products",
            "seller_product_id",
        ),
        ("order_items", "product_id", "products", "product_id"),
        ("order_items", "seller_id", "sellers", "seller_id"),
        ("payments", "order_id", "orders", "order_id"),
        ("shipping", "order_id", "orders", "order_id"),
        ("reviews", "order_id", "orders", "order_id"),
    ]
    for child, child_col, parent, parent_col in fk_rules:
        invalid = ~tables[child][child_col].isin(tables[parent][parent_col])
        checks.append(
            _check(
                f"fk_{child}_{child_col}", not invalid.any(), f"Invalid rows: {int(invalid.sum())}"
            )
        )

    orders = tables["orders"]
    items = tables["order_items"]
    seller_products = tables["seller_products"]
    payments = tables["payments"]
    shipping = tables["shipping"]
    reviews = tables["reviews"]
    checks.append(
        _check(
            "unique_seller_product_pairs",
            not seller_products.duplicated(["seller_id", "product_id"]).any(),
            "Each seller can list a product only once.",
        )
    )
    seller_coverage = set(seller_products["seller_id"]) == set(tables["sellers"]["seller_id"])
    product_coverage = set(seller_products["product_id"]) == set(tables["products"]["product_id"])
    checks.append(
        _check(
            "seller_product_catalog_coverage",
            seller_coverage and product_coverage,
            "Every seller and product has at least one listing.",
        )
    )
    listing_counts = seller_products.groupby("product_id").size()
    cardinality_valid = True
    cardinality_details = "Configuration was not supplied; coverage was validated."
    if config is not None:
        minimum = config.simulation.min_sellers_per_product
        maximum = config.simulation.max_sellers_per_product
        cardinality_valid = bool(listing_counts.between(minimum, maximum).all())
        cardinality_details = f"Each product has between {minimum} and {maximum} sellers."
    checks.append(
        _check(
            "seller_product_cardinality",
            cardinality_valid,
            cardinality_details,
        )
    )

    listing_reference = seller_products.set_index("seller_product_id")[["seller_id", "product_id"]]
    resolved_items = items[["seller_product_id", "seller_id", "product_id"]].join(
        listing_reference,
        on="seller_product_id",
        rsuffix="_listing",
    )
    listing_consistent = (
        resolved_items["seller_id"].eq(resolved_items["seller_id_listing"])
        & resolved_items["product_id"].eq(resolved_items["product_id_listing"])
    ).all()
    checks.append(
        _check(
            "order_item_listing_consistency",
            listing_consistent,
            "Order-item seller and product identifiers match the referenced listing.",
        )
    )
    checks.append(
        _check(
            "one_seller_per_order",
            items.groupby("order_id")["seller_id"].nunique().le(1).all(),
            "Every order is fulfilled by one seller.",
        )
    )

    listing_seller_state = seller_products[["seller_id", "listing_active_flag"]].merge(
        tables["sellers"][["seller_id", "seller_active_flag"]],
        on="seller_id",
        how="left",
    )
    listing_status_valid = listing_seller_state["listing_active_flag"].eq(
        listing_seller_state["seller_active_flag"]
    ).all()
    checks.append(
        _check(
            "seller_product_active_status",
            listing_status_valid,
            "Listing period-end active flags match their sellers.",
        )
    )

    item_purchase_dates = items[["order_id", "seller_product_id"]].merge(
        orders[["order_id", "order_purchase_timestamp"]], on="order_id", how="left"
    )
    item_purchase_dates = item_purchase_dates.merge(
        seller_products[["seller_product_id", "listing_created_at"]],
        on="seller_product_id",
        how="left",
    )
    listing_available = (
        pd.to_datetime(item_purchase_dates["listing_created_at"])
        <= pd.to_datetime(item_purchase_dates["order_purchase_timestamp"])
    ).all()
    checks.append(
        _check(
            "seller_product_available_at_purchase",
            listing_available,
            "Purchased listings existed when their orders were placed.",
        )
    )

    checks.append(
        _check(
            "valid_order_statuses",
            orders["order_status"].isin(ORDER_STATUSES).all(),
            "Allowed values only.",
        )
    )
    checks.append(
        _check(
            "valid_payment_types",
            payments["payment_type"].isin(PAYMENT_TYPES).all(),
            "Allowed values only.",
        )
    )
    checks.append(
        _check(
            "valid_review_scores",
            reviews["review_score"].between(1, 5).all(),
            "Scores are between 1 and 5.",
        )
    )
    state_columns = [
        ("customers", "customer_state"),
        ("sellers", "seller_state"),
        ("shipping", "seller_state"),
        ("shipping", "customer_state"),
    ]
    valid_states = set(STATE_REGIONS)
    state_valid = all(
        tables[table][column].isin(valid_states).all() for table, column in state_columns
    )
    checks.append(
        _check("valid_states", state_valid, "All geography uses recognized US state abbreviations.")
    )
    monetary_columns = [
        ("products", "product_price_base_usd"),
        ("seller_products", "seller_price_usd"),
        ("order_items", "item_price_usd"),
        ("order_items", "shipping_cost_usd"),
        ("order_items", "item_total_usd"),
        ("payments", "payment_value_usd"),
        ("shipping", "shipping_cost_usd"),
    ]
    non_negative = all((tables[table][column] >= 0).all() for table, column in monetary_columns)
    checks.append(
        _check("non_negative_values", non_negative, "Prices and shipping values are non-negative.")
    )

    delivered = orders.loc[orders["order_status"] == "delivered"]
    purchase = pd.to_datetime(delivered["order_purchase_timestamp"])
    approved = pd.to_datetime(delivered["order_approved_at"])
    carrier = pd.to_datetime(delivered["order_delivered_carrier_date"])
    customer = pd.to_datetime(delivered["order_delivered_customer_date"])
    date_valid = (
        (purchase <= approved).all() and (approved <= carrier).all() and (carrier <= customer).all()
    )
    checks.append(
        _check("date_sequence", date_valid, "Delivered-order timestamps are logically ordered.")
    )
    metadata = tables["simulation_metadata"].iloc[0]
    start_date = pd.Timestamp(metadata["start_date"])
    end_date = pd.Timestamp(metadata["end_date"]) + pd.Timedelta(hours=23, minutes=59, seconds=59)
    date_columns = [
        ("customers", "created_at"),
        ("sellers", "created_at"),
        ("sellers", "deactivated_at"),
        ("products", "created_at"),
        ("seller_products", "listing_created_at"),
        ("orders", "order_purchase_timestamp"),
        ("orders", "order_approved_at"),
        ("orders", "order_estimated_delivery_date"),
        ("orders", "order_delivered_carrier_date"),
        ("orders", "order_delivered_customer_date"),
        ("reviews", "review_creation_date"),
        ("reviews", "review_answer_timestamp"),
        ("calendar", "date"),
    ]
    within_range = True
    for table_name, column_name in date_columns:
        values = pd.to_datetime(tables[table_name][column_name].dropna())
        within_range = within_range and values.between(start_date, end_date).all()
    checks.append(
        _check(
            "configured_date_range",
            within_range,
            "All business dates are within the configured period.",
        )
    )

    item_totals = items.groupby("order_id")["item_total_usd"].sum().sort_index()
    payment_totals = payments.groupby("order_id")["payment_value_usd"].sum().sort_index()
    payments_match = item_totals.index.equals(payment_totals.index) and np.allclose(
        item_totals, payment_totals, atol=0.011
    )
    checks.append(
        _check(
            "payment_reconciliation",
            payments_match,
            "Payments match order item totals to the cent.",
        )
    )
    order_ids = set(orders["order_id"])
    checks.append(
        _check(
            "shipping_coverage",
            set(shipping["order_id"]) == order_ids,
            "Exactly one shipping row exists per order.",
        )
    )
    item_shipping = items.groupby("order_id")["shipping_cost_usd"].sum().sort_index()
    order_shipping = shipping.set_index("order_id")["shipping_cost_usd"].sort_index()
    checks.append(
        _check(
            "shipping_reconciliation",
            np.allclose(item_shipping, order_shipping, atol=0.011),
            "Order shipping equals item shipping.",
        )
    )
    reviewed_status = reviews.merge(
        orders[["order_id", "order_status"]], on="order_id", how="left"
    )["order_status"]
    checks.append(
        _check(
            "reviews_for_delivered_orders",
            reviewed_status.eq("delivered").all(),
            "Reviews belong only to delivered orders.",
        )
    )
    scenario_valid = all(
        frame["scenario_name"].notna().all() and frame["scenario_name"].ne("").all()
        for frame in tables.values()
        if "scenario_name" in frame
    )
    checks.append(
        _check(
            "scenario_populated",
            scenario_valid,
            "Scenario names are populated on scenario-bearing tables.",
        )
    )

    seller_deactivation = tables["sellers"].set_index("seller_id")["deactivated_at"].dropna()
    if seller_deactivation.empty:
        churn_valid = True
    else:
        item_dates = items.merge(orders[["order_id", "order_purchase_timestamp"]], on="order_id")
        churn_items = item_dates[item_dates["seller_id"].isin(seller_deactivation.index)].copy()
        churn_items["deactivated_at"] = churn_items["seller_id"].map(seller_deactivation)
        churn_valid = (
            pd.to_datetime(churn_items["order_purchase_timestamp"])
            < pd.to_datetime(churn_items["deactivated_at"])
        ).all()
    checks.append(
        _check(
            "seller_churn_cutoff", churn_valid, "Deactivated sellers receive no post-churn orders."
        )
    )
    return ValidationResult(checks)
