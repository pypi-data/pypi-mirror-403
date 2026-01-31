from typing import Optional

import plotly.express as px

from .styler import BaseStyle

basestyle = BaseStyle()


def bar(
    data,
    x: str,
    y: str,
    color: Optional[str] = None,
    color_discrete_sequence: Optional[list[str]] = None,
    orientation: Optional[str] = None,
    barmode: Optional[str] = None,
    width: int = 750,
    height: int = 490,
    font: str = "Amsterdam Sans",
    **kwargs,
):
    fig = px.bar(
        data_frame=data,
        x=x,
        y=y,
        color=color,
        template=basestyle.get_base_template("bar", orientation=orientation, font=font),
        width=width,
        color_discrete_sequence=color_discrete_sequence,
        height=height,
        barmode=barmode,
        **kwargs,
    )

    fig.update_layout(
        dict(xaxis_title_text="", yaxis_title_text="", legend_title_text="")
    )

    return fig


def stacked_single(
    data,
    x: str,
    y: str,
    color: Optional[str] = None,
    color_discrete_sequence: Optional[list[str]] = None,
    orientation: str = "v",
    font: str = "Amsterdam Sans",
    **kwargs,
):
    fig = bar(
        data=data,
        x=x,
        y=y,
        color=color,
        color_discrete_sequence=color_discrete_sequence,
        barmode="relative",
        orientation=orientation,
        font=font,
        **kwargs,
    )

    if orientation == "v":
        fig.update_xaxes(showticklabels=False)
    if orientation == "h":
        fig.update_yaxes(showticklabels=False)

    return fig


def stacked_multiple(
    data,
    x: str,
    y: str,
    color: str = None,
    color_discrete_sequence: list = None,
    orientation="v",
    font="Amsterdam Sans",
    **kwargs,
):
    fig = bar(
        data=data,
        x=x,
        y=y,
        color=color,
        color_discrete_sequence=color_discrete_sequence,
        barmode="stack",
        orientation=orientation,
        font=font,
        **kwargs,
    )

    return fig


def grouped(
    data,
    x: str,
    y: str,
    color: str = None,
    color_discrete_sequence: list = None,
    orientation="v",
    font="Amsterdam Sans",
    **kwargs,
):
    fig = bar(
        data=data,
        x=x,
        y=y,
        color=color,
        color_discrete_sequence=color_discrete_sequence,
        barmode="group",
        orientation=orientation,
        font=font,
        **kwargs,
    )

    return fig


def single(
    data,
    x: str,
    y: str,
    color_discrete_sequence: list = None,
    orientation="v",
    font="Amsterdam Sans",
    **kwargs,
):
    fig = bar(
        data=data,
        x=x,
        y=y,
        color_discrete_sequence=color_discrete_sequence,
        orientation=orientation,
        barmode="relative",
        font=font,
        **kwargs,
    )

    if orientation == "h":
        fig.update_yaxes(automargin=True)

    return fig
