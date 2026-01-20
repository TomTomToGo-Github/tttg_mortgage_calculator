"""Tests for mortgage calculation module."""
import pytest
import pandas as pd

from mortgage import (
    calculate_mortgage,
    calculate_amortization,
    calculate_property_from_payment,
)


class TestCalculateMortgage:
    """Tests for calculate_mortgage function."""

    def test_standard_mortgage(self):
        """Test standard mortgage calculation with typical values.

        # GIVEN
        A property value of 400,000 with 80,000 down payment,
        4.5% interest rate over 30 years.

        # WHEN
        Calculating the monthly mortgage payment.

        # THEN
        The monthly payment should be approximately 1,621.39.
        """
        # GIVEN
        principal = 400000.0
        down_payment = 80000.0
        interest_rate = 4.5
        years = 30

        # WHEN
        result = calculate_mortgage(principal, interest_rate, years, down_payment)

        # THEN
        assert round(result, 2) == 1621.39

    def test_zero_interest_rate(self):
        """Test mortgage with zero interest rate.

        # GIVEN
        A loan of 120,000 with 0% interest over 10 years.

        # WHEN
        Calculating the monthly payment.

        # THEN
        The payment should be principal divided by total months.
        """
        # GIVEN
        principal = 120000.0
        interest_rate = 0.0
        years = 10

        # WHEN
        result = calculate_mortgage(principal, interest_rate, years)

        # THEN
        expected = 120000.0 / (10 * 12)
        assert result == expected

    def test_down_payment_equals_principal(self):
        """Test when down payment equals or exceeds principal.

        # GIVEN
        A property value of 100,000 with 100,000 down payment.

        # WHEN
        Calculating the monthly payment.

        # THEN
        The payment should be 0 (no loan needed).
        """
        # GIVEN
        principal = 100000.0
        down_payment = 100000.0
        interest_rate = 5.0
        years = 30

        # WHEN
        result = calculate_mortgage(principal, interest_rate, years, down_payment)

        # THEN
        assert result == 0.0

    def test_down_payment_exceeds_principal(self):
        """Test when down payment exceeds principal.

        # GIVEN
        A property value of 100,000 with 150,000 down payment.

        # WHEN
        Calculating the monthly payment.

        # THEN
        The payment should be 0.
        """
        # GIVEN
        principal = 100000.0
        down_payment = 150000.0
        interest_rate = 5.0
        years = 30

        # WHEN
        result = calculate_mortgage(principal, interest_rate, years, down_payment)

        # THEN
        assert result == 0.0

    def test_zero_years(self):
        """Test mortgage with zero years term.

        # GIVEN
        A loan with 0 years term.

        # WHEN
        Calculating the monthly payment.

        # THEN
        The payment should be 0.
        """
        # GIVEN
        principal = 100000.0
        interest_rate = 5.0
        years = 0

        # WHEN
        result = calculate_mortgage(principal, interest_rate, years)

        # THEN
        assert result == 0.0

    def test_very_high_interest_rate(self):
        """Test mortgage with very high interest rate.

        # GIVEN
        A loan with 50% annual interest rate.

        # WHEN
        Calculating the monthly payment.

        # THEN
        The payment should be calculated correctly (very high).
        """
        # GIVEN
        principal = 100000.0
        interest_rate = 50.0
        years = 30

        # WHEN
        result = calculate_mortgage(principal, interest_rate, years)

        # THEN
        assert result > 4000  # Very high monthly payment expected

    def test_very_short_term(self):
        """Test mortgage with 1 year term.

        # GIVEN
        A loan of 12,000 at 12% for 1 year.

        # WHEN
        Calculating the monthly payment.

        # THEN
        The payment should be approximately 1,066.19.
        """
        # GIVEN
        principal = 12000.0
        interest_rate = 12.0
        years = 1

        # WHEN
        result = calculate_mortgage(principal, interest_rate, years)

        # THEN
        assert round(result, 2) == 1066.19


