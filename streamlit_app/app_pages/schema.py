"""Table schema, data dictionary, and relationship reference."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_app.utils.data_loader import list_csv_tables
from streamlit_app.utils.shared import load_table, page_intro, require_dataset

PRIMARY_KEYS = {
    "customers": "customer_id",
    "sellers": "seller_id",
    "products": "product_id",
    "orders": "order_id",
    "order_items": "order_id + order_item_id",
    "payments": "order_id + payment_sequential",
    "shipping": "order_id",
    "reviews": "review_id",
    "calendar": "date",
    "simulation_metadata": "simulation_run_id",
    "data_dictionary": "table_name + column_name",
}

RELATIONSHIPS = (
    ("customers.customer_id", "orders.customer_id", "One customer to many orders"),
    ("orders.order_id", "order_items.order_id", "One order to many items"),
    ("orders.order_id", "payments.order_id", "One order to one or more payments"),
    ("orders.order_id", "shipping.order_id", "One order to one shipping row"),
    ("orders.order_id", "reviews.order_id", "One delivered order to zero or one review"),
    ("products.product_id", "order_items.product_id", "One product to many items"),
    ("sellers.seller_id", "order_items.seller_id", "One seller to many items"),
)

page_intro(
    "Schema and data dictionary",
    "Available tables, inferred pandas data types, documented fields, and known relationships.",
)
dataset_path = require_dataset()
available_tables = list_csv_tables(dataset_path)
if not available_tables:
    st.info("No CSV tables are available in the selected dataset.")
    st.stop()

loaded_tables: dict[str, pd.DataFrame] = {}
summary_rows: list[dict[str, object]] = []
for table_name in available_tables:
    frame = load_table(dataset_path, table_name, required=False)
    if frame is None:
        continue
    loaded_tables[table_name] = frame
    summary_rows.append(
        {
            "table_name": table_name,
            "row_count": len(frame),
            "column_count": len(frame.columns),
            "primary_key": PRIMARY_KEYS.get(table_name, "Not documented"),
        }
    )

st.subheader("Available tables")
st.dataframe(
    pd.DataFrame(summary_rows),
    hide_index=True,
    column_config={
        "row_count": st.column_config.NumberColumn(format="%,d"),
        "column_count": st.column_config.NumberColumn(format="%,d"),
    },
)

if loaded_tables:
    selected_table = st.selectbox(
        "Inspect table schema", tuple(loaded_tables), key="schema_selected_table"
    )
    selected = loaded_tables[selected_table]
    column_schema = pd.DataFrame(
        {
            "column_name": selected.columns,
            "pandas_data_type": [str(dtype) for dtype in selected.dtypes],
            "non_null_rows": [int(selected[column].notna().sum()) for column in selected],
            "null_rows": [int(selected[column].isna().sum()) for column in selected],
        }
    )
    st.dataframe(column_schema, hide_index=True)

st.subheader("Known relationships")
relationship_table = pd.DataFrame(
    RELATIONSHIPS, columns=["primary_key", "foreign_key", "cardinality_note"]
)
st.dataframe(relationship_table, hide_index=True)

data_dictionary = loaded_tables.get("data_dictionary")
if data_dictionary is None:
    st.warning("`data_dictionary.csv` is not available in the selected dataset.")
else:
    st.subheader("Data dictionary")
    table_names = data_dictionary.get("table_name", pd.Series(dtype=str))
    dictionary_tables = sorted(table_names.dropna().unique())
    selected_dictionary_tables = st.multiselect(
        "Dictionary tables",
        dictionary_tables,
        default=dictionary_tables,
        key="schema_dictionary_tables",
    )
    filtered_dictionary = data_dictionary
    if selected_dictionary_tables and "table_name" in data_dictionary:
        filtered_dictionary = data_dictionary[
            data_dictionary["table_name"].isin(selected_dictionary_tables)
        ]
    st.dataframe(filtered_dictionary, hide_index=True)
