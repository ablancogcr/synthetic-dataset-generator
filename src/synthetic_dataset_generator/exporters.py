"""CSV, validation-report, and ZIP export."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from synthetic_dataset_generator.dirty_data import (
    audit_dirty_output,
    inject_dirty_data,
    write_dirty_manifest,
)
from synthetic_dataset_generator.generator import GeneratedDataset
from synthetic_dataset_generator.validators import ValidationResult, validate_dataset


@dataclass(frozen=True)
class ExportResult:
    output_dir: Path
    zip_path: Path | None
    validation: ValidationResult


def dataset_basename(dataset: GeneratedDataset) -> str:
    config = dataset.config
    basename = (
        f"ecommerce_{config.simulation.scenario}_"
        f"{config.dataset.number_of_orders}_seed{config.dataset.random_seed}"
    )
    return f"{basename}_dirty" if config.data_quality.mode == "dirty" else basename


def _prepare_paths(output_root: Path, basename: str, overwrite: bool) -> tuple[Path, Path]:
    output_dir = output_root / basename
    zip_path = output_root / f"{basename}.zip"
    collisions = [path for path in (output_dir, zip_path) if path.exists()]
    if collisions and not overwrite:
        joined = ", ".join(str(path) for path in collisions)
        raise FileExistsError(f"Output already exists: {joined}. Use --overwrite to replace it.")
    if overwrite:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        if zip_path.exists():
            zip_path.unlink()
    output_dir.mkdir(parents=True, exist_ok=False)
    return output_dir, zip_path


def _write_validation(output_dir: Path, result: ValidationResult) -> None:
    payload = result.to_dict()
    (output_dir / "validation_summary.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    lines = [
        "# Validation Summary",
        "",
        f"Overall status: **{payload['overall_status'].upper()}**",
        "",
        f"Checks passed: {payload['checks_passed']} of {payload['checks_total']}",
        f"Expected issues: {payload['checks_expected_issues']}",
        f"Unexpected failures: {payload['checks_failed']}",
        "",
        "| Check | Status | Details |",
        "|---|---|---|",
    ]
    for check in result.checks:
        status = {
            "passed": "PASS",
            "expected_issue": "EXPECTED ISSUE",
            "failed": "FAIL",
        }[check.status]
        lines.append(f"| {check.name} | {status} | {check.details} |")
    (output_dir / "validation_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_dataset(
    dataset: GeneratedDataset,
    output_root: str | Path,
    *,
    overwrite: bool = False,
    progress: Callable[[str], None] | None = None,
) -> ExportResult:
    def report(message: str) -> None:
        if progress is not None:
            progress(message)

    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    output_dir, zip_path = _prepare_paths(output_root, dataset_basename(dataset), overwrite)
    report(f"Created output folder: {output_dir}")
    source_validation = validate_dataset(dataset.tables, config=dataset.config)
    dirty_result = None
    output_tables = dataset.tables
    if dataset.config.data_quality.mode == "dirty" and source_validation.passed:
        report("Injecting deterministic dirty-data defects...")
        dirty_result = inject_dirty_data(dataset.tables, dataset.config)
        output_tables = dirty_result.tables
        report("Injected dirty-data defects using the configured rates.")
    for name, frame in output_tables.items():
        file_path = output_dir / f"{name}.csv"
        frame.to_csv(file_path, index=False, date_format="%Y-%m-%dT%H:%M:%S%z")
        row_label = "row" if len(frame) == 1 else "rows"
        report(f"Created {file_path.name} ({len(frame):,} {row_label}).")
    if dirty_result is not None:
        write_dirty_manifest(output_dir, dirty_result.manifest)
        report("Created dirty_data_manifest.json.")
    report("Running data quality tests...")
    if not source_validation.passed:
        validation = validate_dataset(dataset.tables, output_dir, config=dataset.config)
    elif dirty_result is not None:
        validation = audit_dirty_output(output_dir, dirty_result, source_validation)
    else:
        validation = validate_dataset(output_tables, output_dir, config=dataset.config)
    for check in validation.checks:
        status = {
            "passed": "PASS",
            "expected_issue": "EXPECTED",
            "failed": "FAIL",
        }[check.status]
        report(f"[{status}] {check.name}: {check.details}")
    _write_validation(output_dir, validation)
    report("Created validation_summary.json.")
    report("Created validation_summary.md.")
    payload = validation.to_dict()
    report(
        "Data quality tests: "
        f"{payload['checks_passed']}/{payload['checks_total']} passed, "
        f"{payload['checks_expected_issues']} expected issues, "
        f"{payload['checks_failed']} unexpected failures."
    )
    created_zip: Path | None = None
    if validation.passed and dataset.config.output.create_zip:
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
            for file_path in sorted(output_dir.iterdir()):
                archive.write(file_path, arcname=file_path.name)
        created_zip = zip_path
        report(f"Created ZIP package: {zip_path}")
    elif dataset.config.output.create_zip:
        report("Skipped ZIP package because one or more unexpected data quality tests failed.")
    return ExportResult(output_dir=output_dir, zip_path=created_zip, validation=validation)
