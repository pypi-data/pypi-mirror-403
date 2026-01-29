from __future__ import annotations

from collections.abc import Hashable
from typing import (
    Any,
    Callable,
    Protocol,
    Sequence,
)


class WriteCsvLike(Protocol):
    """compatible with
    @overload
    def to_csv(
        self,
        path_or_buf: None = ...,
        sep: str = ...,
        na_rep: str = ...,
        float_format: str | Callable | None = ...,
        columns: Sequence[Hashable] | None = ...,
        header: bool_t | list[str] = ...,
        index: bool_t = ...,
        index_label: IndexLabel | None = ...,
        mode: str = ...,
        encoding: str | None = ...,
        compression: CompressionOptions = ...,
        quoting: int | None = ...,
        quotechar: str = ...,
        lineterminator: str | None = ...,
        chunksize: int | None = ...,
        date_format: str | None = ...,
        doublequote: bool_t = ...,
        escapechar: str | None = ...,
        decimal: str = ...,
        errors: OpenFileErrors = ...,
        storage_options: StorageOptions = ...,
    ) -> str:"""

    def __call__(
        self,
        path_or_buf: None = ...,
        sep: str = ...,
        na_rep: str = ...,
        float_format: str | Callable | None = ...,
        columns: Sequence[Hashable] | None = ...,
        header: Any | list[str] = ...,
        index: Any = ...,
        index_label: Any | None = ...,
        mode: str = ...,
        encoding: str | None = ...,
        compression: Any = ...,
        quoting: int | None = ...,
        quotechar: str = ...,
        lineterminator: str | None = ...,
        chunksize: int | None = ...,
        date_format: str | None = ...,
        doublequote: Any = ...,
        escapechar: str | None = ...,
        decimal: str = ...,
        errors: Any = ...,
        storage_options: Any = ...,
    ) -> str: ...
