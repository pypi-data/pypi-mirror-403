from __future__ import annotations

from typing import Any, Protocol

from pandas.core.groupby.generic import DataFrameGroupBy


class GroupByLike(Protocol):
    """
    GroupByLike methods are compatible with pandas:
    ::

        def groupby(
            self,
            by=None,
            axis: Axis | lib.NoDefault = lib.no_default,
            level: IndexLabel | None = None,
            as_index: bool = True,
            sort: bool = True,
            group_keys: bool = True,
            observed: bool | lib.NoDefault = lib.no_default,
            dropna: bool = True,
        )
    """

    def __call__(
        self,
        by: Any | None = None,
        axis: int = 0,
        level: Any | None = None,
        as_index: bool = True,
        sort: bool = True,
        group_keys: bool = True,
        observed: bool = False,
        dropna: bool = True,
    ) -> DataFrameGroupBy: ...
