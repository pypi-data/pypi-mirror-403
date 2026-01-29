from __future__ import annotations

import logging
import pickle
from dataclasses import dataclass, field
from typing import Any, Iterator

import pandas
from sqlalchemy import distinct, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from pandax.core.executor._abc import Executor

from .adapters.csvreader import SqliteCsvReader
from .models import DfChunk, DfGroup
from .util import (
    DistributedGroupBy,
    _insert_merged_stored_value_group,
    freeze_call,
    init_chunk,
    norm_key,
)
from .schema import session_factory

logger = logging.getLogger(__name__)


"""SQLite-backed Executor implementation.

This module implements SqliteExecutor, an Executor that stores pandas
DataFrame chunks and grouped DataFrames as pickled blobs inside a SQLite
database via SQLAlchemy. The implementation supports a small fluent builder
API for configuration and exposes iteration and groupby semantics that are
compatible with pandas-like workflows.

Key classes and functions
- SqliteExecutor: main Executor implementation used by the sqlite backend.
- update_group/_update_group_inner: helpers used to update stored group
  aggregates from incoming chunk data.

The docstrings in this module follow the Google style so they can be
rendered nicely by Sphinx (napoleon extension).
"""


@dataclass
class SqliteExecutor(Executor):
    """SQLite backed executor storing pickled DataFrame chunks and groups.

    This class exposes a small builder API for configuration:
    ``session(...)``, ``groupkey(...)`` and ``eager()``
    all return ``self`` so they can be chained.

    Attributes:
        _session (Session | None): SQLAlchemy session used to persist chunks
            and groups. If not set, ``build()`` will create a temporary engine
            and session.
        _groupby_cache (dict): Internal cache mapping groupby call signatures
            to DistributedGroupBy instances.

    Example:
    ::
        executor = (
            SqliteExecutor(chunksize=1_000)
            .session()
            .textFileReader(pd.read_csv("input_file.csv", chunksize=1_000))
            .build()
        )
    """

    _session: Session | None = field(default=None)  # sqlite session

    _groupby_cache = {}

    # --- Builder API -------------------------------------------------

    def groupkey(self, groupkey: str | None) -> "SqliteExecutor":
        """Set the grouping key used by group operations and return ``self``.

        This is a builder-style setter; read the configured value using
        :meth:`Executor.get_groupkey`.

        Args:
            groupkey (str | None): Column name (or None) to use for grouping.

        Returns:
            SqliteExecutor: ``self`` for chaining.
        """
        _empty_iterator = object()

        if (
            self._df is not None
            and next(self.iter_chunks(), _empty_iterator) is _empty_iterator
        ):
            raise RuntimeError(
                'You must set groupkey before loading data, via `SqliteExecutor().session(cls.session).groupkey("a").df(df)`'
            )

        self._groupkey = groupkey
        self.clear_cache()
        return self

    def session(self, session: Session | None = None) -> "SqliteExecutor":
        """Set the SQLAlchemy session and return ``self`` (builder-style).
        If no session is configured, a temporary on-disk SQLite engine and
        session will be created.

        Args:
            session (Session | None): SQLAlchemy session to use.

        Returns:
            SqliteExecutor: ``self`` for chaining.
        """
        if session is None:
            session = session_factory()
        self._session = session
        return self

    def eager(self) -> "SqliteExecutor":
        """Enable eager execution and return ``self`` (builder-style).

        Eager execution changes internal flags and can affect how groupby
        operations are represented. See class documentation for details.

        Returns:
            SqliteExecutor: ``self`` for chaining.
        """
        self.is_eager = True
        return self

    def df(self, df: pandas.DataFrame):
        """Set an in-memory DataFrame to be persisted when ``build()`` is run.

        Args:
            df (pandas.DataFrame): DataFrame to partition and store as chunks.

        Raises:
            TypeError: if `df` is not a pandas DataFrame

        Returns:
            SqliteExecutor: ``self`` for chaining.
        """
        if not isinstance(df, pandas.DataFrame):
            raise TypeError("Must provide pandas DataFrame `df`")
        if self._session is None:
            raise ValueError("Session must be built using .session()")
        self._df = df
        chunksize = self.chunksize if self.chunksize is not None else 10_000
        for chunk_id, start in enumerate(range(0, len(self._df), chunksize)):
            chunk = self._df.iloc[start : start + chunksize].copy()

            init_chunk(self._session, self.get_groupkey(), chunk_id, chunk)
        return self

    def textFileReader(self, textFileReader: Iterator[pandas.DataFrame]):
        """Consume an iterator of DataFrame chunks and persist them.

        Args:
            textFileReader (Iterator[pandas.DataFrame]): Iterator yielding
                DataFrame partitions (e.g. pandas read_csv with chunksize).

        Returns:
            SqliteExecutor: ``self`` for chaining.
        """
        for chunk_id, chunk in enumerate(textFileReader):
            init_chunk(self._session, self.get_groupkey(), chunk_id, chunk)
        return self

    # --- Chunks API ------------------------------------------------

    def iter_chunks(self):
        """Yield stored chunk id and unpickled DataFrame for each stored chunk.

        Yields:
            Iterator[tuple[int, pandas.DataFrame]]: (chunk_id, DataFrame)
        """
        q = (
            self._session.query(DfChunk.id, DfChunk.data)
            .yield_per(1)  # batch size
            .enable_eagerloads(False)
        )
        for chunk_id, data in q:
            yield chunk_id, pickle.loads(data)

    def iter_groups(self):
        """Yield stored group key and unpickled grouped DataFrame blob.

        Yields:
            Iterator[tuple[str | None, pandas.DataFrame]]: (group_key, DataFrame)
        """
        q = (
            self._session.query(DfGroup.groupbykeys, DfGroup.data)
            .yield_per(1)
            .enable_eagerloads(False)
            .order_by(DfGroup.groupbykeys)
        )
        for key, data in q:
            yield key, pickle.loads(data)

    def update_group(self, df: pandas.DataFrame):
        """Update stored per-group aggregates using ``df``.

        If the executor has no configured group key this is a no-op.

        Args:
            df (pandas.DataFrame): DataFrame whose groups should be merged
                into the stored group rows.
        """
        # logger.debug("call update group %s", df)
        if self.get_groupkey() is None:
            return
        return update_group(self._session, self.get_groupkey(), df)

    def clear_groups(self) -> None:
        """Clear stored groups in the database and clear caches.

        This deletes all DfGroup rows from the configured session and
        resets the in-memory groupby cache.
        """
        self.clear_cache()
        if self._session is None:
            return
        self._session.query(DfGroup).delete()

    # --- Pandas Compat API ---------------------------------------------

    def _groupby(self, *ac, **av):
        """Return a groupby-like object over stored partitions.

        This method mirrors pandas.DataFrame.groupby semantics but returns a
        DistributedGroupBy wrapper that will iterate over partition-local
        groupby iterators and present a global view for reductions and
        concatenation-like operations.
        """
        # respect Executor API getter for groupkey
        if self.get_groupkey() is None:
            obj = pickle.loads(self._session.scalars(select(DfChunk)).first().data)
            return obj.groupby(*ac, **av)
        # cache key for the GROUPBY SPEC only (not downstream ops)
        gb_key = freeze_call(ac, av)

        if gb_key not in self._groupby_cache:
            # store a FACTORY that recreates the iterator each time
            def factory():
                return self._iter_groupby(*ac, **av)

            self._groupby_cache[gb_key] = DistributedGroupBy(factory)

        return self._groupby_cache[gb_key]

    def _iter_groupby(self, *ac, **av):
        """Internal iterator that yields per-partition groupby objects.

        Yields:
            Iterator[pandas.core.groupby.generic.DataFrameGroupBy]:
                partition-local DataFrameGroupBy objects.
        """
        unique_keys = select(distinct(DfGroup.groupbykeys))
        for groupbykey in self._session.scalars(unique_keys):
            if groupbykey is None:
                continue
            yield pickle.loads(
                self._session.scalars(
                    select(DfGroup).where(DfGroup.groupbykeys == groupbykey)
                )
                .first()
                .data
            ).groupby(*ac, **av)

    # --- Resource management ------------------------------------------------

    def clear_cache(self) -> None:
        """Clear internal groupby cache."""
        self._groupby_cache = {}

    def rebuild_groups(self, flush_every: int = 1) -> None:
        """Rebuild DfGroup rows from stored chunks.

        This reads all stored chunks, groups rows by the configured group key,
        and writes combined group blobs into the DfGroup table. ``flush_every``
        controls how often buffered per-group frames are flushed to the DB to
        limit memory usage.

        Args:
            flush_every (int): How many chunks to process before flushing
                per-group buffers to the database.

        Raises:
            RuntimeError: if the session is not set on the executor.
        """
        if self._session is None:
            raise RuntimeError("Session not set")
        if self.get_groupkey() is None:
            return

        groupkey = self.get_groupkey()

        self.clear_groups()

        buffers: dict[str, pandas.DataFrame] = {}
        seen = 0

        for _chunk_id, chunk in self.iter_chunks():
            for raw_key, gdf in chunk.groupby(groupkey):
                key = norm_key(raw_key)

                # buffer in memory
                if key in buffers:
                    buffers[key] = pandas.concat(
                        [buffers[key], gdf], ignore_index=False
                    )
                else:
                    buffers[key] = gdf.copy()

            seen += 1
            if seen % flush_every == 0:
                self._flush_group_buffers(buffers)
                buffers.clear()

        # final flush
        if buffers:
            self._flush_group_buffers(buffers)
            buffers.clear()

        self._session.commit()

    # # --- I/O API ------------------------------------------------------

    def read_csv(self, *ac, **av):
        """Read CSV via the sqlite-backed CSV reader.

        This returns the reader instance's read_csv callable which mirrors
        pandas.read_csv semantics but stores partitions directly into the
        sqlite-backed executor.
        """
        reader = SqliteCsvReader(self)
        return reader.read_csv(*ac, **av)

    @staticmethod
    def _ensure_df_iter(obj: Any) -> Iterator[pandas.DataFrame]:
        if isinstance(obj, pandas.DataFrame):
            yield obj
            return

        yield from obj

    # --- SQLite backed DataFrame chunks

    def _flush_group_buffers(self, buffers: dict[str, pandas.DataFrame]) -> None:
        """Merge in-memory buffers into per-group stored blobs in the DB.

        For each buffered group key, the stored blob (if present) is loaded,
        concatenated with the new rows, and re-inserted. The method purposely
        limits memory use by flushing multiple groups in a batch.
        """
        for key, df in buffers.items():
            existing = self._session.execute(
                select(DfGroup.data).where(DfGroup.groupbykeys == key)
            ).scalar_one_or_none()

            if existing is None:
                merged = df
            else:
                head = pickle.loads(existing)
                merged = pandas.concat([head, df], ignore_index=False)

            _insert_merged_stored_value_group(self._session, key, merged)

        self._session.flush()
        self._session.expunge_all()

    def write_chunk(self, key: int, val: pandas.DataFrame) -> None:
        """Write (or update) a chunk row in the DB.

        Args:
            key (int): Chunk identifier.
            val (pandas.DataFrame): DataFrame chunk to store.
        """
        data = pickle.dumps(val, protocol=pickle.HIGHEST_PROTOCOL)
        stmt = (
            insert(DfChunk)
            .values(id=key, data=data)
            .on_conflict_do_update(index_elements=[DfChunk.id], set_={"data": data})
        )
        self._session.execute(stmt)

    def get_session(self) -> Session:
        """Return the configured SQLAlchemy session.

        Returns:
            Session: SQLAlchemy session used by the executor.
        """
        return self._session


