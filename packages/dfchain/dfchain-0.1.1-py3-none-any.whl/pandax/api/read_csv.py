from pandax.backends import sqlite
from pandax.backends.sqlite import SqliteExecutor
from pandax.backends.sqlite.schema import (
    _create_default_engine,
    _create_default_session,
)


def get_default_executor():
    executor = SqliteExecutor()
    engine = _create_default_engine()
    session = _create_default_session(engine)

    executor = executor.session(session)
    return executor


def get_default_backend():

    return sqlite


def read_csv(*ac, **av):
    return get_default_backend().read_csv(*ac, **av)


__all__ = ["get_default_executor", "read_csv"]
