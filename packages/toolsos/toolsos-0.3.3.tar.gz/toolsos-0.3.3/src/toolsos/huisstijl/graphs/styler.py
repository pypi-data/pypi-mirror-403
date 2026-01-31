import json

import plotly.graph_objects as go
import requests
from requests import ConnectionError

from .graph_styles import STYLE_NEW

# class BaseStyle:
#     style_url = (
#         "https://raw.githubusercontent.com/jbosga-ams/oistyle/main/base_style.json"
#     )

#     def __init__(self):
#         self.grab_styling()

#     def grab_styling(self, style_path: str = None):
#         if not style_path:
#             try:
#                 res = requests.get(self.style_url).json()
#             except ConnectionError:
#                 print("Failed grabbing basestyle from the interwebs")
#                 # Add option to manually provide json file
#         else:
#             res = json.loads()

#         for k, v in res.items():
#             setattr(self, k, v)

#         self.font = "Amsterdam Sans ExtraBold, Corbel"

#     def _get_axis_format(self):
#         self.gridline_color = "#dbdbdb"  # Jorren vragen om deze aan te passen

#         return {
#             "zerolinecolor": self.gridline_color,
#             "gridcolor": self.gridline_color,
#             "gridwidth": self.gridline_width,
#             "showline": True,
#             "linewidth": self.gridline_width,
#             "linecolor": self.gridline_color,
#             #             "mirror": True,
#             "showgrid": False,
#         }

#     def _get_base_template_layout(self):
#         return go.layout.Template(
#             layout={
#                 "font": {"family": self.font, "size": self.font_size},
#                 "plot_bgcolor": self.plot_bgcolor,
#                 "colorway": self.colors["darkblue_lightblue_gradient_5"],
#                 "separators": ",",  # Jorren vragen om deze toe te voegen
#             }
#         )

#     def get_base_template(
#         self, graph_type: str = None, orientation: str = None, colors: str = None
#     ):
#         """[summary]

#         Args:
#             graph_type (str, optional): Pick 'bar', 'line' or 'bar'. Defaults to None.
#             orientation (str, optional): [description]. Pick horizontal ('h') or vertical 'v'. Defaults to None.
#             colors (str, optional): Set basecolors. Defaults to None.

#         Raises:
#             ValueError: [description]

#         Returns:
#             [type]: [description]
#         """
#         base_template = self._get_base_template_layout()
#         axis_format = self._get_axis_format()

#         if graph_type == "bar":
#             if orientation in ["v", "vertical"]:
#                 base_template.layout.xaxis.update(axis_format)
#                 base_template.layout.yaxis.update(zeroline=False)
#             elif orientation in ["h", "horizontal"]:
#                 base_template.layout.yaxis.update(axis_format)
#                 base_template.layout.xaxis.update(zeroline=False)
#             else:
#                 raise ValueError(
#                     "Orientation ('v'/'vertical' or 'h'/'horizontal') should be supplied with graph_type=='bar'"
#                 )

#         elif graph_type == "line":
#             base_template.layout.xaxis.update(axis_format)

#         if colors:
#             base_template.layout.update({"colorway": colors})

#         return base_template

#     def get_ois_colors(self, colorscale):
#         colorscale = self.colors.get(colorscale, [])
#         if not colorscale:
#             raise Exception(f"Kies uit {self.colors.keys()}")

#         return colorscale


class BaseStyle:
    def __init__(self, style_path=None):
        if style_path is None:
            self.style = STYLE_NEW
        else:
            with open(style_path) as file:
                self.style = json.load(file)

    def _get_axis_format(self):

        return {
            "zerolinecolor": self.style["gridline_color"],
            "gridcolor": self.style["gridline_color"],
            "gridwidth": self.style["gridline_width"],
            "showline": True,
            "linewidth": self.style["gridline_width"],
            "linecolor": self.style["gridline_color"],
            "showgrid": self.style["showgrid"],
        }

    def _get_base_template_layout(self, font):
        if font == "Amsterdam Sans":
            font_ = self.style["font"]
            font_bold_ = self.style["font_bold"]
        elif font == "Corbel":
            font_ = self.style["font_corbel"]
            font_bold_ = self.style["font_bold_corbel"]
        else:
            raise ValueError("Font should be 'Amsterdam Sans' or 'Corbel'")

        return go.layout.Template(
            layout={
                "xaxis": {
                    "tickfont": font_bold_,
                },
                "yaxis": {
                    "tickfont": font_bold_,
                },
                "legend": {"font": font_},
                "plot_bgcolor": self.style["plot_bgcolor"],
                "separators": ",",
                "font": font_bold_,
            }
        )

    def get_base_template(
        self,
        graph_type: str = None,
        orientation: str = None,
        colors: str = None,
        font: str = "Amsterdam Sans",
    ):
        """[summary]

        Args:
            graph_type (str, optional): Pick 'bar', 'line' or 'bar'. Defaults to None.
            orientation (str, optional): [description]. Pick horizontal ('h') or vertical 'v'. Defaults to None.
            colors (str, optional): Set basecolors. Defaults to None.

        Raises:
            ValueError: [description]

        Returns:
            [type]: [description]
        """
        base_template = self._get_base_template_layout(font)
        axis_format = self._get_axis_format()

        if graph_type == "bar":
            if orientation in ["v", "vertical"]:
                base_template.layout.xaxis.update(axis_format)
                base_template.layout.yaxis.update(zeroline=False)
            elif orientation in ["h", "horizontal"]:
                base_template.layout.yaxis.update(axis_format)
                base_template.layout.xaxis.update(zeroline=False)
            else:
                raise ValueError(
                    "Orientation ('v'/'vertical' or 'h'/'horizontal') should be supplied with graph_type=='bar'"
                )

        elif graph_type == "line":
            base_template.layout.xaxis.update(axis_format)

        if colors:
            base_template.layout.update({"colorway": colors})

        return base_template
