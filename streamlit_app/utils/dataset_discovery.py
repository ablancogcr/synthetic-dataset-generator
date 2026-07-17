"""Discover generated dataset packages on the local filesystem."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

CORE_TABLES = frozenset(
    {"orders", "order_items", "customers", "products", "seller_products"}
)


@dataclass(frozen=True)
class DatasetDirectory:
    """Description of a directory that resembles a generated dataset."""

    path: Path
    available_tables: tuple[str, ...]
    missing_core_tables: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.missing_core_tables


@dataclass(frozen=True)
class DiscoveryResult:
    """Valid datasets and incomplete candidate directories."""

    datasets: tuple[DatasetDirectory, ...]
    incomplete: tuple[DatasetDirectory, ...]


def inspect_dataset_directory(path: str | Path) -> DatasetDirectory | None:
    """Inspect one directory without traversing beyond it."""
    directory = Path(path).expanduser()
    if not directory.is_dir():
        return None

    tables = tuple(sorted(file.stem for file in directory.glob("*.csv") if file.is_file()))
    has_generator_artifact = bool(tables) or any(
        (directory / name).is_file()
        for name in ("validation_summary.json", "validation_summary.md")
    )
    if not has_generator_artifact:
        return None

    missing = tuple(sorted(CORE_TABLES.difference(tables)))
    return DatasetDirectory(
        path=directory.resolve(),
        available_tables=tables,
        missing_core_tables=missing,
    )


def discover_datasets(root: str | Path) -> DiscoveryResult:
    """Find valid and incomplete dataset directories directly below ``root``."""
    root_path = Path(root).expanduser()
    if not root_path.is_dir():
        return DiscoveryResult(datasets=(), incomplete=())

    candidates = [
        candidate
        for child in root_path.iterdir()
        if child.is_dir() and (candidate := inspect_dataset_directory(child)) is not None
    ]
    candidates.sort(key=lambda item: item.path.name.lower())
    return DiscoveryResult(
        datasets=tuple(item for item in candidates if item.is_valid),
        incomplete=tuple(item for item in candidates if not item.is_valid),
    )
