from __future__ import annotations

import json
from collections.abc import Callable
from zipfile import ZipFile

import pandas as pd

from synthetic_dataset_generator.config import GeneratorConfig, ScenarioConfig
from synthetic_dataset_generator.dirty_data import inject_dirty_data
from synthetic_dataset_generator.exporters import dataset_basename, export_dataset
from synthetic_dataset_generator.generator import DatasetGenerator


def _dirty_config(config: GeneratorConfig, **overrides: float) -> GeneratorConfig:
    values = config.model_dump()
    values["data_quality"] = {
        "mode": "dirty",
        "null_rate": 0.02,
        "missing_day_rate": 0.02,
        "incorrect_date_format_rate": 0.02,
        "invalid_type_rate": 0.02,
        "negative_value_rate": 0.02,
        "empty_order_rate": 0.02,
        **overrides,
    }
    return GeneratorConfig.model_validate(values)


def test_dirty_injection_is_structured_and_protects_identifiers(
    config_factory: Callable[..., GeneratorConfig], scenarios: dict[str, ScenarioConfig]
) -> None:
    config = _dirty_config(config_factory(orders=400, seed=17))
    clean = DatasetGenerator(config, scenarios["baseline"]).generate()
    dirty = inject_dirty_data(clean.tables, config)

    assert dirty.missing_days
    assert dirty.empty_order_ids
    assert dirty.manifest["data_quality_mode"] == "dirty"
    assert all(count > 0 for count in dirty.manifest["summary"].values())

    order_dates = pd.to_datetime(
        dirty.tables["orders"]["order_purchase_timestamp"], errors="coerce"
    ).dt.date.astype("string")
    calendar_dates = pd.to_datetime(dirty.tables["calendar"]["date"]).dt.date.astype("string")
    assert set(dirty.missing_days).isdisjoint(set(order_dates.dropna()))
    assert set(dirty.missing_days) <= set(calendar_dates)
    for table_name in ("orders", "order_items", "payments", "shipping", "reviews"):
        assert dirty.removed_order_ids.isdisjoint(set(dirty.tables[table_name]["order_id"]))

    assert dirty.empty_order_ids <= set(dirty.tables["orders"]["order_id"])
    assert dirty.empty_order_ids.isdisjoint(set(dirty.tables["order_items"]["order_id"]))
    assert dirty.empty_order_ids <= set(dirty.tables["payments"]["order_id"])
    assert dirty.empty_order_ids <= set(dirty.tables["shipping"]["order_id"])

    protected = {
        "customers": ("customer_id", "customer_unique_id"),
        "seller_products": (
            "seller_product_id",
            "seller_id",
            "product_id",
            "scenario_name",
        ),
        "orders": ("order_id", "customer_id", "scenario_name"),
        "order_items": (
            "order_id",
            "order_item_id",
            "seller_product_id",
            "product_id",
            "seller_id",
        ),
        "payments": ("order_id", "payment_sequential"),
        "shipping": ("order_id",),
        "reviews": ("review_id", "order_id"),
        "calendar": ("date",),
    }
    for table_name, columns in protected.items():
        assert not dirty.tables[table_name][list(columns)].isna().any().any()
    listing_targets = {
        (target.defect_type, target.column)
        for target in dirty.cell_targets
        if target.table == "seller_products"
    }
    assert ("negative_values", "seller_price_usd") in listing_targets
    assert ("incorrect_date_formats", "listing_created_at") in listing_targets
    assert ("invalid_types", "listing_active_flag") in listing_targets


