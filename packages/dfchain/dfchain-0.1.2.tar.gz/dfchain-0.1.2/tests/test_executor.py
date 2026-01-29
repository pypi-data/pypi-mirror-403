import unittest

from dfchain.backends.sqlite import SqliteExecutor

from dfchain.api.pipeline import transform, Pipeline

from dfchain.backends.sqlite.models import DfChunk, Base
from dfchain.backends.sqlite.adapters.csvreader import (
    SqliteCsvReader,
    SqliteCsvWriter,
)

from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select

import pandas
import pickle
import pandas.testing as pdt

import blottercli.distributed_functions as F


class TestSqliteExecutor(unittest.TestCase):
    """Unit tests for basic SqliteExecutor persistence and iteration."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        # Ensure a clean in-memory schema
        Base.metadata.drop_all(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        with Session(cls.engine) as session:
            cls.executor = (
                SqliteExecutor()
                .groupkey("lkid")
                .session(session)
                # .read_csv("fixtures/blotter-new.csv", parse_dates=True)
            )
            csv = SqliteCsvReader(cls.executor)
            csv.read_csv("fixtures/blotter-new.csv", parse_dates=True)

    def test_from_path_persists_chunks_and_iter_chunks_returns_df(self):
        # initialize executor using builder pattern (session + from_csv)

        chunks = list(self.executor.iter_chunks())
        self.assertGreater(len(chunks), 0)
        for idx, chunk in chunks:
            self.assertIsInstance(chunk, pandas.DataFrame)

    def test_stored_chunks_unpickle_to_df(self):

        stored = list(self.executor._session.scalars(select(DfChunk)))
        self.assertGreater(len(stored), 0)
        for row in stored:
            df = pickle.loads(row.data)
            self.assertIsInstance(df, pandas.DataFrame)


class TestDistributedTasks(unittest.TestCase):
    """Tests for distributed task integration using a small deterministic DataFrame."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.drop_all(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        # Keep a session open for the lifetime of these tests
        cls.session = Session(cls.engine)

        df = F.init_df()
        # Persist the small DataFrame into DB-backed executor
        # cls.executor = SqliteExecutor.from_df(df, cls.session, "a")
        cls.executor = SqliteExecutor().groupkey("a").session(cls.session).df(df)

    @classmethod
    def tearDownClass(cls):
        cls.session.close()

    def test_iter_chunks_returns_original_row_count(self):
        idx_chunks = list(self.executor.iter_chunks())
        d_idx_chunks = {idx: chunk for idx, chunk in idx_chunks}

        self.assertGreater(len(idx_chunks), 0)
        total_rows = sum(len(c) for c in d_idx_chunks.values())
        self.assertEqual(total_rows, len(F.init_df()))

    def test_iter_groups_matches_unique_group_keys(self):
        groups = list(self.executor.iter_groups())
        unique_keys = set(F.init_df()["a"])  # grouping on column 'a'
        self.assertEqual(len(groups), len(unique_keys))
        for key, g in groups:
            self.assertIsInstance(g, pandas.DataFrame)
            # each group should contain rows for a single 'a' value
            self.assertEqual(g["a"].nunique(), 1)

    def test_transform_add_1_increments_values(self):
        # Use a fresh executor built from the same in-memory DB to avoid mutating shared state

        result_chunks = list(transform(self.executor, F.add_1))
        self.assertGreater(len(result_chunks), 0)
        # idx, chunk = result_chunks[0]
        d_idx_chunks = {idx: chunk for idx, chunk in result_chunks}

        concatenated = pandas.concat(
            d_idx_chunks.values(), ignore_index=True
        ).reset_index(drop=True)
        expected = F.init_df().reset_index(drop=True) + 1

        # Compare only numeric columns present in expected
        numeric_cols = expected.select_dtypes(include=["number"]).columns.tolist()
        pdt.assert_frame_equal(
            concatenated[numeric_cols].reset_index(drop=True), expected[numeric_cols]
        )


