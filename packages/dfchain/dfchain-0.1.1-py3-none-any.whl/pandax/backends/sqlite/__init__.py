from ...core._api import ReadCsvLike
from .adapters.csvreader import SqliteCsvReader
from .executor_impl import SqliteExecutor

from .schema import _create_default_engine, _create_default_session


class _read_csv_factory(ReadCsvLike):
    reader: SqliteCsvReader

    def __init__(self):
        engine = _create_default_engine()
        session = _create_default_session(engine)

        executor = SqliteExecutor().session(session)
        self.reader = SqliteCsvReader(executor)

    def __call__(self, filepath_or_buffer, *ac, **av):
        self.reader.read_csv(filepath_or_buffer, *ac, **av)
        return self.reader.executor


read_csv = _read_csv_factory()

__all__ = ["read_csv"]
