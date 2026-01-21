"""Formatting utilities for currency and numeric display."""


def format_currency(value: float, symbol: str = "€", use_space: bool = True) -> str:
    """Format a number as currency with thousand separators.

    Parameters
    ----------
    value : float
        The numeric value to format.
    symbol : str, optional
        Currency symbol to prepend, by default "€".
    use_space : bool, optional
        If True, use space as thousand separator (1 000.00).
        If False, use comma (1,000.00). By default True.

    Returns
    -------
    str
        Formatted currency string.
    """
    if use_space:
        # Format with space as thousand separator
        formatted = f"{value:,.2f}".replace(",", " ")
    else:
        # Format with comma as thousand separator
        formatted = f"{value:,.2f}"

    return f"{symbol}{formatted}"


def format_number(value: float, use_space: bool = True) -> str:
    """Format a number with thousand separators.

    Parameters
    ----------
    value : float
        The numeric value to format.
    use_space : bool, optional
        If True, use space as thousand separator (1 000.00).
        If False, use comma (1,000.00). By default True.

    Returns
    -------
    str
        Formatted number string.
    """
    if use_space:
        return f"{value:,.2f}".replace(",", " ")
    else:
        return f"{value:,.2f}"


def parse_formatted_number(text: str, default: float = 0.0) -> float:
    """Parse a formatted number string back to float.

    Parameters
    ----------
    text : str
        Formatted number string (may contain spaces, commas, currency symbols).
    default : float, optional
        Value to return if parsing fails, by default 0.0.

    Returns
    -------
    float
        Parsed numeric value, or default if parsing fails.
    """
    try:
        # Remove currency symbols, spaces, and handle comma as thousand sep
        cleaned = text.replace("€", "").replace("$", "").replace(" ", "")
        cleaned = cleaned.replace(",", "")
        return float(cleaned)
    except (ValueError, AttributeError):
        return default
