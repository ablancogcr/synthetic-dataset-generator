from __future__ import annotations

from collections.abc import Callable

import yaml

from synthetic_dataset_generator.config import GeneratorConfig
from synthetic_dataset_generator.workflow import GenerationRequest, run_generation


def test_shared_workflow_creates_cli_equivalent_package(
    tmp_path, config_factory: Callable[..., GeneratorConfig]
) -> None:
    config = config_factory(orders=60, scenario="logistics_improvement", seed=17)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    output_root = tmp_path / "output"
    messages: list[str] = []

    run = run_generation(
        GenerationRequest(
            config_path=config_path,
            scenarios_path="config/scenarios.yaml",
            output_root=output_root,
        ),
        progress=messages.append,
    )

    assert run.exit_code == 0
    assert run.result.output_dir == output_root / "ecommerce_logistics_improvement_60_seed17"
    assert run.result.zip_path == output_root / "ecommerce_logistics_improvement_60_seed17.zip"
    assert run.result.zip_path.is_file()
    assert "Synthetic Dataset Generator" in messages
    assert "Starting dataset generation..." in messages
    assert "Creating dataset files..." in messages
    assert any(message.startswith("  Created customers.csv") for message in messages)
    assert messages[-1] == "  Validation: PASSED"


def test_shared_workflow_preserves_dirty_cli_semantics(
    tmp_path, config_factory: Callable[..., GeneratorConfig]
) -> None:
    config = config_factory(orders=120)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    output_root = tmp_path / "output"

    run = run_generation(
        GenerationRequest(
            config_path=config_path,
            scenarios_path="config/scenarios.yaml",
            output_root=output_root,
            dirty=True,
        )
    )

    assert run.exit_code == 0
    assert run.result.output_dir.name == "ecommerce_baseline_120_seed42_dirty"
    assert run.result.zip_path is not None
    assert run.result.validation.overall_status == "expected_issues"
