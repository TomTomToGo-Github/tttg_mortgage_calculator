"""Tests for expenses calculation module."""
import pytest

from src.expenses import total_monthly_expenses


class TestTotalMonthlyExpenses:
    """Tests for total_monthly_expenses function."""

    def test_standard_expenses(self):
        """Test standard expense calculation.

        # GIVEN
        Base expenses of 3000.

        # WHEN
        Calculating total monthly expenses.

        # THEN
        The result should be 3000.
        """
        # GIVEN
        base = 3000.0

        # WHEN
        result = total_monthly_expenses(base)

        # THEN
        assert result == 3000.0

    def test_zero_expenses(self):
        """Test zero expenses.

        # GIVEN
        Base expenses of 0.

        # WHEN
        Calculating total monthly expenses.

        # THEN
        The result should be 0.
        """
        # GIVEN / WHEN
        result = total_monthly_expenses(0.0)

        # THEN
        assert result == 0.0

    def test_large_expenses(self):
        """Test large expense value.

        # GIVEN
        Base expenses of 100,000.

        # WHEN
        Calculating total monthly expenses.

        # THEN
        The result should be 100,000.
        """
        # GIVEN
        base = 100000.0

        # WHEN
        result = total_monthly_expenses(base)

        # THEN
        assert result == 100000.0

    def test_decimal_expenses(self):
        """Test expenses with decimal places.

        # GIVEN
        Base expenses of 1234.56.

        # WHEN
        Calculating total monthly expenses.

        # THEN
        The result should be 1234.56.
        """
        # GIVEN
        base = 1234.56

        # WHEN
        result = total_monthly_expenses(base)

        # THEN
        assert result == 1234.56
