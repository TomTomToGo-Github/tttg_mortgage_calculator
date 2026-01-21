def convert_usd_to_eur(
    amount_usd: float,
    exchange_rate: float,
    transaction_fee: float = 0.0,
) -> float:
    """Convert USD amount to EUR with optional transaction fee.

    Parameters
    ----------
    amount_usd : float
        Amount in US dollars.
    exchange_rate : float
        Current USD to EUR exchange rate (e.g., 0.92 means 1 USD = 0.92 EUR).
    transaction_fee : float, optional
        Fixed monthly transaction fee in EUR, by default 0.0.

    Returns
    -------
    float
        Net amount in EUR after conversion and fee deduction.
    """
    converted = float(amount_usd) * float(exchange_rate)
    return max(0.0, converted - float(transaction_fee))


def total_monthly_income(
    primary_income: float,
    secondary_income: float,
    stock_income_eur: float,
) -> float:
    """Calculate total monthly income from all sources.

    Parameters
    ----------
    primary_income : float
        Net monthly income of the first person (EUR).
    secondary_income : float
        Net monthly income of the second person (EUR).
    stock_income_eur : float
        Monthly income from stocks or dividends (EUR, after conversion).

    Returns
    -------
    float
        Total monthly income in EUR.
    """
    return float(primary_income) + float(secondary_income) + float(stock_income_eur)
