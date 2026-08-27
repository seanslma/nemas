import polars as pl
from datetime import date
from nemas.data import get_url, read_zip


def get_latest_pd7day_rrp():
    url = 'https://nemweb.com.au/Reports/CURRENT/PD7Day'
    latest = get_url(url, latest_n=1, url_only=True)
    print(latest.item(0, 'url'))
    data = read_zip(
        latest.item(0, 'url'),
        tables=['pricesolution'],
        columns=['interval_datetime', 'regionid', 'RRP'],
        schemas={
            'pricesolution': {
                'interval_datetime': pl.Datetime,
                'REGIONID': pl.Utf8,
                'rrp': pl.Float64,
            }
        },
        conditions={
            'PRICESOLUTION': (
                (pl.col('regionid') == 'NSW1')
                & (pl.col('interval_datetime').dt.date() == date.today())
                & (pl.col('rrp') > 60)
            )
        },
    )
    df = data['pricesolution']

    return df


if __name__ == '__main__':
    import time

    t0 = time.time()
    df = get_latest_pd7day_rrp()
    print(f'time: {time.time() - t0:.3f} seconds')

    print(df)
