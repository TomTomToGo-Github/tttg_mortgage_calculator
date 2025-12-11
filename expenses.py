

def total_monthly_expenses(base_expenses: float) -> float:
    """Return total monthly expenses.

    Parameters
    ----------
    base_expenses : float
        Total monthly expenses across all categories.

    Returns
    -------
    float
        Total monthly expenses.

    Notes
    -----
    This is a simple wrapper for now but allows you to later split expenses
    into categories (rent, food, transport, etc.) without changing callers.
    """

    return float(base_expenses)
