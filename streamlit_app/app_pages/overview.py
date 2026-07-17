"""Overview KPIs and monthly trends."""

from __future__ import annotations

import streamlit as st

from streamlit_app.utils.charts import bar_chart, line_chart
from streamlit_app.utils.shared import (
    load_table,
    load_tables,
    page_intro,
    require_dataset,
    show_disclaimer,
)
from streamlit_app.utils.streamlit_cache import (
    monthly_performance_cached,
    overview_metrics_cached,
)

page_intro(
    "Synthetic ecommerce dataset overview",
    "Key measures and monthly patterns from the selected generated dataset.",
)
show_disclaimer()
dataset_path = require_dataset()

core = load_tables(dataset_path, ("orders", "order_items", "customers", "sellers", "products"))
if core is None:
    st.stop()

shipping = load_table(dataset_path, "shipping", required=False)
reviews = load_table(dataset_path, "reviews", required=False)

try:
    metrics = overview_metrics_cached(
        core["orders"],
        core["order_items"],
        core["customers"],
        core["sellers"],
        core["products"],
        shipping,
        reviews,
    )
    monthly = monthly_performance_cached(core["orders"], core["order_items"])
except ValueError as exc:
    st.error(str(exc))
    st.stop()

with st.container(horizontal=True):
    st.metric("Orders", f"{metrics.order_count:,}", border=True)
    st.metric("Customers", f"{metrics.customer_count:,}", border=True)
    st.metric("Sellers", f"{metrics.seller_count:,}", border=True)
    st.metric("Products", f"{metrics.product_count:,}", border=True)

with st.container(horizontal=True):
    st.metric("Product revenue", f"${metrics.product_revenue:,.2f}", border=True)
    st.metric("Shipping revenue", f"${metrics.shipping_revenue:,.2f}", border=True)
    st.metric("Total order value", f"${metrics.total_order_value:,.2f}", border=True)
    st.metric("Average order value", f"${metrics.average_order_value:,.2f}", border=True)
    late_rate = (
        f"{metrics.late_delivery_rate:.1%}"
        if metrics.late_delivery_rate is not None
        else "Not available"
    )
    review_score = (
        f"{metrics.average_review_score:.2f} / 5"
        if metrics.average_review_score is not None
        else "Not available"
    )
    st.metric("Late delivery rate", late_rate, border=True)
    st.metric("Average review score", review_score, border=True)

metadata = st.session_state.get("dataset_metadata", {})
seed = metadata.get("random_seed")
seed_display = seed if seed is not None else "Not available"
with st.container(border=True):
    st.subheader("Simulation context")
    st.write(
        f"**Scenario:** {metadata.get('scenario_name') or 'Not available'}  \n"
        f"**Date range:** {metadata.get('start_date') or 'Unknown'} to "
        f"{metadata.get('end_date') or 'Unknown'}  \n"
        f"**Random seed:** {seed_display}"
    )

if monthly.empty:
    st.info("No valid order purchase dates are available for monthly charts.")
else:
    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            line_chart(
                monthly,
                x="month",
                y="order_count",
                title="Monthly order count",
                x_title="Purchase month",
                y_title="Distinct orders",
            ),
            width="stretch",
        )
        st.plotly_chart(
            line_chart(
                monthly,
                x="month",
                y="average_order_value",
                title="Monthly average order value",
                x_title="Purchase month",
                y_title="Average order value (USD)",
                currency=True,
            ),
            width="stretch",
        )
    with right:
        st.plotly_chart(
            line_chart(
                monthly,
                x="month",
                y="total_order_value",
                title="Monthly total order value",
                x_title="Purchase month",
                y_title="Total order value (USD)",
                currency=True,
            ),
            width="stretch",
        )
        orders = core["orders"]
        if "order_status" in orders:
            statuses = (
                orders.groupby("order_status", as_index=False)
                .agg(order_count=("order_id", "nunique"))
                .sort_values("order_count", ascending=False)
            )
            st.plotly_chart(
                bar_chart(
                    statuses,
                    x="order_status",
                    y="order_count",
                    title="Order status distribution",
                    x_title="Order status",
                    y_title="Distinct orders",
                ),
                width="stretch",
            )

with st.expander("Metric definitions"):
    st.markdown(
        "- **Product revenue:** sum of `item_price_usd` from `order_items.csv`.\n"
        "- **Shipping revenue:** sum of `shipping_cost_usd` from `order_items.csv`.\n"
        "- **Total order value:** sum of `item_total_usd` from `order_items.csv`.\n"
        "- **Average order value:** total order value divided by distinct orders in `orders.csv`."
    )
