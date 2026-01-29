from abc import ABC, abstractmethod
from collections.abc import Hashable
from dataclasses import dataclass, field
from typing import Any, Iterable, TypeVar

from .groupbylike import GroupByLike

DataFrameLike = TypeVar("DataFrameLike")


@dataclass
class PartitionAble(ABC):

    _groupkey: Hashable | None = field(default=None)

    # --- grouping / chunking -------------------------------------------

    @abstractmethod
    def _groupby(self, *args: Any, **kwargs: Any) -> "GroupByLike":
        """Low‑level groupby implementation for the underlying backend."""

    @abstractmethod
    def write_chunk(self, key: int, val: "DataFrameLike"): ...

    @abstractmethod
    def update_group(self, df: "DataFrameLike") -> None:
        """Update the current group with the provided dataframe."""

    @abstractmethod
    def clear_groups(self) -> None:
        """Clear any cached grouping state maintained by the executor."""

    @abstractmethod
    def rebuild_groups(self, flush_every: int = 1) -> None: ...

    # --- streaming -------------------------------------------

    @abstractmethod
    def iter_chunks(self) -> Iterable["DataFrameLike"]:
        """Iterate over the dataframe in chunks.

        The chunking strategy (by row count, partition, etc.) is left to the
        concrete implementation.
        """

    @abstractmethod
    def iter_groups(self) -> Iterable[tuple[Hashable, "DataFrameLike"]]:
        """Iterate over grouped data as ``(key, group_df)`` pairs."""

    # --- accessors -------------------------------------------

    def get_groupkey(self) -> Hashable:
        """Accessor method"""
        return self._groupkey

    @property
    def groupby(self, *args: Any, **kwargs: Any) -> "GroupByLike":
        """Return a groupby object for the wrapped dataframe.

        This is a thin wrapper around :meth:`_groupby` to keep the public API
        backend‑agnostic while allowing implementations to choose the concrete
        groupby type.
        """

        return self._groupby
