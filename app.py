import json
import os

import streamlit as st


# Initialize Stock Estimator defaults in session state (shared across all pages)
def init_stock_estimator_state() -> None:
    """Initialize Stock Estimator session state from defaults.json or hardcoded defaults."""
    if "_stock_estimator_initialized" in st.session_state:
        return

    stock_defaults = {
        "stock_start_price": 40.0,
        "usd_to_eur": 0.92,
        "yearly_growth_rate": 0.0,
        "projection_years": 5,
        "projection_extra_months": 0,
        "rsu_enabled": True,
        "rsu_transaction_fee": 9.99,
        "rsu_selling_loss": 0.05,
        "rsu_blocks": [
            {
                "total_stocks": 500,
                "start_offset": 2,
                "vest_months": 48,
                "delay_months": 12,
                "hidden": False,
            }
        ],
        "espp_enabled": True,
        "espp_gross_income": 5000.0,
        "espp_contribution": 10.0,
        "espp_start_offset": 0,
        "espp_vesting_interval": 6,
        "espp_discount": 15.0,
        "self_enabled": True,
        "self_net_income": 3500.0,
        "self_investment_type": "Fixed Amount",
        "self_investment_pct": 10.0,
        "self_investment_amt": 350.0,
    }

    settings_path = os.path.join("saved_settings", "stock_estimator", "defaults.json")
    if os.path.exists(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            saved_defaults = json.load(f)
        for key, default_value in stock_defaults.items():
            if key not in st.session_state:
                st.session_state[key] = saved_defaults.get(key, default_value)
    else:
        for key, default_value in stock_defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    st.session_state["_stock_estimator_initialized"] = True


# Initialize on app start
init_stock_estimator_state()

# Page definitions
overview_page = st.Page("pages/overview.py", title="Overview", icon="💰", default=True)
income_page = st.Page("pages/income_expenses.py", title="Income & Expenses", icon="💰")
stock_page = st.Page("pages/stock_estimator.py", title="Stock Estimator", icon="📈")
wealth_page = st.Page("pages/wealth_calculator.py", title="Wealth Estimator", icon="🏠")

pg = st.navigation([overview_page, income_page, stock_page, wealth_page])
pg.run()
