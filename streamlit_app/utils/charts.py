"""Small Plotly helpers with consistent labels and axis formatting."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def line_chart(
    data: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str,
    x_title: str,
    y_title: str,
    currency: bool = False,
    percentage: bool = False,
) -> go.Figure:
    figure = px.line(data, x=x, y=y, markers=True, title=title)
    return _format_figure(
        figure,
        x_title=x_title,
        y_title=y_title,
        currency=currency,
        percentage=percentage,
    )


def bar_chart(
    data: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str,
    x_title: str,
    y_title: str,
    currency: bool = False,
    percentage: bool = False,
    horizontal: bool = False,
    color: str | None = None,
) -> go.Figure:
    if horizontal:
        figure = px.bar(data, x=y, y=x, color=color, orientation="h", title=title)
        figure = _format_figure(
            figure,
            x_title=y_title,
            y_title=x_title,
            currency=currency,
            percentage=percentage,
            value_axis="x",
        )
    else:
        figure = px.bar(data, x=x, y=y, color=color, title=title)
        figure = _format_figure(
            figure,
            x_title=x_title,
            y_title=y_title,
            currency=currency,
            percentage=percentage,
        )
    return figure


def scatter_chart(
    data: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str,
    x_title: str,
    y_title: str,
    color: str | None = None,
) -> go.Figure:
    figure = px.scatter(
        data,
        x=x,
        y=y,
        color=color,
        opacity=0.55,
        title=title,
        render_mode="svg",
    )
    return _format_figure(figure, x_title=x_title, y_title=y_title)


def _format_figure(
    figure: go.Figure,
    *,
    x_title: str,
    y_title: str,
    currency: bool = False,
    percentage: bool = False,
    value_axis: str = "y",
) -> go.Figure:
    figure.update_layout(
        xaxis_title=x_title,
        yaxis_title=y_title,
        hovermode="closest",
        legend_title_text="",
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )
    axis_update: dict[str, object] = {"rangemode": "tozero"}
    if currency:
        axis_update.update(tickprefix="$", tickformat=",.2f")
    if percentage:
        axis_update.update(tickformat=".1%")
    figure.update_layout(**{f"{value_axis}axis": axis_update})
    return figure
