import json
import os

import streamlit as st
import plotly.express as px

from src.formatting import format_currency, format_number, parse_formatted_number
from src.income import convert_usd_to_eur
from src.mortgage import (
    calculate_amortization,
    calculate_mortgage,
    calculate_property_from_payment,
)
from src.net_worth import calculate_net_worth


SETTINGS_DIR = os.path.join("saved_settings", "wealth_calculator")


# Default values for all inputs
CURRENCY_DEFAULTS = {
    "income1": 3000.0,
    "income2": 1200.0,
    "stock_income_usd": 600.0,
    "espp_income_eur": 0.0,
    "monthly_expenses": 1000.0,
    "initial_bank_balance": 50000.0,
    "initial_stock_wealth": 20000.0,
    "financial_buffer": 10000.0,
    "property_value": 800000.0,
    "down_payment": 200000.0,
}

# Default values for number inputs (rates, fees, years)
NUMBER_DEFAULTS = {
    "usd_eur_rate": 0.92,
    "transaction_fee": 5.0,
    "bank_return": 0.5,
    "stock_growth": 2.0,
    "bank_reserve_ratio": 1.0,
    "interest_rate": 2.5,
    "loan_term": 30,
    "home_appreciation": 2.0,
    "projection_years": 30,
}

# Zero values for number inputs
NUMBER_ZEROS = {
    "usd_eur_rate": 1.0,
    "transaction_fee": 0.0,
    "bank_return": 0.0,
    "stock_growth": 0.0,
    "bank_reserve_ratio": 0.0,
    "interest_rate": 2.0,
    "loan_term": 35,
    "home_appreciation": 0.0,
    "projection_years": 35,
}


def currency_input(label: str, default: float, key: str) -> float:
    """Render a text input with thousand-separator formatting.

    Parameters
    ----------
    label : str
        Label for the input field.
    default : float
        Default numeric value.
    key : str
        Unique Streamlit widget key.

    Returns
    -------
    float
        Parsed numeric value from user input.
    """
    # Initialize session state with formatted default if not present
    if key not in st.session_state:
        st.session_state[key] = format_number(default)

    # Get the current value from our session state
    current_value = st.session_state[key]
    
    # Create the text input widget with the current value
    input_key = f"{key}_input"
    text_value = st.text_input(label, value=current_value, key=input_key)
    parsed = parse_formatted_number(text_value, default)

    # Update only the base key with formatted value for consistency
    # Don't modify the widget's session state key to avoid StreamlitAPIException
    st.session_state[key] = format_number(parsed)

    return parsed


def zero_all_fields() -> None:
    """Set all input fields to zero (or minimum allowed value)."""
    for key in CURRENCY_DEFAULTS:
        st.session_state[key] = format_number(0.0)
    for key, value in NUMBER_ZEROS.items():
        st.session_state[key] = value
    # Reset monthly payment tracking
    if "monthly_payment" in st.session_state:
        del st.session_state["monthly_payment"]
    if "last_calc_payment" in st.session_state:
        del st.session_state["last_calc_payment"]
    # Set flag to trigger widget updates
    st.session_state["_fields_zeroed"] = True


def reset_all_fields() -> None:
    """Reset all input fields to their default values."""
    for key, value in CURRENCY_DEFAULTS.items():
        st.session_state[key] = format_number(value)
    for key, value in NUMBER_DEFAULTS.items():
        st.session_state[key] = value
    # Reset monthly payment tracking
    if "monthly_payment" in st.session_state:
        del st.session_state["monthly_payment"]
    if "last_calc_payment" in st.session_state:
        del st.session_state["last_calc_payment"]
    # Set flag to trigger widget updates
    st.session_state["_fields_reset"] = True


