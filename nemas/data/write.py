"""
Partitioned Parquet writer with append/upsert support and file-size control.

Layout produced on disk (Hive-style partitioning):
    base_path/year=2026/month=8/<group>-<table>-<uuid>.parquet

Requirements:
    pip install pyarrow polars

Works with local filesystem paths, S3 (s3://...), GCS (gs://...), or Azure,
as long as you pass the matching pyarrow filesystem via `filesystem=`.
"""

from __future__ import annotations

import uuid
from typing import NamedTuple

import polars as pl
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


class PartCol(NamedTuple):
    name: str
    value: int | str


class PartInfo(NamedTuple):
    cols: tuple[PartCol, ...]

    def value_for(self, name: str) -> int | str:
        for col in self.cols:
            if col.name == name:
                return col.value
        raise KeyError(name)


def _partition_filter(
    part_info: PartInfo,
) -> pc.Expression:
    filter = None
    for col in part_info.cols:
        cur_filter = pc.field(col.name) == col.value
        filter = cur_filter if filter is None else filter & cur_filter
    return filter


def _partition_mask(
    table: pa.Table, part_info: PartInfo,
) -> pc.Expression:
    mask = None
    for col in part_info.cols:
        cur_mask = pc.equal(table[col.name], col.value)
        mask = cur_mask if mask is None else pc.and_(mask, cur_mask)
    return mask


def _partition_from_row(
    row: tuple[object, ...],
    partition_schema: tuple[tuple[str, pa.DataType], ...],
) -> PartInfo:
    return PartInfo(
        cols=tuple(
            PartCol(name=name, value=value)
            for (name, _), value in zip(partition_schema, row)
        )
    )


def _partition_expr(name: str, date_col: str) -> pl.Expr | None:
    if name == 'year':
        return pl.col(date_col).dt.year().cast(pl.Int32).alias('year')
    if name == 'month':
        return pl.col(date_col).dt.month().cast(pl.Int32).alias('month')
    if name == 'day':
        return pl.col(date_col).dt.day().cast(pl.Int32).alias('day')
    return None


def _read_partition(
    dataset: ds.Dataset,
    part_info: PartInfo,
) -> pa.Table | None:
    filter = _partition_filter(part_info)
    table = dataset.to_table(filter=filter)
    return table if table.num_rows > 0 else None


def add_partition_cols(
    df: pl.DataFrame,
    date_col: str,
    partition_schema: list[tuple[str, pa.DataType]] | None = None,
) -> pl.DataFrame:
    """
    Derive supported date-based partition columns and validate the remaining
    partition columns already exist on the DataFrame.
    """
    if partition_schema is None:
        return df

    exprs = []
    missing_cols = []
    for name, _ in partition_schema:
        if name in df.columns:
            continue
        expr = _partition_expr(name, date_col)
        if expr is not None:
            exprs.append(expr)
        else:
            missing_cols.append(name)
    if missing_cols:
        raise KeyError(
            'Unsupported partition columns: ' + ', '.join(missing_cols)
        )

    if not exprs:
        return df
    else:
        return df.with_columns(exprs)


def estimate_max_rows_per_file(
    table: pa.Table,
    target_filesize_mb: int,
    compression_factor: float = 3.0,
) -> int:
    """
    PyArrow's write_dataset controls file size via row counts, not bytes.
    Estimate an appropriate row count from the in-memory table's average
    row size, then convert the target MB into a row limit.

    `compression_factor` is a guess at how much smaller Parquet's on-disk
    (compressed + encoded) size is vs. the in-memory Arrow size. The default
    (3x) is a reasonable starting point for mixed numeric/text data, but it's
    very data-dependent. Highly repetitive/text-heavy data compresses much
    more (10x+), and high-entropy numeric/random data much less (1.5-2x). Run
    `calibrate_compression_factor` once against a real sample of your data
    and pass the result in here for accurate file sizing.
    """
    if table.num_rows == 0:
        return 1  # nothing to write, value doesn't matter

    avg_row_bytes = table.nbytes / table.num_rows
    target_file_bytes = target_filesize_mb * 1024 * 1024 * compression_factor
    max_rows = max(1, int(target_file_bytes / avg_row_bytes))

    return max_rows


