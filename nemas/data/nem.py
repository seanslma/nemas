import re
import logging
import polars as pl
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
from typing import IO

from nemas.utils import to_lowercase, to_uppercase
from nemas.data.web import get_html
from nemas.data.filter import apply_filters


__all__ = [
    'read_nem_zip',
]

logger = logging.getLogger(__name__)


def standardize_params(
    tables: list | None = None,
    columns: list[str] | dict[str, list[str]] | None = None,
    schemas: dict[str, dict] | None = None,
    conditions: dict[str, pl.Expr | list[tuple]] | None = None,
    conditions_lowercase: bool = False,
) -> tuple[
    list | None,
    dict[str, list[str]] | None,
    dict[str, dict] | None,
    dict[str, pl.Expr | list[tuple]] | None,
]:
    """
    Standardize the parameters for reading NEM zip files.

    Parameters
    ----------
    tables : list[str] | None
        List of table names to read. If None, read all tables.
    columns : list[str] | dict[str, list[str]] | None
        List of columns to read, or dict of table_name -> list of columns.
        If None, read all columns.
    schemas : dict[str, dict] | None
        Dict of table_name -> schema dict (column_name -> polars dtype).
        If None, infer schema from the CSV.
    conditions : dict[str, pl.Expr | list[tuple]] | None
        Dict of table_name -> filter conditions. Each condition can be a polars
        expression or a list of tuples (column, operator, value).
    conditions_lowercase : bool
        If True, convert all column names in conditions to lowercase.

    Returns
    -------
    tuple[
        list | None,
        dict[str, list[str]] | None,
        dict[str, dict] | None,
        dict[str, pl.Expr | list[tuple]] | None,
    ]
        Standardized tables, columns, schemas, and conditions.
    """
    if tables is not None:
        if isinstance(tables, str):
            tables = [tables]
        elif not isinstance(tables, list):
            raise TypeError(
                f'Invalid type for `tables`: {type(tables)}.'
                ' Must be str, list, or None.'
            )
        tables = to_uppercase(tables)
    if columns is not None:
        if isinstance(columns, (str, list)):
            if tables is not None and len(tables) == 1:
                columns = {
                    tables[0]: [columns] if isinstance(columns, str) else columns
                }
            else:
                columns = None
                logger.warning(
                    'The `columns` parameter ignored. It is not a dict of lists.'
                )
        elif not isinstance(columns, dict):
            columns = None
            logger.warning(
                'The `columns` parameter ignored. It is not a dict of lists.'
            )
        columns = to_uppercase(columns, dict_values=True)
    if schemas is not None:
        if not isinstance(schemas, dict):
            schemas = None
            logger.warning(
                'The `schemas` parameter ignored. It is not a dict of dicts.'
            )
        else:
            val = next(iter(schemas.values()), None)
            if not isinstance(val, dict):
                if tables is not None and len(tables) == 1:
                    schemas = {tables[0]: schemas}
                else:
                    schemas = None
                    logger.warning(
                        'The `schemas` parameter ignored. It is not a dict of dicts.'
                    )
        schemas = to_uppercase(schemas, dict_values=True)
    if conditions is not None:
        if not isinstance(conditions, dict):
            if tables is not None and len(tables) == 1:
                conditions = {
                    tables[0]: conditions
                    if isinstance(conditions, (list, pl.Expr))
                    else [conditions]
                }
            else:
                conditions = None
                logger.warning(
                    'The `conditions` parameter ignored.'
                    ' It is not a dict of tuples or polars expressions.'
                )
        if conditions_lowercase:
            conditions = to_lowercase(conditions, dict_values=True)
        else:
            conditions = to_uppercase(conditions, dict_values=True)
    return tables, columns, schemas, conditions


def get_source_bytes(
    source: str | Path | IO[str] | IO[bytes] | bytes,
    *,
    requests_session=None,
) -> bytes:
    # Normalize source into raw bytes
    if isinstance(source, bytes):
        raw_bytes = source
        default_name = 'downloaded.zip'
    elif isinstance(source, (str, Path)):
        source_str = str(source)
        if source_str.startswith(('http://', 'https://')):
            raw_bytes = get_html(
                source_str, session=requests_session, ret_type='content'
            )
            default_name = Path(source_str).name or 'downloaded.zip'
        else:
            path = Path(source_str)
            if not path.exists():
                raise FileNotFoundError(f'File not exist: {path}')
            raw_bytes = path.read_bytes()
            default_name = path.name
    elif hasattr(source, 'read'):
        # File-like object (IO[str] or IO[bytes])
        content = source.read()
        raw_bytes = content.encode() if isinstance(content, str) else content
        default_name = getattr(source, 'name', 'downloaded.zip')
        default_name = Path(default_name).name if default_name else 'downloaded.zip'
    else:
        raise TypeError(f'Unsupported source type: {type(source)!r}')

    return raw_bytes, default_name


