"""Pipeline utilities for blottertools.

This module defines the Transformation protocol, a lightweight type for
functions/objects that transform pandas DataFrames, and the Pipeline class
that composes a sequence of such transformations and runs them using an
Executor. The design intentionally keeps transformations simple: a
Transformation may be any callable that accepts a DataFrame and an
Executor and returns a DataFrame. This allows a transformation to be a
plain function.
"""

from __future__ import annotations

import logging
from typing import Iterator, Protocol, Sequence, Optional

import pandas

from pandax.core.executor import Executor

# pylint: disable=missing-function-docstring

logger = logging.getLogger(__name__)


class Transformation(Protocol):
    """Callable protocol representing a DataFrame transformation.

    A Transformation is any callable that accepts a pandas.DataFrame, and
    optionally an Executor and returns a pandas.DataFrame.

    Example:
        A transformation can be a function
        ::
            import pandas as pd
            from blottertools import task

            @task
            def add_flag(df: pd.DataFrame, _executor, threshold: float = 0.5) -> pd.DataFrame:
                df = df.copy()
                df["flag"] = df["score"] > threshold
                return df

    """

    def __call__(
        self, df: pandas.DataFrame, _executor: Optional[Executor], **kwargs
    ) -> pandas.DataFrame:
        """If the Executor is provided, the transformation can utilize a pre-built
        group index for distributed processing.

        Args:
            df (pandas.DataFrame): Input DataFrame
            _executor (Optional[Executor]): Executor that will run the transformation.
            **kwargs: Additional keyword arguments supplied by the caller.

        Returns:
            pandas.DataFrame: Transformed DataFrame.
        """


class Pipeline:
    """Compose and run a sequence of Transformations.

    The Pipeline object holds an ordered sequence of Transformation callables
    and provides a single :meth:`run` method which executes each step in
    order using the provided :class:`Executor`.

    Attributes:
        steps (Sequence[Transformation]): Ordered list of transformations.

    Example:
        >>> pipeline = Pipeline([step1, step2])
        >>> pipeline.run(executor)
    """

    steps: Sequence[Transformation]

    def __init__(self, steps: Sequence[Transformation]) -> None:
        """Create a new Pipeline.

        Args:
            steps: Sequence of callables that implement the Transformation
                protocol. Each step will be applied to every chunk yielded by
                the executor.
        """
        self.steps = list(steps)

    def run(self, executor: Executor) -> None:
        """Execute the pipeline using ``executor``.

        For each transformation in :attr:`steps`, the pipeline applies the
        transformation across all chunks provided by the executor via
        :func:`transform`. By default, transformed chunks are written back
        to the executor using :meth:`Executor.write_chunk` (unless the
        executor is configured as inplace). After each step, if the
        executor has a group key configured and is not in eager mode, the
        pipeline rebuilds group blobs via :meth:`Executor.rebuild_groups`.

        Args:
            executor (Executor): Executor responsible for storing and
                iterating over DataFrame chunks.
        """
        for step in self.steps:
            for idx, out in transform(executor, step):
                if not executor.is_inplace:
                    executor.write_chunk(idx, out)  # or update_df(out, idx)

            if executor.is_eager:
                continue

            if executor.get_groupkey() is not None:
                executor.rebuild_groups(flush_every=1)


def transform(executor: Executor, f: Transformation) -> Iterator[pandas.DataFrame]:
    """Apply a transformation across the executor's stored chunks.

    This helper iterates executor.iter_chunks(), applying the provided
    transformation ``f`` to each chunk. If the executor is configured as
    eager and a group key is present, the resulting fragment will be
    immediately merged into the stored groups via
    :meth:`Executor.update_group`.

    Args:
        executor (Executor): Executor providing chunk iteration.
        f (Transformation): Transformation to apply to each chunk.

    Yields:
        Iterator[tuple[int, pandas.DataFrame]]: Pairs of (chunk_id, DataFrame)
            with the transformed DataFrame for each chunk.
    """
    for idx, df in executor.iter_chunks():  # yield (id, df)
        out = f(df, executor, _inplace=executor.is_inplace)  # df -> df
        if executor.is_eager and executor.get_groupkey() is not None:
            executor.update_group(out)
        yield idx, out
