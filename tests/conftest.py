"""Pytest configuration and shared fixtures."""
import sys
from pathlib import Path

import pytest


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def standard_net_worth_params():
    """Provide standard parameters for net worth calculation tests.

    Returns
    -------
    dict
        Dictionary of standard financial parameters.
    """
    return {
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


@pytest.fixture
def zero_params():
    """Provide parameters with all zeros (except required minimums).

    Returns
    -------
    dict
        Dictionary of zero/minimum financial parameters.
    """
    return {
        "initial_bank_balance": 0.0,
        "monthly_income1": 0.0,
        "monthly_income2": 0.0,
        "stock_income": 0.0,
        "monthly_expenses": 0.0,
        "years": 1,
        "property_value": 0.0,
        "home_appreciation_rate": 0.0,
        "investment_return_rate": 0.0,
        "stock_growth_rate": 0.0,
        "mortgage_rate": 0.0,
        "mortgage_years": 1,
        "down_payment": 0.0,
        "initial_stock_wealth": 0.0,
        "bank_reserve_ratio": 0.0,
    }
