"""Marketplace demand, category, seller, geography, and payment analysis."""

from __future__ import annotations

import streamlit as st

from streamlit_app.utils.charts import bar_chart, line_chart
from streamlit_app.utils.metrics import seller_revenue_concentration
from streamlit_app.utils.shared import load_table, load_tables, page_intro, require_dataset
from streamlit_app.utils.streamlit_cache import (
    category_performance_cached,
    customer_geography_cached,
    monthly_performance_cached,
    payment_distribution_cached,
    seller_performance_cached,
)

page_intro(
    "Marketplace analysis",
    "Descriptive demand, category, seller, customer geography, and payment patterns.",
)
dataset_path = require_dataset()
tables = load_tables(dataset_path, ("orders", "order_items", "products", "sellers", "customers"))
if tables is None:
    st.stop()
payments = load_table(dataset_path, "payments", required=False)

try:
    monthly = monthly_performance_cached(tables["orders"], tables["order_items"])
    categories = category_performance_cached(tables["order_items"], tables["products"])
    sellers = seller_performance_cached(tables["order_items"], tables["sellers"])
except ValueError as exc:
    st.error(str(exc))
    st.stop()

if not monthly.empty:
    left, middle, right = st.columns(3)
    with left:
        st.plotly_chart(
            line_chart(
                monthly,
                x="month",
                y="order_count",
                title="Monthly orders",
                x_title="Purchase month",
                y_title="Distinct orders",
            ),
            width="stretch",
        )
    with middle:
        st.plotly_chart(
            line_chart(
                monthly,
                x="month",
                y="product_revenue",
                title="Monthly product revenue",
                x_title="Purchase month",
                y_title="Product revenue (USD)",
                currency=True,
            ),
            width="stretch",
        )
    with right:
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

category_left, category_right = st.columns(2)
with category_left:
    st.plotly_chart(
        bar_chart(
            categories.sort_values("product_revenue"),
            x="product_category",
            y="product_revenue",
            title="Product revenue by category",
            x_title="Product category",
            y_title="Product revenue (USD)",
            currency=True,
            horizontal=True,
        ),
        width="stretch",
    )
with category_right:
    st.plotly_chart(
        bar_chart(
            categories.sort_values("order_count"),
            x="product_category",
            y="order_count",
            title="Distinct order count by category",
            x_title="Product category",
            y_title="Distinct orders containing category",
            horizontal=True,
        ),
        width="stretch",
    )

concentration = seller_revenue_concentration(sellers["product_revenue"])
with st.container(horizontal=True):
    st.metric("Top 5 seller revenue share", f"{concentration.top_5_share:.1%}", border=True)
    st.metric("Top 10 seller revenue share", f"{concentration.top_10_share:.1%}", border=True)
    st.metric("Sellers with revenue", f"{len(sellers):,}", border=True)

st.plotly_chart(
    bar_chart(
        sellers.head(15).sort_values("product_revenue"),
        x="seller_id",
        y="product_revenue",
        title="Top sellers by product revenue",
        x_title="Seller",
        y_title="Product revenue (USD)",
        currency=True,
        horizontal=True,
    ),
    width="stretch",
)
st.caption(
    "Seller concentration uses item-level product revenue once per order item; seller attributes "
    "are joined only after aggregation."
)

geography_dimension = st.segmented_control(
    "Customer geography",
    options=["State", "Region"],
    default="State",
    key="marketplace_geography_dimension",
)
dimension_column = "customer_state" if geography_dimension == "State" else "customer_region"
try:
    geography = customer_geography_cached(tables["orders"], tables["customers"], dimension_column)
except ValueError as exc:
    st.error(str(exc))
else:
    st.plotly_chart(
        bar_chart(
            geography.head(20),
            x=dimension_column,
            y="order_count",
            title=f"Orders by customer {geography_dimension.lower()}",
            x_title=geography_dimension,
            y_title="Distinct orders",
        ),
        width="stretch",
    )

if payments is not None:
    try:
        payment_distribution = payment_distribution_cached(payments)
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.plotly_chart(
            bar_chart(
                payment_distribution,
                x="payment_type",
                y="payment_value",
                title="Payment value by payment type",
                x_title="Payment type",
                y_title="Payment value (USD)",
                currency=True,
            ),
            width="stretch",
        )
        st.dataframe(
            payment_distribution,
            hide_index=True,
            column_config={
                "payment_value": st.column_config.NumberColumn(format="$%.2f"),
            },
        )
        st.caption(
            "Payment rows and distinct orders are both shown because one order can use multiple "
            "payment records or types."
        )
