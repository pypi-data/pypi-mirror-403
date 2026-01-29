"""Pandas backend for :mod:`blottertools`.

This subpackage provides an :class:`~blottertools.core.executor.Executor`
implementation backed by an in‑memory :class:`pandas.DataFrame`.

The main entry point is :class:`.PandasExecutor`, which wraps a single
dataframe and exposes the generic executor interface used throughout
:mod:`blottertools`.

Typical usage::

    import pandas as pd
    from blottertools.backends.pandas import PandasExecutor

    df = pd.DataFrame({"x": [1, 2, 3], "y": [10, 20, 30]})
    ex = PandasExecutor().df(df).build()

    # iterate as a single group
    for key, group in ex.iter_groups():
        ...

"""

from .executor_impl import PandasExecutor
