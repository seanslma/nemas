# import nemas as nm

# nm.revenue.generator()

# nm.revenue.battery()

# nm.revenue.wind()

# nm.revenue.solar()

# nm.revenue.storage()

# nm.revenue.region()

import polars as pl

from nemas import market, engine


# analytics/revenue.py — derived, multi-source
def revenue(start, end, raw_data_cache, group_by='duid', resample=None) -> pl.DataFrame:
    """Combines market.generation + market.price + engine.registry to compute $."""
    pass
    # gen_df = market.generation.get_generation(start, end, raw_data_cache)
    # price_df = market.price.get_price(start, end, raw_data_cache)
    # registry_df = engine.registry.get_duid_registry(raw_data_cache)
    # return _compute_revenue(gen_df, price_df, registry_df, group_by, resample)