def init_session_state() -> None:
    """Initialize session state with default values if not present."""
    for key, value in NUMBER_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_warning_css(buffer_breach: bool) -> str:
    """Generate CSS to highlight fields when buffer is breached.

    Parameters
    ----------
    buffer_breach : bool
        Whether the financial buffer has been breached.

    Returns
    -------
    str
        CSS string to inject into the page.
    """
    if not buffer_breach:
        return ""

    return """
    <style>
    /* Style for warning fields when buffer is breached */
    div[data-testid="stTextInput"]:has(input[aria-label="Primary Income (Net)"]) input,
    div[data-testid="stTextInput"]:has(input[aria-label="Secondary Income (Net)"]) input,
    div[data-testid="stTextInput"]:has(input[aria-label="Monthly Expenses"]) input,
    div[data-testid="stTextInput"]:has(input[aria-label="Property Value"]) input,
    div[data-testid="stTextInput"]:has(input[aria-label="Monthly Payment"]) input {
        border: 2px solid #ff4b4b !important;
        background-color: #fff0f0 !important;
    }
    </style>
    """


def get_preset_input_keys() -> tuple[list[str], list[str], str, str]:
    currency_keys = [
        "income1",
        "income2",
        "stock_income_usd",
        "espp_income_eur",
        "monthly_expenses",
        "initial_bank_balance",
        "initial_stock_wealth",
        "financial_buffer",
        "property_value",
        "down_payment",
    ]

    number_keys = [
        "usd_eur_rate",
        "transaction_fee",
        "bank_return",
        "stock_growth",
        "bank_reserve_ratio",
        "interest_rate",
        "loan_term",
        "home_appreciation",
        "projection_years",
    ]

    checkbox_key = "sell_stocks_monthly"
    selectbox_key = "sells_per_year_label"
    monthly_payment_key = "monthly_payment"

    return currency_keys, number_keys, checkbox_key, selectbox_key, monthly_payment_key


def get_saved_presets() -> list[str]:
    """Get list of saved preset files.

    Returns
    -------
    list[str]
        List of saved preset names (without .json extension).
    """
    if not os.path.exists(SETTINGS_DIR):
        return []
    files = [f[:-5] for f in os.listdir(SETTINGS_DIR) if f.endswith(".json")]
    return sorted(files)