def update_group(session, groupkey, chunk):
    """Update stored groups using an incoming chunk DataFrame.

    The function will group the chunk by ``groupkey`` and merge each
    group into the DfGroup table using ``_update_group_inner``.

    Args:
        session (Session): SQLAlchemy session to use.
        groupkey (str | None): Column to group by. If None, the function
            is a no-op.
        chunk (pandas.DataFrame): Incoming chunk to merge.
    """
    if groupkey is None:
        # _update_group_inner(session, "0", chunk)
        return

    for raw_key, group_df in chunk.groupby(groupkey):
        _update_group_inner(session, raw_key, group_df)


def _update_group_inner(session, raw_key, group_df: "pandas.DataFrame"):
    """Internal helper to merge a single group into the stored blob.

    The function attempts to update rows by aligning common indices and
    columns, overwriting existing values for overlapping cells and
    appending new columns when necessary.

    Args:
        session (Session): SQLAlchemy session to use.
        raw_key (Any): Raw group key value coming from DataFrame.groupby.
        group_df (pandas.DataFrame): DataFrame representing the group's rows.
    """
    key = norm_key(raw_key)

    existing = session.execute(
        select(DfGroup.data).where(DfGroup.groupbykeys == key)
    ).scalar_one_or_none()

    head_df = pickle.loads(existing) if existing is not None else None

    if head_df is None or (isinstance(head_df, pandas.DataFrame) and head_df.empty):
        merged = group_df.copy()
    else:
        # 1) align rows (update() implicitly aligns; make it explicit + cheap)
        common_index = head_df.index.intersection(group_df.index)
        if common_index.empty:
            # nothing to update; keep existing
            merged = head_df
        else:
            # work on a copy to avoid mutating cached object in surprising ways
            merged = head_df.copy()

            # 2) overwrite columns that exist in both
            common_cols = merged.columns.intersection(group_df.columns)
            if len(common_cols):
                merged.loc[common_index, common_cols] = group_df.loc[
                    common_index, common_cols
                ].to_numpy(copy=False)

            # 3) add brand-new columns from group_df
            new_cols = group_df.columns.difference(merged.columns)
            if len(new_cols):
                merged.loc[common_index, new_cols] = group_df.loc[
                    common_index, new_cols
                ].to_numpy(copy=False)

    _insert_merged_stored_value_group(session, key, merged)
