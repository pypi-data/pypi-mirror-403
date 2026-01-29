"""Pandas backend executor implementation.

This module provides :class:`PandasExecutor`, an in‑memory implementation of
:class:`blottertools.core.executor.Executor` that wraps a single
:pandas:`pandas.DataFrame` instance and exposes grouping and chunking hooks
used by higher‑level APIs.
"""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass
from typing import Any, Iterable

import pandas
from pandas.core.groupby.generic import DataFrameGroupBy

from pandax.core.executor._abc import Executor


@dataclass
class PandasExecutor(Executor):
    """Executor implementation backed by an in‑memory :class:`pandas.DataFrame`.

    ``PandasExecutor`` is a lightweight in‑memory executor that wraps a
    :class:`pandas.DataFrame` and implements the grouping and chunking hooks
    defined by :class:`blottertools.core.executor.PartitionAble`.

    Attributes:
        _df (:obj:`pandas.DataFrame` or `None`, default `None`):
            The wrapped dataframe. It can be provided at construction time or
            later via :meth:`df`.
        is_eager (bool, default `False`): Hint for task execution mode.
            When ``True``, tasks may execute eagerly rather than building a deferred plan.
            The exact semantics are defined by higher‑level APIs.
        is_inplace (bool, default `False`):
            When ``True``, task functions are expected to mutate ``_df`` in
            place. When ``False``, tasks should treat ``_df`` as immutable and
            reassign a new dataframe instead.
        chunksize (int or `None`, default `None`)
            Optional hint used by higher‑level code to determine how many rows
            to process per chunk when streaming or partitioning the data.

    Note:
        The pandas backend is designed for in‑memory use and does not maintain
        an index by group key. As a result, methods that would write changes
        back to specific groups (``update_group``, ``clear_groups``,
        ``rebuild_groups``) raise :class:`NotImplementedError`.
    """

    def df(self, df):
        """Set the wrapped dataframe and return self for fluent construction.

        Parameters:
            df (:class:`pandas.DataFrame`): Dataframe to wrap.

        Returns:
            `self` (:obj:`PandasExecutor`): The executor instance.
        """
        self._df = df
        return self

    # --- grouping -------------------------------------------------

    def _groupby(self, *args: Any, **kwargs: Any) -> DataFrameGroupBy:
        """Low‑level groupby implementation.

        This simply delegates to :meth:`pandas.DataFrame.groupby` with the
        provided arguments and returns a pandas :class:`DataFrameGroupBy`.
        """
        return self._df.groupby(*args, **kwargs)

    def iter_groups(self) -> Iterable[tuple[Hashable, pandas.DataFrame]]:
        """Iterate grouped data as ``(key, group_df)`` pairs.

        If :attr:`_groupkey` is ``None``, yield a single pair
        ``(None, self._df)`` containing the whole dataframe.
        Otherwise, perform ``self._df.groupby(self._groupkey)`` and yield
        the resulting ``(key, group)`` pairs produced by pandas.
        """
        if self._groupkey is None:
            # No grouping defined; yield the whole dataframe as a single group
            yield (None, self._df)
            return

        for key, group in self._df.groupby(self._groupkey):
            yield key, group

    def update_group(self, df: pandas.DataFrame) -> None:
        """Update the current group with the provided dataframe.

        The pandas backend does not maintain an index by group key, so there
        is no safe default way to update a single group in place. This
        method therefore raises :class:`NotImplementedError`. Backends that
        support indexed group updates (for example, a database backend)
        should provide an implementation.
        """
        # Without a defined grouping key or current group context, we cannot
        # implement a safe default. This method is therefore a no‑op by
        # default and should be overridden where group updates are needed.
        raise NotImplementedError("PandasExecutor does not index by groupkeys")

    def clear_groups(self) -> None:
        """Clear any cached grouping state.

        The pandas executor does not cache grouped state keyed by a group
        index, so this method raises :class:`NotImplementedError`.
        """
        raise NotImplementedError("PandasExecutor does not index by groupkeys")

    def rebuild_groups(self, flush_every: int = 1):
        """Rebuild or re‑materialize groups.

        Parameters:
            flush_every (`int`, optional): Hint controlling how often to flush
                intermediate state. Not implemented for the in‑memory pandas backend.
        """
        raise NotImplementedError("PandasExecutor does not index by groupkeys")

    # --- chunking -------------------------------------------------

    def iter_chunks(self) -> Iterable[pandas.DataFrame]:
        """Iterate dataframe chunks.

        The default in‑memory strategy yields a single chunk containing the
        entire dataframe. Callers that require more advanced chunking
        behaviour should subclass :class:`PandasExecutor` or use a
        different :class:`~blottertools.core.executor.Executor`
        implementation.

        Note:
            The default implementation yields a ``(key, chunk)`` pair where the
            ``key`` is ``0`` and ``chunk`` is the full dataframe. Higher‑level
            code should account for this convention when consuming the iterator.
        """
        # Simple default: a single chunk containing the whole dataframe.
        # Callers that need more advanced behavior can override this in a
        # subclass or provide a different Executor implementation.
        yield (0, self._df)

    def write_chunk(self, key, val):
        """Write a processed chunk back to the executor.

        The pandas backend treats the entire dataframe as one chunk; this
        method therefore replaces ``self._df`` with ``val`` and ignores the
        provided ``key``.
        """
        self._df = val