def calibrate_compression_factor(sample_table: pa.Table) -> float:
    """
    Write a representative sample of your real data to a throwaway Parquet
    file and measure actual in-memory-size / on-disk-size. Use the result as
    `compression_factor` in estimate_max_rows_per_file (and pass it through
    append_partitioned/upsert_partitioned/compact_partitions) for accurate
    file-size targeting on your specific data.
    """
    import io

    buf = io.BytesIO()
    pq.write_table(sample_table, buf)
    on_disk_bytes = buf.tell()
    if on_disk_bytes == 0:
        return 3.0  # fall back to default
    return sample_table.nbytes / on_disk_bytes


# --------------------------------------------------------------------------
# Append (no updates, just add new rows to partitions)
# --------------------------------------------------------------------------


def append_partitioned(
    df: pl.DataFrame,
    base_path: str,
    date_col: str,
    partition_schema: list[tuple[str, pa.DataType]] | None = None,
    target_file_size_mb: int = 128,
    target_rows_per_group: int = 100_000,
    compression_factor: float = 3.0,
    sort_by: list[str] | None = None,
    compression: str = 'zstd',
    filesystem = None,
) -> None:
    """
    Append rows to a partitioned Parquet dataset.

    Safe to call repeatedly. Each call writes new, uniquely-named files,
    so nothing existing gets overwritten. A single call with a large
    DataFrame is automatically split into multiple target_file_size_mb
    files, not written as one large file.

    `sort_by`: sort rows within each written file by these columns before
    writing. Polars/DuckDB use Parquet row-group min/max statistics to skip
    row groups that can't satisfy a filter. Sorting by the columns you
    filter on most (e.g. a timestamp) makes those stats tight and allows
    most row groups to be skipped on selective queries.
    """
    df = add_partition_cols(df, date_col, partition_schema)
    table = df.to_arrow()

    if sort_by:
        table = table.sort_by([(col, 'ascending') for col in sort_by])

    max_rows_per_file = estimate_max_rows_per_file(
        table, target_file_size_mb, compression_factor
    )
    max_rows_per_group = min(
        max_rows_per_file, target_rows_per_group
    )
    file_options = ds.ParquetFileFormat().make_write_options(
        compression=compression, write_statistics=True
    )

    ds.write_dataset(
        data=table,
        base_dir=base_path,
        format='parquet',
        partitioning=ds.partitioning(partition_schema, flavor='hive'),
        # Unique filenames per write -> existing files are left untouched
        basename_template=f'part-{uuid.uuid4().hex}-{{i}}.parquet',
        max_rows_per_file=max_rows_per_file,
        max_rows_per_group=max_rows_per_group,
        existing_data_behavior='overwrite_or_ignore',
        file_options=file_options,
        filesystem=filesystem,
    )


# --------------------------------------------------------------------------
# Upsert (update existing rows by key, insert new ones)
# --------------------------------------------------------------------------


