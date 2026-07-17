from __future__ import annotations

from collections.abc import Callable

from synthetic_dataset_generator.config import GeneratorConfig, ScenarioConfig
from synthetic_dataset_generator.exporters import export_dataset
from synthetic_dataset_generator.generator import DatasetGenerator
from synthetic_dataset_generator.validators import validate_dataset


def test_valid_dataset_passes_all_checks(
    config_factory: Callable[..., GeneratorConfig], scenarios: dict[str, ScenarioConfig]
) -> None:
    dataset = DatasetGenerator(config_factory(orders=180), scenarios["baseline"]).generate()
    result = validate_dataset(dataset.tables)
    assert result.passed, [check for check in result.checks if not check.passed]


def test_failed_validation_writes_reports_but_not_zip(
    tmp_path, config_factory: Callable[..., GeneratorConfig], scenarios: dict[str, ScenarioConfig]
) -> None:
    dataset = DatasetGenerator(config_factory(orders=80), scenarios["baseline"]).generate()
    dataset.tables["orders"].loc[0, "customer_id"] = "missing_customer"
    result = export_dataset(dataset, tmp_path)
    assert not result.validation.passed
    assert result.zip_path is None
    assert (result.output_dir / "validation_summary.json").is_file()
    assert (result.output_dir / "validation_summary.md").is_file()


def test_listing_validation_detects_mismatches_and_duplicate_pairs(
    config_factory: Callable[..., GeneratorConfig], scenarios: dict[str, ScenarioConfig]
) -> None:
    config = config_factory(orders=100)
    dataset = DatasetGenerator(config, scenarios["baseline"]).generate()
    tables = {name: frame.copy(deep=True) for name, frame in dataset.tables.items()}
    listings = tables["seller_products"]
    items = tables["order_items"]

    items.loc[0, "seller_product_id"] = listings.iloc[1]["seller_product_id"]
    listings.loc[1, ["seller_id", "product_id"]] = listings.loc[
        0, ["seller_id", "product_id"]
    ].to_numpy()

    result = validate_dataset(tables, config=config)
    failures = {check.name for check in result.unexpected_failures}
    assert "unique_seller_product_pairs" in failures
    assert "order_item_listing_consistency" in failures
