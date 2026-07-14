"""Calendar dimension generation."""

from __future__ import annotations

from datetime import date

import pandas as pd

from synthetic_dataset_generator.schemas import columns_for


def holiday_period(dates: pd.Series | pd.DatetimeIndex) -> pd.Series:
    values = pd.Series(dates)
    return ((values.dt.month == 11) & (values.dt.day >= 15)) | (values.dt.month == 12)


def promotion_period(dates: pd.Series | pd.DatetimeIndex) -> pd.Series:
    values = pd.Series(dates)
    return (
        ((values.dt.month == 7) & (values.dt.day <= 7))
        | ((values.dt.month == 11) & values.dt.day.between(20, 30))
        | ((values.dt.month == 12) & values.dt.day.between(10, 20))
    )


def generate_calendar(start_date: date, end_date: date) -> pd.DataFrame:
    dates = pd.date_range(start_date, end_date, freq="D")
    date_series = pd.Series(dates)
    months = date_series.dt.month
    season = pd.cut(
        months,
        bins=[0, 2, 5, 8, 11, 12],
        labels=["winter", "spring", "summer", "fall", "winter"],
        ordered=False,
    )
    calendar = pd.DataFrame(
        {
            "date": dates,
            "year": dates.year,
            "quarter": dates.quarter,
            "month": dates.month,
            "month_name": dates.month_name(),
            "week": dates.isocalendar().week.to_numpy(dtype=int),
            "day_of_week": dates.dayofweek,
            "day_name": dates.day_name(),
            "is_weekend": dates.dayofweek >= 5,
            "is_holiday_period": holiday_period(date_series).to_numpy(),
            "is_promotion_period": promotion_period(date_series).to_numpy(),
            "season": season.astype(str).to_numpy(),
        }
    )
    return calendar[columns_for("calendar")]
