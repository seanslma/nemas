# import nemas as nm

# nm.price.region()

# nm.price.duid()

# nm.price.station()

# nm.price.technology()

# nm.price.statistics()

# nm.price.duration_curve()

# nm.price.negative_events()

# nm.price.volatility()

import polars as pl


# market/price.py — descriptive, single-source
def get_price(
    start,
    end,
    raw_data_cache,
    region=None,
    **kwargs,
) -> pl.DataFrame:
    """Raw DISPATCHPRICE, optionally filtered by region."""
    pass
    # return engine.cache.compile('DISPATCHPRICE', start, end, raw_data_cache, ...)


def price_stats(
    start,
    end,
    raw_data_cache,
    group_by='region',
    resample=None,
) -> pl.DataFrame:
    """Avg/max/min/duration-curve stats on price alone. No other table involved."""
    df = get_price(start, end, raw_data_cache)
    pass
    # return _aggregations.summarize(df, group_by, resample)
