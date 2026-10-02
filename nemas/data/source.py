import polars as pl
import requests
from pathlib import Path

from .web import get_url


FILEPATH_TEMPLATE = {
    'mmsdm': (
        'https://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/{year}/'
        'MMSDM_{year}_{month:02d}/MMSDM_Historical_Data_SQLLoader/DATA/'
    ),
    'archive': '',
    'current': '',
}

FILENAME_TEMPLATE = {
    'mmsdm': (
        r'(?i)^(PUBLIC_DVD_{file_mask}[0-9]?_{year}{month:02d}010000\.zip'
        r'|PUBLIC_ARCHIVE#{file_mask}#FILE[0-9]{{2}}#{year}{month:02d}010000\.zip)$'
    ),
    'archive': '',
    'current': '',
}


def get_filepath(
    source_type: str,
    year: int,
    month: int,
) -> str:
    return FILEPATH_TEMPLATE[source_type].format(year=year, month=month)


def get_filename_pattern(
    source_type: str,
    file_mask: str,
    year: int,
    month: int,
) -> str:
    return FILENAME_TEMPLATE[source_type].format(
        file_mask=file_mask, year=year, month=month
    )


def get_table_files(
    df_url: pl.DataFrame,
    source_type: str,
    file_mask: str,
    year: int,
    month: int,
) -> pl.DataFrame:
    filename_pattern = get_filename_pattern(source_type, file_mask, year, month)
    df = df_url.filter(pl.col('filename').str.contains(filename_pattern))
    return df


def get_sources(
    table_config: dict,
    year: int,
    month: int,
    data_dir: str = None,
    session: requests.Session = None,
) -> list[str]:
    file_mask = table_config['file_mask']
    filepath = get_filepath(
        source_type='mmsdm',
        year=year,
        month=month,
    )
    df_url = get_url(filepath, session=session, url_only=False, cache=True)
    df_files = get_table_files(
        df_url=df_url,
        source_type='mmsdm',
        file_mask=file_mask,
        year=year,
        month=month,
    )
    sources = []
    for file in df_files['filename']:
        in_zip_dir = False
        if data_dir is not None:
            source = Path(data_dir, f'_zips/{year}/{month:02}/{file}')
            # exists in zip dir
            if source.exists():
                in_zip_dir = True
        if in_zip_dir:
            # get from zip dir
            sources.append(source)
        else:
            # get from nemweb
            url = get_url(file)
            sources.append(url.item(0, 'url'))
    return sources
