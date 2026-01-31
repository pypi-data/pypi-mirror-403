from __future__ import annotations

from functools import reduce
from typing import Iterable, Union

import polars as pl


def agg_multiple(
    cols: Union[str, list[str]], funcs: Union[str, list[str]]
) -> list[pl.Expr]:
    if isinstance(cols, str):
        cols = [cols]
    if isinstance(funcs, str):
        funcs = [funcs]

    exprs = []
    for col in cols:
        for func in funcs:
            exprs.append(getattr(pl.col(col), func)().alias(f"{col}_{func}"))

    return exprs


def complete(df: pl.DataFrame, cols: Iterable[str]) -> pl.DataFrame:
    combs = reduce(
        lambda x, y: x.join(y, how="cross"),
        [df.select(pl.col(col).unique()) for col in cols],
    )

    return combs.join(df, on=cols, how="left")
