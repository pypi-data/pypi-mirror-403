from typing import TYPE_CHECKING, Any, Iterable, Optional

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import axis
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch


def plot_choropleth(
    gdf: gpd.GeoDataFrame,
    column: str,
    colors: Iterable[str],
    column_label: Optional[bool] = False,
    column_label_kwargs: Optional[dict[Any]] = None,
    legend_title: Optional[str] = None,
    edgecolor: str = "grey",
    figsize: tuple[int, int] = (10, 8),
    bbox_to_anchor: tuple[float, int] = (-0.05, 0),
    ax: Optional[axis.Axis] = None,
):
    _ax = ax

    # plotten
    if not ax:
        fig, ax = plt.subplots(figsize=figsize)

    gdf.plot(
        column=column,
        cmap=ListedColormap(colors),
        ax=ax,
        categorical=True,
        edgecolor=edgecolor,
        linewidth=0.2,
    )

    try:
        labels = gdf[column].cat.categories
    except AttributeError:
        plt.close("all")
        raise Exception(
            """
                The column provided should be an categorical column. Use pd.Categorical(df[column])
                to turn the column into a Categorical column. If the order of the legend is important
                provide the levels and set ordered=True
            """
        )

    if not column_label_kwargs:
        column_label_kwargs = {}

    if column_label:
        for x, y, label in zip(
            gdf.geometry.representative_point().x,
            gdf.geometry.representative_point().y,
            gdf[column_label],
        ):
            ax.annotate(
                label,
                xy=(x, y),
                xytext=(0, 0),
                textcoords="offset points",
                **column_label_kwargs,
            )

    # Create custom legend using the 'colors' and 'labels' variables, with a grey border
    legend_elements = _build_legend(colors, labels)

    # Move the legend to the bottom left outside the plot
    ax.legend(
        handles=legend_elements,
        bbox_to_anchor=bbox_to_anchor,
        loc="lower left",
        title=legend_title,
        frameon=False,
    )

    # lat/lon uit
    ax.set_axis_off()

    # laten zien
    plt.tight_layout()

    if not _ax:
        return fig, ax


def _build_legend(colors, labels):
    return [
        Patch(facecolor=color, label=label, edgecolor="#b0b0b0")
        for color, label in zip(colors, labels)
    ]
