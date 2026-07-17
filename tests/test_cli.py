from __future__ import annotations

from collections.abc import Callable

import yaml

from synthetic_dataset_generator.cli import main
from synthetic_dataset_generator.config import GeneratorConfig


def test_cli_exports_zip_and_handles_collision(
    tmp_path, capsys, config_factory: Callable[..., GeneratorConfig]
) -> None:
    config = config_factory(orders=60)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    output = tmp_path / "output"
    args = [
        "generate",
        "--config",
        str(config_path),
        "--scenarios",
        "config/scenarios.yaml",
        "--output",
        str(output),
    ]
    assert main(args) == 0
    output_text = capsys.readouterr().out
    assert "Synthetic Dataset Generator" in output_text
    assert "Starting dataset generation..." in output_text
    assert "Created customers.csv" in output_text
    assert "Running data quality tests..." in output_text
    assert "[PASS] required_tables" in output_text
    assert "Created validation_summary.json." in output_text
    assert "Data quality tests:" in output_text
    assert "Generation complete." in output_text
    folder = output / "ecommerce_baseline_60_seed42"
    archive = output / "ecommerce_baseline_60_seed42.zip"
    assert folder.is_dir()
    assert archive.is_file()
    assert main(args) == 2
    assert main([*args, "--overwrite"]) == 0
