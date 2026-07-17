"""Output schemas and data-dictionary metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnSpec:
    data_type: str
    description: str
    nullable: bool = False


def _spec(data_type: str, description: str, nullable: bool = False) -> ColumnSpec:
    return ColumnSpec(data_type, description, nullable)


SCHEMA_REGISTRY: dict[str, dict[str, ColumnSpec]] = {
    "customers": {
        "customer_id": _spec("string", "Synthetic customer record identifier."),
        "customer_unique_id": _spec("string", "Stable synthetic customer identity."),
        "customer_state": _spec("string", "US state abbreviation."),
        "customer_city": _spec("string", "City consistent with the assigned state."),
        "customer_region": _spec("string", "US census-style region."),
        "customer_zip_prefix": _spec("string", "Synthetic five-digit ZIP prefix."),
        "customer_segment": _spec("string", "Behavioral customer segment."),
        "customer_lifecycle_stage": _spec("string", "Customer lifecycle stage."),
        "created_at": _spec("date", "Synthetic customer creation date."),
    },
    "sellers": {
        "seller_id": _spec("string", "Synthetic seller identifier."),
        "seller_state": _spec("string", "Seller state abbreviation."),
        "seller_city": _spec("string", "Seller city."),
        "seller_region": _spec("string", "Seller region."),
        "seller_zip_prefix": _spec("string", "Synthetic seller ZIP prefix."),
        "seller_segment": _spec("string", "Seller operating segment."),
        "seller_quality_score": _spec("float", "Synthetic seller quality score from 0 to 1."),
        "seller_fulfillment_capacity": _spec("float", "Relative fulfillment capacity from 0 to 1."),
        "seller_active_flag": _spec("boolean", "Whether the seller is active at period end."),
        "created_at": _spec("date", "Synthetic seller creation date."),
        "deactivated_at": _spec("date", "Seller deactivation date in churn scenario.", True),
    },
    "products": {
        "product_id": _spec("string", "Synthetic product identifier."),
        "product_category": _spec("string", "Generic English product category."),
        "product_name": _spec("string", "Generic non-branded product name."),
        "product_weight_g": _spec("integer", "Product weight in grams."),
        "product_length_cm": _spec("float", "Product length in centimeters."),
        "product_height_cm": _spec("float", "Product height in centimeters."),
        "product_width_cm": _spec("float", "Product width in centimeters."),
        "product_price_base_usd": _spec("float", "Base synthetic product price in USD."),
        "created_at": _spec("date", "Synthetic product creation date."),
    },
    "orders": {
        "order_id": _spec("string", "Synthetic order identifier."),
        "customer_id": _spec("string", "Customer placing the order."),
        "order_status": _spec("string", "Order fulfillment status."),
        "order_purchase_timestamp": _spec("datetime", "Order purchase timestamp."),
        "order_approved_at": _spec("datetime", "Payment approval timestamp.", True),
        "order_estimated_delivery_date": _spec("date", "Estimated delivery date."),
        "order_delivered_carrier_date": _spec("datetime", "Carrier handoff timestamp.", True),
        "order_delivered_customer_date": _spec("datetime", "Customer delivery timestamp.", True),
        "order_year": _spec("integer", "Purchase year."),
        "order_quarter": _spec("integer", "Purchase quarter."),
        "order_month": _spec("integer", "Purchase month."),
        "order_week": _spec("integer", "ISO purchase week."),
        "order_day_of_week": _spec("integer", "Purchase weekday where Monday is 0."),
        "is_weekend": _spec("boolean", "Whether purchase occurred on a weekend."),
        "is_holiday_period": _spec("boolean", "Whether purchase occurred in holiday season."),
        "is_promotion_period": _spec("boolean", "Whether purchase occurred in a promotion window."),
        "scenario_name": _spec("string", "Scenario used for this order."),
    },
    "order_items": {
        "order_id": _spec("string", "Parent order identifier."),
        "order_item_id": _spec("integer", "One-based item sequence within order."),
        "product_id": _spec("string", "Purchased product identifier."),
        "seller_id": _spec("string", "Seller fulfilling the order."),
        "item_price_usd": _spec("float", "Synthetic item price in USD."),
        "shipping_cost_usd": _spec("float", "Allocated item shipping cost in USD."),
        "item_total_usd": _spec("float", "Item price plus shipping cost in USD."),
        "scenario_name": _spec("string", "Scenario used for this item."),
    },
    "payments": {
        "order_id": _spec("string", "Paid order identifier."),
        "payment_sequential": _spec("integer", "One-based payment sequence."),
        "payment_type": _spec("string", "Synthetic payment method."),
        "payment_installments": _spec("integer", "Installment count."),
        "payment_value_usd": _spec("float", "Payment value in USD."),
        "scenario_name": _spec("string", "Scenario used for this payment."),
    },
    "shipping": {
        "order_id": _spec("string", "Shipped order identifier."),
        "seller_state": _spec("string", "Origin state."),
        "customer_state": _spec("string", "Destination state."),
        "seller_region": _spec("string", "Origin region."),
        "customer_region": _spec("string", "Destination region."),
        "shipping_distance_band": _spec(
            "string", "Same-state, same-region, cross-region, or remote band."
        ),
        "shipping_zone": _spec("string", "Synthetic route zone."),
        "estimated_delivery_days": _spec("integer", "Estimated delivery days."),
        "actual_delivery_days": _spec("integer", "Actual delivery days.", True),
        "delivery_delay_days": _spec("integer", "Days delivered after estimate.", True),
        "late_delivery_flag": _spec("boolean", "Whether delivery missed its estimate."),
        "shipping_cost_usd": _spec("float", "Order shipping cost in USD."),
        "scenario_name": _spec("string", "Scenario used for shipping."),
    },
    "reviews": {
        "review_id": _spec("string", "Synthetic review identifier."),
        "order_id": _spec("string", "Reviewed delivered order."),
        "review_score": _spec("integer", "Review score from 1 to 5."),
        "review_creation_date": _spec("date", "Review creation date."),
        "review_answer_timestamp": _spec("datetime", "Synthetic response timestamp."),
        "review_sentiment_label": _spec("string", "Negative, neutral, or positive sentiment."),
        "satisfaction_risk_flag": _spec("boolean", "Whether score is 1 or 2."),
        "scenario_name": _spec("string", "Scenario used for the review."),
    },
    "calendar": {
        "date": _spec("date", "Calendar date."),
        "year": _spec("integer", "Calendar year."),
        "quarter": _spec("integer", "Calendar quarter."),
        "month": _spec("integer", "Month number."),
        "month_name": _spec("string", "Month name."),
        "week": _spec("integer", "ISO week."),
        "day_of_week": _spec("integer", "Weekday where Monday is 0."),
        "day_name": _spec("string", "Weekday name."),
        "is_weekend": _spec("boolean", "Weekend flag."),
        "is_holiday_period": _spec("boolean", "Holiday-season flag."),
        "is_promotion_period": _spec("boolean", "Promotion-window flag."),
        "season": _spec("string", "Meteorological season."),
    },
    "simulation_metadata": {
        "simulation_run_id": _spec("string", "Unique synthetic simulation run identifier."),
        "dataset_name": _spec("string", "Configured dataset name."),
        "domain": _spec("string", "Dataset domain."),
        "scenario_name": _spec("string", "Applied scenario."),
        "random_seed": _spec("integer", "Root random seed."),
        "generated_at": _spec("datetime", "UTC generation timestamp."),
        "start_date": _spec("date", "Configured period start."),
        "end_date": _spec("date", "Configured period end."),
        "requested_number_of_orders": _spec("integer", "Configured order count before defects."),
        "number_of_orders": _spec("integer", "Generated order count."),
        "number_of_customers": _spec("integer", "Generated customer count."),
        "number_of_sellers": _spec("integer", "Generated seller count."),
        "number_of_products": _spec("integer", "Generated product count."),
        "currency": _spec("string", "Synthetic monetary unit."),
        "data_quality_mode": _spec("string", "Whether the output is clean or intentionally dirty."),
        "disclaimer": _spec("string", "Synthetic-data usage disclaimer."),
    },
    "data_dictionary": {
        "table_name": _spec("string", "Dataset table."),
        "column_name": _spec("string", "Column in the table."),
        "data_type": _spec("string", "Logical data type."),
        "description": _spec("string", "Human-readable field definition."),
        "example_value": _spec("string", "Example generated value.", True),
        "nullable": _spec("boolean", "Whether blank values are allowed."),
    },
}

REQUIRED_FILES = [f"{name}.csv" for name in SCHEMA_REGISTRY]


def columns_for(table: str) -> list[str]:
    return list(SCHEMA_REGISTRY[table])
