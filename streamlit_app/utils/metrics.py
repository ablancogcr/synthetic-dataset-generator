"""Reusable ecommerce calculations for the local dataset viewer."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class OverviewMetrics:
    order_count: int
    customer_count: int
    seller_count: int
    product_count: int
    product_revenue: float
    shipping_revenue: float
    total_order_value: float
    average_order_value: float
    late_delivery_rate: float | None
    average_review_score: float | None


@dataclass(frozen=True)
class SellerConcentration:
    top_5_share: float
    top_10_share: float


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def _boolean(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype("string").str.lower().isin({"true", "1", "yes"})


def _require(frame: pd.DataFrame, columns: set[str], table_name: str) -> None:
    missing = columns.difference(frame.columns)
    if missing:
        joined = ", ".join(sorted(missing))
        raise ValueError(f"{table_name} is missing required columns: {joined}")


def calculate_overview_metrics(
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    customers: pd.DataFrame,
    sellers: pd.DataFrame,
    products: pd.DataFrame,
    shipping: pd.DataFrame | None = None,
    reviews: pd.DataFrame | None = None,
) -> OverviewMetrics:
    """Calculate viewer KPIs without multiplying order-level records."""
    _require(orders, {"order_id"}, "orders")
    _require(
        order_items,
        {"order_id", "item_price_usd", "shipping_cost_usd", "item_total_usd"},
        "order_items",
    )
    order_count = int(orders["order_id"].nunique())
    product_revenue = float(_numeric(order_items["item_price_usd"]).sum())
    shipping_revenue = float(_numeric(order_items["shipping_cost_usd"]).sum())
    total_order_value = float(_numeric(order_items["item_total_usd"]).sum())

    late_delivery_rate: float | None = None
    if shipping is not None and "late_delivery_flag" in shipping and not shipping.empty:
        late_delivery_rate = float(_boolean(shipping["late_delivery_flag"]).mean())

    average_review_score: float | None = None
    if reviews is not None and "review_score" in reviews and not reviews.empty:
        scores = pd.to_numeric(reviews["review_score"], errors="coerce").dropna()
        if not scores.empty:
            average_review_score = float(scores.mean())

    return OverviewMetrics(
        order_count=order_count,
        customer_count=_entity_count(customers, "customer_id"),
        seller_count=_entity_count(sellers, "seller_id"),
        product_count=_entity_count(products, "product_id"),
        product_revenue=product_revenue,
        shipping_revenue=shipping_revenue,
        total_order_value=total_order_value,
        average_order_value=total_order_value / order_count if order_count else 0.0,
        late_delivery_rate=late_delivery_rate,
        average_review_score=average_review_score,
    )


def _entity_count(frame: pd.DataFrame, identifier: str) -> int:
    return int(frame[identifier].nunique()) if identifier in frame else int(len(frame))


def monthly_performance(orders: pd.DataFrame, order_items: pd.DataFrame) -> pd.DataFrame:
    """Aggregate order counts and values by purchase month at one row per order."""
    _require(orders, {"order_id", "order_purchase_timestamp"}, "orders")
    _require(
        order_items,
        {"order_id", "item_price_usd", "shipping_cost_usd", "item_total_usd"},
        "order_items",
    )
    item_values = (
        order_items.assign(
            item_price_usd=_numeric(order_items["item_price_usd"]),
            shipping_cost_usd=_numeric(order_items["shipping_cost_usd"]),
            item_total_usd=_numeric(order_items["item_total_usd"]),
        )
        .groupby("order_id", as_index=False)[
            ["item_price_usd", "shipping_cost_usd", "item_total_usd"]
        ]
        .sum()
    )

    order_values = orders[["order_id", "order_purchase_timestamp"]].drop_duplicates("order_id")
    order_values = order_values.merge(item_values, on="order_id", how="left")
    value_columns = ["item_price_usd", "shipping_cost_usd", "item_total_usd"]
    order_values[value_columns] = order_values[value_columns].fillna(0.0)
    order_values["month"] = (
        pd.to_datetime(order_values["order_purchase_timestamp"], errors="coerce")
        .dt.to_period("M")
        .dt.to_timestamp()
    )
    order_values = order_values.dropna(subset=["month"])

    monthly = order_values.groupby("month", as_index=False).agg(
        order_count=("order_id", "nunique"),
        product_revenue=("item_price_usd", "sum"),
        shipping_revenue=("shipping_cost_usd", "sum"),
        total_order_value=("item_total_usd", "sum"),
    )
    monthly["average_order_value"] = np.divide(
        monthly["total_order_value"],
        monthly["order_count"],
        out=np.zeros(len(monthly), dtype=float),
        where=monthly["order_count"].to_numpy() != 0,
    )
    return monthly.sort_values("month", ignore_index=True)


def category_performance(order_items: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Aggregate product revenue and distinct orders by product category."""
    _require(order_items, {"order_id", "product_id", "item_price_usd"}, "order_items")
    _require(products, {"product_id", "product_category"}, "products")
    categories = products[["product_id", "product_category"]].drop_duplicates("product_id")
    joined = order_items[["order_id", "product_id", "item_price_usd"]].merge(
        categories, on="product_id", how="left", validate="many_to_one"
    )
    joined["item_price_usd"] = _numeric(joined["item_price_usd"])
    joined["product_category"] = joined["product_category"].fillna("Unknown")
    return (
        joined.groupby("product_category", as_index=False)
        .agg(
            product_revenue=("item_price_usd", "sum"),
            order_count=("order_id", "nunique"),
        )
        .sort_values("product_revenue", ascending=False, ignore_index=True)
    )


