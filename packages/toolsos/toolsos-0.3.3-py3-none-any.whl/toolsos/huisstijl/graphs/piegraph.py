import plotly.express as px

from .styler import BaseStyle

basestyle = BaseStyle()


def pie(
    data,
    names,
    values,
    hole: float = 0.4,
    width=750,
    height=490,
    text_format: str = None,
    color_discrete_sequence=None,
    font="Amsterdam Sans",
    **kwargs,
):
    fig = px.pie(
        data_frame=data,
        names=names,
        values=values,
        width=width,
        height=height,
        hole=hole,
        template=BaseStyle().get_base_template(font=font),
        color_discrete_sequence=color_discrete_sequence,
        **kwargs,
    )

    if text_format:
        fig.update_traces(texttemplate=text_format)

    return fig
