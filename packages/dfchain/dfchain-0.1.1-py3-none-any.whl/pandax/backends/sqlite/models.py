from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import LargeBinary, String
from typing import Optional


class Base(DeclarativeBase):
    pass


class DfChunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)

    groupbykeys: Mapped[Optional[str]] = mapped_column(String)

    data: Mapped[bytes] = mapped_column(LargeBinary())


class DfGroup(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)

    groupbykeys: Mapped[str] = mapped_column(String, unique=True)

    data: Mapped[bytes] = mapped_column(LargeBinary())
