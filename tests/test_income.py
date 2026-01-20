"""Tests for income calculation module."""
import pytest

from income import convert_usd_to_eur, total_monthly_income


class TestConvertUsdToEur:
    """Tests for convert_usd_to_eur function."""

    def test_standard_conversion(self):
        """Test standard USD to EUR conversion.

        # GIVEN
        An amount of 1000 USD with exchange rate 0.92.

        # WHEN
        Converting to EUR.

        # THEN
        The result should be 920 EUR.
        """
        # GIVEN
        amount_usd = 1000.0
        exchange_rate = 0.92

        # WHEN
        result = convert_usd_to_eur(amount_usd, exchange_rate)

        # THEN
        assert result == 920.0

    def test_conversion_with_fee(self):
        """Test conversion with transaction fee.

        # GIVEN
        An amount of 1000 USD with rate 0.92 and 5 EUR fee.

        # WHEN
        Converting to EUR.

        # THEN
        The result should be 920 - 5 = 915 EUR.
        """
        # GIVEN
        amount_usd = 1000.0
        exchange_rate = 0.92
        fee = 5.0

        # WHEN
        result = convert_usd_to_eur(amount_usd, exchange_rate, fee)

        # THEN
        assert result == 915.0

    def test_zero_amount(self):
        """Test conversion of zero amount.

        # GIVEN
        An amount of 0 USD.

        # WHEN
        Converting to EUR.

        # THEN
        The result should be 0 EUR (fee not deducted from zero).
        """
        # GIVEN
        amount_usd = 0.0
        exchange_rate = 0.92
        fee = 5.0

        # WHEN
        result = convert_usd_to_eur(amount_usd, exchange_rate, fee)

        # THEN
        assert result == 0.0  # max(0, 0 - 5) = 0

    def test_fee_exceeds_converted_amount(self):
        """Test when fee exceeds converted amount.

        # GIVEN
        A small amount where fee exceeds conversion result.

        # WHEN
        Converting to EUR.

        # THEN
        The result should be 0 (not negative).
        """
        # GIVEN
        amount_usd = 5.0
        exchange_rate = 0.92
        fee = 10.0

        # WHEN
        result = convert_usd_to_eur(amount_usd, exchange_rate, fee)

        # THEN
        assert result == 0.0  # max(0, 4.6 - 10) = 0

    def test_zero_exchange_rate(self):
        """Test with zero exchange rate.

        # GIVEN
        An exchange rate of 0.

        # WHEN
        Converting to EUR.

        # THEN
        The result should be 0.
        """
        # GIVEN
        amount_usd = 1000.0
        exchange_rate = 0.0

        # WHEN
        result = convert_usd_to_eur(amount_usd, exchange_rate)

        # THEN
        assert result == 0.0

    def test_high_exchange_rate(self):
        """Test with exchange rate greater than 1.

        # GIVEN
        An exchange rate of 1.5 (hypothetical strong EUR).

        # WHEN
        Converting to EUR.

        # THEN
        The result should be 1500 EUR.
        """
        # GIVEN
        amount_usd = 1000.0
        exchange_rate = 1.5

        # WHEN
        result = convert_usd_to_eur(amount_usd, exchange_rate)

        # THEN
        assert result == 1500.0


class TestTotalMonthlyIncome:
    """Tests for total_monthly_income function."""

    def test_standard_income(self):
        """Test standard income calculation.

        # GIVEN
        Primary income 3000, secondary 2000, stock 500.

        # WHEN
        Calculating total monthly income.

        # THEN
        The result should be 5500.
        """
        # GIVEN
        primary = 3000.0
        secondary = 2000.0
        stock = 500.0

        # WHEN
        result = total_monthly_income(primary, secondary, stock)

        # THEN
        assert result == 5500.0

    def test_zero_incomes(self):
        """Test with all zero incomes.

        # GIVEN
        All income sources are 0.

        # WHEN
        Calculating total monthly income.

        # THEN
        The result should be 0.
        """
        # GIVEN / WHEN
        result = total_monthly_income(0.0, 0.0, 0.0)

        # THEN
        assert result == 0.0

    def test_single_income_source(self):
        """Test with only primary income.

        # GIVEN
        Only primary income of 5000.

        # WHEN
        Calculating total monthly income.

        # THEN
        The result should be 5000.
        """
        # GIVEN / WHEN
        result = total_monthly_income(5000.0, 0.0, 0.0)

        # THEN
        assert result == 5000.0

    def test_only_stock_income(self):
        """Test with only stock income.

        # GIVEN
        Only stock income of 1000.

        # WHEN
        Calculating total monthly income.

        # THEN
        The result should be 1000.
        """
        # GIVEN / WHEN
        result = total_monthly_income(0.0, 0.0, 1000.0)

        # THEN
        assert result == 1000.0
