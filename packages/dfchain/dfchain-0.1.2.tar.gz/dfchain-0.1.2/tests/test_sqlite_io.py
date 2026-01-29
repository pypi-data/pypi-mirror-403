import unittest
import pandas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from dfchain.backends.sqlite import read_csv
from dfchain.backends.sqlite import SqliteExecutor
from dfchain.backends.sqlite.models import Base
from dfchain.backends.sqlite.adapters.csvreader import (
    SqliteCsvReader,
    SqliteCsvWriter,
)


# class TestSqliteIO(unittest.TestCase):
#     # TODO: this is broken until sqlite_io
#     def test_read_csv_creates_executor_and_persists_chunks(self):
#         executor = read_csv(
#             "fixtures/blotter-new.csv", groupkey="lkid", parse_dates=True
#         )

#         self.assertIsInstance(executor, SqliteExecutor)

#         chunks = list(executor.iter_chunks())
#         self.assertGreater(len(chunks), 0)
#         for idx, chunk in chunks:
#             self.assertIsInstance(chunk, pandas.DataFrame)

#     def test_read_csv_accepts_session(self):
#         engine = create_engine("sqlite:///:memory:")
#         Base.metadata.create_all(bind=engine)
#         session = Session(engine)

#         executor = read_csv(
#             "fixtures/blotter-new.csv",
#             groupkey="lkid",
#             session=session,
#             parse_dates=True,
#         )
#         self.assertIs(executor._session, session)


class TestSqliteCsvReaderFactory(unittest.TestCase):
    def test_read_csv_creates_executor_and_persists_chunks(self):
        import dfchain.backends.sqlite as pandasflow

        # pandasflow.

        executor = pandasflow.read_csv("fixtures/blotter-new.csv", parse_dates=True)
        self.assertIsInstance(executor, SqliteExecutor)

        chunks = list(executor.iter_chunks())
        self.assertGreater(len(chunks), 0)
        for idx, chunk in chunks:
            self.assertIsInstance(chunk, pandas.DataFrame)

    def test_native_pandas_readcsv(self):

        lazy_df = pandas.read_csv(
            "fixtures/blotter-new.csv", parse_dates=True, chunksize=2
        )
        executor = SqliteExecutor().session().textFileReader(lazy_df)

        chunks = list(executor.iter_chunks())
        self.assertGreater(len(chunks), 0)
        for idx, chunk in chunks:
            self.assertIsInstance(chunk, pandas.DataFrame)


if __name__ == "__main__":
    unittest.main()
