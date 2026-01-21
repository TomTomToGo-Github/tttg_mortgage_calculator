# Financial Calculator

A Streamlit-based multipage web application for financial planning, mortgage calculations, and expense tracking.

## Features

### 🏠 Wealth Calculator
- **Mortgage Calculation**: Calculate monthly payments based on property value, interest rate, loan term, and down payment
- **Reverse Calculation**: Adjust monthly payment to find the corresponding property value
- **Net Worth Projection**: Track wealth composition over time including bank reserves, stock portfolio, and home equity
- **Income Management**: Support for multiple income sources including USD stock dividends with EUR conversion
- **Interactive Charts**: Visualize liquid assets, mortgage progress, property value, and net worth projections
- **Financial Buffer Warning**: Alerts when bank reserves drop below a specified threshold

### 💰 Income & Expenses Tracker
- **Monthly Items**: Track recurring monthly income and expenses
- **Yearly Items**: Track one-off annual income and expenses
- **Calculate Monthly Button**: Convert yearly items to monthly equivalents (divided by 12)
- **Summary Metrics**: View monthly/yearly totals, net income, and savings rate
- **Visualizations**: Pie charts for income vs expenses, bar charts for detailed breakdowns

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit app:

```bash
streamlit run app.py
```

## Dependencies

- **streamlit** - Web application framework
- **pandas** - Data manipulation
- **numpy** - Numerical computations
- **plotly** - Interactive charts
- **pytest** - Testing framework

## Project Structure

```
├── app.py                  # Main entry point (multipage app)
├── pages/
│   ├── 1_Wealth_Calculator.py    # Wealth and net worth page
│   └── 2_Income_Expenses.py      # Income/expenses tracker page
├── src/
│   ├── mortgage.py         # Mortgage calculation functions
│   ├── net_worth.py        # Net worth projection logic
│   ├── income.py           # Income conversion utilities
│   ├── expenses.py         # Expense handling
│   └── formatting.py       # Currency and number formatting
├── requirements.txt        # Python dependencies
└── tests/                  # Unit tests
```

## Testing

Run tests with pytest:

```bash
pytest
```
