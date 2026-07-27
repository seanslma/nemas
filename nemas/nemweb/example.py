def get_latest_pd7day_rrp():
    from datetime import date
    from .parser import get_nem_url, read_nem_zip
    import time
    import polars as pl

    t0 = time.time()
    url = 'https://nemweb.com.au/Reports/CURRENT/PD7Day'
    latest = get_nem_url(url, latest_n=1, url_only=True)
    print(latest.row(0)[0])
    dat = read_nem_zip(
        latest.row(0)[0],
        tables=['PRICESOLUTION'],
        schemas={'PRICESOLUTION': {'INTERVAL_DATETIME': pl.Datetime, 'REGIONID': pl.Utf8, 'RRP': pl.Float64}},
    )
    df = dat['PRICESOLUTION'].filter(
        (pl.col('REGIONID') == 'NSW1') & (pl.col('INTERVAL_DATETIME').dt.date() == date.today()
    )
    print(f'time: {time.time() - t0:.3f}')
    print(df)
