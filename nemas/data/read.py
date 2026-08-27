import polars as pl
from pathlib import Path
from datetime import datetime
from ..config.config import TABLE_CONFIG


def get_data(
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
