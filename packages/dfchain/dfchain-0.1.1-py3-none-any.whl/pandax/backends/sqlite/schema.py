"""
Docstring for blottertools.backends.sqlite.schema
"""

from __future__ import annotations

import os
import tempfile

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from .models import Base


def _create_default_engine(engine_url: str | None = None) -> Engine:
    """Create a SQLAlchemy engine.

    If engine_url is None, create a temporary on-disk SQLite database and
    return an engine connected to it.
    """
    if engine_url is None:
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        engine_url = f"sqlite:///{path}"

    return create_engine(engine_url)


def _create_default_session(engine) -> Session:
    Base.metadata.create_all(bind=engine)
    session = Session(engine)
    return session


def session_factory():
    engine = _create_default_engine()
    session = _create_default_session(engine)
    return session


__all__ = ["_create_default_engine", "_create_default_session", "session_factory"]
