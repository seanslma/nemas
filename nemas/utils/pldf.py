import polars as pl


def merge_df_dicts(
    dict1: dict[str, pl.DataFrame],
    dict2: dict[str, pl.DataFrame],
) -> dict[str, pl.DataFrame]:
    merged = {}
    all_keys = set(dict1.keys()) | set(dict2.keys())

    for key in all_keys:
        if key in dict1 and key in dict2:
            merged[key] = pl.concat([dict1[key], dict2[key]], how='vertical_relaxed')
        elif key in dict1:
            merged[key] = dict1[key]
        else:
            merged[key] = dict2[key]

    return merged
