"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from synthetic_dataset_generator.config import apply_overrides, load_config, load_scenarios
from synthetic_dataset_generator.exporters import export_dataset
from synthetic_dataset_generator.generator import DatasetGenerator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="synthetic-dataset-generator",
        description="Generate fully synthetic ecommerce datasets for analytics practice.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser("generate", help="Generate and validate a dataset package.")
    generate.add_argument(
        "--config", default="config/default_config.yaml", help="Generator YAML path."
    )
    generate.add_argument(
        "--scenarios", default="config/scenarios.yaml", help="Scenario YAML path."
    )
    generate.add_argument("--output", default="data/output", help="Parent output directory.")
    generate.add_argument(
        "--scenario",
        choices=["baseline", "holiday_spike", "logistics_improvement", "seller_churn"],
    )
    generate.add_argument("--orders", type=int, help="Override generated order count.")
    generate.add_argument("--seed", type=int, help="Override random seed.")
    generate.add_argument(
        "--dirty",
        action="store_true",
        default=None,
        help="Enable deterministic dirty-data generation using configured rates.",
    )
    generate.add_argument(
        "--overwrite", action="store_true", help="Replace the named output package."
    )
    return parser


def run_generate(args: argparse.Namespace) -> int:
    print("Synthetic Dataset Generator")
    print("Starting dataset generation...")
    print(f"  Config: {Path(args.config)}")
    print(f"  Scenarios: {Path(args.scenarios)}")
    print("Loading and validating configuration...")
    config = apply_overrides(
        load_config(Path(args.config)),
        scenario=args.scenario,
        orders=args.orders,
        seed=args.seed,
        dirty=args.dirty,
    )
    scenarios = load_scenarios(Path(args.scenarios))
    scenario = scenarios[config.simulation.scenario]
    print("Configuration ready:")
    print(f"  Scenario: {config.simulation.scenario}")
    print(f"  Orders: {config.dataset.number_of_orders:,}")
    print(f"  Date range: {config.dataset.start_date} to {config.dataset.end_date}")
    print(f"  Random seed: {config.dataset.random_seed}")
    print(f"  Data quality mode: {config.data_quality.mode}")
    print(f"  Output root: {Path(args.output)}")
    print("Generating dataset tables...")

    def report(message: str) -> None:
        print(f"  {message}")

    dataset = DatasetGenerator(config, scenario, progress=report).generate()
    print("Creating dataset files...")
    result = export_dataset(
        dataset,
        Path(args.output),
        overwrite=args.overwrite,
        progress=report,
    )
    print("Generation complete.")
    print(f"  Dataset folder: {result.output_dir}")
    if result.zip_path is not None:
        print(f"  ZIP package: {result.zip_path}")
    print(f"  Validation: {result.validation.overall_status.upper()}")
    return 0 if result.validation.passed else 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            return run_generate(args)
    except (FileNotFoundError, FileExistsError, ValueError, ValidationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
