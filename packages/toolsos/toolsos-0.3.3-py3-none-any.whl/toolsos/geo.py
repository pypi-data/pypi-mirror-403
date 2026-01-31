from __future__ import annotations

from pathlib import Path
from typing import Any, Union

import geopandas as gpd
import pandas as pd
import requests


def get_geo_json(
    level: str, year: Union[int, Any], with_water: bool = False, mra: bool = False
) -> dict[str, str]:
    """_summary_

    Args:
        level (str): 'stadsdelen'/'gebieden'/'wijken'/'buurten'
        year (int): jaar

    Returns:
        dict[str, str]: geo json containg of the desired level and year
    """
    base_url = "https://gitlab.com/os-amsterdam/datavisualisatie-onderzoek-en-statistiek/-/raw/main/public/geo"

    if level not in ["buurten", "wijken", "gebieden", "stadsdelen"]:
        raise ValueError(
            "level should be 'buurten', 'wijken', 'gebieden' or 'stadsdelen'"
        )

    if mra:
        level = f"{level}-mra"
        base_url = f"{base_url}/mra"
    else:
        base_url = f"{base_url}/amsterdam"

    if (year <= 2020) and not mra:
        year = "2015-2020"

    if with_water:
        url = f"{base_url}/{year}/{level}-{year}-geo.json"
    else:
        url = f"{base_url}/{year}/{level}-{year}-zw-geo.json"

    json = requests.get(url).json()

    return json


def get_geo_dataframe(
    level: str,
    year: Union[int, Any],
    with_water: bool = False,
    mra: bool = False,
    from_crs=4326,
    to_crs=28992,
):

    gdf = gpd.GeoDataFrame.from_features(
        get_geo_json(level=level, year=year, with_water=with_water, mra=mra)
    )

    gdf = gdf.set_crs(from_crs).to_crs(to_crs)

    return gdf


def merge_data_to_gdf(
    data: str, gdf: gpd.GeoDataFrame, key_data: str = "code", key_gdf: str = "code"
) -> gpd.GeoDataFrame:
    p = Path(data)
    if p.suffix == ".csv":
        df = pd.read_csv(data)
    elif p.suffix in [".xlsx", ".xls"]:
        df = pd.read_excel(data)
    else:
        raise ValueError(f"File type not supported: {p.suffix}")

    return gdf.merge(df, how="left", left_on=key_data, right_on=key_gdf)


def extract_name_code_table(geo_json: dict[str, str]) -> dict[str, str]:
    """_summary_

    Args:
        geo_json (dict[str, str]): geo_json of a specific level and year

    Returns:
        dict[str, str]: dictionary containing the mapping 'naam': 'year'
    """
    naam_code = {}
    f: Any  # Add explicit type hint for complex dict structure
    for f in geo_json["features"]:
        properties = f.get("properties")
        naam_code[properties["naam"]] = properties["code"]
    return naam_code


def get_geo_name_code(level: str, year: int, mra: bool = False) -> dict[str, str]:
    """_summary_

    Args:
        level (str): 'stadsdelen'/'gebieden'/'wijken'/'buurten'
        year (int): jaar

    Returns:
        dict[str, str]: _description_
    """
    json = get_geo_json(level=level, year=year, mra=mra)
    name_code = extract_name_code_table(json)
    return name_code


if __name__ == "__main__":
    ...
    # print(get_geo_json("buurten", 2021, mra=False))
    # print(get_geo_json("buurten", 2018, mra=False))

    # print(get_geo_json("buurten", 2021, mra=True))
    # print(get_geo_json("buurten", 2018, mra=True))

    print(get_geo_name_code("wijken", 2020, mra=False))
    print(get_geo_name_code("wijken", 2020, mra=True))


# https://gitlab.com/os-amsterdam/datavisualisatie-onderzoek-en-statistiek/-/raw/main/geo/mra//2015-2020/buurten-mra-2015-2020-zw-geo.json