def test_dirty_targets_are_deterministic_and_namespaced(
    config_factory: Callable[..., GeneratorConfig], scenarios: dict[str, ScenarioConfig]
) -> None:
    config = _dirty_config(config_factory(orders=240, seed=29))
    first = inject_dirty_data(
        DatasetGenerator(config, scenarios["baseline"]).generate().tables, config
    )
    second = inject_dirty_data(
        DatasetGenerator(config, scenarios["baseline"]).generate().tables, config
    )

    assert first.manifest == second.manifest
    assert first.cell_targets == second.cell_targets
    for table_name in (
        "customers",
        "sellers",
        "products",
        "seller_products",
        "orders",
        "order_items",
        "payments",
        "shipping",
        "reviews",
        "calendar",
    ):
        pd.testing.assert_frame_equal(first.tables[table_name], second.tables[table_name])

    changed_rate = _dirty_config(config_factory(orders=240, seed=29), null_rate=0.04)
    changed = inject_dirty_data(
        DatasetGenerator(changed_rate, scenarios["baseline"]).generate().tables,
        changed_rate,
    )
    unchanged_first = [
        target for target in first.cell_targets if target.defect_type != "null_values"
    ]
    unchanged_changed = [
        target for target in changed.cell_targets if target.defect_type != "null_values"
    ]
    assert unchanged_first == unchanged_changed

    different_seed = _dirty_config(config_factory(orders=240, seed=30))
    different = inject_dirty_data(
        DatasetGenerator(different_seed, scenarios["baseline"]).generate().tables,
        different_seed,
    )
    first_locations = [
        (target.defect_type, target.table, target.column, target.row_position)
        for target in first.cell_targets
    ]
    different_locations = [
        (target.defect_type, target.table, target.column, target.row_position)
        for target in different.cell_targets
    ]
    assert first_locations != different_locations


def test_dirty_export_packages_expected_issues_and_counts_only_manifest(
    tmp_path,
    config_factory: Callable[..., GeneratorConfig],
    scenarios: dict[str, ScenarioConfig],
) -> None:
    config = _dirty_config(config_factory(orders=320, seed=31))
    dataset = DatasetGenerator(config, scenarios["baseline"]).generate()

    assert dataset_basename(dataset) == "ecommerce_baseline_320_seed31_dirty"
    result = export_dataset(dataset, tmp_path)

    assert result.validation.passed
    assert result.validation.overall_status == "expected_issues"
    assert result.validation.expected_issues
    assert result.zip_path is not None
    manifest_path = result.output_dir / "dirty_data_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_text = manifest_path.read_text(encoding="utf-8")
    assert manifest["summary"]["missing_days"] > 0
    assert manifest["summary"]["empty_orders"] > 0
    assert "order_000" not in manifest_text
    assert "row_id" not in manifest_text
    assert "2024-" not in manifest_text
    assert "2025-" not in manifest_text
    assert "2026-" not in manifest_text

    validation = json.loads(
        (result.output_dir / "validation_summary.json").read_text(encoding="utf-8")
    )
    assert validation["overall_status"] == "expected_issues"
    assert validation["source_integrity_status"] == "passed"
    assert validation["checks_expected_issues"] >= 6
    assert validation["checks_failed"] == 0

    csv_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in result.output_dir.glob("*.csv")
    )
    assert "not_a_number" in csv_text
    assert "invalid_date" in csv_text
    reviews = pd.read_csv(result.output_dir / "reviews.csv")
    items = pd.read_csv(result.output_dir / "order_items.csv")
    seller_products = pd.read_csv(result.output_dir / "seller_products.csv")
    assert pd.to_numeric(reviews["review_score"], errors="coerce").min() < 0
    assert pd.to_numeric(items["item_price_usd"], errors="coerce").min() < 0
    assert pd.to_numeric(seller_products["seller_price_usd"], errors="coerce").min() < 0
    assert seller_products["seller_product_id"].notna().all()
    assert seller_products["seller_id"].notna().all()
    assert seller_products["product_id"].notna().all()
    with ZipFile(result.zip_path) as archive:
        assert "dirty_data_manifest.json" in archive.namelist()


def test_invalid_clean_source_still_blocks_dirty_zip(
    tmp_path,
    config_factory: Callable[..., GeneratorConfig],
    scenarios: dict[str, ScenarioConfig],
) -> None:
    config = _dirty_config(config_factory(orders=80))
    dataset = DatasetGenerator(config, scenarios["baseline"]).generate()
    dataset.tables["orders"].loc[0, "customer_id"] = "missing_customer"

    result = export_dataset(dataset, tmp_path)

    assert not result.validation.passed
    assert result.validation.overall_status == "failed"
    assert result.zip_path is None
    assert not (result.output_dir / "dirty_data_manifest.json").exists()
