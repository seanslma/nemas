import polars as pl
from nemas.data.nem import standardize_params


def test_standardize_params():
    t, c, s, d = standardize_params(
        tables='t1',
        columns='c1',
        schemas={
            't1': {
                'c1': pl.Datetime,
                'c2': pl.Utf8,
                'c3': pl.Float64,
            }
        },
        conditions=('c3', '>', 100),
    )
    assert t == ['T1']
    assert c == {'T1': ['C1']}
    assert s == {
        'T1': {
            'C1': pl.Datetime,
            'C2': pl.Utf8,
            'C3': pl.Float64,
        }
    }
    assert d == {'T1': [('C3', '>', 100)]}
