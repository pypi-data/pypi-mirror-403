from __future__ import annotations

from collections.abc import Hashable
from typing import (
    Any,
    Callable,
    Iterable,
    Literal,
    Mapping,
    Protocol,
    Sequence,
)

from pandas.io.parsers.readers import TextFileReader


class ReadCsvLike(Protocol):
    """
    ReadCsvLike methods are compatible with pandas:
    ::

        def read_csv(
            filepath_or_buffer: FilePath | ReadCsvBuffer[bytes] | ReadCsvBuffer[str],
            *,
            sep: str | None | lib.NoDefault = ...,
            delimiter: str | None | lib.NoDefault = ...,
            header: int | Sequence[int] | None | Literal["infer"] = ...,
            names: Sequence[Hashable] | None | lib.NoDefault = ...,
            index_col: IndexLabel | Literal[False] | None = ...,
            usecols: UsecolsArgType = ...,
            dtype: DtypeArg | None = ...,
            engine: CSVEngine | None = ...,
            converters: Mapping[Hashable, Callable] | None = ...,
            true_values: list | None = ...,
            false_values: list | None = ...,
            skipinitialspace: bool = ...,
            skiprows: list[int] | int | Callable[[Hashable], bool] | None = ...,
            skipfooter: int = ...,
            nrows: int | None = ...,
            na_values: Hashable
            | Iterable[Hashable]
            | Mapping[Hashable, Iterable[Hashable]]
            | None = ...,
            na_filter: bool = ...,
            verbose: bool | lib.NoDefault = ...,
            skip_blank_lines: bool = ...,
            parse_dates: bool | Sequence[Hashable] | None = ...,
            infer_datetime_format: bool | lib.NoDefault = ...,
            keep_date_col: bool | lib.NoDefault = ...,
            date_parser: Callable | lib.NoDefault = ...,
            date_format: str | dict[Hashable, str] | None = ...,
            dayfirst: bool = ...,
            cache_dates: bool = ...,
            iterator: Literal[True],
            chunksize: int | None = ...,
            compression: CompressionOptions = ...,
            thousands: str | None = ...,
            decimal: str = ...,
            lineterminator: str | None = ...,
            quotechar: str = ...,
            quoting: int = ...,
            doublequote: bool = ...,
            escapechar: str | None = ...,
            comment: str | None = ...,
            encoding: str | None = ...,
            encoding_errors: str | None = ...,
            dialect: str | csv.Dialect | None = ...,
            on_bad_lines=...,
            delim_whitespace: bool | lib.NoDefault = ...,
            low_memory: bool = ...,
            memory_map: bool = ...,
            float_precision: Literal["high", "legacy"] | None = ...,
            storage_options: StorageOptions = ...,
            dtype_backend: DtypeBackend | lib.NoDefault = ...,
    )
    """

    def __call__(
        self,
        filepath_or_buffer: Any,
        *,
        sep: str | None | Any = ...,
        delimiter: str | None | Any = ...,
        header: int | Sequence[int] | None | Literal["infer"] = ...,
        names: Sequence[Hashable] | None | Any = ...,
        index_col: Any | Literal[False] | None = ...,
        usecols: Any = ...,
        dtype: Any | None = ...,
        engine: Any | None = ...,
        converters: Mapping[Hashable, Callable] | None = ...,
        true_values: list | None = ...,
        false_values: list | None = ...,
        skipinitialspace: bool = ...,
        skiprows: list[int] | int | Callable[[Hashable], bool] | None = ...,
        skipfooter: int = ...,
        nrows: int | None = ...,
        na_values: (
            Hashable | Iterable[Hashable] | Mapping[Hashable, Iterable[Hashable]] | None
        ) = ...,
        na_filter: bool = ...,
        verbose: bool | Any = ...,
        skip_blank_lines: bool = ...,
        parse_dates: bool | Sequence[Hashable] | None = ...,
        infer_datetime_format: bool | Any = ...,
        keep_date_col: bool | Any = ...,
        date_parser: Callable | Any = ...,
        date_format: str | dict[Hashable, str] | None = ...,
        dayfirst: bool = ...,
        cache_dates: bool = ...,
        iterator: Literal[True],
        chunksize: int | None = ...,  # overriden
        compression: Any = ...,
        thousands: str | None = ...,
        decimal: str = ...,
        lineterminator: str | None = ...,
        quotechar: str = ...,
        quoting: int = ...,
        doublequote: bool = ...,
        escapechar: str | None = ...,
        comment: str | None = ...,
        encoding: str | None = ...,
        encoding_errors: str | None = ...,
        dialect: str | Any | None = ...,
        on_bad_lines=...,
        delim_whitespace: bool | Any = ...,
        low_memory: bool = ...,
        memory_map: bool = ...,
        float_precision: Literal["high", "legacy"] | None = ...,
        storage_options: Any = ...,
        dtype_backend: Any = ...,
    ) -> TextFileReader: ...
