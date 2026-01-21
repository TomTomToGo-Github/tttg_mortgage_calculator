"""Tests for formatting utility module."""
import pytest

from src.formatting import format_currency, format_number, parse_formatted_number


class TestFormatCurrency:
    """Tests for format_currency function."""

    def test_standard_format_with_space(self):
        """Test standard currency formatting with space separator.

        # GIVEN
        A value of 1234567.89.

        # WHEN
        Formatting with space separator.

        # THEN
        The result should be "€1 234 567.89".
        """
        # GIVEN
        value = 1234567.89

        # WHEN
        result = format_currency(value, use_space=True)

        # THEN
        assert result == "€1 234 567.89"

    def test_standard_format_with_comma(self):
        """Test standard currency formatting with comma separator.

        # GIVEN
        A value of 1234567.89.

        # WHEN
        Formatting with comma separator.

        # THEN
        The result should be "€1,234,567.89".
        """
        # GIVEN
        value = 1234567.89

        # WHEN
        result = format_currency(value, use_space=False)

        # THEN
        assert result == "€1,234,567.89"

    def test_zero_value(self):
        """Test formatting zero.

        # GIVEN
        A value of 0.

        # WHEN
        Formatting.

        # THEN
        The result should be "€0.00".
        """
        # GIVEN / WHEN
        result = format_currency(0.0)

        # THEN
        assert result == "€0.00"

    def test_negative_value(self):
        """Test formatting negative value.

        # GIVEN
        A negative value.

        # WHEN
        Formatting.

        # THEN
        The result should include the negative sign.
        """
        # GIVEN
        value = -1234.56

        # WHEN
        result = format_currency(value)

        # THEN
        assert result == "€-1 234.56"

    def test_custom_symbol(self):
        """Test formatting with custom currency symbol.

        # GIVEN
        A value with dollar symbol.

        # WHEN
        Formatting with "$" symbol.

        # THEN
        The result should use the dollar symbol.
        """
        # GIVEN
        value = 1000.00

        # WHEN
        result = format_currency(value, symbol="$")

        # THEN
        assert result == "$1 000.00"

    def test_small_value(self):
        """Test formatting small value.

        # GIVEN
        A value less than 1.

        # WHEN
        Formatting.

        # THEN
        The result should show two decimal places.
        """
        # GIVEN
        value = 0.99

        # WHEN
        result = format_currency(value)

        # THEN
        assert result == "€0.99"


class TestFormatNumber:
    """Tests for format_number function."""

    def test_standard_format(self):
        """Test standard number formatting.

        # GIVEN
        A value of 1234567.89.

        # WHEN
        Formatting with space separator.

        # THEN
        The result should be "1 234 567.89".
        """
        # GIVEN
        value = 1234567.89

        # WHEN
        result = format_number(value, use_space=True)

        # THEN
        assert result == "1 234 567.89"

    def test_format_with_comma(self):
        """Test number formatting with comma separator.

        # GIVEN
        A value of 1234567.89.

        # WHEN
        Formatting with comma separator.

        # THEN
        The result should be "1,234,567.89".
        """
        # GIVEN
        value = 1234567.89

        # WHEN
        result = format_number(value, use_space=False)

        # THEN
        assert result == "1,234,567.89"

    def test_zero(self):
        """Test formatting zero.

        # GIVEN
        A value of 0.

        # WHEN
        Formatting.

        # THEN
        The result should be "0.00".
        """
        # GIVEN / WHEN
        result = format_number(0.0)

        # THEN
        assert result == "0.00"


class TestParseFormattedNumber:
    """Tests for parse_formatted_number function."""

    def test_parse_space_separated(self):
        """Test parsing space-separated number.

        # GIVEN
        A string "1 234 567.89".

        # WHEN
        Parsing.

        # THEN
        The result should be 1234567.89.
        """
        # GIVEN
        text = "1 234 567.89"

        # WHEN
        result = parse_formatted_number(text)

        # THEN
        assert result == 1234567.89

    def test_parse_comma_separated(self):
        """Test parsing comma-separated number.

        # GIVEN
        A string "1,234,567.89".

        # WHEN
        Parsing.

        # THEN
        The result should be 1234567.89.
        """
        # GIVEN
        text = "1,234,567.89"

        # WHEN
        result = parse_formatted_number(text)

        # THEN
        assert result == 1234567.89

    def test_parse_with_euro_symbol(self):
        """Test parsing number with euro symbol.

        # GIVEN
        A string "€1 234.56".

        # WHEN
        Parsing.

        # THEN
        The result should be 1234.56.
        """
        # GIVEN
        text = "€1 234.56"

        # WHEN
        result = parse_formatted_number(text)

        # THEN
        assert result == 1234.56

    def test_parse_with_dollar_symbol(self):
        """Test parsing number with dollar symbol.

        # GIVEN
        A string "$1,234.56".

        # WHEN
        Parsing.

        # THEN
        The result should be 1234.56.
        """
        # GIVEN
        text = "$1,234.56"

        # WHEN
        result = parse_formatted_number(text)

        # THEN
        assert result == 1234.56

    def test_parse_plain_number(self):
        """Test parsing plain number string.

        # GIVEN
        A string "1234.56".

        # WHEN
        Parsing.

        # THEN
        The result should be 1234.56.
        """
        # GIVEN
        text = "1234.56"

        # WHEN
        result = parse_formatted_number(text)

        # THEN
        assert result == 1234.56

    def test_parse_invalid_returns_default(self):
        """Test parsing invalid string returns default.

        # GIVEN
        An invalid string "abc".

        # WHEN
        Parsing with default 100.0.

        # THEN
        The result should be 100.0.
        """
        # GIVEN
        text = "abc"
        default = 100.0

        # WHEN
        result = parse_formatted_number(text, default)

        # THEN
        assert result == default

    def test_parse_empty_string_returns_default(self):
        """Test parsing empty string returns default.

        # GIVEN
        An empty string.

        # WHEN
        Parsing with default 50.0.

        # THEN
        The result should be 50.0.
        """
        # GIVEN
        text = ""
        default = 50.0

        # WHEN
        result = parse_formatted_number(text, default)

        # THEN
        assert result == default

    def test_parse_none_returns_default(self):
        """Test parsing None returns default.

        # GIVEN
        None value.

        # WHEN
        Parsing with default 25.0.

        # THEN
        The result should be 25.0.
        """
        # GIVEN
        text = None
        default = 25.0

        # WHEN
        result = parse_formatted_number(text, default)

        # THEN
        assert result == default

    def test_parse_zero(self):
        """Test parsing zero.

        # GIVEN
        A string "0.00".

        # WHEN
        Parsing.

        # THEN
        The result should be 0.0.
        """
        # GIVEN
        text = "0.00"

        # WHEN
        result = parse_formatted_number(text)

        # THEN
        assert result == 0.0

    def test_parse_negative(self):
        """Test parsing negative number.

        # GIVEN
        A string "-1 234.56".

        # WHEN
        Parsing.

        # THEN
        The result should be -1234.56.
        """
        # GIVEN
        text = "-1 234.56"

        # WHEN
        result = parse_formatted_number(text)

        # THEN
        assert result == -1234.56
