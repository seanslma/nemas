import re
import polars as pl
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
from typing import IO

from .web import get_html


__all__ = [
    'read_nem_zip',
]

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
    schemas: dict[str, list[str] | dict[str, pl.DataType]] = None,
    filters: dict[str, bool | list[bool]] = None,
) -> dict:
    raw = zip_file.read(file_name)

    # get table start and end rows
    table_metadata = (
        pl.read_csv(
            raw,
            skip_rows=0,
            columns=[0,2],
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
        .filter(
            pl.lit(True)
            if tables is None
            else pl.col('tbl').is_in(tables)
        )
    )

    # read tables
    dfs = {}
    for table_name, skip_rows, row_end in table_metadata.iter_rows():
        n_rows = row_end - skip_rows
        schema = None if schemas is None else schemas.get(table_name, None)
        if schema is None:
            cols = None
            dtypes = None
        elif isinstance(schema, list):
            cols = schema
            dtypes = None
        elif isinstance(schema, dict):
            cols = list(schema.keys())
            dtypes = list(schema.values())
        else:
            raise TypeError(
                f'Invalid schema type for table {table_name}: {type(schema)}'
            )
        df = (
            pl.read_csv(
                raw,
                columns=cols,
                skip_lines=skip_rows,
                schema_overrides=dtypes,
                batch_size=8192 // 4,
                n_rows=n_rows,
                # low_memory=True,
                has_header=True,
                ignore_errors=True,
                truncate_ragged_lines=True,
                try_parse_dates=True,
            )
        )
        if filters is not None:
            table_filters = filters.get(table_name, None)
            if table_filters is not None:
                df = df.filter(table_filters)
        dfs[table_name] = df

    return dfs


def read_nem_zip(
    source: str | Path | IO[str] | IO[bytes] | bytes,
    *,
    requests_session = None,
    tables: list = None,
    schemas: dict = None,
    save_zip: bool = False,
    zip_path: str | Path | None = None,
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
    save_zip : bool
        If True, save the raw zip bytes to `zip_path` (or a default name).
    zip_path : str | Path, optional
        Where to save the zip if keep_zip=True. Defaults to the source filename
        (or "downloaded.zip" if it can't be inferred, e.g. from a URL/buffer).
    """
    raw_bytes, default_name = get_source_bytes(
        source, requests_session=requests_session
    )
    buffer = BytesIO(raw_bytes)

    # Save to disk if requested
    if save_zip:
        save_path = Path(zip_path) if zip_path else Path(default_name)
        save_path.write_bytes(buffer.getvalue())

    # Process from the same buffer
    data = {}
    buffer.seek(0)
    with ZipFile(buffer) as zf:
        for file in zf.filelist:
            if re.search(r'.+(\.(csv|CSV))$', file.filename):
                dfs = read_zip_csv(zf, file_name=file.filename, tables=tables, schemas=schemas)
                data |= dfs
    return data
