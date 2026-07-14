"""CSV, validation-report, and ZIP export."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from synthetic_dataset_generator.generator import GeneratedDataset
from synthetic_dataset_generator.validators import ValidationResult, validate_dataset


@dataclass(frozen=True)
class ExportResult:
    output_dir: Path
    zip_path: Path | None
    validation: ValidationResult


def dataset_basename(dataset: GeneratedDataset) -> str:
    config = dataset.config
    return (
        f"ecommerce_{config.simulation.scenario}_"
        f"{config.dataset.number_of_orders}_seed{config.dataset.random_seed}"
    )


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
        "",
        "| Check | Status | Details |",
        "|---|---|---|",
    ]
    for check in result.checks:
        lines.append(f"| {check.name} | {'PASS' if check.passed else 'FAIL'} | {check.details} |")
    (output_dir / "validation_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_dataset(
    dataset: GeneratedDataset, output_root: str | Path, *, overwrite: bool = False
) -> ExportResult:
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    output_dir, zip_path = _prepare_paths(output_root, dataset_basename(dataset), overwrite)
    for name, frame in dataset.tables.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False, date_format="%Y-%m-%dT%H:%M:%S%z")
    validation = validate_dataset(dataset.tables, output_dir)
    _write_validation(output_dir, validation)
    created_zip: Path | None = None
    if validation.passed and dataset.config.output.create_zip:
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
            for file_path in sorted(output_dir.iterdir()):
                archive.write(file_path, arcname=file_path.name)
        created_zip = zip_path
    return ExportResult(output_dir=output_dir, zip_path=created_zip, validation=validation)
