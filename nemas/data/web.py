import re
import requests
import polars as pl
from urllib.parse import urlparse
from typing import Literal

from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from nemas.utils.cache import ttl_cached


__all__ = [
    'get_html',
    'get_url',
    'get_url_base',
]


def get_url_base(url: str) -> str:
    """
    Return the base URL (up to the last slash) of a given URL.
    """
    parsed = urlparse(url)
    base_url = f'{parsed.scheme}://{parsed.netloc}/'
    return base_url


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
        return True
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return exc.response.status_code in {429, 500, 502, 503, 504}
    return False


@ttl_cached(namespace='html', exclude=['session', 'cache'])
@retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(4),
    wait=wait_exponential_jitter(initial=2, max=16),
    reraise=True,
)
def get_html(
    url,
    *,
    session: requests.Session = None,
    ret_type: Literal['text', 'content'] = 'text',
    cache: bool = False,
) -> str | bytes:
    resp = (session or requests).get(url, timeout=16)
    resp.raise_for_status()
    return resp.text if ret_type == 'text' else resp.content


def get_url(
    url: str,
    *,
    session: requests.Session = None,
    latest_n: int = None,
    last_file: str = None,
    url_only: bool = True,
    full_url: bool = True,
    cache: bool = False,
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

    html = get_html(url, session=session, ret_type='text', cache=cache)
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
