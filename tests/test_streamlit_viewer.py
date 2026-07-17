from __future__ import annotations

import json

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from streamlit_app.utils.data_loader import (
    DataLoadError,
    file_signature,
    load_metadata,
    read_csv_file,
)
from streamlit_app.utils.dataset_discovery import (
    CORE_TABLES,
    discover_datasets,
    inspect_dataset_directory,
)
from streamlit_app.utils.metrics import (
    calculate_overview_metrics,
    monthly_performance,
    seller_revenue_concentration,
)
from streamlit_app.utils.schema_diagram import build_mermaid_er_diagram
from streamlit_app.utils.validation_loader import load_validation_report


def _write_csv(directory, table_name: str, content: str = "id\n1\n") -> None:
    (directory / f"{table_name}.csv").write_text(content, encoding="utf-8")


def test_generate_page_exposes_the_cli_options_only():
    app = AppTest.from_file("streamlit_app/app_pages/generate.py")
    app.run()

    assert not app.exception
    assert [item.label for item in app.text_input] == [
        "Config YAML path",
        "Output directory",
        "Scenarios YAML path",
    ]
    assert [item.label for item in app.number_input] == ["Order count", "Random seed"]
    assert [item.label for item in app.checkbox] == [
        "Enable dirty-data mode",
        "Overwrite an existing matching package",
    ]
    assert [item.label for item in app.selectbox] == ["Scenario"]
    assert [item.label for item in app.button] == ["Generate dataset"]


def test_dataset_discovery_separates_valid_and_incomplete_directories(tmp_path):
    valid = tmp_path / "valid_dataset"
    valid.mkdir()
    for table_name in CORE_TABLES:
        _write_csv(valid, table_name)

    incomplete = tmp_path / "incomplete_dataset"
    incomplete.mkdir()
    _write_csv(incomplete, "orders")

    unrelated = tmp_path / "notes"
    unrelated.mkdir()
    (unrelated / "README.txt").write_text("not a dataset", encoding="utf-8")

    result = discover_datasets(tmp_path)

    assert [dataset.path.name for dataset in result.datasets] == ["valid_dataset"]
    assert [dataset.path.name for dataset in result.incomplete] == ["incomplete_dataset"]
    assert inspect_dataset_directory(unrelated) is None


def test_metadata_and_csv_loading_helpers(tmp_path):
    _write_csv(tmp_path, "orders", "order_id,value\norder_1,12.5\n")
    (tmp_path / "simulation_metadata.csv").write_text(
        "scenario_name,number_of_orders,random_seed\nbaseline,1,42\n",
        encoding="utf-8",
    )

    orders = read_csv_file(tmp_path / "orders.csv")
    metadata = load_metadata(tmp_path)
    resolved, modified_time = file_signature(tmp_path / "orders.csv")

    assert orders.to_dict("records") == [{"order_id": "order_1", "value": 12.5}]
    assert metadata["scenario_name"] == "baseline"
    assert metadata["number_of_orders"] == 1
    assert resolved.endswith("orders.csv")
    assert modified_time > 0


def test_missing_optional_loaders_return_empty_results(tmp_path):
    assert load_metadata(tmp_path) == {}
    assert load_validation_report(tmp_path) is None
    with pytest.raises(DataLoadError, match="Missing file"):
        read_csv_file(tmp_path / "orders.csv")


def test_overview_and_monthly_aov_do_not_duplicate_multi_item_orders():
    orders = pd.DataFrame(
        {
            "order_id": ["order_1", "order_2"],
            "order_purchase_timestamp": ["2026-01-05", "2026-01-20"],
        }
    )
    order_items = pd.DataFrame(
        {
            "order_id": ["order_1", "order_1", "order_2"],
            "item_price_usd": [10.0, 15.0, 5.0],
            "shipping_cost_usd": [2.0, 3.0, 5.0],
            "item_total_usd": [12.0, 18.0, 10.0],
        }
    )
    customers = pd.DataFrame({"customer_id": ["customer_1", "customer_2"]})
    sellers = pd.DataFrame({"seller_id": ["seller_1"]})
    products = pd.DataFrame({"product_id": ["product_1", "product_2"]})

    overview = calculate_overview_metrics(orders, order_items, customers, sellers, products)
    monthly = monthly_performance(orders, order_items)

    assert overview.product_revenue == 30.0
    assert overview.shipping_revenue == 10.0
    assert overview.total_order_value == 40.0
    assert overview.average_order_value == 20.0
    assert monthly.loc[0, "order_count"] == 2
    assert monthly.loc[0, "average_order_value"] == 20.0


def test_seller_revenue_concentration_uses_ranked_revenue_shares():
    revenue = pd.Series([120, 100, 80, 60, 40, 30, 20, 10, 8, 6, 4, 2])

    concentration = seller_revenue_concentration(revenue)

    assert concentration.top_5_share == pytest.approx(400 / 480)
    assert concentration.top_10_share == pytest.approx(474 / 480)


