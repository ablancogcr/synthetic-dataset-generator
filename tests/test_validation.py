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
