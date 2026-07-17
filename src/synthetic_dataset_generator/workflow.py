"""Shared dataset-generation workflow for command-line and local UI callers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from synthetic_dataset_generator.config import apply_overrides, load_config, load_scenarios
from synthetic_dataset_generator.exporters import ExportResult, export_dataset
from synthetic_dataset_generator.generator import DatasetGenerator

ProgressCallback = Callable[[str], None]


@dataclass(frozen=True)
class GenerationRequest:
    """Inputs that correspond to the ``generate`` CLI command options."""

    config_path: Path
    scenarios_path: Path
    output_root: Path
    scenario: str | None = None
    orders: int | None = None
    seed: int | None = None
    dirty: bool | None = None
    overwrite: bool = False


@dataclass(frozen=True)
class GenerationRun:
    """Completed generation details shared by the CLI and Streamlit page."""

    result: ExportResult

    @property
    def exit_code(self) -> int:
        return 0 if self.result.validation.passed else 1


def run_generation(
    request: GenerationRequest,
    *,
    progress: ProgressCallback | None = None,
) -> GenerationRun:
    """Generate and export a dataset while emitting the canonical CLI progress messages."""

    def report(message: str) -> None:
        if progress is not None:
            progress(message)

    report("Synthetic Dataset Generator")
    report("Starting dataset generation...")
    report(f"  Config: {request.config_path}")
    report(f"  Scenarios: {request.scenarios_path}")
    report("Loading and validating configuration...")
    config = apply_overrides(
        load_config(request.config_path),
        scenario=request.scenario,
        orders=request.orders,
        seed=request.seed,
        dirty=request.dirty,
    )
    scenarios = load_scenarios(request.scenarios_path)
    scenario = scenarios[config.simulation.scenario]
    report("Configuration ready:")
    report(f"  Scenario: {config.simulation.scenario}")
    report(f"  Orders: {config.dataset.number_of_orders:,}")
    report(f"  Date range: {config.dataset.start_date} to {config.dataset.end_date}")
    report(f"  Random seed: {config.dataset.random_seed}")
    report(f"  Data quality mode: {config.data_quality.mode}")
    report(f"  Output root: {request.output_root}")
    report("Generating dataset tables...")

    def nested_report(message: str) -> None:
        report(f"  {message}")

    dataset = DatasetGenerator(config, scenario, progress=nested_report).generate()
    report("Creating dataset files...")
    result = export_dataset(
        dataset,
        request.output_root,
        overwrite=request.overwrite,
        progress=nested_report,
    )
    report("Generation complete.")
    report(f"  Dataset folder: {result.output_dir}")
    if result.zip_path is not None:
        report(f"  ZIP package: {result.zip_path}")
    report(f"  Validation: {result.validation.overall_status.upper()}")
    return GenerationRun(result=result)