def test_validation_loader_reads_generator_report_and_markdown(tmp_path):
    payload = {
        "overall_status": "failed",
        "checks_passed": 1,
        "checks_total": 2,
        "checks": [
            {"name": "required_tables", "passed": True, "details": "Missing tables: []"},
            {"name": "valid_scores", "passed": False, "details": "Invalid rows: 2"},
        ],
    }
    (tmp_path / "validation_summary.json").write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / "validation_summary.md").write_text("# Validation Summary\n", encoding="utf-8")

    report = load_validation_report(tmp_path)

    assert report is not None
    assert report.overall_status == "failed"
    assert len(report.passed_checks) == 1
    assert len(report.failed_checks) == 1
    assert report.markdown == "# Validation Summary\n"


def test_validation_loader_classifies_expected_issues_and_reads_manifest(tmp_path):
    payload = {
        "overall_status": "expected_issues",
        "checks_passed": 1,
        "checks_expected_issues": 1,
        "checks_failed": 0,
        "checks_total": 2,
        "checks": [
            {"name": "source_schema", "passed": True, "status": "passed", "details": "OK"},
            {
                "name": "dirty_null_values",
                "passed": False,
                "expected": True,
                "status": "expected_issue",
                "details": "Found 5",
            },
        ],
    }
    manifest = {
        "data_quality_mode": "dirty",
        "defects": [
            {
                "defect_type": "null_values",
                "table": "orders",
                "column": "order_status",
                "affected_count": 5,
            }
        ],
    }
    (tmp_path / "validation_summary.json").write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / "dirty_data_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    report = load_validation_report(tmp_path)

    assert report is not None
    assert report.overall_status == "expected_issues"
    assert len(report.expected_issue_checks) == 1
    assert report.failed_checks == ()
    assert report.dirty_manifest == manifest


def test_viewer_metrics_tolerate_dirty_numeric_and_date_values():
    orders = pd.DataFrame(
        {
            "order_id": ["order_1", "order_2"],
            "order_purchase_timestamp": ["2026-01-05", "invalid_date"],
        }
    )
    order_items = pd.DataFrame(
        {
            "order_id": ["order_1", "order_2"],
            "item_price_usd": ["10.0", "not_a_number"],
            "shipping_cost_usd": ["2.0", "not_a_number"],
            "item_total_usd": ["12.0", "not_a_number"],
        }
    )

    monthly = monthly_performance(orders, order_items)

    assert len(monthly) == 1
    assert monthly.loc[0, "total_order_value"] == 12.0


def test_validation_loader_handles_markdown_without_json(tmp_path):
    (tmp_path / "validation_summary.md").write_text("# Summary\n", encoding="utf-8")

    report = load_validation_report(tmp_path)

    assert report is not None
    assert report.overall_status == "unknown"
    assert report.markdown == "# Summary\n"


def test_schema_diagram_marks_keys_and_switches_column_detail():
    tables = {
        "customers": pd.DataFrame(
            {"customer_id": ["customer_1"], "customer_segment": ["occasional_buyer"]}
        ),
        "orders": pd.DataFrame(
            {
                "order_id": ["order_1"],
                "customer_id": ["customer_1"],
                "order_status": ["delivered"],
            }
        ),
        "data_dictionary": pd.DataFrame(
            {
                "table_name": ["customers", "orders", "orders"],
                "column_name": ["customer_id", "order_id", "customer_id"],
                "data_type": ["string", "string", "string"],
            }
        ),
    }
    primary_keys = {
        "customers": "customer_id",
        "orders": "order_id",
        "data_dictionary": "table_name + column_name",
    }
    relationships = (
        (
            "customers.customer_id",
            "orders.customer_id",
            "One customer to many orders",
            "||--o{",
            "places",
        ),
    )

    compact = build_mermaid_er_diagram(
        tables, primary_keys, relationships, include_all_columns=False
    )
    full = build_mermaid_er_diagram(
        tables, primary_keys, relationships, include_all_columns=True
    )

    assert "string customer_id PK" in compact
    assert "string customer_id FK" in compact
    assert "customers ||--o{ orders : places" in compact
    assert "customer_segment" not in compact
    assert "order_status" not in compact
    assert "customer_segment" in full
    assert "order_status" in full


def test_schema_diagram_supports_seller_product_bridge():
    tables = {
        "sellers": pd.DataFrame({"seller_id": ["seller_1"]}),
        "products": pd.DataFrame({"product_id": ["product_1"]}),
        "seller_products": pd.DataFrame(
            {
                "seller_product_id": ["seller_product_1"],
                "seller_id": ["seller_1"],
                "product_id": ["product_1"],
            }
        ),
    }
    primary_keys = {
        "sellers": "seller_id",
        "products": "product_id",
        "seller_products": "seller_product_id",
    }
    relationships = (
        (
            "sellers.seller_id",
            "seller_products.seller_id",
            "Seller listings",
            "||--|{",
            "offers",
        ),
        (
            "products.product_id",
            "seller_products.product_id",
            "Product listings",
            "||--|{",
            "listed_by",
        ),
    )

    diagram = build_mermaid_er_diagram(
        tables, primary_keys, relationships, include_all_columns=False
    )

    assert "seller_product_id PK" in diagram
    assert "seller_id FK" in diagram
    assert "product_id FK" in diagram
    assert "sellers ||--|{ seller_products : offers" in diagram