class TestDistributedTasksPipeline(unittest.TestCase):
    """Tests for distributed task integration using a small deterministic DataFrame."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.drop_all(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        # Keep a session open for the lifetime of these tests
        cls.session = Session(cls.engine)

        df = F.init_df()
        # Persist the small DataFrame into DB-backed executor
        cls.executor = SqliteExecutor().groupkey("a").session(cls.session).df(df)

    def test_pipeline_sum_margin_b_adds_aggregated_columns(self):

        pipeline = Pipeline([F.sum_margin_b])

        # Should run without raising
        pipeline.run(self.executor)

        idx_chunks = list(self.executor.iter_chunks())
        d_idx_chunks = {idx: chunk for idx, chunk in idx_chunks}
        chunks = d_idx_chunks.values()
        df_all = pandas.concat(chunks, ignore_index=True)

        # Expect aggregation columns from sum_margin_b join; common suffixes used in implementation
        self.assertTrue(
            any(col.endswith("b_list") or col == "b_list" for col in df_all.columns)
        )
        self.assertTrue(
            any(col.endswith("b_sum") or col == "b_sum" for col in df_all.columns)
        )


class TestDistributedPipeline(unittest.TestCase):
    """Small integration test for running a Pipeline over the SqliteExecutor."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.drop_all(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        df = F.init_df()
        cls.session = Session(cls.engine)
        cls.executor = (
            SqliteExecutor().session(cls.session).groupkey("a").df(df).eager()
        )
        cls.pipeline = Pipeline([F.sum_margin_b])

    @classmethod
    def tearDownClass(cls):
        cls.session.close()

    def test_pipeline_updates_chunks(self):
        # Run pipeline and assert resulting chunks contain expected aggregation columns
        self.pipeline.run(self.executor)
        idx_chunks = list(self.executor.iter_chunks())
        d_idx_chunks = {idx: chunk for idx, chunk in idx_chunks}
        chunks = d_idx_chunks.values()
        self.assertGreater(len(chunks), 0)
        df_all = pandas.concat(chunks, ignore_index=True)

        self.assertTrue(
            any(col.endswith("b_sum") or col == "b_sum" for col in df_all.columns)
        )
        # Ensure aggregated column has at least one non-null value
        sum_cols = [c for c in df_all.columns if c.endswith("b_sum") or c == "b_sum"]
        if sum_cols:
            self.assertFalse(df_all[sum_cols[0]].isna().all())


class TestDistributedPipelineNoGroupKey(unittest.TestCase):
    """Small integration test for running a Pipeline over the SqliteExecutor."""

    # no groupkey

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.drop_all(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        df = F.init_df()
        cls.session = Session(cls.engine)
        cls.executor = SqliteExecutor().session(cls.session).df(df)
        # cls.executor = SqliteExecutor.from_df(df, cls.session)
        cls.pipeline = Pipeline([F.sum_margin_b])

    @classmethod
    def tearDownClass(cls):
        cls.session.close()

    def test_pipeline_updates_chunks(self):
        # Run pipeline and assert resulting chunks contain expected aggregation columns
        self.pipeline.run(self.executor)
        idx_chunks = list(self.executor.iter_chunks())
        d_idx_chunks = {idx: chunk for idx, chunk in idx_chunks}
        chunks = d_idx_chunks.values()
        self.assertGreater(len(chunks), 0)
        df_all = pandas.concat(chunks, ignore_index=True)

        self.assertTrue(
            any(col.endswith("b_sum") or col == "b_sum" for col in df_all.columns)
        )
        # Ensure aggregated column has at least one non-null value
        sum_cols = [c for c in df_all.columns if c.endswith("b_sum") or c == "b_sum"]
        if sum_cols:
            self.assertFalse(df_all[sum_cols[0]].isna().all())


class TestDistributedPipelineBlotterNew(unittest.TestCase):
    """Smoke test: run the real blotter-new pipeline end-to-end but only assert basic invariants."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.drop_all(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        cls.session = Session(cls.engine)

        cls.executor = (
            SqliteExecutor(1024).groupkey(["lkid", "date"]).session(cls.session)
        )
        from dfchain.backends.sqlite.adapters.csvreader import SqliteCsvReader

        csv = SqliteCsvReader(cls.executor)
        csv.read_csv(
            "./fixtures/sample2_options_positions_520_rows.csv",
            parse_dates=True,
        )

        steps = [
            F.step1_create_pk,
            F.step2_sector_pal_date,
            F.step3_impute_ticker,
            F.step4_compute_open_liq,
            F.step5_compute_fund_value,
            F.step6_agg_daily,
        ]
        cls.pipeline = Pipeline(steps)

    @classmethod
    def tearDownClass(cls):
        cls.session.close()

    def test_pipeline_smoke(self):
        from dfchain.backends.sqlite.adapters.csvreader import SqliteCsvWriter

        self.pipeline.run(self.executor)

        idx_chunks = list(self.executor.iter_chunks())
        d_idx_chunks = {idx: chunk for idx, chunk in idx_chunks}
        chunks = d_idx_chunks.values()
        self.assertGreater(len(chunks), 0)

        df_all = pandas.concat(chunks, ignore_index=True)

        check_cols = ["lkid", "date", "analyst", "sector", "pal", "exposure", "return"]
        self.assertTrue(set(check_cols).issubset(set(df_all.columns)))
        csvwriter = SqliteCsvWriter(self.executor)
        csvwriter.to_csv(
            "./distributed-blotter-new.csv",
            index=False,
            columns=["lkid", "date", "analyst", "sector", "pal", "exposure", "return"],
            float_format="%.16f",
            date_format="%Y-%m-%d",
        )


if __name__ == "__main__":
    unittest.main()
