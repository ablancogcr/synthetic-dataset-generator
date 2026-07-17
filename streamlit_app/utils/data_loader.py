"""Testable file-loading helpers used by the Streamlit cache layer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


class DataLoadError(ValueError):
    """Raised when a local viewer file cannot be loaded."""


def file_signature(path: str | Path) -> tuple[str, int]:
    """Return a resolved path and modification time for cache invalidation."""
    file_path = Path(path).expanduser().resolve()
    try:
        modified_time = file_path.stat().st_mtime_ns
    except OSError as exc:
        raise DataLoadError(f"Cannot access {file_path.name}: {exc}") from exc
    return str(file_path), modified_time


def read_csv_file(path: str | Path) -> pd.DataFrame:
    """Read a CSV with a concise, viewer-friendly error."""
    file_path = Path(path)
    if not file_path.is_file():
        raise DataLoadError(f"Missing file: {file_path.name}")
    try:
        return pd.read_csv(file_path, low_memory=False)
    except (OSError, UnicodeError, pd.errors.ParserError) as exc:
        raise DataLoadError(f"Could not parse {file_path.name}: {exc}") from exc


def load_metadata(dataset_dir: str | Path) -> dict[str, Any]:
    """Load the first simulation metadata row, returning an empty mapping if absent."""
    metadata_path = Path(dataset_dir) / "simulation_metadata.csv"
    if not metadata_path.is_file():
        return {}
    metadata = read_csv_file(metadata_path)
    if metadata.empty:
        return {}
    row = metadata.iloc[0]
    return {column: (None if pd.isna(value) else value) for column, value in row.items()}


def list_csv_tables(dataset_dir: str | Path) -> tuple[str, ...]:
    """Return available CSV table names in a dataset directory."""
    directory = Path(dataset_dir)
    if not directory.is_dir():
        return ()
    return tuple(sorted(file.stem for file in directory.glob("*.csv") if file.is_file()))
