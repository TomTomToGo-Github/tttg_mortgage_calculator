"""Tests for net worth calculation module."""
import pytest
import pandas as pd

from net_worth import calculate_net_worth


class TestCalculateNetWorth:
    """Tests for calculate_net_worth function."""

    def test_standard_projection(self):
        """Test standard net worth projection.

        # GIVEN
        Typical financial inputs over 10 years.

        # WHEN
        Calculating net worth projection.

        # THEN
        The result should be a DataFrame with expected columns.
        """
        # GIVEN
        params = {
            "initial_bank_balance": 50000.0,
            "monthly_income1": 3000.0,
            "monthly_income2": 2000.0,
            "stock_income": 500.0,
            "monthly_expenses": 3000.0,
            "years": 10,
            "property_value": 400000.0,
            "home_appreciation_rate": 2.0,
            "investment_return_rate": 1.5,
            "stock_growth_rate": 7.0,
            "mortgage_rate": 4.5,
            "mortgage_years": 30,
            "down_payment": 80000.0,
            "initial_stock_wealth": 20000.0,
            "bank_reserve_ratio": 0.3,
        }

        # WHEN
        result = calculate_net_worth(**params)

        # THEN
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 10 * 12 + 1  # 10 years * 12 months + month 0
        expected_cols = [
            "Month", "Net Worth", "Bank Reserve", "Stock Wealth",
            "Liquid Assets", "Home Value", "Home Equity",
            "Mortgage Balance", "Principal Paid",
        ]
        for col in expected_cols:
            assert col in result.columns

    def test_zero_income(self):
        """Test projection with zero income.

        # GIVEN
        Zero income with expenses and mortgage.

        # WHEN
        Calculating net worth projection.

        # THEN
        Bank reserve should decrease over time.
        """
        # GIVEN
        params = {
            "initial_bank_balance": 100000.0,
            "monthly_income1": 0.0,
            "monthly_income2": 0.0,
            "stock_income": 0.0,
            "monthly_expenses": 1000.0,
            "years": 5,
            "property_value": 200000.0,
            "home_appreciation_rate": 2.0,
            "investment_return_rate": 1.0,
            "stock_growth_rate": 5.0,
            "mortgage_rate": 4.0,
            "mortgage_years": 30,
            "down_payment": 50000.0,
            "initial_stock_wealth": 0.0,
            "bank_reserve_ratio": 1.0,
        }

        # WHEN
        result = calculate_net_worth(**params)

        # THEN
        # Bank reserve should decrease (negative cash flow)
        first_bank = result.iloc[0]["Bank Reserve"]
        last_bank = result.iloc[-1]["Bank Reserve"]
        assert last_bank < first_bank

    def test_zero_expenses(self):
        """Test projection with zero expenses.

        # GIVEN
        Income with zero expenses.

        # WHEN
        Calculating net worth projection.

        # THEN
        Liquid assets should grow faster.
        """
        # GIVEN
        params = {
            "initial_bank_balance": 50000.0,
            "monthly_income1": 5000.0,
            "monthly_income2": 0.0,
            "stock_income": 0.0,
            "monthly_expenses": 0.0,
            "years": 5,
            "property_value": 200000.0,
            "home_appreciation_rate": 2.0,
            "investment_return_rate": 1.0,
            "stock_growth_rate": 5.0,
            "mortgage_rate": 4.0,
            "mortgage_years": 30,
            "down_payment": 50000.0,
            "initial_stock_wealth": 0.0,
            "bank_reserve_ratio": 1.0,
        }

        # WHEN
        result = calculate_net_worth(**params)

        # THEN
        first_liquid = result.iloc[0]["Liquid Assets"]
        last_liquid = result.iloc[-1]["Liquid Assets"]
        assert last_liquid > first_liquid

    def test_no_property(self):
        """Test projection with zero property value.

        # GIVEN
        No property (property value equals down payment).

        # WHEN
        Calculating net worth projection.

        # THEN
        Home equity should be zero throughout.
        """
        # GIVEN
        params = {
            "initial_bank_balance": 50000.0,
            "monthly_income1": 3000.0,
            "monthly_income2": 2000.0,
            "stock_income": 0.0,
            "monthly_expenses": 2000.0,
            "years": 5,
            "property_value": 100000.0,
            "home_appreciation_rate": 2.0,
            "investment_return_rate": 1.0,
            "stock_growth_rate": 5.0,
            "mortgage_rate": 4.0,
            "mortgage_years": 30,
            "down_payment": 100000.0,  # Equals property value
            "initial_stock_wealth": 0.0,
            "bank_reserve_ratio": 1.0,
        }

        # WHEN
        result = calculate_net_worth(**params)

        # THEN
        # Mortgage balance should be 0 throughout
        assert all(result["Mortgage Balance"] == 0.0)

    def test_reinvest_dividends_true(self):
        """Test with dividends reinvested directly to stocks.

        # GIVEN
        Stock income with reinvest_dividends=True.

        # WHEN
        Calculating net worth projection.

        # THEN
        Stock wealth should grow by stock income each month.
        """
        # GIVEN
        params = {
            "initial_bank_balance": 50000.0,
            "monthly_income1": 3000.0,
            "monthly_income2": 0.0,
            "stock_income": 500.0,
            "monthly_expenses": 2000.0,
            "years": 1,
            "property_value": 200000.0,
            "home_appreciation_rate": 0.0,
            "investment_return_rate": 0.0,
            "stock_growth_rate": 0.0,  # No growth, just reinvestment
            "mortgage_rate": 0.0,
            "mortgage_years": 30,
            "down_payment": 50000.0,
            "initial_stock_wealth": 10000.0,
            "bank_reserve_ratio": 1.0,  # All savings to bank
            "reinvest_dividends": True,
        }

        # WHEN
        result = calculate_net_worth(**params)

        # THEN
        # Stock wealth should increase by ~500/month (reinvested dividends)
        first_stock = result.iloc[0]["Stock Wealth"]
        last_stock = result.iloc[-1]["Stock Wealth"]
        # After 12 months: 10000 + 12*500 = 16000
        assert last_stock > first_stock
        assert abs(last_stock - 16000.0) < 1.0

    def test_reinvest_dividends_false(self):
        """Test with dividends treated as regular income.

        # GIVEN
        Stock income with reinvest_dividends=False.

        # WHEN
        Calculating net worth projection.

        # THEN
        Stock income should go through savings ratio split.
        """
        # GIVEN
        params = {
            "initial_bank_balance": 50000.0,
            "monthly_income1": 3000.0,
            "monthly_income2": 0.0,
            "stock_income": 500.0,
            "monthly_expenses": 2000.0,
            "years": 1,
            "property_value": 200000.0,
            "home_appreciation_rate": 0.0,
            "investment_return_rate": 0.0,
            "stock_growth_rate": 0.0,
            "mortgage_rate": 0.0,
            "mortgage_years": 30,
            "down_payment": 50000.0,
            "initial_stock_wealth": 10000.0,
            "bank_reserve_ratio": 1.0,  # All savings to bank
            "reinvest_dividends": False,
        }

        # WHEN
        result = calculate_net_worth(**params)

        # THEN
        # Stock wealth should stay at 10000 (no reinvestment, ratio=1.0)
        last_stock = result.iloc[-1]["Stock Wealth"]
        assert abs(last_stock - 10000.0) < 1.0

    def test_all_savings_to_stocks(self):
        """Test with bank_reserve_ratio=0 (all to stocks).

        # GIVEN
        Bank reserve ratio of 0.

        # WHEN
        Calculating net worth projection.

        # THEN
        All positive cash flow should go to stocks.
        """
        # GIVEN
        params = {
            "initial_bank_balance": 50000.0,
            "monthly_income1": 5000.0,
            "monthly_income2": 0.0,
            "stock_income": 0.0,
            "monthly_expenses": 2000.0,
            "years": 1,
            "property_value": 200000.0,
            "home_appreciation_rate": 0.0,
            "investment_return_rate": 0.0,
            "stock_growth_rate": 0.0,
            "mortgage_rate": 0.0,
            "mortgage_years": 30,
            "down_payment": 50000.0,
            "initial_stock_wealth": 0.0,
            "bank_reserve_ratio": 0.0,  # All to stocks
        }

        # WHEN
        result = calculate_net_worth(**params)

        # THEN
        # Bank should stay at initial (0 after down payment)
        # Stock should grow by monthly cash flow
        first_bank = result.iloc[0]["Bank Reserve"]
        last_bank = result.iloc[-1]["Bank Reserve"]
        assert abs(first_bank - last_bank) < 1.0  # Bank unchanged

    def test_negative_cash_flow_draws_from_bank(self):
        """Test that negative cash flow draws from bank first.

        # GIVEN
        Expenses exceeding income.

        # WHEN
        Calculating net worth projection.

        # THEN
        Bank reserve should decrease first.
        """
        # GIVEN
        params = {
            "initial_bank_balance": 100000.0,
            "monthly_income1": 1000.0,
            "monthly_income2": 0.0,
            "stock_income": 0.0,
            "monthly_expenses": 2000.0,  # 1000 deficit/month
            "years": 2,
            "property_value": 200000.0,
            "home_appreciation_rate": 0.0,
            "investment_return_rate": 0.0,
            "stock_growth_rate": 0.0,
            "mortgage_rate": 0.0,
            "mortgage_years": 30,
            "down_payment": 50000.0,
            "initial_stock_wealth": 20000.0,
            "bank_reserve_ratio": 0.5,
        }

        # WHEN
        result = calculate_net_worth(**params)

        # THEN
        # Bank should decrease, stocks should stay stable initially
        first_bank = result.iloc[0]["Bank Reserve"]
        last_bank = result.iloc[-1]["Bank Reserve"]
        assert last_bank < first_bank

    def test_home_appreciation(self):
        """Test that home value appreciates correctly.

        # GIVEN
        A property with 12% annual appreciation (compounded monthly).

        # WHEN
        Calculating net worth projection for 1 year.

        # THEN
        Home value should increase by approximately 12.68% (monthly compounding).
        """
        # GIVEN
        initial_property = 200000.0
        params = {
            "initial_bank_balance": 100000.0,
            "monthly_income1": 5000.0,
            "monthly_income2": 0.0,
            "stock_income": 0.0,
            "monthly_expenses": 2000.0,
            "years": 1,
            "property_value": initial_property,
            "home_appreciation_rate": 12.0,  # 12% annual, compounded monthly
            "investment_return_rate": 0.0,
            "stock_growth_rate": 0.0,
            "mortgage_rate": 4.0,
            "mortgage_years": 30,
            "down_payment": 50000.0,
            "initial_stock_wealth": 0.0,
            "bank_reserve_ratio": 1.0,
        }

        # WHEN
        result = calculate_net_worth(**params)

        # THEN
        final_home_value = result.iloc[-1]["Home Value"]
        # Monthly compounding: (1 + 0.12/12)^12 = 1.1268...
        expected_value = initial_property * ((1 + 0.12 / 12) ** 12)
        assert abs(final_home_value - expected_value) < 1.0

    def test_principal_paid_increases(self):
        """Test that principal paid increases over time.

        # GIVEN
        A standard mortgage.

        # WHEN
        Calculating net worth projection.

        # THEN
        Principal paid should increase each month.
        """
        # GIVEN
        params = {
            "initial_bank_balance": 100000.0,
            "monthly_income1": 5000.0,
            "monthly_income2": 0.0,
            "stock_income": 0.0,
            "monthly_expenses": 2000.0,
            "years": 5,
            "property_value": 300000.0,
            "home_appreciation_rate": 2.0,
            "investment_return_rate": 1.0,
            "stock_growth_rate": 5.0,
            "mortgage_rate": 4.0,
            "mortgage_years": 30,
            "down_payment": 60000.0,
            "initial_stock_wealth": 0.0,
            "bank_reserve_ratio": 1.0,
        }

        # WHEN
        result = calculate_net_worth(**params)

        # THEN
        first_principal = result.iloc[0]["Principal Paid"]
        last_principal = result.iloc[-1]["Principal Paid"]
        assert last_principal > first_principal

    def test_one_year_projection(self):
        """Test minimum projection period of 1 year.

        # GIVEN
        A 1 year projection.

        # WHEN
        Calculating net worth projection.

        # THEN
        Result should have 13 rows (month 0 + 12 months).
        """
        # GIVEN
        params = {
            "initial_bank_balance": 50000.0,
            "monthly_income1": 3000.0,
            "monthly_income2": 0.0,
            "stock_income": 0.0,
            "monthly_expenses": 2000.0,
            "years": 1,
            "property_value": 200000.0,
            "home_appreciation_rate": 2.0,
            "investment_return_rate": 1.0,
            "stock_growth_rate": 5.0,
            "mortgage_rate": 4.0,
            "mortgage_years": 30,
            "down_payment": 50000.0,
            "initial_stock_wealth": 0.0,
            "bank_reserve_ratio": 1.0,
        }

        # WHEN
        result = calculate_net_worth(**params)

        # THEN
        assert len(result) == 13  # month 0 + 12 months
