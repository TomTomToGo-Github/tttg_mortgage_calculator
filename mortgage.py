import pandas as pd


def calculate_mortgage(
    principal: float,
    annual_interest_rate: float,
    years: int,
    down_payment: float = 0.0,
) -> float:
    """Calculate the monthly mortgage payment.

    Parameters
    ----------
    principal : float
        Total purchase price of the property.
    annual_interest_rate : float
        Annual interest rate of the mortgage in percent.
    years : int
        Loan term in years.
    down_payment : float, optional
        Upfront payment reducing the principal, by default 0.0.

    Returns
    -------
    float
        Monthly mortgage payment.
    """
    if principal <= down_payment:
        return 0.0

    principal = principal - down_payment

    if years <= 0:
        return 0.0

    if annual_interest_rate == 0:
        return principal / (years * 12)

    monthly_rate = annual_interest_rate / 12 / 100
    num_payments = years * 12

    monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / (
        (1 + monthly_rate) ** num_payments - 1
    )
    return monthly_payment


def calculate_amortization(
    principal: float,
    annual_interest_rate: float,
    years: int,
    down_payment: float = 0.0,
    extra_payment: float = 0.0,
) -> pd.DataFrame:
    """Generate an amortization schedule.

    Parameters
    ----------
    principal : float
        Total purchase price of the property.
    annual_interest_rate : float
        Annual interest rate of the mortgage in percent.
    years : int
        Loan term in years.
    down_payment : float, optional
        Upfront payment reducing the principal, by default 0.0.
    extra_payment : float, optional
        Additional monthly payment towards principal, by default 0.0.

    Returns
    -------
    pandas.DataFrame
        Amortization schedule with payments and remaining balance per month.
    """
    if principal <= down_payment:
        return pd.DataFrame()

    principal = principal - down_payment

    monthly_rate = annual_interest_rate / 12 / 100
    num_payments = years * 12
    monthly_payment = calculate_mortgage(principal, annual_interest_rate, years)

    balance = principal
    schedule = []

    for month in range(1, num_payments + 1):
        interest_payment = balance * monthly_rate
        principal_payment = monthly_payment - interest_payment + extra_payment

        if balance < principal_payment:
            principal_payment = balance

        balance -= principal_payment

        schedule.append(
            {
                "Month": month,
                "Principal Payment": principal_payment,
                "Interest Payment": interest_payment,
                "Total Payment": principal_payment + interest_payment,
                "Remaining Balance": max(balance, 0),
            }
        )

        if balance <= 0:
            break

    return pd.DataFrame(schedule)
