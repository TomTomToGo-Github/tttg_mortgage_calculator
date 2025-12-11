

def total_monthly_income(
    primary_income: float,
    secondary_income: float,
    stock_income: float,
) -> float:
    """Calculate total monthly income from all sources.

    Parameters
    ----------
    primary_income : float
        Net monthly income of the first person.
    secondary_income : float
        Net monthly income of the second person.
    stock_income : float
        Monthly income from stocks or dividends.

    Returns
    -------
    float
        Total monthly income.
    """

    return float(primary_income) + float(secondary_income) + float(stock_income)
