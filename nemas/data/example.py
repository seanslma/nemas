def get_latest_pd7day_rrp():
    from datetime import date
    import time
    import polars as pl
    from nemas.data.web import get_nem_url
    from nemas.data.nem import read_nem_zip

    t0 = time.time()
    url = 'https://nemweb.com.au/Reports/CURRENT/PD7Day'
    latest = get_nem_url(url, latest_n=1, url_only=True)
    print(latest.item(0, 'url'))
    data = read_nem_zip(
        latest.item(0, 'url'),
        tables=['pricesolution'],
        columns=['interval_datetime', 'REGIONID', 'RRP'],
        schemas={
            'pricesolution': {
                'interval_datetime': pl.Datetime,
                'REGIONID': pl.Utf8,
                'RRP': pl.Float64,
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
    print(f'time: {time.time() - t0:.3f}')
    print(df)


if __name__ == '__main__':
    get_latest_pd7day_rrp()
