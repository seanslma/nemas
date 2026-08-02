import re
import requests
import polars as pl
from urllib.parse import urlparse
from typing import Literal


__all__ = [
    'get_html',
    'get_nem_url',
    'get_url_base',
]


def get_url_base(url: str) -> str:
    """
    Return the base URL (up to the last slash) of a given URL.
    """
    parsed = urlparse(url)
    base_url = f'{parsed.scheme}://{parsed.netloc}/'
    return base_url


def get_html(
    url,
    *,
    session=None,
    ret_type: Literal['text', 'content'] = 'text',
) -> str | bytes:
    if session:
        resp = session.get(url)
    else:
        resp = requests.get(url)
    resp.raise_for_status()
    if ret_type == 'text':
        return resp.text
    else:
        return resp.content


def get_nem_url(
    url: str,
    *,
    session=None,
    latest_n: int = None,
    last_file: str = None,
    url_only: bool = True,
    full_url: bool = True,
) -> pl.DataFrame:
    """
    Return a DataFrame of NEM files from a given URL.

    The DataFrame will contain the following columns:
    - date: The date of the file (if url_only is False)
    - size_bytes: The size of the file in bytes (if url_only is False)
    - url: The href of the file
    - filename: The filename of the file (if url_only is False)

    """
    if url_only:
        href_id = 0
        cols = ['url']
        pattern = re.compile(r'<A HREF="([^"]+)">')
    else:
        href_id = 2
        cols = ['date', 'size_bytes', 'url', 'filename']
        pattern = re.compile(
            r'(\w+, \w+ \d{1,2}, \d{4} \d{1,2}:\d{2} [AP]M)\s+'
            r'(\d+)\s+'
            r'<A HREF="([^"]+)">([^<]+)</A>'
        )

    html = get_html(url, session=session, ret_type='text')
    if last_file:
        idx = html.rfind(last_file)
        if idx != -1:
            html = html[idx:]  # only parse everything after last known file

    matches = pattern.findall(html)

    # drop the last seen entry itself if it's still in the slice
    if last_file:
        matches = [m for m in matches if last_file not in m[href_id]]

    # get latest n only, such as the latest one
    if latest_n:
        matches = matches[-latest_n:]

    df = pl.DataFrame(
        matches,
        schema=cols,
        orient='row',
    )

    if full_url:
        url_base = get_url_base(url)
        df = df.with_columns(
            pl.when(pl.col('url').str.starts_with('http'))
            .then(pl.col('url'))
            .otherwise(pl.lit(url_base) + pl.col('url'))
            .alias('url')
        )

    return df
