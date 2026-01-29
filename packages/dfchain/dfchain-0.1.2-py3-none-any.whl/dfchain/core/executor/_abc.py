from __future__ import annotations

from dataclasses import dataclass, field

from .partitionable import DataFrameLike, PartitionAble


@dataclass
class Executor(PartitionAble):
    """Abstract interface for DataFrame executors.

    Implementations wrap a ``DataFrameLike`` instance and provide helpers for
    grouping and chunked iteration. The underlying dataframe is stored in
    ``self._df`` and exposed via the :attr:`df` property.
    """

    _df: DataFrameLike | None = field(default=None)

    is_eager: bool = field(default=False)
    is_inplace: bool = field(default=False)

    chunksize: int | None = field(default=None)

    # --- representation -------------------------------------------------

    def __str__(self) -> str:
        return str(self._df)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(df={repr(self._df)})"
