import plotly.express as px

from .styler import BaseStyle

basestyle = BaseStyle()


def line(
    data,
    x,
    y,
    color: None,
    width=750,
    height=490,
    color_discrete_sequence=None,
    font="Amsterdam Sans",
    **kwargs,
):
    fig = px.line(
        data_frame=data,
        x=x,
        y=y,
        color=color,
        width=width,
        height=height,
        color_discrete_sequence=color_discrete_sequence,
        template=BaseStyle().get_base_template(graph_type="line", font=font),
        **kwargs,
    )

    fig.update_layout(
        dict(xaxis_title_text="", yaxis_title_text="", legend_title_text="")
    )

    return fig