def upsert_partitioned(
    df: pl.DataFrame,
    base_path: str,
    key_cols: list[str],
    date_col: str = 'event_date',
    partition_schema: tuple[tuple[str, pa.DataType], ...] | None = None,
    target_file_size_mb: int = 128,
    target_rows_per_group: int = 100_000,
    compression_factor: float = 3.0,
    sort_by: list[str] | None = None,
    compression: str = 'zstd',
    filesystem=None,
) -> None:
    """
    Upsert rows into a partitioned Parquet dataset.

    Strategy: since Parquet files are immutable, we
      1. figure out which partitions the incoming data touches
      2. read only those partitions back into memory
      3. concat old + new, drop duplicates on `key_cols` keeping the newest
      4. rewrite just those partitions from scratch

    This is correct for a single writer. If you have concurrent writers,
    use Delta Lake (deltalake package, .merge()) or Apache Iceberg instead:
    they handle concurrent upserts safely via transaction logs; this
    read-merge-rewrite approach does not.
    """
    df = add_partition_cols(df, date_col, partition_schema)
    incoming = df.to_arrow()

    part_cols = (
        [] if partition_schema is None
        else [name for name, _ in partition_schema]
    )
    touched_partitions = [
        _partition_from_row(row, partition_schema)
        for row in df.select(part_cols).unique().iter_rows()
    ]

    # Open the dataset once so _read_partition doesn't re-scan metadata N times
    try:
        existing_dataset: ds.Dataset | None = ds.dataset(
            base_path, format='parquet', filesystem=filesystem
        )
        if len(existing_dataset.files) == 0:
            existing_dataset = None
    except FileNotFoundError:
        existing_dataset = None

    file_options = ds.ParquetFileFormat().make_write_options(
        compression=compression, write_statistics=True
    )

    for partition in touched_partitions:
        existing = (
            _read_partition(existing_dataset, partition)
            if existing_dataset is not None
            else None
        )
        new_slice = incoming.filter(
            _partition_mask(incoming, partition)
        )
        merged = _merge_upsert(existing, new_slice, key_cols, sort_by)

        max_rows_per_file = estimate_max_rows_per_file(
            merged, target_file_size_mb, compression_factor
        )
        max_rows_per_group = min(
            max_rows_per_file, target_rows_per_group
        )

        # Rewrite this partition from scratch: delete_matching clears out
        # existing files for this partition dir before writing the merged set.
        ds.write_dataset(
            data=merged,
            base_dir=base_path,
            format='parquet',
            partitioning=ds.partitioning(partition_schema, flavor='hive'),
            basename_template=f'part-{uuid.uuid4().hex}-{{i}}.parquet',
            max_rows_per_file=max_rows_per_file,
            max_rows_per_group=max_rows_per_group,
            existing_data_behavior='delete_matching',
            file_options=file_options,
            filesystem=filesystem,
        )


def _merge_upsert(
    existing: pa.Table | None,
    new_slice: pa.Table,
    key_cols: list[str],
    sort_by: list[str] | None = None,
) -> pa.Table:
    if existing is None or existing.num_rows == 0:
        result = new_slice
    else:
        existing_df = pl.from_arrow(existing)
        new_df = pl.from_arrow(new_slice)

        # Concat with new rows last, then drop duplicate keys keeping the LAST
        # occurrence (i.e. the new/incoming version wins).
        # maintain_order=True is required so that 'last' reliably means the
        # incoming row rather than an arbitrary survivor.
        combined = pl.concat([existing_df, new_df])
        combined = combined.unique(
            subset=key_cols, keep='last', maintain_order=True
        )
        result = combined.to_arrow()

    if sort_by:
        result = result.sort_by([(col, 'ascending') for col in sort_by])
    return result


# --------------------------------------------------------------------------
# Compaction (periodic maintenance -- run separately from append/upsert)
# --------------------------------------------------------------------------
#
# Sorting during compaction (via `sort_by`) matters for read performance:
# Parquet stores min/max stats per row group, and query engines use those to
# skip row groups that can't match a filter. If your data is sorted by the
# column(s) you filter on most (e.g. an id or a secondary timestamp), each
# row group covers a narrow value range, so selective queries skip most of
# the file instead of scanning it all.


