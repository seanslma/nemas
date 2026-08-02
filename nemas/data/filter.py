import operator
import polars as pl


__all__ = [
    'build_filter_expr',
    'apply_filters',
]


OPS = {
    '==': operator.eq,
    '!=': operator.ne,
    '>': operator.gt,
    '>=': operator.ge,
    '<': operator.lt,
    '<=': operator.le,
}
LOGICAL = {'or', 'and'}


def build_leaf(item: tuple, df: pl.DataFrame) -> pl.Expr:
    col, op, val = item
    if col not in df.columns:
        raise ValueError(
            f'Column `{col}` not found in dataframe. Available columns: {df.columns})'
        )

    col_expr = pl.col(col)

    # cast datetime column to date if comparing against a date-only value
    if (
        df.schema[col] == pl.Datetime
        and hasattr(val, 'year')
        and not hasattr(val, 'hour')
    ):
        col_expr = col_expr.dt.date()

    op = op.lower() if isinstance(op, str) else op
    if op in OPS:
        return OPS[op](col_expr, val)
    elif op == 'in':
        return col_expr.is_in(val)
    elif op == 'not in':
        return ~col_expr.is_in(val)
    else:
        raise ValueError(f'Unsupported operator: {op}')


def parse_condition(item, df: pl.DataFrame) -> pl.Expr:
    if isinstance(item, pl.Expr):
        return item

    if isinstance(item, tuple) and len(item) == 3:
        left, mid, right = item
        if isinstance(mid, str) and mid.lower() in LOGICAL:
            left_expr = parse_condition(left, df)
            right_expr = parse_condition(right, df)
            return (
                left_expr | right_expr
                if mid.lower() == 'or'
                else left_expr & right_expr
            )
        else:
            return build_leaf(item, df)

    raise ValueError(f'Unrecognized condition format: {item!r}')


def build_filter_expr(
    df: pl.DataFrame,
    conditions: pl.Expr | list[tuple],
) -> pl.Expr:
    if isinstance(conditions, pl.Expr):
        return conditions

    expr = None
    for item in conditions:
        cond = parse_condition(item, df)
        expr = cond if expr is None else expr & cond
    return expr


def apply_filters(
    df: pl.DataFrame,
    conditions: pl.Expr | list[tuple] = None,
) -> pl.DataFrame:
    if conditions is None:
        return df
    else:
        return df.filter(build_filter_expr(df, conditions))
