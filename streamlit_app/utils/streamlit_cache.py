"""Bounded Streamlit caches keyed by local file modification time."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from streamlit_app.utils.data_loader import load_metadata, read_csv_file
from streamlit_app.utils.metrics import (
    OverviewMetrics,
    calculate_overview_metrics,
    category_performance,
    customer_geography,
    monthly_performance,
    payment_type_distribution,
    review_delivery_relationship,
    seller_performance,
    shipping_by_distance,
)
from streamlit_app.utils.validation_loader import ValidationReport, load_validation_report


@st.cache_data(max_entries=128, show_spinner=False)
def load_csv_cached(path: str, modified_time_ns: int) -> pd.DataFrame:
    """Load a CSV; ``modified_time_ns`` invalidates regenerated files."""
    del modified_time_ns
    return read_csv_file(path)


@st.cache_data(max_entries=32, show_spinner=False)
def load_metadata_cached(dataset_dir: str, modified_time_ns: int | None) -> dict[str, object]:
    del modified_time_ns
    return load_metadata(dataset_dir)


@st.cache_data(max_entries=32, show_spinner=False)
def load_validation_cached(
    dataset_dir: str,
    json_modified_time_ns: int | None,
    markdown_modified_time_ns: int | None,
    manifest_modified_time_ns: int | None,
) -> ValidationReport | None:
    del json_modified_time_ns, markdown_modified_time_ns, manifest_modified_time_ns
    return load_validation_report(dataset_dir)


def optional_mtime(path: Path) -> int | None:
    """Return a file mtime or ``None`` for an optional missing file."""
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return None


@st.cache_data(max_entries=24, show_spinner=False)
def overview_metrics_cached(
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    customers: pd.DataFrame,
    sellers: pd.DataFrame,
    products: pd.DataFrame,
    shipping: pd.DataFrame | None,
    reviews: pd.DataFrame | None,
) -> OverviewMetrics:
    return calculate_overview_metrics(
        orders, order_items, customers, sellers, products, shipping, reviews
    )


@st.cache_data(max_entries=24, show_spinner=False)
def monthly_performance_cached(orders: pd.DataFrame, order_items: pd.DataFrame) -> pd.DataFrame:
    return monthly_performance(orders, order_items)


@st.cache_data(max_entries=24, show_spinner=False)
def category_performance_cached(order_items: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    return category_performance(order_items, products)


@st.cache_data(max_entries=24, show_spinner=False)
def seller_performance_cached(order_items: pd.DataFrame, sellers: pd.DataFrame) -> pd.DataFrame:
    return seller_performance(order_items, sellers)


@st.cache_data(max_entries=24, show_spinner=False)
def customer_geography_cached(
    orders: pd.DataFrame, customers: pd.DataFrame, dimension: str
) -> pd.DataFrame:
    return customer_geography(orders, customers, dimension)


@st.cache_data(max_entries=24, show_spinner=False)
def payment_distribution_cached(payments: pd.DataFrame) -> pd.DataFrame:
    return payment_type_distribution(payments)


@st.cache_data(max_entries=24, show_spinner=False)
def shipping_by_distance_cached(shipping: pd.DataFrame) -> pd.DataFrame:
    return shipping_by_distance(shipping)


@st.cache_data(max_entries=24, show_spinner=False)
def review_delivery_cached(reviews: pd.DataFrame, shipping: pd.DataFrame) -> pd.DataFrame:
    return review_delivery_relationship(reviews, shipping)


@st.cache_data(max_entries=24, show_spinner=False)
def dataframe_to_csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8")
