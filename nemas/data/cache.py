from pathlib import Path
from datetime import datetime
import polars as pl

from ..config.config import TABLE_CONFIG
from .parse import read_zip


def partition_path(
    base_dir: Path,
    table_name: str,
    granularity: str,
    ts: datetime = None,
) -> Path:
    """
    Build the Hive-style partition directory for a given row timestamp.
    """
    path = base_dir / table_name.lower()
    if granularity is None:
        return path

    parts = [
        f'year={ts.year}',
        f'month={ts.month:02d}',
    ]
    if granularity == 'day':
        parts.append(f'day={ts.day:02d}')

    return path / Path(*parts)


def cast_to_schema(df: pl.DataFrame, schema: dict) -> pl.DataFrame:
    """
    Cast/select columns to the canonical schema, adding any missing
    columns as nulls so downstream partitions have a consistent layout.
    """
    exprs = []
    for col, dtype in schema.items():
        if col in df.columns:
            exprs.append(pl.col(col).cast(dtype, strict=False))
        else:
            exprs.append(pl.lit(None, dtype=dtype).alias(col))
    return df.select(exprs)


def save_parquet(
    df: pl.DataFrame,
    table_name: str,
    base_dir: Path,
) -> None:
    """
    Cast a table's DataFrame (as produced by read_nem_zip) to its canonical
    schema and write partitioned Parquet. Each partition directory is
    overwritten wholesale (delete-and-rewrite) so re-running a day/month is
    idempotent and safely handles NEMWEB revisions/republished files.
    """
    if df.is_empty():
        return

    config = TABLE_CONFIG[table_name]
    schema = config['schema']
    partition_col = config['partition_column']
    granularity = config['partition_granularity']

    df = cast_to_schema(df, schema)

    if partition_col is None:
        # Static/reference table: single file, overwrite in place.
        out_dir = base_dir / table_name.lower()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f'{table_name.lower()}.parquet'
        df.write_parquet(out_path)
        return

    # Partitioned table: group rows by their partition key, write per-partition.
    group_cols = [
        pl.col(partition_col).dt.year().alias('year'),
        pl.col(partition_col).dt.month().alias('month'),
    ]
    if granularity == 'day':
        group_cols.append(
            pl.col(partition_col).dt.day().alias('day'),
        )
    for key, group in df.group_by(group_cols):
        sample_ts = group.item(0, partition_col)
        out_dir = partition_path(base_dir, table_name, granularity, sample_ts)
        out_dir.mkdir(parents=True, exist_ok=True)

        # Delete-and-rewrite this partition to absorb NEMWEB revisions cleanly.
        # TODO: Consider writing multiple parquet files
        tmp = out_dir / 'part-0.tmp.parquet'
        group.write_parquet(tmp, compression='zstd')
        tmp.replace(out_dir / 'part-0.parquet')


def write_nem_zip(
    source: Path,
    base_dir: Path,
) -> None:
    """
    Read every table out of a NEMWEB zip (via read_nem_zip) and ingest each
    one that's in TABLE_CONFIG into its partitioned Parquet store. Tables
    present in the zip but not in TABLE_CONFIG are skipped.

    Raw zip archiving (raw_archive_dir/<table>/year/month/day/) is assumed
    handled upstream by the downloader, per the earlier discussion.
    """
    tables = read_zip(source)  # dict[str, pl.DataFrame]

    for table_name, df in tables.items():
        if table_name not in TABLE_CONFIG:
            continue
        save_parquet(df, table_name, base_dir)


def cache_data(tables: str | list[str] = None):
    """
    Cache all tables in TABLE_CONFIG to the partitioned Parquet store. This
    is a convenience function for interactive exploration, but is not intended
    for production use (which should instead read the partitioned Parquet store).
    """
    raw_dir = Path('raw')
    parquet_dir = Path('parquet')
    for table_name in TABLE_CONFIG:
        table_dir = raw_dir / table_name.lower()
        if not table_dir.exists():
            continue
        for zip_file in table_dir.glob('*.zip'):
            write_nem_zip(zip_file, parquet_dir)


if __name__ == '__main__':
    # Example usage:
    #
    # write_nem_zip(
    #     zip_path=Path("raw/DISPATCHPRICE/2026/07/20/PUBLIC_DISPATCHPRICE_202607201205.zip"),
    #     table_name="DISPATCHPRICE",
    #     raw_archive_dir=Path("raw"),
    #     scratch_dir=Path("scratch"),
    #     ase_dir=Path("parquet"),
    # )
    pass
