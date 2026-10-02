from pathlib import Path
from datetime import datetime
import requests
import polars as pl

from ..config import get_table_config
from ..utils import merge_df_dicts, get_year_month_list
from .source import get_sources
from .parse import parse_zip


def get_data_by_month(
    table_config: str,
    year: int,
    month: int,
    data_dir: str = None,
    save_zip: bool = False,
    session: requests.Session = None,
) -> dict[str, pl.DataFrame]:
    """
    Get data for the specified table and year/month.
    """
    data = {}
    for source in get_sources(table_config, year, month, data_dir, session):
        zip_path = None
        if save_zip and data_dir is not None:
            zip_path = Path(data_dir) / f'_zips/{year}/{month:02}'
        dat = parse_zip(
            source, requests_session=session, zip_path=zip_path, save_zip=save_zip
        )
        data = merge_df_dicts(data, dat)
    return data


def get_data(
    table: str,
    start_date: str,
    end_date: str,
    data_dir: str = None,
    save_zip: bool = False,
) -> dict[str, pl.DataFrame]:
    """
    Get data for the specified table and date range.
    """
    data = {}
    table_config = get_table_config(table)
    if table_config is None:
        raise ValueError(f'Table `{table}` not found in TABLE_CONFIG.')
    with requests.Session() as session:
        session.headers.update({'User-Agent': 'nemas/1.0'})
        for year, month in get_year_month_list(start_date, end_date):
            dat = get_data_by_month(
                table_config, year, month, data_dir, save_zip, session
            )
            data = merge_df_dicts(data, dat)
    return data


def cache_data(
    tables: str | list[str] = None,
    start_date: str = None,
    end_date: str = None,
    data_dir: str = None,
    save_zip: bool = True,
):
    """
    Cache all tables in TABLE_CONFIG to the partitioned Parquet store.
    """
    # get data and write to partitioned parquets
    with requests.Session() as session:
        session.headers.update({'User-Agent': 'nemas/1.0'})
        for table in tables:
            table_config = get_table_config(table)
            for year, month in get_year_month_list(start_date, end_date):
                data = get_data_by_month(
                    table_config, year, month, data_dir, save_zip, session
                )
                for table, df in data.items():
                    write_parquet(df, table, data_dir)
    # compact partitions
    compact_partitions()


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


def write_parquet(
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

    config = get_table_config[table_name]
    partition_col = config['partition_column']
    granularity = config['partition_granularity']

    # Static/reference table: single file, overwrite in place
    if partition_col is None:
        out_dir = base_dir / table_name.lower()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f'{table_name.lower()}.parquet'  # FIXME: use real name
        df.write_parquet(out_path)
        return

    # Partitioned table: group rows by their partition key, write per-partition
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


def compact_partitions():
    pass


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
