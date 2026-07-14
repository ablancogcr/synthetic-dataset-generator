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
        "--overwrite", action="store_true", help="Replace the named output package."
    )
    return parser


def run_generate(args: argparse.Namespace) -> int:
    config = apply_overrides(
        load_config(Path(args.config)),
        scenario=args.scenario,
        orders=args.orders,
        seed=args.seed,
    )
    scenarios = load_scenarios(Path(args.scenarios))
    scenario = scenarios[config.simulation.scenario]
    dataset = DatasetGenerator(config, scenario).generate()
    result = export_dataset(dataset, Path(args.output), overwrite=args.overwrite)
    print(f"Dataset folder: {result.output_dir}")
    if result.zip_path is not None:
        print(f"ZIP package: {result.zip_path}")
    print(f"Validation: {'PASSED' if result.validation.passed else 'FAILED'}")
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
