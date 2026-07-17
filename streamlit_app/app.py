"""Entry point for the local synthetic ecommerce dataset app."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Streamlit places this nested entrypoint directory on sys.path. Add the repository root so the
# streamlit_app package remains importable when launched with the documented command.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from streamlit_app.utils.data_loader import DataLoadError  # noqa: E402
from streamlit_app.utils.dataset_discovery import (  # noqa: E402
    DatasetDirectory,
    discover_datasets,
    inspect_dataset_directory,
)
from streamlit_app.utils.shared import DEFAULT_OUTPUT_ROOT, GITHUB_URL  # noqa: E402
from streamlit_app.utils.streamlit_cache import (  # noqa: E402
    load_metadata_cached,
    optional_mtime,
)

st.set_page_config(
    page_title="Synthetic dataset generator",
    page_icon=":material/table_view:",
    layout="wide",
)


def dataset_label(path_value: str) -> str:
    path = Path(path_value)
    return f"{path.name} — {path.parent}"


discovery = discover_datasets(DEFAULT_OUTPUT_ROOT)
dataset_by_path: dict[str, DatasetDirectory] = {
    str(dataset.path): dataset for dataset in discovery.datasets
}
generated_dataset_value = st.session_state.get("generated_dataset_path")
if generated_dataset_value:
    generated_dataset = inspect_dataset_directory(generated_dataset_value)
    if generated_dataset is not None and generated_dataset.is_valid:
        dataset_by_path[str(generated_dataset.path)] = generated_dataset

with st.sidebar:
    st.header("Dataset")
    st.caption("Reads generated CSV packages from this computer only.")
    custom_folder = st.text_input(
        "Other local dataset folder",
        placeholder=r"C:\path\to\generated_dataset",
        help=(
            "Enter the exact folder containing generated CSV files. The viewer does not upload it."
        ),
        key="custom_dataset_folder",
    ).strip()

    if custom_folder:
        custom_dataset = inspect_dataset_directory(custom_folder)
        if custom_dataset is None:
            st.warning("That folder does not exist or contains no generator output files.")
        elif not custom_dataset.is_valid:
            missing = ", ".join(f"{name}.csv" for name in custom_dataset.missing_core_tables)
            st.warning(f"That dataset is incomplete. Missing: {missing}.")
        else:
            dataset_by_path[str(custom_dataset.path)] = custom_dataset

    options = sorted(dataset_by_path, key=lambda value: Path(value).name.lower())
    pending_selection = st.session_state.pop("pending_dataset_selection", None)
    if pending_selection in options:
        st.session_state["selected_dataset_path"] = pending_selection
    current = st.session_state.get("selected_dataset_path")
    if current not in options:
        st.session_state["selected_dataset_path"] = options[0] if options else None

    if options:
        selected_value = st.selectbox(
            "Selected dataset",
            options,
            format_func=dataset_label,
            key="selected_dataset_path",
        )
        selected = dataset_by_path[selected_value]
        metadata_path = selected.path / "simulation_metadata.csv"
        try:
            metadata = load_metadata_cached(str(selected.path), optional_mtime(metadata_path))
        except DataLoadError as exc:
            st.error(str(exc))
            metadata = {}
        st.session_state["dataset_metadata"] = metadata

        st.divider()
        st.caption("Scenario")
        st.write(metadata.get("scenario_name") or "Not available")
        st.caption("Order count")
        order_count = metadata.get("number_of_orders")
        st.write(f"{int(order_count):,}" if order_count is not None else "Not available")
        st.caption("Date range")
        start = metadata.get("start_date") or "Unknown"
        end = metadata.get("end_date") or "Unknown"
        st.write(f"{start} to {end}")
        st.caption("Random seed")
        seed = metadata.get("random_seed")
        st.write(str(int(seed)) if seed is not None else "Not available")
        st.caption("Data quality mode")
        st.write(metadata.get("data_quality_mode") or "clean")
        st.caption("Available tables")
        st.write(", ".join(selected.available_tables))
    else:
        st.session_state["dataset_metadata"] = {}
        if not DEFAULT_OUTPUT_ROOT.exists():
            st.info("`data/output/` does not exist yet. Generate a dataset first.")
        else:
            st.info("No complete generated datasets were found under `data/output/`.")

    if discovery.incomplete:
        with st.expander("Incomplete folders"):
            for candidate in discovery.incomplete:
                missing = ", ".join(f"{name}.csv" for name in candidate.missing_core_tables)
                st.write(f"**{candidate.path.name}:** missing {missing}")

    st.link_button("View source repository", GITHUB_URL, icon=":material/code:")

pages = [
    st.Page("app_pages/generate.py", title="Generate dataset", icon=":material/add_box:"),
    st.Page("app_pages/overview.py", title="Overview", icon=":material/dashboard:"),
    st.Page("app_pages/data_explorer.py", title="Data explorer", icon=":material/table_view:"),
    st.Page(
        "app_pages/marketplace_analysis.py",
        title="Marketplace analysis",
        icon=":material/analytics:",
    ),
    st.Page(
        "app_pages/shipping_and_reviews.py",
        title="Shipping and reviews",
        icon=":material/local_shipping:",
    ),
    st.Page("app_pages/data_quality.py", title="Data quality", icon=":material/fact_check:"),
    st.Page("app_pages/schema.py", title="Schema", icon=":material/account_tree:"),
]

navigation = st.navigation(pages, position="top")
navigation.run()