class TestCalculateAmortization:
    """Tests for calculate_amortization function."""

    def test_standard_amortization(self):
        """Test standard amortization schedule generation.

        # GIVEN
        A property value of 200,000 with 40,000 down payment,
        5% interest over 30 years.

        # WHEN
        Generating the amortization schedule.

        # THEN
        The schedule should have correct structure and values.
        """
        # GIVEN
        principal = 200000.0
        down_payment = 40000.0
        interest_rate = 5.0
        years = 30

        # WHEN
        result = calculate_amortization(
            principal, interest_rate, years, down_payment
        )

        # THEN
        assert isinstance(result, pd.DataFrame)
        assert len(result) <= years * 12
        assert "Month" in result.columns
        assert "Principal Payment" in result.columns
        assert "Interest Payment" in result.columns
        assert "Remaining Balance" in result.columns
        # Final balance should be 0 or very close
        assert result.iloc[-1]["Remaining Balance"] < 1.0

    def test_amortization_down_payment_equals_principal(self):
        """Test amortization when down payment equals principal.

        # GIVEN
        A property value equal to down payment.

        # WHEN
        Generating the amortization schedule.

        # THEN
        An empty DataFrame should be returned.
        """
        # GIVEN
        principal = 100000.0
        down_payment = 100000.0
        interest_rate = 5.0
        years = 30

        # WHEN
        result = calculate_amortization(
            principal, interest_rate, years, down_payment
        )

        # THEN
        assert result.empty

    def test_amortization_first_payment_breakdown(self):
        """Test that first payment has correct interest/principal split.

        # GIVEN
        A loan of 100,000 at 12% (1% monthly) for 30 years.

        # WHEN
        Generating the amortization schedule.

        # THEN
        First month interest should be exactly 1% of principal.
        """
        # GIVEN
        principal = 100000.0
        interest_rate = 12.0  # 1% monthly
        years = 30

        # WHEN
        result = calculate_amortization(principal, interest_rate, years)

        # THEN
        first_interest = result.iloc[0]["Interest Payment"]
        assert round(first_interest, 2) == 1000.00  # 1% of 100,000

    def test_amortization_with_extra_payment(self):
        """Test amortization with extra monthly payment.

        # GIVEN
        A loan with extra monthly payment.

        # WHEN
        Generating the amortization schedule.

        # THEN
        The loan should be paid off faster.
        """
        # GIVEN
        principal = 100000.0
        interest_rate = 5.0
        years = 30

        # WHEN
        result_normal = calculate_amortization(principal, interest_rate, years)
        result_extra = calculate_amortization(
            principal, interest_rate, years, extra_payment=200.0
        )

        # THEN
        assert len(result_extra) < len(result_normal)


class TestCalculatePropertyFromPayment:
    """Tests for calculate_property_from_payment function."""

    def test_roundtrip_standard(self):
        """Test that property -> payment -> property gives same result.

        # GIVEN
        A standard mortgage scenario.

        # WHEN
        Calculating payment from property, then property from payment.

        # THEN
        The property values should match.
        """
        # GIVEN
        original_property = 400000.0
        down_payment = 80000.0
        interest_rate = 4.5
        years = 30

        # WHEN
        payment = calculate_mortgage(
            original_property, interest_rate, years, down_payment
        )
        recovered_property = calculate_property_from_payment(
            payment, interest_rate, years, down_payment
        )

        # THEN
        assert abs(recovered_property - original_property) < 0.01

    def test_zero_payment(self):
        """Test with zero payment.

        # GIVEN
        A payment of 0.

        # WHEN
        Calculating property value.

        # THEN
        Property should equal down payment.
        """
        # GIVEN
        payment = 0.0
        down_payment = 50000.0

        # WHEN
        result = calculate_property_from_payment(payment, 4.5, 30, down_payment)

        # THEN
        assert result == down_payment

    def test_zero_interest_rate(self):
        """Test with zero interest rate.

        # GIVEN
        A payment with 0% interest.

        # WHEN
        Calculating property value.

        # THEN
        Property should be payment * months + down payment.
        """
        # GIVEN
        payment = 1000.0
        years = 10
        down_payment = 20000.0

        # WHEN
        result = calculate_property_from_payment(payment, 0.0, years, down_payment)

        # THEN
        expected = payment * years * 12 + down_payment
        assert result == expected

    def test_high_payment(self):
        """Test with high payment value.

        # GIVEN
        A high monthly payment.

        # WHEN
        Calculating property value.

        # THEN
        Property value should be higher.
        """
        # GIVEN
        payment = 5000.0
        interest_rate = 4.0
        years = 30
        down_payment = 100000.0

        # WHEN
        result = calculate_property_from_payment(
            payment, interest_rate, years, down_payment
        )

        # THEN
        # Verify by calculating payment from result
        verify_payment = calculate_mortgage(
            result, interest_rate, years, down_payment
        )
        assert abs(verify_payment - payment) < 0.01