def save_current_preset(preset_name: str) -> None:
    """Save current settings to a JSON file.

    Parameters
    ----------
    preset_name : str
        Name for the preset file.
    """
    name = (preset_name or "").strip()
    if not name:
        st.error("Please enter a preset name.")
        return

    os.makedirs(SETTINGS_DIR, exist_ok=True)

    currency_keys, number_keys, checkbox_key, selectbox_key, _ = get_preset_input_keys()
    preset: dict[str, object] = {}

    for key in currency_keys:
        preset[key] = st.session_state.get(key, "")
    for key in number_keys:
        preset[key] = st.session_state.get(key)
    preset[checkbox_key] = st.session_state.get(checkbox_key, False)
    preset[selectbox_key] = st.session_state.get(selectbox_key, "12 (monthly)")

    filepath = os.path.join(SETTINGS_DIR, f"{name}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(preset, f, indent=2)


def load_preset(preset_name: str) -> None:
    """Load settings from a JSON file.

    Parameters
    ----------
    preset_name : str
        Name of the preset file to load.
    """
    if not preset_name or preset_name == "(no presets saved)":
        return

    filepath = os.path.join(SETTINGS_DIR, f"{preset_name}.json")
    if not os.path.exists(filepath):
        return

    with open(filepath, "r", encoding="utf-8") as f:
        preset = json.load(f)

    currency_keys, number_keys, checkbox_key, selectbox_key, monthly_payment_key = (
        get_preset_input_keys()
    )

    for key in currency_keys:
        value = preset.get(key)
        if value is not None:
            st.session_state[key] = value

    for key in number_keys:
        value = preset.get(key)
        if value is not None:
            st.session_state[key] = value

    if checkbox_key in preset:
        st.session_state[checkbox_key] = bool(preset[checkbox_key])

    if selectbox_key in preset:
        st.session_state[selectbox_key] = preset[selectbox_key]

    if monthly_payment_key in st.session_state:
        del st.session_state[monthly_payment_key]
    if "last_calc_payment" in st.session_state:
        del st.session_state["last_calc_payment"]


def delete_preset(preset_name: str) -> None:
    """Delete a saved preset file.

    Parameters
    ----------
    preset_name : str
        Name of the preset file to delete.
    """
    if not preset_name or preset_name == "(no presets saved)":
        return

    filepath = os.path.join(SETTINGS_DIR, f"{preset_name}.json")
    if os.path.exists(filepath):
        os.remove(filepath)


def load_preset_and_update(preset_name: str) -> None:
    """Load preset and update current preset tracking."""
    load_preset(preset_name)
    st.session_state["_current_preset"] = preset_name


def delete_preset_and_update(preset_name: str) -> None:
    """Delete preset and update current preset tracking."""
    delete_preset(preset_name)
    # If we deleted the current preset, reset to first available
    if preset_name == st.session_state.get("_current_preset"):
        remaining_presets = get_saved_presets()
        if remaining_presets:
            st.session_state["_current_preset"] = remaining_presets[0]


def load_preset_callback() -> None:
    """Callback function for load button."""
    selected = st.session_state.get("selected_preset", "(no presets saved)")
    if selected != "(no presets saved)":
        load_preset_and_update(selected)


def delete_preset_callback() -> None:
    """Callback function for delete button."""
    selected = st.session_state.get("selected_preset", "(no presets saved)")
    if selected != "(no presets saved)":
        delete_preset_and_update(selected)


def import_ie_callback() -> None:
    """Callback function for importing from Income & Expenses."""
    total_income = st.session_state.get("summary_monthly_income")
    total_expenses = st.session_state.get("summary_monthly_expenses")

    # If not in session state, load from defaults file
    if total_income is None or total_expenses is None:
        ie_settings_path = os.path.join(
            "saved_settings", "income_expenses", "defaults.json"
        )
        if os.path.exists(ie_settings_path):
            with open(ie_settings_path, "r", encoding="utf-8") as f:
                ie_settings = json.load(f)

            calc_mode = ie_settings.get("calc_mode", "separate")
            raw_monthly_income = sum(
                item["amount"]
                for item in ie_settings.get("income_monthly_items", [])
                if not item.get("hidden", False)
            )
            raw_monthly_expenses = sum(
                item["amount"]
                for item in ie_settings.get("expense_monthly_items", [])
                if not item.get("hidden", False)
            )
            converted_yearly_income = sum(
                item["amount"]
                for item in ie_settings.get("income_monthly_items", [])
                if "original_yearly" in item and not item.get("hidden", False)
            )
            converted_yearly_expenses = sum(
                item["amount"]
                for item in ie_settings.get("expense_monthly_items", [])
                if "original_yearly" in item and not item.get("hidden", False)
            )

            if calc_mode == "monthly":
                total_income = raw_monthly_income + converted_yearly_income
                total_expenses = raw_monthly_expenses + converted_yearly_expenses
            else:
                total_income = raw_monthly_income
                total_expenses = raw_monthly_expenses
        else:
            total_income = 0.0
            total_expenses = 0.0

    st.session_state["income1"] = format_number(total_income)
    st.session_state["monthly_expenses"] = format_number(total_expenses)
    # Set flag to trigger widget updates
    st.session_state["_income_imported"] = True


def import_stock_callback() -> None:
    """Callback function for importing from Stock Estimator."""
    # Import stock income from Stock Estimator
    # First try session state, then fall back to defaults.json
    stock_settings = {}

    # Check if Stock Estimator has been initialized in session state
    if "_stock_estimator_initialized" in st.session_state:
        # Read from session state
        stock_settings = {
            "rsu_enabled": st.session_state.get("rsu_enabled", True),
            "rsu_blocks": st.session_state.get("rsu_blocks", []),
            "stock_start_price": st.session_state.get("stock_start_price", 40.0),
            "espp_enabled": st.session_state.get("espp_enabled", True),
            "espp_gross_income": st.session_state.get("espp_gross_income", 5000.0),
            "espp_contribution": st.session_state.get("espp_contribution", 10.0),
            "espp_discount": st.session_state.get("espp_discount", 15.0),
        }
    else:
        # Fall back to defaults.json
        stock_settings_path = os.path.join(
            "saved_settings", "stock_estimator", "defaults.json"
        )
        if os.path.exists(stock_settings_path):
            with open(stock_settings_path, "r", encoding="utf-8") as f:
                stock_settings = json.load(f)

    # Calculate RSU monthly income (USD) from RSU blocks
    rsu_monthly_usd = 0.0
    if stock_settings.get("rsu_enabled", False):
        rsu_blocks = stock_settings.get("rsu_blocks", [])
        stock_price = stock_settings.get("stock_start_price", 40.0)

        for block in rsu_blocks:
            if block.get("hidden", False):
                continue
            total_stocks = block.get("total_stocks", 0)
            vest_months = block.get("vest_months", 48)
            if vest_months > 0:
                # Quarterly vesting = stocks per quarter / 3 months
                stocks_per_month = total_stocks / vest_months / 2
                # Value in USD (before tax, fees, etc.)
                rsu_monthly_usd += stocks_per_month * stock_price

    # Calculate ESPP monthly contribution value (EUR)
    espp_monthly_eur = 0.0
    if stock_settings.get("espp_enabled", False):
        espp_gross = stock_settings.get("espp_gross_income", 0.0)
        espp_contrib_pct = stock_settings.get("espp_contribution", 0.0) / 100
        espp_discount = stock_settings.get("espp_discount", 15.0) / 100
        # Monthly contribution + discount benefit
        monthly_contrib = espp_gross * espp_contrib_pct
        # Approximate monthly value including discount benefit
        espp_monthly_eur = monthly_contrib * (1 + espp_discount)

    # Always update values (even if 0 when disabled)
    st.session_state["stock_income_usd"] = format_number(rsu_monthly_usd)
    st.session_state["espp_income_eur"] = format_number(espp_monthly_eur)
    # Set flag to trigger widget updates
    st.session_state["_stock_imported"] = True


def main() -> None:
    """Run the Streamlit wealth estimator app."""
    st.set_page_config(
        page_title="Wealth Estimator",
        page_icon="🏠",
        layout="wide",
    )

    # Make dividers more prominent
    st.markdown(
        """
        <style>
        [data-testid="stVerticalBlockBorderWrapper"] hr,
        [data-testid="stSidebar"] hr,
        div[data-testid="stHorizontalBlock"] hr,
        .stDivider hr,
        hr {
            border: none !important;
            border-top: 3px solid #888 !important;
            margin: 1.5em 0 !important;
            height: 0 !important;
            background: transparent !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🏠 Wealth Estimator")

    # Initialize session state for number inputs
    init_session_state()
    
    # Auto-load first available preset on startup (only for this page)
    if "_wealth_calculator_settings_loaded" not in st.session_state:
        preset_options = get_saved_presets()
        if preset_options:
            # Store which preset we're loading
            st.session_state["_current_preset"] = preset_options[0]
            load_preset(preset_options[0])
            st.session_state["_wealth_calculator_settings_loaded"] = True
            # Trigger rerun to ensure widgets display loaded values
            st.rerun()
    
    # Check if any callback operations need to trigger widget updates
    needs_rerun = False
    if st.session_state.get("_income_imported", False):
        st.session_state["_income_imported"] = False
        needs_rerun = True
    if st.session_state.get("_stock_imported", False):
        st.session_state["_stock_imported"] = False
        needs_rerun = True
    if st.session_state.get("_fields_zeroed", False):
        st.session_state["_fields_zeroed"] = False
        needs_rerun = True
    if st.session_state.get("_fields_reset", False):
        st.session_state["_fields_reset"] = False
        needs_rerun = True
    
    if needs_rerun:
        st.rerun()

    # Check if buffer was breached in previous run (for styling)
    buffer_breach = st.session_state.get("buffer_breach", False)

    # Inject warning CSS if buffer is breached
    if buffer_breach:
        st.markdown(get_warning_css(True), unsafe_allow_html=True)

    # ------------------------------------------------------------------ Sidebar
    with st.sidebar:
        st.divider()
        st.subheader("💾 Settings")
        preset_options = get_saved_presets()
        has_presets = len(preset_options) > 0
        select_options = preset_options if has_presets else ["(no presets saved)"]
        
        # Get current preset from session state, default to first if not set
        current_preset = st.session_state.get("_current_preset", preset_options[0] if preset_options else "(no presets saved)")
        # Find index of current preset
        default_index = 0
        if current_preset in select_options:
            default_index = select_options.index(current_preset)
        
        selected_preset = st.selectbox(
            "Load Settings",
            options=select_options,
            index=default_index,
            key="selected_preset",
        )
        col_load, col_delete = st.columns(2)
        with col_load:
            st.button(
                "Load",
                on_click=load_preset_callback,
                disabled=not has_presets,
                use_container_width=True,
            )
        with col_delete:
            st.button(
                "Delete",
                on_click=delete_preset_callback,
                disabled=not has_presets,
                use_container_width=True,
            )

        preset_name = st.text_input("Save Current Settings As", key="preset_name")
        if st.button("Save", key="save_preset_btn", use_container_width=True):
            save_current_preset(preset_name)

        st.divider()

        # Zero and Reset buttons
        st.button(
            "0️⃣ Zero Monetary Fields", on_click=zero_all_fields, use_container_width=True
        )
        st.button(
            "🔄 Reset Defaults", on_click=reset_all_fields, use_container_width=True
        )

        st.divider()

        # Income & Expenses
        st.subheader("💰 Monthly Income & Expenses")
        col1, col2 = st.columns(2)
        with col1:
            st.button(
                "📥 Import from Income & Expenses",
                on_click=import_ie_callback,
                use_container_width=True,
                key="import_ie_btn",
            )
        with col2:
            st.button(
                "📥 Import from Stock Estimator",
                on_click=import_stock_callback,
                use_container_width=True,
                key="import_stock_btn",
            )
        col1, col2 = st.columns(2)
        with col1:
            income1 = currency_input("Primary Income (Net)", 3000.0, "income1")
        with col2:
            income2 = currency_input("Secondary Income (Net)", 1200.0, "income2")
        monthly_expenses = currency_input(
            "Monthly Expenses", 1000.0, "monthly_expenses"
        )

        # Stock income with USD to EUR conversion
        col1, col2 = st.columns(2)
        with col1:
            stock_income_usd = currency_input(
                "Stock Income (USD, e.g. RSU)", 600.0, "stock_income_usd"
            )
        with col2:
            espp_income_eur = currency_input(
                "Income Stock Buys (€, e.g. ESPP)", 0.0, "espp_income_eur"
            )

        st.divider()

        # Savings & Investments
        st.subheader("💼 Savings & Investments")
        col1, col2 = st.columns(2)
        with col1:
            initial_bank_balance = currency_input(
                "Initial Bank Balance", 50000.0, "initial_bank_balance"
            )
        with col2:
            initial_stock_wealth = currency_input(
                "Initial Stock Portfolio", 20000.0, "initial_stock_wealth"
            )
        col1, col2 = st.columns(2)
        with col1:
            bank_return = st.number_input(
                "Bank Interest (%)",
                min_value=0.0,
                step=0.1,
                key="bank_return",
            )
        with col2:
            stock_growth = st.number_input(
                "Stock Growth (%)",
                min_value=-20.0,
                step=0.5,
                key="stock_growth",
            )
        bank_reserve_ratio = st.slider(
            "Savings → Bank vs Stocks",
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            help="Fraction of monthly savings kept in bank (rest goes to stocks)",
            key="bank_reserve_ratio",
        )

        # Sell stocks checkbox and selling parameters
        sell_stocks_monthly = st.checkbox(
            "Sell stocks via schedule",
            value=False,
            key="sell_stocks_monthly",
            help="If checked, stock income is sold and converted to cash. "
                 "Otherwise kept in stock portfolio.",
        )

        # Selling parameters (only relevant when selling)
        sells_per_year_options = {
            "1/12 (biennial)": 1/12,
            "1/6": 1/6,
            "1/4 (every 4y)": 1/4,
            "1/3": 1/3,
            "1/2 (biannual)": 1/2,
            "1": 1.0,
            "2": 2.0,
            "3": 3.0,
            "4 (quarterly)": 4.0,
            "6": 6.0,
            "12 (monthly)": 12.0,
        }
        col1, col2, col3 = st.columns(3)
        with col1:
            usd_eur_rate = st.number_input(
                "USD/EUR",
                min_value=0.01,
                step=0.01,
                format="%.4f",
                key="usd_eur_rate",
                disabled=not sell_stocks_monthly,
            )
        with col2:
            selling_fee = st.number_input(
                "Selling Fee (€)",
                min_value=0.0,
                step=1.0,
                key="transaction_fee",
                disabled=not sell_stocks_monthly,
            )
        with col3:
            selectbox_key = "sells_per_year_label"
            # Only set index if no session state value exists to avoid conflict
            if selectbox_key in st.session_state:
                sells_per_year_label = st.selectbox(
                    "Sells/Year",
                    options=list(sells_per_year_options.keys()),
                    key=selectbox_key,
                    disabled=not sell_stocks_monthly,
                )
            else:
                sells_per_year_label = st.selectbox(
                    "Sells/Year",
                    options=list(sells_per_year_options.keys()),
                    index=10,  # Default to "12 (monthly)"
                    key=selectbox_key,
                    disabled=not sell_stocks_monthly,
                )
        sells_per_year = sells_per_year_options[sells_per_year_label]

        # Calculate stock income based on selling frequency
        if sell_stocks_monthly and sells_per_year > 0:
            # Fee is applied per sell, distributed across months
            # e.g., 4 sells/year = fee applied 4 times/year = fee/3 per month on average
            monthly_fee_equivalent = (selling_fee * sells_per_year) / 12
            rsu_income = convert_usd_to_eur(
                stock_income_usd, usd_eur_rate, monthly_fee_equivalent
            )
        else:
            # No selling, no fee
            rsu_income = stock_income_usd * usd_eur_rate

        # Total stock income = RSU (converted) + ESPP (already in EUR)
        stock_income = rsu_income + espp_income_eur
        # reinvest_dividends is the inverse of sell_stocks_monthly
        reinvest_dividends = not sell_stocks_monthly
        st.caption(f"Net stock income: {format_currency(stock_income)}")

        st.divider()

        # Assumptions (must come before Property & Mortgage for interest_rate/loan_term)
        st.subheader("📈 Assumptions")
        col1, col2 = st.columns(2)
        with col1:
            interest_rate = st.number_input(
                "Annual Interest Rate (%)",
                min_value=0.1,
                step=0.1,
                key="interest_rate",
            )
        with col2:
            loan_term = st.number_input(
                "Loan Term (years)",
                min_value=1,
                max_value=40,
                step=1,
                key="loan_term",
            )
        col1, col2 = st.columns(2)
        with col1:
            home_appreciation = st.number_input(
                "Annual Home Appreciation (%)",
                min_value=-10.0,
                step=0.5,
                key="home_appreciation",
            )
        with col2:
            projection_years = st.number_input(
                "Projection Years",
                min_value=1,
                max_value=50,
                step=1,
                key="projection_years",
            )

        st.divider()

        # Property & Mortgage
        st.subheader("🏡 Property & Mortgage")
        col1, col2 = st.columns(2)
        with col1:
            property_value = currency_input(
                "Property Value", 800000.0, "property_value"
            )
        with col2:
            down_payment = currency_input("Down Payment", 200000.0, "down_payment")
        financial_buffer = currency_input(
            "Financial Buffer (Min Bank Reserve)", 10000.0, "financial_buffer"
        )

        # Calculate and display monthly mortgage payment
        calc_monthly_payment = calculate_mortgage(
            property_value, interest_rate, loan_term, down_payment
        )
        calc_monthly_capacity = income1 + income2 - monthly_expenses

        # Initialize monthly payment in session state if needed
        if "monthly_payment" not in st.session_state:
            st.session_state["monthly_payment"] = format_number(calc_monthly_payment)
        if "monmonthly_capacity_payment" not in st.session_state:
            st.session_state["monthly_capacity"] = format_number(calc_monthly_capacity)
        if "stock_income" not in st.session_state:
            st.session_state["monthly_capacity"] = format_number(calc_monthly_capacity)
        # Check if property/mortgage inputs changed - update payment display
        if "last_calc_payment" not in st.session_state:
            st.session_state["last_calc_payment"] = calc_monthly_payment
        if abs(calc_monthly_payment - st.session_state["last_calc_payment"]) > 0.01:
            st.session_state["monthly_payment"] = format_number(calc_monthly_payment)
            st.session_state["last_calc_payment"] = calc_monthly_payment

        # Monthly payment input
        payment_text = st.text_input(
            "Monthly Mortgage Payment Due [€]",
            value=st.session_state["monthly_payment"],
            key="monthly_payment_input",
            help="Edit to adjust property value to meet this payment",
        )
        monthly_capacity_text = st.text_input(
            "Monthly Money Capacity [€]",
            value=st.session_state["monthly_capacity"],
            key="monthly_capacity_input",
            help="The spare money from calculating income + stocks converted to money - expenses. Must be greater than monthly payment.",
        )
        monthly_stock_text = st.text_input(
            "Monthly Stock Capacity [€]",
            value=stock_income,
            key="monthly_stock_capacity_input",
            help="The spare stocks not converted into money yet",
        )


        edited_payment = parse_formatted_number(payment_text, calc_monthly_payment)

        # If user edited the payment, calculate new property value
        if abs(edited_payment - calc_monthly_payment) > 0.01:
            new_property_value = calculate_property_from_payment(
                edited_payment, interest_rate, loan_term, down_payment
            )
            # Update property value in session state
            st.session_state["property_value"] = format_number(new_property_value)
            st.session_state["monthly_payment"] = format_number(edited_payment)
            st.session_state["last_calc_payment"] = edited_payment
            st.rerun()

    # --------------------------------------------------------------- Calculations
    monthly_payment = calculate_mortgage(
        property_value,
        interest_rate,
        loan_term,
        down_payment,
    )
    amortization_schedule = calculate_amortization(
        property_value,
        interest_rate,
        loan_term,
        down_payment,
    )

    net_worth_df = calculate_net_worth(
        initial_bank_balance=initial_bank_balance,
        monthly_income1=income1,
        monthly_income2=income2,
        stock_income=stock_income,
        monthly_expenses=monthly_expenses,
        years=projection_years,
        property_value=property_value,
        home_appreciation_rate=home_appreciation,
        investment_return_rate=bank_return,
        stock_growth_rate=stock_growth,
        mortgage_rate=interest_rate,
        mortgage_years=loan_term,
        down_payment=down_payment,
        initial_stock_wealth=initial_stock_wealth,
        bank_reserve_ratio=bank_reserve_ratio,
        reinvest_dividends=reinvest_dividends,
    )

    # Add Year column for charting
    net_worth_df["Year"] = net_worth_df["Month"] / 12

    # --------------------------------------------------------- Buffer Warning Check
    min_bank_reserve = net_worth_df["Bank Reserve"].min()
    buffer_breach = min_bank_reserve < financial_buffer

    # Check if breach status changed - if so, rerun to update CSS styling
    previous_breach = st.session_state.get("buffer_breach", False)
    if buffer_breach != previous_breach:
        st.session_state["buffer_breach"] = buffer_breach
        st.rerun()

    # Store breach status in session state for CSS styling
    st.session_state["buffer_breach"] = buffer_breach

    if buffer_breach:
        # Find when the breach first occurs
        breach_months = net_worth_df[
            net_worth_df["Bank Reserve"] < financial_buffer
        ]["Month"]
        first_breach_month = int(breach_months.iloc[0]) if len(breach_months) > 0 else 0
        first_breach_year = first_breach_month / 12

        st.error(
            f"⚠️ **Financial Buffer Warning**: Bank reserve drops below "
            f"{format_currency(financial_buffer)} after {first_breach_year:.1f} years "
            f"(month {first_breach_month}). Minimum reached: "
            f"{format_currency(min_bank_reserve)}. "
            f"Consider adjusting income, expenses, or property value."
        )

    # ------------------------------------------------------------------- Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Monthly Mortgage Payment",
            format_currency(monthly_payment),
        )
    with col2:
        if not amortization_schedule.empty:
            total_interest = amortization_schedule["Interest Payment"].sum()
        else:
            total_interest = 0.0
        st.metric("Total Interest Paid", format_currency(total_interest))
    with col3:
        final_net_worth = net_worth_df["Net Worth"].iloc[-1]
        st.metric(
            f"Projected Net Worth in {projection_years} Years",
            format_currency(final_net_worth),
        )

    # -------------------------------------------------------------------- Charts
    # 1. Liquid Assets Breakdown (Bank Reserve vs Stock Wealth)
    st.subheader("💰 Liquid Assets Breakdown")
    fig_liquid = px.area(
        net_worth_df,
        x="Year",
        y=["Bank Reserve", "Stock Wealth"],
        title="Bank Reserve vs Stock Portfolio Over Time",
        labels={"value": "Amount (€)", "variable": "Asset Type"},
        color_discrete_map={"Bank Reserve": "#2E86AB", "Stock Wealth": "#A23B72"},
    )
    fig_liquid.update_layout(
        yaxis_tickformat=",.0f",
        separators=", ",
    )
    st.plotly_chart(fig_liquid, width="stretch")

    # 2. Mortgage Progress (Principal Paid vs Remaining Balance)
    st.subheader("🏦 Mortgage Progress")
    fig_mortgage = px.area(
        net_worth_df,
        x="Year",
        y=["Principal Paid", "Mortgage Balance"],
        title="Loan Paid vs Remaining Balance",
        labels={"value": "Amount (€)", "variable": "Status"},
        color_discrete_map={"Principal Paid": "#28A745", "Mortgage Balance": "#DC3545"},
    )
    fig_mortgage.update_layout(
        yaxis_tickformat=",.0f",
        separators=", ",
    )
    st.plotly_chart(fig_mortgage, width="stretch")

    # 3. Property Value Over Time
    st.subheader("🏠 Property Value")
    fig_property = px.line(
        net_worth_df,
        x="Year",
        y="Home Value",
        title="Property Value Over Time",
        labels={"Home Value": "Value (€)", "Year": "Years from Now"},
    )
    fig_property.update_layout(
        yaxis_tickformat=",.0f",
        separators=", ",
    )
    fig_property.update_traces(line_color="#28A745")
    st.plotly_chart(fig_property, width="stretch")

    # 4. Net Worth Projection
    st.subheader("📈 Net Worth Projection")
    fig = px.line(
        net_worth_df,
        x="Year",
        y="Net Worth",
        title="Net Worth Projection Over Time",
        labels={"Net Worth": "Net Worth (€)", "Year": "Years from Now"},
    )
    fig.update_layout(
        yaxis_tickformat=",.0f",
        separators=", ",
    )
    st.plotly_chart(fig, width="stretch")

    # 5. Wealth Composition (overall breakdown)
    st.subheader("📊 Wealth Composition")
    fig2 = px.area(
        net_worth_df,
        x="Year",
        y=["Bank Reserve", "Stock Wealth", "Home Equity"],
        title="Total Wealth Composition Over Time",
        labels={"value": "Amount (€)", "variable": "Category"},
    )
    fig2.update_layout(
        yaxis_tickformat=",.0f",
        separators=", ",
    )
    st.plotly_chart(fig2, width="stretch")

    # ----------------------------------------------------------------- Raw Data
    if st.checkbox("Show Raw Data"):
        st.subheader("Net Worth Projection Data")
        # Format numeric columns with thousand separators for display
        display_df = net_worth_df.copy()
        numeric_cols = [
            "Net Worth",
            "Bank Reserve",
            "Stock Wealth",
            "Liquid Assets",
            "Home Equity",
            "Home Value",
            "Mortgage Balance",
            "Principal Paid",
        ]
        for col in numeric_cols:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(
                    lambda x: format_currency(x)
                )
        st.dataframe(display_df)

        if not amortization_schedule.empty:
            st.subheader("Amortization Schedule Data")
            display_amort_df = amortization_schedule.copy()
            amort_numeric_cols = [
                "Principal Payment",
                "Interest Payment",
                "Total Payment",
                "Remaining Balance",
            ]
            for col in amort_numeric_cols:
                if col in display_amort_df.columns:
                    display_amort_df[col] = display_amort_df[col].apply(
                        lambda x: format_currency(x)
                    )
            st.dataframe(display_amort_df)


if __name__ == "__main__":
    main()
