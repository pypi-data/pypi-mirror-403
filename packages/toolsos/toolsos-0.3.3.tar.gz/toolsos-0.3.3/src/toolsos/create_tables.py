from __future__ import annotations

import pandas as pd


def custom_round(x: int, base: int = 10) -> int:
    return int(base * round(float(x) / base))


def create_table(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    tbl = df.groupby(cols).size().reset_index().rename(columns={0: "aantal"})
    tbl["aantal"] = tbl["aantal"].apply(
        custom_round
    )  # Je kan hier nog '* 100' achter zetten als je het naar een percentage wil omzetten
    tbl["grp_size"] = tbl.groupby(cols[:-1])["aantal"].transform("sum")
    tbl["aandeel"] = tbl["aantal"] / tbl["grp_size"]

    # Eventueel grp_size kolom weer droppen
    # tbl = tbl.drop(columns="grp_size")

    return tbl


def create_tables(
    df: pd.DataFrame, tables: dict[str, list[str]]
) -> dict[str, pd.DataFrame]:
    rs = {}
    for k, v in tables.items():
        rs[k] = create_table(df, v)
    return rs
