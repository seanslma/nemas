from datetime import datetime


def get_year_month_list(
    start_date: str,
    end_date: str,
) -> list[tuple[int, int]]:
    """
    Return a list of (year, month) tuples from start_date up to end_date.

    Parameters:
    -----------
    start_date : str
        Start date in 'YYYY-MM-DD' format
    end_date : str
        End date in 'YYYY-MM-DD' format (exclusive).

    Returns:
    --------
    list of tuples
        A list of (year, month) tuples for each month in the range.
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    # total months since year 0, as integers
    start_idx = start.year * 12 + (start.month - 1)
    end_idx = end.year * 12 + (end.month - 1)
    if end.day > 1:
        end_idx += 1  # end_date's own month is partially included, so keep it

    return [(idx // 12, idx % 12 + 1) for idx in range(start_idx, end_idx)]