def compact_partitions(
    base_path: str,
    partition_schema: tuple[tuple[str, pa.DataType], ...] | None = None,
    target_file_size_mb: int = 128,
    target_rows_per_group: int = 100_000,
    sort_by: list[str] | None = None,
    compression: str = 'zstd',
    filesystem=None,
) -> None:
    """
    Scan every partition and rewrite it as a small number of
    target_file_size_mb files, optionally sorted for better row-group pruning.

    Safe-ish rewrite ordering: new compacted files are written first (with
    unique names), then old files are deleted -- so a reader mid-scan sees
    a superset of correct data rather than a gap. It is not a full atomic
    swap, so avoid running this against a partition with an active
    concurrent writer; schedule it for a quiet period.

    Add another partition key such as region/duid_bucket?
    """
    try:
        dataset = ds.dataset(base_path, format='parquet', filesystem=filesystem)
    except FileNotFoundError:
        return  # nothing written yet

    fs = filesystem or dataset.filesystem
    files_by_partition: dict[PartInfo, list[str]] = {}

    for file_path in dataset.files:
        part_info = _parse_partition_cols(file_path, partition_schema)
        files_by_partition.setdefault(part_info, []).append(file_path)

    for part_info, file_paths in files_by_partition.items():
        table = dataset.to_table(filter=_partition_filter(part_info))
        if sort_by:
            table = table.sort_by([(col, 'ascending') for col in sort_by])

        max_rows_per_file = estimate_max_rows_per_file(table, target_file_size_mb)
        max_rows_per_group = min(max_rows_per_file, target_rows_per_group)
        # full parameter list is here:
        # https://arrow.apache.org/docs/python/generated/pyarrow.parquet.write_table.html
        file_options = ds.ParquetFileFormat().make_write_options(
            compression=compression,
            write_statistics=True,
        )

        ds.write_dataset(
            data=table,
            base_dir=base_path,
            format='parquet',
            partitioning=ds.partitioning(partition_schema, flavor='hive'),
            basename_template=f'compact-{uuid.uuid4().hex}-{{i}}.parquet',
            max_rows_per_file=max_rows_per_file,
            max_rows_per_group=max_rows_per_group,
            existing_data_behavior='overwrite_or_ignore',  # keep old files for now
            file_options=file_options,
            filesystem=filesystem,
        )

        # Now that the compacted replacement files exist,
        # remove the old fragmented ones.
        for old_path in file_paths:
            fs.delete_file(old_path)


def _parse_partition_cols(
    file_path: str,
    partition_schema: tuple[tuple[str, pa.DataType], ...] | None = None,
) -> PartInfo:
    """
    Extract hive-partitioned values from a file path using the provided schema.
    """
    schema = dict(partition_schema)
    part_cols: list[PartCol] = []
    for part in file_path.split('/'):
        items = part.split('=')
        if len(items) != 2 or items[0] not in schema:
            continue
        col = items[0]
        typ = schema[col]
        raw_val = items[1]
        if pa.types.is_integer(typ):
            val = int(raw_val)
        elif pa.types.is_string(typ):
            val = raw_val
        else:
            raise TypeError(f'Unsupported partition type for parsing: {typ}')
        part_cols.append(
            PartCol(
                name=col,
                value=val,
            )
        )
    return PartInfo(cols=tuple(part_cols))


# --------------------------------------------------------------------------
# Example usage
# --------------------------------------------------------------------------

if __name__ == '__main__':
    base_path = 'c:/test/data/nem'  # or "s3://my-bucket/events", etc.

    # First load: plain append
    df1 = pl.DataFrame(
        {
            'id': [1, 2, 3],
            'event_date': ['2026-08-01', '2026-08-15', '2026-07-20'],
            'value': [10, 20, 30],
        }
    )
    append_partitioned(
        df=df1,
        base_path=base_path,
        date_col='event_date',
        target_file_size_mb=128,
    )

    # Later: update id=2's value and insert a new row -> upsert
    df2 = pl.DataFrame(
        {
            'id': [2, 4],
            'event_date': ['2026-08-15', '2026-08-16'],
            'value': [999, 40],
        }
    )
    upsert_partitioned(
        df=df2,
        base_path=base_path,
        key_cols=['id'],
        date_col='event_date',
    )

    # Periodically (e.g. a nightly cron job / Airflow task), compact each
    # partition's accumulated small files into a handful of right-sized
    # ones. Sort by whatever column your downstream queries filter on most
    # so row-group stats let readers skip irrelevant data.
    compact_partitions(
        base_path=base_path,
        target_file_size_mb=128,
        min_files_to_trigger=4,
        sort_by=['id'],
    )
