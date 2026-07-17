"""Build Mermaid entity-relationship diagrams from loaded dataset tables."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

import pandas as pd

Relationship = tuple[str, str, str, str, str]


def _identifier(value: str) -> str:
    """Return a Mermaid-safe identifier while preserving readable names."""
    identifier = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if identifier and identifier[0].isdigit():
        identifier = f"field_{identifier}"
    return identifier or "unnamed"


def _data_type(value: object) -> str:
    """Normalize documented and pandas types to Mermaid-safe type labels."""
    normalized = str(value).strip().lower()
    if normalized.startswith("datetime"):
        return "datetime"
    if normalized.startswith(("int", "uint")):
        return "integer"
    if normalized.startswith("float"):
        return "float"
    if normalized in {"bool", "boolean"}:
        return "boolean"
    if normalized in {"object", "str", "string"}:
        return "string"
    return _identifier(normalized or "string")


def _split_reference(reference: str) -> tuple[str, str]:
    table_name, column_name = reference.split(".", maxsplit=1)
    return table_name, column_name


def _documented_types(tables: Mapping[str, pd.DataFrame]) -> dict[tuple[str, str], str]:
    data_dictionary = tables.get("data_dictionary")
    required = {"table_name", "column_name", "data_type"}
    if data_dictionary is None or not required.issubset(data_dictionary.columns):
        return {}

    return {
        (str(row.table_name), str(row.column_name)): _data_type(row.data_type)
        for row in data_dictionary.loc[:, sorted(required)].itertuples(index=False)
    }


def build_mermaid_er_diagram(
    tables: Mapping[str, pd.DataFrame],
    primary_keys: Mapping[str, str],
    relationships: Sequence[Relationship],
    *,
    include_all_columns: bool,
) -> str:
    """Create a Mermaid ER diagram for the available tables.

    Compact diagrams contain primary and foreign keys only. Full diagrams include
    every loaded column and prefer documented data types over inferred pandas types.
    """
    foreign_keys: dict[str, set[str]] = {}
    for _, foreign_reference, _, _, _ in relationships:
        table_name, column_name = _split_reference(foreign_reference)
        foreign_keys.setdefault(table_name, set()).add(column_name)

    documented_types = _documented_types(tables)
    lines = ["erDiagram"]

    for table_name, frame in tables.items():
        primary_columns = {
            column.strip()
            for column in primary_keys.get(table_name, "").split("+")
            if column.strip()
        }
        key_columns = primary_columns | foreign_keys.get(table_name, set())
        columns = list(frame.columns)
        if not include_all_columns:
            columns = [column for column in columns if column in key_columns]

        if not columns:
            continue

        lines.append(f"    {_identifier(table_name)} {{")
        for column_name in columns:
            column_type = documented_types.get(
                (table_name, column_name), _data_type(frame[column_name].dtype)
            )
            markers: list[str] = []
            if column_name in primary_columns:
                markers.append("PK")
            if column_name in foreign_keys.get(table_name, set()):
                markers.append("FK")
            marker_text = f" {', '.join(markers)}" if markers else ""
            lines.append(
                f"        {column_type} {_identifier(column_name)}{marker_text}"
            )
        lines.append("    }")

    available_tables = set(tables)
    for primary_reference, foreign_reference, _, connector, label in relationships:
        primary_table, _ = _split_reference(primary_reference)
        foreign_table, _ = _split_reference(foreign_reference)
        if primary_table in available_tables and foreign_table in available_tables:
            lines.append(
                f"    {_identifier(primary_table)} {connector} "
                f"{_identifier(foreign_table)} : {label}"
            )

    return "\n".join(lines)
