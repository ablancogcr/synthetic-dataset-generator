"""Load the generator's validation reports without reimplementing validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ValidationLoadError(ValueError):
    """Raised when a validation report exists but cannot be parsed."""


@dataclass(frozen=True)
class ValidationReport:
    overall_status: str
    checks_passed: int
    checks_total: int
    checks: tuple[dict[str, Any], ...]
    markdown: str | None

    @property
    def failed_checks(self) -> tuple[dict[str, Any], ...]:
        warning_checks = self.warnings
        return tuple(
            check
            for check in self.checks
            if check.get("passed") is False and check not in warning_checks
        )

    @property
    def passed_checks(self) -> tuple[dict[str, Any], ...]:
        return tuple(check for check in self.checks if check.get("passed") is True)

    @property
    def warnings(self) -> tuple[dict[str, Any], ...]:
        return tuple(
            check
            for check in self.checks
            if str(check.get("status", "")).lower() == "warning"
            or bool(check.get("warning", False))
        )


def load_validation_report(dataset_dir: str | Path) -> ValidationReport | None:
    """Load JSON and Markdown validation artifacts when present."""
    directory = Path(dataset_dir)
    json_path = directory / "validation_summary.json"
    markdown_path = directory / "validation_summary.md"
    markdown = markdown_path.read_text(encoding="utf-8") if markdown_path.is_file() else None

    if not json_path.is_file() and markdown is None:
        return None
    if not json_path.is_file():
        return ValidationReport(
            overall_status="unknown",
            checks_passed=0,
            checks_total=0,
            checks=(),
            markdown=markdown,
        )
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationLoadError(f"Could not parse {json_path.name}: {exc}") from exc

    raw_checks = payload.get("checks", [])
    checks = tuple(check for check in raw_checks if isinstance(check, dict))
    return ValidationReport(
        overall_status=str(payload.get("overall_status", "unknown")),
        checks_passed=int(payload.get("checks_passed", sum(bool(c.get("passed")) for c in checks))),
        checks_total=int(payload.get("checks_total", len(checks))),
        checks=checks,
        markdown=markdown,
    )
