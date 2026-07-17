"""Create a dataset package through the same workflow as the CLI."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from pydantic import ValidationError

from streamlit_app.utils.shared import DEFAULT_OUTPUT_ROOT, PROJECT_ROOT, SYNTHETIC_DISCLAIMER
from synthetic_dataset_generator.config import load_config
from synthetic_dataset_generator.workflow import GenerationRequest, run_generation

DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "default_config.yaml"
DEFAULT_SCENARIOS_PATH = PROJECT_ROOT / "config" / "scenarios.yaml"
SCENARIOS = ("baseline", "holiday_spike", "logistics_improvement", "seller_churn")


def resolve_local_path(value: str) -> Path:
    """Resolve form paths relative to the repository, like the documented CLI command."""
    path = Path(value.strip()).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


try:
    defaults = load_config(DEFAULT_CONFIG_PATH)
except (FileNotFoundError, OSError, ValidationError, ValueError) as exc:
    st.error(f"Unable to load the default generator configuration: {exc}")
    st.stop()

st.title("Generate dataset")
st.caption("Run the same local generation workflow as `synthetic-dataset-generator generate`.")
st.info(SYNTHETIC_DISCLAIMER, icon=":material/info:")

previous_run = st.session_state.get("generation_result")
if previous_run:
    status_state = "complete" if previous_run["validation_passed"] else "error"
    with st.status("Last generation output", state=status_state, expanded=False):
        for message in previous_run["messages"]:
            st.write(message)

    if previous_run["validation_passed"]:
        st.success(f"Validation: {previous_run['validation_status']}")
    else:
        st.error(f"Validation: {previous_run['validation_status']}")
    st.caption("Dataset folder")
    st.code(previous_run["output_dir"], language=None)

    zip_path = Path(previous_run["zip_path"]) if previous_run["zip_path"] else None
    if zip_path is not None and zip_path.is_file():
        st.download_button(
            "Download ZIP package",
            data=lambda: zip_path.read_bytes(),
            file_name=zip_path.name,
            mime="application/zip",
            on_click="ignore",
            icon=":material/download:",
            type="primary",
        )
    st.page_link(
        "app_pages/overview.py",
        label="Open generated dataset",
        icon=":material/dashboard:",
    )
    st.divider()

with st.form("generate_dataset_form", enter_to_submit=False):
    st.subheader("CLI options")
    left, right = st.columns(2)
    with left:
        config_value = st.text_input(
            "Config YAML path",
            value=str(DEFAULT_CONFIG_PATH.relative_to(PROJECT_ROOT)),
            help="Equivalent to `--config`.",
        )
        output_value = st.text_input(
            "Output directory",
            value=str(DEFAULT_OUTPUT_ROOT.relative_to(PROJECT_ROOT)),
            help="Equivalent to `--output`.",
        )
        scenario_value = st.selectbox(
            "Scenario",
            SCENARIOS,
            index=SCENARIOS.index(defaults.simulation.scenario),
            help="Equivalent to `--scenario`.",
        )
        dirty_value = st.checkbox(
            "Enable dirty-data mode",
            value=False,
            help=(
                "Equivalent to adding `--dirty`; when clear, the config file's data-quality "
                "mode is kept."
            ),
        )
    with right:
        scenarios_value = st.text_input(
            "Scenarios YAML path",
            value=str(DEFAULT_SCENARIOS_PATH.relative_to(PROJECT_ROOT)),
            help="Equivalent to `--scenarios`.",
        )
        orders_value = st.number_input(
            "Order count",
            min_value=1,
            value=defaults.dataset.number_of_orders,
            step=1,
            help="Equivalent to `--orders`.",
        )
        seed_value = st.number_input(
            "Random seed",
            min_value=0,
            value=defaults.dataset.random_seed,
            step=1,
            help="Equivalent to `--seed`.",
        )
        overwrite_value = st.checkbox(
            "Overwrite an existing matching package",
            value=False,
            help=(
                "Equivalent to `--overwrite`. This only replaces the exact derived output "
                "folder and ZIP."
            ),
        )

    submitted = st.form_submit_button(
        "Generate dataset",
        type="primary",
        icon=":material/play_arrow:",
        width="stretch",
    )

if submitted:
    messages: list[str] = []
    status = st.status("Generating dataset...", expanded=True)

    def report(message: str) -> None:
        messages.append(message)
        status.write(message)

    try:
        request = GenerationRequest(
            config_path=resolve_local_path(config_value),
            scenarios_path=resolve_local_path(scenarios_value),
            output_root=resolve_local_path(output_value),
            scenario=scenario_value,
            orders=int(orders_value),
            seed=int(seed_value),
            dirty=True if dirty_value else None,
            overwrite=overwrite_value,
        )
        if not request.config_path.is_file():
            raise FileNotFoundError(f"Config file does not exist: {request.config_path}")
        if not request.scenarios_path.is_file():
            raise FileNotFoundError(f"Scenarios file does not exist: {request.scenarios_path}")

        run = run_generation(request, progress=report)
    except (FileNotFoundError, OSError, KeyError, ValidationError, ValueError) as exc:
        status.update(label="Dataset generation failed", state="error", expanded=True)
        st.error(str(exc))
    else:
        validation_passed = run.result.validation.passed
        status.update(
            label=("Dataset generation complete" if validation_passed else "Validation failed"),
            state=("complete" if validation_passed else "error"),
            expanded=not validation_passed,
        )
        st.session_state["generation_result"] = {
            "messages": messages,
            "output_dir": str(run.result.output_dir),
            "zip_path": str(run.result.zip_path) if run.result.zip_path else None,
            "validation_status": run.result.validation.overall_status.upper(),
            "validation_passed": validation_passed,
        }
        st.session_state["generated_dataset_path"] = str(run.result.output_dir)
        st.session_state["pending_dataset_selection"] = str(run.result.output_dir.resolve())
        st.rerun()
