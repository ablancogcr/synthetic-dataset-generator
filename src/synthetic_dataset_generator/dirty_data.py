"""Deterministic dirty-data injection and serialized-output auditing."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from synthetic_dataset_generator.config import GeneratorConfig
from synthetic_dataset_generator.random import rng_for
from synthetic_dataset_generator.schemas import REQUIRED_FILES, SCHEMA_REGISTRY
from synthetic_dataset_generator.validators import ValidationCheck, ValidationResult

STRUCTURAL_CHILD_TABLES = ("order_items", "payments", "shipping", "reviews")
EXCLUDED_TABLES = {"simulation_metadata", "data_dictionary"}
PROTECTED_COLUMNS: dict[str, set[str]] = {
    "customers": {"customer_id", "customer_unique_id"},
    "sellers": {"seller_id"},
    "products": {"product_id"},
    "seller_products": {
        "seller_product_id",
        "seller_id",
        "product_id",
        "scenario_name",
    },
    "orders": {"order_id", "customer_id", "scenario_name"},
    "order_items": {
        "order_id",
        "order_item_id",
        "seller_product_id",
        "product_id",
        "seller_id",
        "scenario_name",
    },
    "payments": {"order_id", "payment_sequential", "scenario_name"},
    "shipping": {"order_id", "scenario_name"},
    "reviews": {"review_id", "order_id", "scenario_name"},
    "calendar": {"date"},
}
NEGATIVE_VALUE_COLUMNS = {
    ("products", "product_price_base_usd"),
    ("seller_products", "seller_price_usd"),
    ("order_items", "item_price_usd"),
    ("order_items", "shipping_cost_usd"),
    ("order_items", "item_total_usd"),
    ("payments", "payment_value_usd"),
    ("shipping", "shipping_cost_usd"),
    ("reviews", "review_score"),
}


@dataclass(frozen=True)
class CellTarget:
    defect_type: str
    table: str
    column: str
    row_position: int
    expected_value: object


@dataclass
class DirtyDataResult:
    tables: dict[str, pd.DataFrame]
    manifest: dict[str, Any]
    cell_targets: tuple[CellTarget, ...]
    missing_days: tuple[str, ...]
    removed_order_ids: frozenset[str]
    empty_order_ids: frozenset[str]


def _affected_count(rate: float, population: int) -> int:
    if rate <= 0 or population <= 0:
        return 0
    return min(population, max(1, int(rate * population + 0.5)))


def _choose_positions(
    *,
    seed: int,
    namespace: str,
    population: int,
    rate: float,
    claimed: set[int],
) -> list[int]:
    available = np.array([position for position in range(population) if position not in claimed])
    count = _affected_count(rate, len(available))
    if count == 0:
        return []
    chosen = rng_for(seed, namespace).choice(available, size=count, replace=False)
    positions = sorted(int(position) for position in np.atleast_1d(chosen))
    claimed.update(positions)
    return positions


def _remove_missing_days(
    tables: dict[str, pd.DataFrame], config: GeneratorConfig
) -> tuple[tuple[str, ...], frozenset[str]]:
    orders = tables["orders"]
    purchase_dates = pd.to_datetime(orders["order_purchase_timestamp"]).dt.normalize()
    active_dates = np.array(sorted(purchase_dates.dropna().unique()))
    count = _affected_count(config.data_quality.missing_day_rate, len(active_dates))
    if count == 0:
        return (), frozenset()

    chosen = rng_for(config.dataset.random_seed, "dirty:missing_days").choice(
        active_dates, size=count, replace=False
    )
    chosen_dates = pd.DatetimeIndex(pd.to_datetime(chosen)).normalize()
    removed_mask = purchase_dates.isin(chosen_dates)
    removed_ids = frozenset(orders.loc[removed_mask, "order_id"].astype(str))
    tables["orders"] = orders.loc[~removed_mask].reset_index(drop=True)
    for table_name in STRUCTURAL_CHILD_TABLES:
        tables[table_name] = (
            tables[table_name]
            .loc[~tables[table_name]["order_id"].astype(str).isin(removed_ids)]
            .reset_index(drop=True)
        )
    missing_days = tuple(sorted(timestamp.date().isoformat() for timestamp in chosen_dates))
    return missing_days, removed_ids


def _remove_empty_order_items(
    tables: dict[str, pd.DataFrame], config: GeneratorConfig
) -> frozenset[str]:
    orders = tables["orders"]
    count = _affected_count(config.data_quality.empty_order_rate, len(orders))
    if count == 0:
        return frozenset()
    chosen = rng_for(config.dataset.random_seed, "dirty:empty_orders").choice(
        orders["order_id"].astype(str).to_numpy(), size=count, replace=False
    )
    empty_ids = frozenset(str(order_id) for order_id in np.atleast_1d(chosen))
    items = tables["order_items"]
    tables["order_items"] = (
        items.loc[~items["order_id"].astype(str).isin(empty_ids)].reset_index(drop=True)
    )
    return empty_ids


def _eligible_columns(kind: str) -> list[tuple[str, str]]:
    eligible: list[tuple[str, str]] = []
    for table_name, schema in SCHEMA_REGISTRY.items():
        if table_name in EXCLUDED_TABLES:
            continue
        protected = PROTECTED_COLUMNS.get(table_name, set())
        for column_name, spec in schema.items():
            if column_name in protected:
                continue
            matches_kind = (
                (kind == "null_values" and not spec.nullable and spec.data_type == "string")
                or (
                    kind == "incorrect_date_formats"
                    and spec.data_type in {"date", "datetime"}
                )
                or (
                    kind == "invalid_types"
                    and spec.data_type in {"integer", "float", "boolean"}
                    and (table_name, column_name) not in NEGATIVE_VALUE_COLUMNS
                )
            )
            if matches_kind:
                eligible.append((table_name, column_name))
    return eligible


def _add_cell_defects(
    tables: dict[str, pd.DataFrame], config: GeneratorConfig
) -> tuple[CellTarget, ...]:
    seed = config.dataset.random_seed
    targets: list[CellTarget] = []
    claimed: dict[tuple[str, str], set[int]] = {}
    date_variant = 0

    defect_specs = (
        ("null_values", config.data_quality.null_rate, _eligible_columns("null_values")),
        (
            "incorrect_date_formats",
            config.data_quality.incorrect_date_format_rate,
            _eligible_columns("incorrect_date_formats"),
        ),
        (
            "invalid_types",
            config.data_quality.invalid_type_rate,
            _eligible_columns("invalid_types"),
        ),
        (
            "negative_values",
            config.data_quality.negative_value_rate,
            sorted(NEGATIVE_VALUE_COLUMNS),
        ),
    )
    for defect_type, rate, columns in defect_specs:
        for table_name, column_name in columns:
            frame = tables[table_name]
            if frame.empty or column_name not in frame:
                continue
            key = (table_name, column_name)
            claimed_positions = claimed.setdefault(key, set())
            null_positions = np.flatnonzero(frame[column_name].isna().to_numpy())
            claimed_positions.update(int(position) for position in null_positions)
            positions = _choose_positions(
                seed=seed,
                namespace=f"dirty:{defect_type}:{table_name}:{column_name}",
                population=len(frame),
                rate=rate,
                claimed=claimed_positions,
            )
            if not positions:
                continue
            if defect_type in {"null_values", "incorrect_date_formats", "invalid_types"}:
                frame[column_name] = frame[column_name].astype(object)
            logical_type = SCHEMA_REGISTRY[table_name][column_name].data_type
            for position in positions:
                original = frame.at[position, column_name]
                if defect_type == "null_values":
                    replacement: object = pd.NA
                    expected: object = ""
                elif defect_type == "incorrect_date_formats":
                    timestamp = pd.Timestamp(original)
                    variant = date_variant % 3
                    date_variant += 1
                    if variant == 0:
                        replacement = timestamp.strftime("%m/%d/%Y %H:%M:%S")
                    elif variant == 1:
                        replacement = timestamp.strftime("%d-%m-%Y")
                    else:
                        replacement = "invalid_date"
                    expected = replacement
                elif defect_type == "invalid_types":
                    replacement = (
                        "not_a_boolean" if logical_type == "boolean" else "not_a_number"
                    )
                    expected = replacement
                else:
                    numeric = float(original)
                    replacement = -abs(numeric) if numeric != 0 else -1
                    if logical_type == "integer":
                        replacement = int(replacement)
                    expected = replacement
                frame.at[position, column_name] = replacement
                targets.append(
                    CellTarget(
                        defect_type=defect_type,
                        table=table_name,
                        column=column_name,
                        row_position=position,
                        expected_value=expected,
                    )
                )
    return tuple(targets)


def _build_manifest(
    config: GeneratorConfig,
    targets: tuple[CellTarget, ...],
    missing_days: tuple[str, ...],
    removed_order_ids: frozenset[str],
    empty_order_ids: frozenset[str],
) -> dict[str, Any]:
    grouped = Counter((target.defect_type, target.table, target.column) for target in targets)
    details = [
        {
            "defect_type": defect_type,
            "table": table,
            "column": column,
            "affected_count": count,
        }
        for (defect_type, table, column), count in sorted(grouped.items())
    ]
    details.extend(
        [
            {
                "defect_type": "missing_days",
                "table": "orders",
                "column": "order_purchase_timestamp",
                "affected_count": len(missing_days),
                "related_rows_removed": len(removed_order_ids),
            },
            {
                "defect_type": "empty_orders",
                "table": "order_items",
                "column": "order_id",
                "affected_count": len(empty_order_ids),
            },
        ]
    )
    summary = Counter(target.defect_type for target in targets)
    summary["missing_days"] = len(missing_days)
    summary["empty_orders"] = len(empty_order_ids)
    return {
        "manifest_version": 1,
        "data_quality_mode": "dirty",
        "random_seed": config.dataset.random_seed,
        "configuration": config.data_quality.model_dump(),
        "summary": dict(sorted(summary.items())),
        "defects": details,
    }


def inject_dirty_data(
    tables: dict[str, pd.DataFrame], config: GeneratorConfig
) -> DirtyDataResult:
    """Return dirty copies plus private audit targets and a counts-only public manifest."""
    dirty_tables = {name: frame.copy(deep=True) for name, frame in tables.items()}
    missing_days, removed_ids = _remove_missing_days(dirty_tables, config)
    empty_ids = _remove_empty_order_items(dirty_tables, config)
    for table_name, frame in dirty_tables.items():
        dirty_tables[table_name] = frame.reset_index(drop=True)

    metadata = dirty_tables["simulation_metadata"]
    metadata.loc[0, "requested_number_of_orders"] = config.dataset.number_of_orders
    metadata.loc[0, "number_of_orders"] = len(dirty_tables["orders"])
    metadata.loc[0, "data_quality_mode"] = "dirty"

    targets = _add_cell_defects(dirty_tables, config)
    manifest = _build_manifest(config, targets, missing_days, removed_ids, empty_ids)
    return DirtyDataResult(
        tables=dirty_tables,
        manifest=manifest,
        cell_targets=targets,
        missing_days=missing_days,
        removed_order_ids=removed_ids,
        empty_order_ids=empty_ids,
    )


def write_dirty_manifest(output_dir: Path, manifest: dict[str, Any]) -> None:
    (output_dir / "dirty_data_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


def _load_raw_tables(output_dir: Path) -> dict[str, pd.DataFrame]:
    return {
        table_name: pd.read_csv(
            output_dir / f"{table_name}.csv",
            dtype=str,
            keep_default_na=False,
            na_filter=False,
        )
        for table_name in SCHEMA_REGISTRY
    }


def _cell_target_matches(target: CellTarget, raw_tables: dict[str, pd.DataFrame]) -> bool:
    frame = raw_tables[target.table]
    if target.row_position >= len(frame) or target.column not in frame:
        return False
    actual = frame.iloc[target.row_position][target.column]
    if target.defect_type == "negative_values":
        numeric = pd.to_numeric(pd.Series([actual]), errors="coerce").iloc[0]
        return bool(pd.notna(numeric) and numeric < 0)
    return str(actual) == str(target.expected_value)


def _expected_issue_check(name: str, expected_count: int, actual_count: int) -> ValidationCheck:
    details = f"Expected {expected_count:,} injected defects; found {actual_count:,} after export."
    if expected_count == 0:
        return ValidationCheck(name=name, passed=actual_count == 0, details=details)
    if actual_count == expected_count:
        return ValidationCheck(name=name, passed=False, expected=True, details=details)
    return ValidationCheck(name=name, passed=False, details=details)


def audit_dirty_output(
    output_dir: Path,
    dirty: DirtyDataResult,
    source_validation: ValidationResult,
) -> ValidationResult:
    """Audit the serialized dirty package without coercing or repairing source values."""
    raw_tables = _load_raw_tables(output_dir)
    checks = [
        ValidationCheck(
            name=f"source_{check.name}",
            passed=check.passed,
            details=check.details,
        )
        for check in source_validation.checks
    ]
    required = [*REQUIRED_FILES, "dirty_data_manifest.json"]
    missing_files = [name for name in required if not (output_dir / name).is_file()]
    checks.append(
        ValidationCheck(
            name="required_files",
            passed=not missing_files,
            details=f"Missing files: {missing_files}",
        )
    )

    expected_by_type = Counter(target.defect_type for target in dirty.cell_targets)
    actual_by_type = Counter(
        target.defect_type
        for target in dirty.cell_targets
        if _cell_target_matches(target, raw_tables)
    )
    for defect_type in (
        "null_values",
        "incorrect_date_formats",
        "invalid_types",
        "negative_values",
    ):
        checks.append(
            _expected_issue_check(
                f"dirty_{defect_type}",
                expected_by_type[defect_type],
                actual_by_type[defect_type],
            )
        )

    order_ids = set(raw_tables["orders"]["order_id"])
    calendar_dates = set(
        pd.to_datetime(raw_tables["calendar"]["date"], errors="coerce")
        .dropna()
        .dt.date.astype(str)
    )
    removed_absent = dirty.removed_order_ids.isdisjoint(order_ids) and all(
        dirty.removed_order_ids.isdisjoint(set(raw_tables[name]["order_id"]))
        for name in STRUCTURAL_CHILD_TABLES
    )
    missing_days_match = removed_absent and set(dirty.missing_days).issubset(calendar_dates)
    checks.append(
        _expected_issue_check(
            "dirty_missing_days",
            len(dirty.missing_days),
            len(dirty.missing_days) if missing_days_match else 0,
        )
    )

    item_ids = set(raw_tables["order_items"]["order_id"])
    payment_ids = set(raw_tables["payments"]["order_id"])
    shipping_ids = set(raw_tables["shipping"]["order_id"])
    matching_empty_orders = sum(
        order_id in order_ids
        and order_id not in item_ids
        and order_id in payment_ids
        and order_id in shipping_ids
        for order_id in dirty.empty_order_ids
    )
    checks.append(
        _expected_issue_check(
            "dirty_empty_orders", len(dirty.empty_order_ids), matching_empty_orders
        )
    )

    try:
        manifest = json.loads((output_dir / "dirty_data_manifest.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        manifest = None
    checks.append(
        ValidationCheck(
            name="dirty_manifest_serialization",
            passed=manifest == dirty.manifest,
            details="Counts-only manifest matches the injected defect summary.",
        )
    )
    return ValidationResult(checks=checks, source_integrity_status="passed")