def seller_performance(order_items: pd.DataFrame, sellers: pd.DataFrame) -> pd.DataFrame:
    """Aggregate item revenue once per seller, with optional seller attributes."""
    _require(order_items, {"seller_id", "item_price_usd", "order_id"}, "order_items")
    performance = (
        order_items.assign(item_price_usd=_numeric(order_items["item_price_usd"]))
        .groupby("seller_id", as_index=False)
        .agg(
            product_revenue=("item_price_usd", "sum"),
            order_count=("order_id", "nunique"),
        )
    )
    if "seller_id" in sellers:
        attributes = sellers.drop_duplicates("seller_id")
        keep = [
            column
            for column in ("seller_id", "seller_segment", "seller_state", "seller_region")
            if column in attributes
        ]
        performance = performance.merge(
            attributes[keep], on="seller_id", how="left", validate="one_to_one"
        )
    return performance.sort_values("product_revenue", ascending=False, ignore_index=True)


def seller_revenue_concentration(seller_revenue: pd.Series) -> SellerConcentration:
    """Return the top-five and top-ten share of seller product revenue."""
    revenue = pd.to_numeric(seller_revenue, errors="coerce").fillna(0.0).clip(lower=0)
    total = float(revenue.sum())
    if total == 0:
        return SellerConcentration(top_5_share=0.0, top_10_share=0.0)
    ranked = revenue.sort_values(ascending=False)
    return SellerConcentration(
        top_5_share=float(ranked.head(5).sum() / total),
        top_10_share=float(ranked.head(10).sum() / total),
    )


def customer_geography(
    orders: pd.DataFrame, customers: pd.DataFrame, dimension: str
) -> pd.DataFrame:
    """Count distinct orders by a customer geography dimension."""
    if dimension not in {"customer_state", "customer_region"}:
        raise ValueError("dimension must be customer_state or customer_region")
    _require(orders, {"order_id", "customer_id"}, "orders")
    _require(customers, {"customer_id", dimension}, "customers")
    geography = customers[["customer_id", dimension]].drop_duplicates("customer_id")
    joined = (
        orders[["order_id", "customer_id"]]
        .drop_duplicates("order_id")
        .merge(geography, on="customer_id", how="left", validate="many_to_one")
    )
    joined[dimension] = joined[dimension].fillna("Unknown")
    return (
        joined.groupby(dimension, as_index=False)
        .agg(order_count=("order_id", "nunique"))
        .sort_values("order_count", ascending=False, ignore_index=True)
    )


def payment_type_distribution(payments: pd.DataFrame) -> pd.DataFrame:
    """Summarize payment rows, distinct orders, and value by payment type."""
    _require(payments, {"order_id", "payment_type", "payment_value_usd"}, "payments")
    values = payments.assign(payment_value_usd=_numeric(payments["payment_value_usd"]))
    return (
        values.groupby("payment_type", as_index=False)
        .agg(
            payment_rows=("payment_type", "size"),
            order_count=("order_id", "nunique"),
            payment_value=("payment_value_usd", "sum"),
        )
        .sort_values("payment_value", ascending=False, ignore_index=True)
    )


def shipping_by_distance(shipping: pd.DataFrame) -> pd.DataFrame:
    """Summarize average per-order shipping cost and delivery performance by distance."""
    _require(
        shipping,
        {
            "shipping_distance_band",
            "shipping_cost_usd",
            "late_delivery_flag",
            "estimated_delivery_days",
            "actual_delivery_days",
            "delivery_delay_days",
        },
        "shipping",
    )
    values = shipping.copy()
    for column in (
        "shipping_cost_usd",
        "estimated_delivery_days",
        "actual_delivery_days",
        "delivery_delay_days",
    ):
        values[column] = pd.to_numeric(values[column], errors="coerce")
    values["late_delivery_flag"] = _boolean(values["late_delivery_flag"])
    return values.groupby("shipping_distance_band", as_index=False).agg(
        shipment_count=("shipping_distance_band", "size"),
        average_shipping_cost=("shipping_cost_usd", "mean"),
        late_delivery_rate=("late_delivery_flag", "mean"),
        average_estimated_days=("estimated_delivery_days", "mean"),
        average_actual_days=("actual_delivery_days", "mean"),
        average_delay_days=("delivery_delay_days", "mean"),
    )


def review_delivery_relationship(reviews: pd.DataFrame, shipping: pd.DataFrame) -> pd.DataFrame:
    """Join one review to one order-level shipment for descriptive analysis."""
    _require(reviews, {"order_id", "review_score", "satisfaction_risk_flag"}, "reviews")
    _require(shipping, {"order_id", "late_delivery_flag", "delivery_delay_days"}, "shipping")
    delivery = shipping[["order_id", "late_delivery_flag", "delivery_delay_days"]].drop_duplicates(
        "order_id"
    )
    relationship = reviews[["order_id", "review_score", "satisfaction_risk_flag"]].merge(
        delivery, on="order_id", how="left", validate="many_to_one"
    )
    relationship["review_score"] = pd.to_numeric(relationship["review_score"], errors="coerce")
    relationship["delivery_delay_days"] = pd.to_numeric(
        relationship["delivery_delay_days"], errors="coerce"
    )
    relationship["late_delivery_flag"] = _boolean(relationship["late_delivery_flag"])
    relationship["satisfaction_risk_flag"] = _boolean(relationship["satisfaction_risk_flag"])
    return relationship
