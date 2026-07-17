"""Shared page state, loading, and empty-state helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from streamlit_app.utils.data_loader import DataLoadError, file_signature
from streamlit_app.utils.streamlit_cache import load_csv_cached

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "output"
GITHUB_URL = "https://github.com/ablancogcr/synthetic-dataset-generator"
SYNTHETIC_DISCLAIMER = (
    "This viewer displays fully synthetic data. It contains no real customers, sellers, "
    "orders, companies, or performance and must not be used as real market data or for "
    "operational decisions."
)


def selected_dataset_path() -> Path | None:
    value = st.session_state.get("selected_dataset_path")
    return Path(value) if value else None


def require_dataset() -> Path:
    dataset_path = selected_dataset_path()
    if dataset_path is None or not dataset_path.is_dir():
        st.info(
            "Generate a dataset under `data/output/`, or provide an exact local dataset folder "
            "in the sidebar."
        )
        st.stop()
    return dataset_path


def load_table(
    dataset_path: Path, table_name: str, *, required: bool = True
) -> pd.DataFrame | None:
    csv_path = dataset_path / f"{table_name}.csv"
    if not csv_path.is_file():
        message = f"`{csv_path.name}` is not available in the selected dataset."
        (st.error if required else st.warning)(message)
        return None
    try:
        resolved, modified_time = file_signature(csv_path)
        return load_csv_cached(resolved, modified_time)
    except DataLoadError as exc:
        st.error(str(exc))
        return None


def load_tables(
    dataset_path: Path, table_names: tuple[str, ...], *, required: bool = True
) -> dict[str, pd.DataFrame] | None:
    tables: dict[str, pd.DataFrame] = {}
    for table_name in table_names:
        table = load_table(dataset_path, table_name, required=required)
        if table is None:
            if required:
                return None
            continue
        tables[table_name] = table
    return tables


def page_intro(title: str, description: str) -> None:
    st.title(title)
    st.caption(description)
    metadata = st.session_state.get("dataset_metadata", {})
    if metadata.get("data_quality_mode") == "dirty":
        st.warning(
            "This is an intentionally dirty training dataset. Viewer metrics can exclude or "
            "coerce invalid cells for display; use Data explorer to inspect the unchanged CSV "
            "values.",
            icon=":material/warning:",
        )


def show_disclaimer() -> None:
    st.info(SYNTHETIC_DISCLAIMER, icon=":material/info:")
