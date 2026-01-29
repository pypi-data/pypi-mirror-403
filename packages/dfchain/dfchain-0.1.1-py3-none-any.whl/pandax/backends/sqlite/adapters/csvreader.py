"""
Docstring for blottertools.backends.sqlite.adapters.csvreader
"""

from typing import Any, Generator

import pandas
from pandas.io.parsers.readers import TextFileReader

from pandax.core._api import ReadCsvLike, WriteCsvLike

from ..util import ensure_df_iter, init_chunk

# from .. import SqliteExecutor


class SqliteCsvReader:
    executor: "SqliteExecutor"

    def __init__(self, executor) -> None:
        self.executor = executor

    # --- I/O API ------------------------------------------------------

    def _read_csv(self, *ac, **av) -> None:
        # use configured chunksize; pass other args to pandas.read_csv
        reader: TextFileReader = pandas.read_csv(
            *ac, chunksize=self.executor.chunksize, **av
        )
        for i, chunk in enumerate(ensure_df_iter(reader)):
            chunk: pandas.DataFrame
            init_chunk(
                self.executor.get_session(), self.executor.get_groupkey(), i, chunk
            )
        # return self

    @property
    def read_csv(self) -> ReadCsvLike:
        """Instance-level entry point that behaves like pandas.read_csv.

        Usage: ``executor.session(s).from_csv(path_or_buf, **kwargs)``
        """
        return self._read_csv


class SqliteCsvWriter:
    executor: "SqliteExecutor"

    def __init__(self, executor) -> None:
        self.executor = executor

    # --- I/O API ------------------------------------------------------

    @property
    def to_csv(self) -> WriteCsvLike:
        """Return a callable that writes stored chunks to CSV.

        The returned callable delegates to pandas.DataFrame.to_csv on each
        in-memory chunk.
        """
        return self._to_csv

    def _to_csv(self, *ac, **av) -> None:
        _iter: Generator[tuple[Any, Any], Any, None] = self.executor.iter_chunks()
        idx, first = next(_iter)
        first.to_csv(*ac, **av)
        for idx, df in _iter:
            df.to_csv(*ac, mode="a", header=False, **av)
