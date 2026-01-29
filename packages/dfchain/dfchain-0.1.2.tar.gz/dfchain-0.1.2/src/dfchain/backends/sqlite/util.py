from __future__ import annotations

import json
import logging
import pickle
from collections.abc import Hashable
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Iterator, Optional, Tuple, Union

import pandas
import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert

from .models import DfChunk, DfGroup

logger = logging.getLogger(__name__)


def freeze_call(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Hashable:
    """returns a cached/memoized call of groupby.method like agg or simply the items"""

    def _freeze(x: Any) -> Hashable:
        if isinstance(x, dict):
            return tuple(sorted((k, _freeze(v)) for k, v in x.items()))
        if isinstance(x, (list, tuple)):
            return tuple(_freeze(v) for v in x)
        if isinstance(x, set):
            return tuple(sorted(_freeze(v) for v in x))
        if isinstance(x, (pd.DataFrame, pd.Series)):
            return ("<pandas>", type(x).__name__)
        return x

    return (_freeze(args), _freeze(kwargs))


def _key_to_hashable(k: Any) -> Hashable:
    if isinstance(k, tuple):
        return tuple(_key_to_hashable(x) for x in k)
    if isinstance(k, (pd.Timestamp, pd.Timedelta, pd.Period)):
        return str(k)
    try:
        hash(k)
        return k
    except TypeError:
        return str(k)


def ensure_df_iter(obj: Any) -> Iterator[pandas.DataFrame]:
    if isinstance(obj, pandas.DataFrame):
        yield obj
        return

    yield from obj


def init_chunk(session, groupkey, chunk_id, chunk):
    data = pickle.dumps(chunk, protocol=pickle.HIGHEST_PROTOCOL)
    stmt = insert(DfChunk).values(id=chunk_id, data=data)

    with session.begin():
        session.execute(stmt)

        if groupkey is not None:
            init_group(session, groupkey, chunk)
        session.flush()
        session.expunge_all()


def init_group(session, groupkey, chunk):
    """Internal helper: merge chunk groups into stored DfGroup rows."""
    for raw_key, group_df in chunk.groupby(groupkey):
        key = norm_key(raw_key)

        # fetch existing group (if any)
        existing = session.execute(
            select(DfGroup.data).where(DfGroup.groupbykeys == key)
        ).scalar_one_or_none()

        head_df = pickle.loads(existing) if existing is not None else None

        # merge safely
        if head_df is None or (isinstance(head_df, pandas.DataFrame) and head_df.empty):
            merged = group_df.copy()
        else:
            merged = pandas.concat([head_df, group_df], ignore_index=False)

        # upsert: insert merged as the stored value, update to merged on conflict
        _insert_merged_stored_value_group(session, key, merged)

        session.flush()
        session.expunge_all()  # drop ORM identity map refs


def _insert_merged_stored_value_group(session, key, merged):
    data = pickle.dumps(merged, protocol=pickle.HIGHEST_PROTOCOL)
    stmt = (
        insert(DfGroup)
        .values(groupbykeys=key, data=data)
        .on_conflict_do_update(
            index_elements=[DfGroup.groupbykeys],
            set_={"data": data},
        )
    )

    session.execute(stmt)


def norm_key(k) -> str:
    # groupby keys can be scalar or tuple; normalize to stable string
    # avoid treating strings/bytes as general Iterable sequences
    if isinstance(k, (str, bytes)):
        return json.dumps([k], default=str, separators=(",", ":"))
    if isinstance(k, Iterable):
        return json.dumps(list(k), default=str, separators=(",", ":"))
    return json.dumps([k], default=str, separators=(",", ":"))


AggSpec = Union[str, Callable, dict[str, Any], list[Any], tuple[Any, ...], None]


@dataclass
class DistributedGroupBy:
    """
    Docstring for DistributedGroupBy

    :var semantics: Description
    :var pandas: Description
    :vartype pandas: returns
    :var Placeholder: Description
    :vartype Placeholder: keep
    """

    # factory returning a fresh iterator of DataFrameGroupBy objects (one per partition)
    groupby_iter_factory: Callable[
        [], Iterator[pd.core.groupby.generic.DataFrameGroupBy]
    ]

    # optional column selection, to support gb["b"] semantics
    _selection: Optional[Union[str, list[str]]] = None

    _cache: dict[tuple[str, Hashable], Any] = field(
        default_factory=dict, init=False, repr=False
    )

    def clear_cache(self) -> None:
        self._cache.clear()

    def __getitem__(self, key: Union[str, list[str]]) -> "DistributedGroupBy":
        # Return a new wrapper with the selection applied.
        return DistributedGroupBy(self.groupby_iter_factory, _selection=key)

    def __iter__(self) -> Iterator[Tuple[Any, pd.DataFrame]]:
        """
        Global iteration semantics: yield each group key once with concatenated rows.
        (Good for group-wise transforms, not reductions.)
        """
        buckets: dict[Hashable, tuple[Any, list[pd.DataFrame]]] = {}

        for gb in self.groupby_iter_factory():
            if self._selection is not None:
                gb = gb[self._selection]  # type: ignore[index]

            for raw_key, grp in gb:
                hk = _key_to_hashable(raw_key)
                if hk not in buckets:
                    buckets[hk] = (raw_key, [grp])
                else:
                    buckets[hk][1].append(grp)

        for _, (raw_key, frames) in buckets.items():
            yield raw_key, pd.concat(frames, axis=0)

    # ---------- The important bit: reduction wrapper ----------

    def agg(self, func: AggSpec, *args: Any, **kwargs: Any) -> Any:
        """
        Partition-local agg, then global combine.

        Works like pandas: returns a Series/DataFrame depending on selection & func.
        """
        call_key = ("agg", freeze_call((func,) + args, kwargs) + (_key_to_hashable(self._selection),))  # type: ignore[arg-type]
        if call_key in self._cache:
            return self._cache[call_key]

        # 1) run per-partition
        parts: list[Union[pd.Series, pd.DataFrame]] = []
        for gb in self.groupby_iter_factory():
            if self._selection is not None:
                gb = gb[self._selection]  # type: ignore[index]
            parts.append(gb.agg(func, *args, **kwargs))

        # 2) combine
        result = self._combine_agg(parts, func)

        self._cache[call_key] = result
        return result

    def _combine_agg(
        self, parts: list[Union[pd.Series, pd.DataFrame]], func: AggSpec
    ) -> Any:
        """
        Combine already-aggregated partition outputs.

        For many reducers (sum/min/max/count/size), you can just concat and reduce again.
        For 'list', you must concatenate lists across partitions.
        For 'mean', you must do sum/count to avoid mean-of-means.
        """
        if not parts:
            # Mirror pandas-ish empty result
            return (
                pd.Series(dtype="float64")
                if self._selection is not None
                else pd.DataFrame()
            )

        # Determine whether we're combining Series or DataFrame
        is_series = isinstance(parts[0], pd.Series)

        # Concatenate the partition aggregates; index is group key (possibly MultiIndex)
        combined = pd.concat(parts, axis=0)

        # Special-case: list aggregation
        # - pandas gb.agg(list) yields lists per group; across partitions we get multiple lists per key
        # - we want to flatten them, not "list of lists"
        if func is list:
            if isinstance(combined, pd.Series):
                return combined.groupby(
                    level=list(range(combined.index.nlevels))
                ).apply(lambda s: [x for sub in s.tolist() for x in (sub or [])])
            else:
                # DataFrame: apply per column
                lvl = list(range(combined.index.nlevels))
                out = {}
                for col in combined.columns:
                    out[col] = (
                        combined[col]
                        .groupby(level=lvl)
                        .apply(lambda s: [x for sub in s.tolist() for x in (sub or [])])
                    )
                return pd.DataFrame(out)

        # Special-case: mean (correct combine = sum/count)
        if func == "mean":
            # Recompute partials as sum & count in one pass, then combine those
            # (This keeps partition outputs small and gives correct global means.)
            sum_parts: list[Union[pd.Series, pd.DataFrame]] = []
            cnt_parts: list[Union[pd.Series, pd.DataFrame]] = []
            for gb in self.groupby_iter_factory():
                if self._selection is not None:
                    gb = gb[self._selection]  # type: ignore[index]
                sum_parts.append(gb.agg("sum"))
                cnt_parts.append(gb.agg("count"))

            ssum = (
                pd.concat(sum_parts, axis=0)
                .groupby(level=list(range(sum_parts[0].index.nlevels)))
                .sum()
            )
            ccnt = (
                pd.concat(cnt_parts, axis=0)
                .groupby(level=list(range(cnt_parts[0].index.nlevels)))
                .sum()
            )
            return ssum / ccnt

        # Default: associative reducers can be combined by applying the same reducer again.
        # This is correct for: sum/min/max/count/size (and often first/last with caveats).
        if isinstance(combined, pd.Series):
            lvl = list(range(combined.index.nlevels))
            if func in ("sum", "min", "max", "count", "size"):
                return getattr(combined.groupby(level=lvl), func)()
            # fallback: groupby-apply the original func (may be slow / may fail)
            return combined.groupby(level=lvl).apply(lambda s: s.agg(func))

        # DataFrame
        lvl = list(range(combined.index.nlevels))
        gb2 = combined.groupby(level=lvl)
        if func in ("sum", "min", "max", "count", "size"):
            return getattr(gb2, func)()
        return gb2.apply(lambda df: df.agg(func))

    # ---------- passthrough for other methods (your existing approach) ----------

    def __getattr__(self, name: str):
        def _method(*args: Any, **kwargs: Any) -> Any:
            call_key = (
                name,
                freeze_call(args, kwargs),
                _key_to_hashable(self._selection),
            )
            if call_key in self._cache:
                return self._cache[call_key]

            outputs: list[Any] = []
            for g in self.groupby_iter_factory():
                if self._selection is not None:
                    g = g[self._selection]  # type: ignore[index]
                attr = getattr(g, name)
                out = attr(*args, **kwargs) if callable(attr) else attr
                outputs.append(out)

            # You likely already have _combine(outputs, name); keep using it.
            result = self._combine(outputs)
            self._cache[call_key] = result
            return result

        return _method

    def _combine(self, outputs: list[Any]) -> Any:
        """
        Placeholder: keep your existing combiner logic.
        For reductions, prefer agg() which has explicit semantics.
        """
        if len(outputs) == 1:
            return outputs[0]
        return outputs
