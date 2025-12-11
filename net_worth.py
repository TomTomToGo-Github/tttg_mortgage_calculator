import pandas as pd

from mortgage import calculate_amortization, calculate_mortgage
from income import total_monthly_income
from expenses import total_monthly_expenses


def calculate_net_worth(
    initial_net_worth: float,
    monthly_income1: float,
    monthly_income2: float,
    stock_income: float,
    monthly_expenses: float,
    years: int,
    property_value: float,
    home_appreciation_rate: float,
    investment_return_rate: float,
    mortgage_rate: float,
    mortgage_years: int,
    down_payment: float = 0.0,
) -> pd.DataFrame:
    """Calculate net worth over time.

    Parameters
    ----------
    initial_net_worth : float
        Initial net worth (savings, investments, etc.).
    monthly_income1 : float
        Net monthly income of the first person.
    monthly_income2 : float
        Net monthly income of the second person.
    stock_income : float
        Monthly income from stocks or dividends.
    monthly_expenses : float
        Total monthly expenses.
    years : int
        Projection horizon in years.
    property_value : float
        Initial property value.
    home_appreciation_rate : float
        Annual home appreciation in percent.
    investment_return_rate : float
        Annual return on liquid investments in percent.
    mortgage_rate : float
        Annual mortgage interest rate in percent.
    mortgage_years : int
        Loan term in years.
    down_payment : float, optional
        Upfront payment reducing the principal, by default 0.0.

    Returns
    -------
    pandas.DataFrame
        Time series with net worth, liquid assets, home equity, home value
        and mortgage balance per month.
    """

    months = years * 12
    monthly_income = total_monthly_income(monthly_income1, monthly_income2, stock_income)
    monthly_expense_total = total_monthly_expenses(monthly_expenses)

    # Mortgage details
    principal = max(0.0, property_value - down_payment)
    monthly_payment = calculate_mortgage(property_value, mortgage_rate, mortgage_years, down_payment)
    amort = calculate_amortization(property_value, mortgage_rate, mortgage_years, down_payment)

    # Initialize state
    months_list = []
    net_worth_list = []
    liquid_assets = [initial_net_worth - down_payment]  # down payment comes from liquid assets
    home_values = [property_value]
    mortgage_balances = [principal]

    for month in range(1, months + 1):
        # Home value
        current_home_value = home_values[-1] * (1 + home_appreciation_rate / 12 / 100)

        # Mortgage balance from amortization schedule (if available)
        if not amort.empty and month <= len(amort):
            current_mortgage_balance = float(amort.iloc[month - 1]["Remaining Balance"])
        else:
            current_mortgage_balance = 0.0

        # Home equity
        current_equity = max(0.0, current_home_value - current_mortgage_balance)

        # Liquid assets (savings + investments)
        monthly_cash_flow = monthly_income - monthly_expense_total - monthly_payment
        current_liquid = liquid_assets[-1] * (1 + investment_return_rate / 12 / 100) + monthly_cash_flow

        months_list.append(month)
        net_worth_list.append(current_liquid + current_equity)
        liquid_assets.append(current_liquid)
        home_values.append(current_home_value)
        mortgage_balances.append(current_mortgage_balance)

    return pd.DataFrame(
        {
            "Month": months_list,
            "Net Worth": net_worth_list,
            "Liquid Assets": liquid_assets[1:],  # skip initial
            "Home Equity": [
                net_worth_list[i] - liquid_assets[i + 1] for i in range(len(net_worth_list))
            ],
            "Home Value": home_values[1:],
            "Mortgage Balance": mortgage_balances[1:],
        }
    )
