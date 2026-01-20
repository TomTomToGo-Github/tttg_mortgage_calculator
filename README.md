# Mortgage and Net Worth Calculator

A Streamlit-based web application for projecting mortgage payments and net worth over time.

## Features

- **Mortgage Calculation**: Calculate monthly payments based on property value, interest rate, loan term, and down payment
- **Reverse Calculation**: Adjust monthly payment to find the corresponding property value
- **Net Worth Projection**: Track wealth composition over time including:
  - Bank reserves
  - Stock portfolio
  - Home equity
- **Income Management**: Support for multiple income sources including USD stock dividends with EUR conversion
- **Interactive Charts**: Visualize liquid assets, mortgage progress, property value, and net worth projections
- **Financial Buffer Warning**: Alerts when bank reserves drop below a specified threshold

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit app:

```bash
streamlit run mortgage_calculator.py
```

## Dependencies

- **streamlit** - Web application framework
- **pandas** - Data manipulation
- **numpy** - Numerical computations
- **plotly** - Interactive charts
- **pytest** - Testing framework

## Project Structure

```
├── mortgage_calculator.py  # Main Streamlit application
├── mortgage.py             # Mortgage calculation functions
├── net_worth.py            # Net worth projection logic
├── income.py               # Income conversion utilities
├── expenses.py             # Expense handling
├── formatting.py           # Currency and number formatting
├── requirements.txt        # Python dependencies
└── tests/                  # Unit tests
```

## Testing

Run tests with pytest:

```bash
pytest
```
