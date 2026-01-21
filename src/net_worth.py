import pandas as pd

from src.mortgage import calculate_amortization, calculate_mortgage
from src.income import total_monthly_income
from src.expenses import total_monthly_expenses


def calculate_net_worth(
    initial_bank_balance: float,
    monthly_income1: float,
    monthly_income2: float,
    stock_income: float,
    monthly_expenses: float,
    years: int,
    property_value: float,
    home_appreciation_rate: float,
    investment_return_rate: float,
    stock_growth_rate: float,
    mortgage_rate: float,
    mortgage_years: int,
    down_payment: float = 0.0,
    initial_stock_wealth: float = 0.0,
    bank_reserve_ratio: float = 0.3,
    reinvest_dividends: bool = True,
) -> pd.DataFrame:
    """Calculate net worth over time with detailed asset breakdown.

    Parameters
    ----------
    initial_bank_balance : float
        Starting money in the bank account.
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
        Annual return on bank savings in percent.
    stock_growth_rate : float
        Annual growth rate of stock portfolio in percent.
    mortgage_rate : float
        Annual mortgage interest rate in percent.
    mortgage_years : int
        Loan term in years.
    down_payment : float, optional
        Upfront payment reducing the principal, by default 0.0.
    initial_stock_wealth : float, optional
        Initial value of stock portfolio, by default 0.0.
    bank_reserve_ratio : float, optional
        Fraction of monthly savings to keep in bank vs invest, by default 0.3.
    reinvest_dividends : bool, optional
        If True, stock income goes directly to stocks. If False, treated as
        regular income affected by bank_reserve_ratio. By default True.

    Returns
    -------
    pandas.DataFrame
        Time series with detailed asset breakdown per month.
    """
    months = years * 12

    # If reinvesting dividends, exclude stock_income from regular income
    if reinvest_dividends:
        monthly_income = total_monthly_income(monthly_income1, monthly_income2, 0.0)
        monthly_dividend_reinvest = stock_income
    else:
        monthly_income = total_monthly_income(
            monthly_income1, monthly_income2, stock_income
        )
        monthly_dividend_reinvest = 0.0

    monthly_expense_total = total_monthly_expenses(monthly_expenses)

    # Mortgage details
    principal = max(0.0, property_value - down_payment)
    monthly_payment = calculate_mortgage(
        property_value, mortgage_rate, mortgage_years, down_payment
    )
    amort = calculate_amortization(
        property_value, mortgage_rate, mortgage_years, down_payment
    )

    # Calculate total principal paid over time
    total_principal_paid = 0.0

    # Initialize state - bank balance is directly the starting bank money
    bank_reserve = [initial_bank_balance]
    stock_wealth = [initial_stock_wealth]
    home_values = [property_value]
    mortgage_balances = [principal]
    principal_paid_list = [down_payment]  # Down payment counts as principal paid

    # Track data - start with month 0 (initial state)
    initial_equity = max(0.0, property_value - principal)
    initial_net_worth = initial_bank_balance + initial_stock_wealth + initial_equity
    months_list = [0]
    net_worth_list = [initial_net_worth]

    for month in range(1, months + 1):
        # Home value appreciation
        current_home_value = home_values[-1] * (1 + home_appreciation_rate / 12 / 100)

        # Mortgage balance and principal paid this month
        if not amort.empty and month <= len(amort):
            current_mortgage_balance = float(
                amort.iloc[month - 1]["Remaining Balance"]
            )
            principal_this_month = float(
                amort.iloc[month - 1]["Principal Payment"]
            )
            total_principal_paid += principal_this_month
        else:
            current_mortgage_balance = 0.0
            principal_this_month = 0.0

        # Stock wealth grows by stock growth rate + reinvested dividends
        current_stock = (
            stock_wealth[-1] * (1 + stock_growth_rate / 12 / 100)
            + monthly_dividend_reinvest
        )

        # Bank reserve grows by investment return rate
        current_bank = bank_reserve[-1] * (1 + investment_return_rate / 12 / 100)

        # Monthly cash flow after expenses and mortgage
        monthly_cash_flow = monthly_income - monthly_expense_total - monthly_payment

        # Split savings between bank reserve and stock investments
        if monthly_cash_flow > 0:
            current_bank += monthly_cash_flow * bank_reserve_ratio
            current_stock += monthly_cash_flow * (1 - bank_reserve_ratio)
        else:
            # Draw from bank first, then stocks if needed
            if current_bank + monthly_cash_flow >= 0:
                current_bank += monthly_cash_flow
            else:
                shortfall = abs(monthly_cash_flow) - current_bank
                current_bank = 0.0
                current_stock = max(0.0, current_stock - shortfall)

        # Home equity
        current_equity = max(0.0, current_home_value - current_mortgage_balance)

        # Total net worth
        current_net_worth = current_bank + current_stock + current_equity

        # Append to lists
        months_list.append(month)
        net_worth_list.append(current_net_worth)
        bank_reserve.append(current_bank)
        stock_wealth.append(current_stock)
        home_values.append(current_home_value)
        mortgage_balances.append(current_mortgage_balance)
        principal_paid_list.append(down_payment + total_principal_paid)

    return pd.DataFrame(
        {
            "Month": months_list,
            "Net Worth": net_worth_list,
            "Bank Reserve": bank_reserve,
            "Stock Wealth": stock_wealth,
            "Liquid Assets": [
                bank_reserve[i] + stock_wealth[i]
                for i in range(len(months_list))
            ],
            "Home Value": home_values,
            "Home Equity": [
                max(0.0, home_values[i] - mortgage_balances[i])
                for i in range(len(months_list))
            ],
            "Mortgage Balance": mortgage_balances,
            "Principal Paid": principal_paid_list,
        }
    )