def read_zip_csv(
    zip_file: ZipFile,
    file_name: str,
    tables: list = None,
    columns: list[str] | dict[str, list[str]] = None,
    schemas: dict[str, list[str] | dict[str, pl.DataType]] = None,
    conditions: dict[str, pl.Expr | list[tuple]] = None,
    header_to_lowercase: bool = True,
) -> dict:
    raw = zip_file.read(file_name)

    # get table start and end rows
    table_metadata = (
        pl.read_csv(
            raw,
            skip_rows=0,
            columns=[0, 2],
            new_columns=['rid', 'flag', 'tbl'],
            batch_size=8192 // 4,
            has_header=False,
            ignore_errors=True,
            schema=None,
            # low_memory=True,
            row_index_name='rid',
        )
        .filter(pl.col('flag').is_in(['I', 'D']))
        .group_by(['tbl'])
        .agg(
            (pl.col('rid').first()).alias('start'),
            (pl.col('rid').last()).alias('end'),
        )
        .filter(pl.lit(True) if tables is None else pl.col('tbl').is_in(tables))
    )

    # read tables
    dfs = {}
    for table_name, skip_rows, row_end in table_metadata.iter_rows():
        n_rows = row_end - skip_rows
        cols = None if columns is None else columns.get(table_name, None)
        schema_overrides = None if schemas is None else schemas.get(table_name, None)
        df = pl.read_csv(
            raw,
            columns=cols,
            skip_lines=skip_rows,
            schema_overrides=schema_overrides,
            batch_size=8192 // 4,
            n_rows=n_rows,
            # low_memory=True,
            has_header=True,
            ignore_errors=True,
            truncate_ragged_lines=True,
            try_parse_dates=True,
        )
        if header_to_lowercase:
            df = df.rename(str.lower)
            table_name = table_name.lower()
        if conditions is not None:
            df = apply_filters(df, conditions.get(table_name, None))

        dfs[table_name] = df

    return dfs


def read_nem_zip(
    source: str | Path | IO[str] | IO[bytes] | bytes,
    *,
    requests_session=None,
    tables: list = None,
    columns: list[str] | dict[str, list[str]] = None,
    schemas: dict[str, dict] = None,
    conditions: dict[str, pl.Expr | list[tuple]] = None,
    save_zip: bool = False,
    zip_path: str | Path | None = None,
    header_to_lowercase: bool = True,
    validate_params: bool = True,
) -> dict[str, pl.DataFrame]:
    """
    Read a NEM zip file from a URL, local filepath, file-like object, or raw bytes.

    Parameters
    ----------
    source : str | Path | IO[str] | IO[bytes] | bytes
        - str/Path that looks like a URL (http:// or https://)
        - str/Path pointing to an existing file
        - file-like object (has `.read()`)
        - bytes
    requests_session : requests.Session, optional
        If provided, use this session for HTTP requests (e.g. for authentication).
    tables : list[str], optional
        List of table names to read. If None, read all tables.
    schemas : dict[str, dict], optional
        Dict of table_name -> schema dict (column_name -> polars dtype).
        If None, infer schema from the CSV.
    conditions : dict[str, pl.Expr | list[tuple]], optional
        Dict of table_name -> filter conditions. Each condition can be a polars
        expression or a list of tuples (column, operator, value).
    save_zip : bool
        If True, save the raw zip bytes to `zip_path` (or a default name).
    zip_path : str | Path, optional
        Where to save the zip if keep_zip=True. Defaults to the source filename
        (or "downloaded.zip" if it can't be inferred, e.g. from a URL/buffer).
    header_to_lowercase : bool
        If True, convert all column names to lowercase.
    validate_params : bool
        If True, validate and standardize the `tables`, `columns`, `schemas`, and
        `conditions` parameters.
    """
    raw_bytes, default_name = get_source_bytes(
        source, requests_session=requests_session
    )
    buffer = BytesIO(raw_bytes)

    # Save to disk if requested
    if save_zip:
        save_path = Path(zip_path) if zip_path else Path(default_name)
        save_path.write_bytes(buffer.getvalue())

    # Standardize parameters
    if validate_params:
        tables, columns, schemas, conditions = standardize_params(
            tables=tables,
            columns=columns,
            schemas=schemas,
            conditions=conditions,
            conditions_lowercase=header_to_lowercase,
        )

    # Process from the same buffer
    data = {}
    buffer.seek(0)
    with ZipFile(buffer) as zf:
        for file in zf.filelist:
            if re.search(r'.+(\.(csv|CSV))$', file.filename):
                dfs = read_zip_csv(
                    zf,
                    file_name=file.filename,
                    tables=tables,
                    columns=columns,
                    schemas=schemas,
                    conditions=conditions,
                    header_to_lowercase=header_to_lowercase,
                )
                data |= dfs
    return data
