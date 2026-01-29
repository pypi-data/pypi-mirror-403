"""Task decorator utilities.

This module provides the ``task`` decorator adapter used to wrap simple
pandas DataFrame-processing functions so they can be used as
Transformations in the :mod:`blottertools.api.pipeline` Pipeline.

The adapter supports two input shapes:
- A single pandas.DataFrame -> pandas.DataFrame function (applied to one
  partition), and
- An iterator of (idx, DataFrame) pairs -> iterator of DataFrames

The returned wrapper presents a consistent signature accepted by the
Pipeline/Executor runtime: it accepts either a DataFrame or an iterator of
(partition id, DataFrame) pairs and returns either a modified DataFrame or
an iterator of DataFrames respectively.

Docstrings follow the Google style for compatibility with Sphinx napoleon.
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Iterator
from typing import Callable, Iterator as TIterator, TypeVar, overload

import pandas as pd

F = TypeVar("F", bound=Callable[..., object])


def is_df_iterator(x) -> bool:
    """Return True when ``x`` is an iterator of DataFrames (not a single DF).

    Args:
        x: Candidate object to test.

    Returns:
        bool: True if ``x`` appears to be an iterator yielding DataFrames.
    """
    return not isinstance(x, pd.DataFrame) and isinstance(x, Iterator)


@overload
def task(
    func: Callable[[pd.DataFrame], pd.DataFrame],
) -> Callable[[pd.DataFrame], pd.DataFrame]: ...


@overload
def task(
    func: Callable[[pd.DataFrame], pd.DataFrame],
) -> Callable[[TIterator[pd.DataFrame]], TIterator[pd.DataFrame]]: ...


def task(func: F) -> F:
    """Decorator adapter that makes simple DataFrame functions compatible
    with Pipeline runtime.

    The original function may accept a pandas.DataFrame and optional
    keyword arguments. If the function accepts an ``_executor`` parameter,
    the wrapper will pass the Executor object through so tasks can
    inspect runtime configuration if necessary.

    Args:
        func: User-provided transformation callable accepting a DataFrame.

    Returns:
        Callable: Wrapped function matching the Pipeline/Executor expected
        signature.
    """
    sig = inspect.signature(func)
    params = sig.parameters

    @functools.wraps(func)
    def wrap_context(
        df,
        _executor=None,
        _inplace: bool = False,
        **av,
    ):
        # Pass executor only if accepted
        if "_executor" in params:
            av["_executor"] = _executor

        # DataFrame must be checked FIRST (it is iterable!)
        if isinstance(df, pd.DataFrame):
            result = func(df if _inplace else df.copy(), **av)

            if _inplace and result is not df:
                raise RuntimeError(
                    "In-place task must return the same DataFrame object."
                )
            return result

        # Iterator path: wrap to yield transformed DataFrames
        if isinstance(df, Iterator):

            def _gen() -> TIterator[pd.DataFrame]:
                for _, chunk in df:
                    out = func(chunk if _inplace else chunk.copy(), **av)
                    if _inplace and out is not chunk:
                        raise RuntimeError(
                            "In-place task must return the same DataFrame object for each chunk "
                            "(avoid rebinding like df = df.reset_index())."
                        )
                    yield out

            return _gen()

        raise TypeError(
            "distributed_task expects a DataFrame or an Iterator[DataFrame]"
        )

    return wrap_context  # type: ignore[return-value]
