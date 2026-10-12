import polars as pl
from pathlib import Path
from datetime import datetime
from ..config.config import TABLE_CONFIG


def read_data(
    tables: str | list[str],
    start_date: datetime,
    end_date: datetime = None,
    columns: list[str] | dict[str, list[str]] = None,
    schemas: dict | dict[str, dict] = None,
    filters: pl.Expr | dict[str, pl.Expr] = None,
) -> dict[str, pl.DataFrame]:
    """
    Return a dict of table_name -> pl.DataFrame for all tables in TABLE_CONFIG.
    This is a convenience function for interactive exploration, but is not
    intended for production use (which should instead read the partitioned
    Parquet store).
    """
    data = {}
    for table_name in TABLE_CONFIG:
        table_dir = Path('parquet') / table_name.lower()
        if not table_dir.exists():
            continue
        data[table_name] = pl.read_parquet(table_dir)
    return data


"""
Efficient reads from a year/month-partitioned Parquet dataset.

DuckDB: SQL over the partitioned files directly,
    with automatic partition pruning, column projection, and row-group
    pruning. Handles larger-than-RAM results by spilling to disk, and lets
    you filter/aggregate/join without pulling everything into Python first.

Requirements:
    pip install duckdb pyarrow polars
"""

from __future__ import annotations
from datetime import datetime, timedelta
import duckdb


def part_ts_filters(
    start_date: str,
    end_date: str,
    ts_col: str,
) -> str:
    """
    Generate a SQL WHERE clause for filtering year/month partitions
    and the timestamp column.
    """
    # convert to datetime
    start_ts = datetime.strptime(start_date, "%Y-%m-%d")
    end_ts = datetime.strptime(end_date, "%Y-%m-%d")

    # get year/month start/end
    start_year = start_ts.year
    start_month = start_ts.month
    end_year = (end_ts - timedelta(milliseconds=1)).year
    end_month = (end_ts - timedelta(milliseconds=1)).month

    # create filter for year/month partitions
    if start_year == end_year:
        part_filter = f"""
            year = {start_year}
            AND month >= {start_month}
            AND month <= {end_month}
        """
    elif start_year == end_year - 1:
        part_filter = f"""
            (year = {start_year} AND month >= {start_month})
            OR (year = {end_year} AND month <= {end_month})
        """
    else:
        part_filter = f"""
            (year = {start_year} AND month >= {start_month})
            OR (year > {start_year} AND year < {end_year})
            OR (year = {end_year} AND month <= {end_month})
        """

    # timestamp filter for the ts_col
    ts_filter = f"{ts_col} >= '{start_date}' AND {ts_col} < '{end_date}'"

    return f'({part_filter}) AND ({ts_filter})'


def read_duckdb(
    base_path: str,
    start_date: str,
    end_date: str,
    ts_col: str,
    cols: list[str] | None = None,
    where_filter: str | None = None,
) -> duckdb.DuckDBPyRelation:
    """
    Query a hive-partitioned Parquet dataset with DuckDB.

    Returns a DuckDBPyRelation (lazy). Call .df() / .arrow() / .pl() to
    materialize, or keep chaining SQL-like operations, or .fetchmany(n) /
    iterate for streaming instead of loading the full result at once.
    """
    qry_cols = ', '.join(f"'{c}'" for c in cols) if cols else '*'
    where = part_ts_filters(
        start_date=start_date,
        end_date=end_date,
        ts_col=ts_col,
    )
    if where_filter:
        where += f'\n   AND ({where_filter})'

    query = f"""
        SELECT {qry_cols}
        FROM read_parquet('{base_path}/**/*.parquet', hive_partitioning = true)
        WHERE {where}
    """
    return duckdb.sql(query)


# --------------------------------------------------------------------------
# Example usage
# --------------------------------------------------------------------------

if __name__ == '__main__':
    path = 'demo_data'

    # lay read
    result = read_duckdb(
        path,
        start_date='2025-01-01',
        end_date='2026-01-01',
        ts_col='ts',
        cols=['id', 'value'],
    )

    # materialize as a Polars DataFrame
    print(result.pl().head())

    # Streaming a large result
    for batch in result.fetch_arrow_reader(batch_size=100_000):
        pass  # process batch (a pyarrow.RecordBatch) incrementally
