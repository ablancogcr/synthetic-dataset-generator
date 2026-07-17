"""Delivery performance and review relationship analysis."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_app.utils.charts import bar_chart, scatter_chart
from streamlit_app.utils.shared import load_table, page_intro, require_dataset
from streamlit_app.utils.streamlit_cache import (
    review_delivery_cached,
    shipping_by_distance_cached,
)

page_intro(
    "Shipping and reviews",
    "Observed delivery and review relationships. These descriptive patterns do not establish "
    "causality.",
)
dataset_path = require_dataset()
shipping = load_table(dataset_path, "shipping", required=False)
reviews = load_table(dataset_path, "reviews", required=False)
orders = load_table(dataset_path, "orders", required=False)
order_items = load_table(dataset_path, "order_items", required=False)
sellers = load_table(dataset_path, "sellers", required=False)

if shipping is None:
    st.info("Shipping analysis requires `shipping.csv`.")
    st.stop()

required_shipping_columns = {
    "late_delivery_flag",
    "estimated_delivery_days",
    "actual_delivery_days",
    "delivery_delay_days",
}
missing_shipping_columns = required_shipping_columns.difference(shipping.columns)
if missing_shipping_columns:
    st.error(
        "shipping.csv is missing required columns: " + ", ".join(sorted(missing_shipping_columns))
    )
    st.stop()

late_flags = shipping["late_delivery_flag"].astype("string").str.lower().isin({"true", "1"})
estimated_days = pd.to_numeric(shipping["estimated_delivery_days"], errors="coerce")
actual_days = pd.to_numeric(shipping["actual_delivery_days"], errors="coerce")
delay_days = pd.to_numeric(shipping["delivery_delay_days"], errors="coerce")

with st.container(horizontal=True):
    st.metric("Late delivery rate", f"{late_flags.mean():.1%}", border=True)
    st.metric("Average estimated delivery", f"{estimated_days.mean():.2f} days", border=True)
    st.metric("Average actual delivery", f"{actual_days.mean():.2f} days", border=True)
    st.metric("Average delivery delay", f"{delay_days.mean():.2f} days", border=True)

try:
    distance = shipping_by_distance_cached(shipping)
except ValueError as exc:
    st.error(str(exc))
    distance = pd.DataFrame()

if not distance.empty:
    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            bar_chart(
                distance,
                x="shipping_distance_band",
                y="average_shipping_cost",
                title="Average shipping cost by distance band",
                x_title="Shipping distance band",
                y_title="Average per-order shipping cost (USD)",
                currency=True,
            ),
            width="stretch",
        )
    with right:
        st.plotly_chart(
            bar_chart(
                distance,
                x="shipping_distance_band",
                y="late_delivery_rate",
                title="Late delivery rate by distance band",
                x_title="Shipping distance band",
                y_title="Late delivery rate",
                percentage=True,
            ),
            width="stretch",
        )

if reviews is None:
    st.info("Review analysis requires `reviews.csv`; shipping metrics remain available above.")
else:
    try:
        relationship = review_delivery_cached(reviews, shipping)
    except ValueError as exc:
        st.error(str(exc))
        relationship = pd.DataFrame()

    if not relationship.empty:
        review_scores = (
            relationship.dropna(subset=["review_score"])
            .groupby("review_score", as_index=False)
            .agg(review_count=("order_id", "size"))
        )
        score_by_late = (
            relationship.dropna(subset=["review_score"])
            .groupby("late_delivery_flag", as_index=False)
            .agg(average_review_score=("review_score", "mean"))
        )
        score_by_late["delivery_status"] = score_by_late["late_delivery_flag"].map(
            {False: "On time or early", True: "Late"}
        )

        with st.container(horizontal=True):
            st.metric(
                "Average review score",
                f"{relationship['review_score'].mean():.2f} / 5",
                border=True,
            )
            st.metric(
                "Satisfaction risk rate",
                f"{relationship['satisfaction_risk_flag'].mean():.1%}",
                border=True,
            )
            st.metric("Reviewed orders", f"{relationship['order_id'].nunique():,}", border=True)

        left, right = st.columns(2)
        with left:
            st.plotly_chart(
                bar_chart(
                    review_scores,
                    x="review_score",
                    y="review_count",
                    title="Review score distribution",
                    x_title="Review score",
                    y_title="Reviews",
                ),
                width="stretch",
            )
        with right:
            st.plotly_chart(
                bar_chart(
                    score_by_late,
                    x="delivery_status",
                    y="average_review_score",
                    title="Average review score by delivery status",
                    x_title="Observed delivery status",
                    y_title="Average review score",
                ),
                width="stretch",
            )

        scatter_data = relationship.dropna(subset=["delivery_delay_days", "review_score"])
        if len(scatter_data) > 5000:
            scatter_data = scatter_data.sample(5000, random_state=42)
        st.plotly_chart(
            scatter_chart(
                scatter_data,
                x="delivery_delay_days",
                y="review_score",
                color="late_delivery_flag",
                title="Observed review score and delivery delay",
                x_title="Delivery delay (days)",
                y_title="Review score",
            ),
            width="stretch",
        )
        st.caption(
            "The charts show association in this synthetic simulation. They do not prove that a "
            "delivery delay caused a particular review score."
        )

coverage: list[str] = []
if orders is not None and "order_id" in orders:
    coverage.append(f"{orders['order_id'].nunique():,} total orders")
if order_items is not None:
    coverage.append(f"{len(order_items):,} order items")
if sellers is not None and "seller_id" in sellers:
    coverage.append(f"{sellers['seller_id'].nunique():,} sellers")
if coverage:
    st.caption("Dataset coverage context: " + "; ".join(coverage) + ".")
