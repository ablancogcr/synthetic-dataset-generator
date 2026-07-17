"""Interactive table preview and CSV download."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_app.utils.data_loader import list_csv_tables
from streamlit_app.utils.shared import load_table, page_intro, require_dataset
from streamlit_app.utils.streamlit_cache import dataframe_to_csv_bytes

page_intro(
    "Data explorer",
    "Preview, search, sort, and download any CSV table in the selected dataset.",
)
dataset_path = require_dataset()
available_tables = list_csv_tables(dataset_path)
if not available_tables:
    st.info("No CSV tables are available in this dataset folder.")
    st.stop()

table_name = st.selectbox("Table", available_tables, key="explorer_table")
table = load_table(dataset_path, table_name)
if table is None:
    st.stop()

with st.container(horizontal=True):
    st.metric("Rows", f"{len(table):,}", border=True)
    st.metric("Columns", f"{len(table.columns):,}", border=True)

st.subheader("Columns and data types")
schema_preview = pd.DataFrame(
    {"column_name": table.columns, "data_type": [str(dtype) for dtype in table.dtypes]}
)
st.dataframe(schema_preview, hide_index=True)

visible_columns = st.multiselect(
    "Visible columns",
    list(table.columns),
    default=list(table.columns),
    key=f"explorer_visible_{table_name}",
)
if not visible_columns:
    st.warning("Select at least one visible column.")
    st.stop()

with st.container(horizontal=True):
    search_text = st.text_input(
        "Text search",
        placeholder="Search displayed columns",
        key=f"explorer_search_{table_name}",
    )
    sort_column = st.selectbox(
        "Sort column",
        ["No sorting", *visible_columns],
        key=f"explorer_sort_{table_name}",
    )
    descending = st.toggle("Descending", key=f"explorer_desc_{table_name}")
    row_limit = st.number_input(
        "Displayed rows",
        min_value=1,
        max_value=max(1, min(len(table), 5000)),
        value=min(max(1, len(table)), 500),
        step=100,
        key=f"explorer_limit_{table_name}",
    )

filtered = table
if search_text:
    searchable = filtered[visible_columns].astype("string")
    mask = searchable.apply(
        lambda column: column.str.contains(search_text, case=False, na=False, regex=False)
    ).any(axis=1)
    filtered = filtered.loc[mask]

if sort_column != "No sorting":
    try:
        filtered = filtered.sort_values(sort_column, ascending=not descending, na_position="last")
    except TypeError:
        st.warning(f"`{sort_column}` contains mixed values and could not be sorted reliably.")

st.caption(f"Showing {min(len(filtered), int(row_limit)):,} of {len(filtered):,} matching rows.")
st.dataframe(filtered.loc[:, visible_columns].head(int(row_limit)), hide_index=True)
st.download_button(
    "Download full table as CSV",
    data=dataframe_to_csv_bytes(table),
    file_name=f"{table_name}.csv",
    mime="text/csv",
    icon=":material/download:",
)
