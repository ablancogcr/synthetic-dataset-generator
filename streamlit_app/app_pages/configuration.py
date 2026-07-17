"""View and safely edit the repository's existing generator configuration values."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any

import streamlit as st
from pydantic import ValidationError

from streamlit_app.utils.config_editor import (
    ConfigValidator,
    read_yaml_mapping,
    save_valid_yaml,
    validate_generator_config,
    validate_scenario_config,
)
from streamlit_app.utils.shared import PROJECT_ROOT

CONFIG_FILES: dict[str, tuple[Path, ConfigValidator]] = {
    "Dataset settings": (
        PROJECT_ROOT / "config" / "default_config.yaml",
        validate_generator_config,
    ),
    "Scenario rules": (PROJECT_ROOT / "config" / "scenarios.yaml", validate_scenario_config),
}
SCENARIOS = ("baseline", "holiday_spike", "logistics_improvement", "seller_churn")


def _widget_key(file_label: str, path: tuple[str, ...]) -> str:
    return "configuration_" + "_".join((file_label.replace(" ", "_").lower(), *path))


def _options_for(path: tuple[str, ...]) -> tuple[str, ...] | None:
    if path[-1] == "scenario":
        return SCENARIOS
    if path[-1] == "mode":
        return ("clean", "dirty")
    if path[-1] == "format":
        return ("csv",)
    if path[-1] == "currency":
        return ("USD",)
    return None


def _edit_value(file_label: str, path: tuple[str, ...], value: Any) -> Any:
    """Render a control for an existing scalar and return its typed value."""
    label = path[-1].replace("_", " ").capitalize()
    key = _widget_key(file_label, path)
    options = _options_for(path)
    if options is not None:
        return st.selectbox(label, options, index=options.index(value), key=key)
    if isinstance(value, bool):
        return st.checkbox(label, value=value, key=key)
    if isinstance(value, int):
        return int(st.number_input(label, value=value, step=1, key=key))
    if isinstance(value, float):
        return float(st.number_input(label, value=value, step=0.001, format="%.6f", key=key))
    if path[-1] in {"start_date", "end_date"}:
        return st.date_input(label, value=date.fromisoformat(str(value)), key=key).isoformat()
    return st.text_input(label, value=str(value), key=key)


def _edit_mapping(
    file_label: str, values: Mapping[str, Any], path: tuple[str, ...] = ()
) -> dict[str, Any]:
    """Render only existing keys, recursively preserving the original mapping structure."""
    edited: dict[str, Any] = {}
    for name, value in values.items():
        current_path = (*path, name)
        if isinstance(value, Mapping):
            st.caption(name.replace("_", " ").capitalize())
            with st.container(border=True):
                edited[name] = _edit_mapping(file_label, value, current_path)
        else:
            edited[name] = _edit_value(file_label, current_path, value)
    return edited


st.title("Configuration")
st.caption("View and edit the existing local YAML settings used by the generator.")
st.warning(
    "This page cannot add or remove parameters. Changes are saved only after the complete file "
    "passes the generator's validation rules.",
    icon=":material/verified_user:",
)

file_label = st.selectbox("Configuration file", tuple(CONFIG_FILES))
config_path, validator = CONFIG_FILES[file_label]

try:
    original = read_yaml_mapping(config_path)
    validator(original)
except (FileNotFoundError, OSError, ValidationError, ValueError) as exc:
    st.error(f"Unable to load a valid {config_path.name}: {exc}")
    st.stop()

st.caption(f"Editing `{config_path.relative_to(PROJECT_ROOT)}`")
with st.form(f"configuration_form_{file_label.replace(' ', '_').lower()}", enter_to_submit=False):
    candidate = _edit_mapping(file_label, deepcopy(original))
    submitted = st.form_submit_button(
        "Save valid changes",
        type="primary",
        icon=":material/save:",
        width="stretch",
    )

if submitted:
    try:
        save_valid_yaml(
            config_path,
            original=original,
            candidate=candidate,
            validator=validator,
        )
    except (OSError, ValidationError, ValueError) as exc:
        st.error(f"Changes were not saved. Fix the validation error: {exc}")
    else:
        st.success(f"Saved validated changes to `{config_path.relative_to(PROJECT_ROOT)}`.")
