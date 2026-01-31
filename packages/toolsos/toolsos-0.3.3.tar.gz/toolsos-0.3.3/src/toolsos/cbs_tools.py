from __future__ import annotations

import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pyreadstat import pyreadstat as prs

if TYPE_CHECKING:
    import pyreadstat


def get_batch_size(path, memory_limit):
    df, _ = prs.read_sav(path, row_limit=1000)

    # memory in megabytes
    mem_size = df.memory_usage().sum() / 1_000_000

    # The amount of blocks (of a thousand rows fit in the memory_limit)
    n_blocks = memory_limit / mem_size

    # Calculate the number of rows that fit within the memory limit
    return round(n_blocks * 1000)


class SavToParquet:
    def __init__(
        self, file: str, folder_out: str, verbose: bool = False, memory_limit=10_000
    ) -> None:
        self.file = file
        self.folder_out = folder_out
        self.verbose = verbose
        self.memory_limit = memory_limit

    @property
    def path_out(self) -> str:
        return str(Path(self.file)).replace(".sav", ".parquet")

    @property
    def chunks(self) -> Iterator[tuple["pyreadstat.metadata_container", pd.DataFrame]]:

        chunksize = get_batch_size(self.file, self.memory_limit)

        if self.verbose:
            print(f"Reading file in blocks of {chunksize} rows")
            print("One such block should fit within the memory limit")

        return prs.read_file_in_chunks(prs.read_sav, self.file, chunksize=chunksize)

    def write_meta_to_json(self) -> None:
        json_path = self.path_out.replace(".parquet", "_meta.json")

        meta_dict = {}
        for attr_name in dir(self.meta):
            if not attr_name.startswith("__"):
                attr = getattr(self.meta, attr_name)

                if isinstance(attr, datetime):
                    attr = attr.strftime("%Y-%m-%d %H:%M:%S")

                meta_dict[attr_name] = attr

        with open(json_path, "w") as file:
            json.dump(meta_dict, file)

    def write_meta_to_pickle(self) -> None:
        pickle_path = self.path_out.replace(".parquet", "_meta.pickle")

        with open(pickle_path, "wb") as file:
            pickle.dump(self.meta, file)

    def write_to_parquet(self) -> None:

        print("Writing table")

        line1, self.meta = prs.read_sav(self.file, row_limit=1)
        schema = pa.Table.from_pandas(line1).schema

        with pq.ParquetWriter(self.path_out, schema) as writer:
            for idx, (df, _) in enumerate(self.chunks):
                if self.verbose:
                    print(f"Writing chunk: {idx: >4}")

                table = pa.Table.from_pandas(df)
                writer.write_table(table)

        print("Writing metadata")
        self.write_meta_to_json()
        self.write_meta_to_pickle()
        print("Done")


def read_parquet_in_chunks(
    path: str, columns: Optional[list[str]] = None
) -> Iterator[pd.DataFrame]:
    parquet_file = pq.ParquetFile(path)
    for table in parquet_file.iter_batches(columns=columns):
        df = table.to_pandas()
        yield df


def read_metadata_container(path: str) -> dict[str, Any]:
    with open(path, "rb") as file:
        return pickle.load(file)


def read_meta_from_json(path: str) -> dict[str, Any]:
    with open(path) as file:
        return json.load(file)
