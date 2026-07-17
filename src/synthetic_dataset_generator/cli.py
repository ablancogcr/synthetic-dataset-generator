"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from synthetic_dataset_generator.workflow import GenerationRequest, run_generation


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


def request_from_args(args: argparse.Namespace) -> GenerationRequest:
    """Map parsed CLI arguments to the shared generation request."""
    return GenerationRequest(
        config_path=Path(args.config),
        scenarios_path=Path(args.scenarios),
        output_root=Path(args.output),
        scenario=args.scenario,
        orders=args.orders,
        seed=args.seed,
        dirty=args.dirty,
        overwrite=args.overwrite,
    )


def run_generate(args: argparse.Namespace) -> int:
    return run_generation(request_from_args(args), progress=print).exit_code


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
