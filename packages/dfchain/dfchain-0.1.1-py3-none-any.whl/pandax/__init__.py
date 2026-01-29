"""Top-level package for blottertools.

Example:
    Constructing a simple task, creating a
    SqliteExecutor that reads CSV chunks into a temporary SQLite-backed
    store, running a pipeline and then re-assembling the stored chunks
    ::

        from blottertools import SqliteExecutor, Pipeline, task
        import pandas as pd

        @task
        def add_dark_border_flag(
            df: pd.DataFrame,
            score_col: str = "border_darkness_score",
            threshold: float = 0.8,
            output_col: str = "has_dark_border",
        ) -> pd.DataFrame:
            df = df.copy()
            df[output_col] = df[score_col] > threshold
            return df


        # Build an executor and stream CSV into it using chunksize
        executor = (
            SqliteExecutor(chunksize=1_000)
            .session()
            .textFileReader(pd.read_csv("api_rawitem.csv", chunksize=1_000))
            .build()
        )

        # Construct a pipeline and run it
        pipeline = Pipeline([add_border_darkness_score, add_dark_border_flag])
        pipeline.run(executor)

        # Re-assemble all stored chunks into a single DataFrame
        merged_df = pd.concat(
            (df for _, df in executor.iter_chunks()),
            ignore_index=True
        )
"""

from .api import Pipeline, read_csv, task
from .backends.sqlite import SqliteExecutor
from .core.executor import Executor
