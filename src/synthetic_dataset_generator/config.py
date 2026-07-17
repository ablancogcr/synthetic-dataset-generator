"""Configuration loading and validation."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator

ScenarioName = Literal["baseline", "holiday_spike", "logistics_improvement", "seller_churn"]
DataQualityMode = Literal["clean", "dirty"]


class DatasetConfig(BaseModel):
    name: str = "Synthetic Ecommerce Dataset"
    domain: str = "ecommerce_marketplace"
    country_context: str = "US-like synthetic marketplace"
    start_date: date = date(2024, 1, 1)
    end_date: date = date(2026, 12, 31)
    number_of_orders: int = Field(default=50_000, gt=0)
    random_seed: int = Field(default=42, ge=0)

    @model_validator(mode="after")
    def validate_dates(self) -> DatasetConfig:
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class OutputConfig(BaseModel):
    format: Literal["csv"] = "csv"
    create_zip: bool = True
    include_data_dictionary: bool = True
    include_validation_report: bool = True


class SimulationConfig(BaseModel):
    scenario: ScenarioName = "baseline"
    customer_count: int = Field(default=20_000, gt=0)
    seller_count: int = Field(default=1_200, gt=0)
    product_count: int = Field(default=8_000, gt=0)
    min_sellers_per_product: int = Field(default=1, gt=0)
    max_sellers_per_product: int = Field(default=4, gt=0)
    min_items_per_order: int = Field(default=1, gt=0)
    max_items_per_order: int = Field(default=5, gt=0)
    repeat_customer_rate: float = Field(default=0.18, ge=0, le=1)

    @model_validator(mode="after")
    def validate_item_range(self) -> SimulationConfig:
        if self.max_items_per_order < self.min_items_per_order:
            raise ValueError("max_items_per_order must be at least min_items_per_order")
        if self.max_sellers_per_product < self.min_sellers_per_product:
            raise ValueError(
                "max_sellers_per_product must be at least min_sellers_per_product"
            )
        if self.max_sellers_per_product > self.seller_count:
            raise ValueError("max_sellers_per_product cannot exceed seller_count")
        if self.product_count * self.max_sellers_per_product < self.seller_count:
            raise ValueError(
                "product_count * max_sellers_per_product must be at least seller_count"
            )
        return self


class BusinessRulesConfig(BaseModel):
    currency: Literal["USD"] = "USD"
    allow_cancelled_orders: bool = True
    allow_late_deliveries: bool = True
    allow_missing_reviews: bool = True


class DataQualityConfig(BaseModel):
    mode: DataQualityMode = "clean"
    null_rate: float = Field(default=0.01, ge=0, le=1)
    missing_day_rate: float = Field(default=0.005, ge=0, le=1)
    incorrect_date_format_rate: float = Field(default=0.005, ge=0, le=1)
    invalid_type_rate: float = Field(default=0.002, ge=0, le=1)
    negative_value_rate: float = Field(default=0.002, ge=0, le=1)
    empty_order_rate: float = Field(default=0.002, ge=0, le=1)


class GeneratorConfig(BaseModel):
    dataset: DatasetConfig = Field(default_factory=DatasetConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    business_rules: BusinessRulesConfig = Field(default_factory=BusinessRulesConfig)
    data_quality: DataQualityConfig = Field(default_factory=DataQualityConfig)


class ScenarioConfig(BaseModel):
    q4_multiplier: float = Field(gt=0)
    november_multiplier: float = Field(gt=0)
    december_multiplier: float = Field(gt=0)
    shipping_cost_multiplier: float = Field(gt=0)
    transit_days_multiplier: float = Field(gt=0)
    delay_probability_multiplier: float = Field(ge=0)
    review_score_shift: float
    category_multipliers: dict[str, float] = Field(default_factory=dict)
    seller_churn_fraction: float = Field(ge=0, lt=1)
    seller_churn_at_fraction: float = Field(gt=0, lt=1)


def load_config(path: str | Path) -> GeneratorConfig:
    """Load and validate generator YAML configuration."""
    config_path = Path(path)
    with config_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return GeneratorConfig.model_validate(data)


def load_scenarios(path: str | Path) -> dict[str, ScenarioConfig]:
    """Load and validate scenario behavior definitions."""
    scenario_path = Path(path)
    with scenario_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    scenarios = {name: ScenarioConfig.model_validate(values) for name, values in data.items()}
    expected = {"baseline", "holiday_spike", "logistics_improvement", "seller_churn"}
    missing = expected.difference(scenarios)
    if missing:
        raise ValueError(f"Missing scenario definitions: {', '.join(sorted(missing))}")
    return scenarios


def apply_overrides(
    config: GeneratorConfig,
    *,
    scenario: str | None = None,
    orders: int | None = None,
    seed: int | None = None,
    dirty: bool | None = None,
) -> GeneratorConfig:
    """Return a validated config with CLI values taking precedence."""
    values = config.model_dump()
    if scenario is not None:
        values["simulation"]["scenario"] = scenario
    if orders is not None:
        values["dataset"]["number_of_orders"] = orders
    if seed is not None:
        values["dataset"]["random_seed"] = seed
    if dirty is not None:
        values["data_quality"]["mode"] = "dirty" if dirty else "clean"
    return GeneratorConfig.model_validate(values)
