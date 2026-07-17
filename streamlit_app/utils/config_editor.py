"""Safe YAML editing helpers for the local configuration page."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import yaml

from synthetic_dataset_generator.config import GeneratorConfig, ScenarioConfig

YamlMapping = dict[str, Any]
ConfigValidator = Callable[[Mapping[str, Any]], None]
EXPECTED_SCENARIOS = frozenset(
    {"baseline", "holiday_spike", "logistics_improvement", "seller_churn"}
)


def read_yaml_mapping(path: str | Path) -> YamlMapping:
    """Load a YAML mapping without applying model defaults or changing its shape."""
    yaml_path = Path(path)
    with yaml_path.open(encoding="utf-8") as handle:
        content = yaml.safe_load(handle)
    if not isinstance(content, dict):
        raise ValueError(f"{yaml_path.name} must contain a YAML mapping.")
    return deepcopy(content)


def validate_generator_config(values: Mapping[str, Any]) -> None:
    """Validate default configuration values with the generator's production schema."""
    GeneratorConfig.model_validate(values)


def validate_scenario_config(values: Mapping[str, Any]) -> None:
    """Validate scenario configuration values with the generator's production schema."""
    missing = EXPECTED_SCENARIOS.difference(values)
    if missing:
        raise ValueError(f"Missing scenario definitions: {', '.join(sorted(missing))}")
    for name, scenario_values in values.items():
        if not isinstance(scenario_values, Mapping):
            raise ValueError(f"Scenario '{name}' must contain a mapping.")
        ScenarioConfig.model_validate(scenario_values)


def _matching_shape(original: Any, candidate: Any) -> bool:
    """Return whether two values have exactly the same nested mapping keys."""
    if isinstance(original, Mapping):
        return (
            isinstance(candidate, Mapping)
            and set(original) == set(candidate)
            and all(_matching_shape(original[key], candidate[key]) for key in original)
        )
    return not isinstance(candidate, Mapping)


def save_valid_yaml(
    path: str | Path,
    *,
    original: Mapping[str, Any],
    candidate: Mapping[str, Any],
    validator: ConfigValidator,
) -> None:
    """Validate and atomically persist existing YAML values without allowing new keys."""
    if not _matching_shape(original, candidate):
        raise ValueError(
            "The configuration structure changed; adding or removing parameters is not allowed."
        )
    validator(candidate)

    yaml_path = Path(path)
    serialized = yaml.safe_dump(
        dict(candidate),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=yaml_path.parent,
        prefix=f".{yaml_path.stem}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temporary_path = Path(handle.name)
        handle.write(serialized)
    try:
        temporary_path.replace(yaml_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
