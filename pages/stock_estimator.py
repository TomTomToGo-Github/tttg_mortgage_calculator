"""Stock Estimator page for RSU, ESPP, and self-buying calculations."""
import json
import math
import os

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.formatting import format_currency, format_number


SETTINGS_DIR = os.path.join("saved_settings", "stock_estimator")

# Default values for initialization
STOCK_ESTIMATOR_DEFAULTS = {
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


def init_session_state() -> None:
    """Initialize session state from defaults.json or hardcoded defaults.

    Only runs once on first app initialization.
    """
    if "_stock_estimator_initialized" in st.session_state:
        return

    # Try to load from defaults.json first
    defaults_path = os.path.join(SETTINGS_DIR, "defaults.json")
    if os.path.exists(defaults_path):
        with open(defaults_path, "r", encoding="utf-8") as f:
            saved_defaults = json.load(f)
        # Use saved defaults, falling back to hardcoded for missing keys
        for key, default_value in STOCK_ESTIMATOR_DEFAULTS.items():
            if key not in st.session_state:
                st.session_state[key] = saved_defaults.get(key, default_value)
    else:
        # Use hardcoded defaults
        for key, default_value in STOCK_ESTIMATOR_DEFAULTS.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    st.session_state["_stock_estimator_initialized"] = True


def get_saved_settings() -> list[str]:
    """Get list of saved settings files.

    Returns
    -------
    list[str]
        List of saved settings names (without .json extension).
    """
    if not os.path.exists(SETTINGS_DIR):
        return []
    files = [f[:-5] for f in os.listdir(SETTINGS_DIR) if f.endswith(".json")]
    return sorted(files)


def save_current_settings(settings_name: str) -> None:
    """Save current settings to a JSON file.

    Parameters
    ----------
    settings_name : str
        Name for the settings file.
    """
    name = (settings_name or "").strip()
    if not name:
        st.error("Please enter a settings name.")
        return

    os.makedirs(SETTINGS_DIR, exist_ok=True)

    settings = {
        "stock_start_price": st.session_state.get("stock_start_price", 40.0),
        "usd_to_eur": st.session_state.get("usd_to_eur", 0.92),
        "yearly_growth_rate": st.session_state.get("yearly_growth_rate", 0.0),
        "projection_years": st.session_state.get("projection_years", 5),
        "projection_extra_months": st.session_state.get("projection_extra_months", 0),
        "rsu_enabled": st.session_state.get("rsu_enabled", True),
        "rsu_transaction_fee": st.session_state.get("rsu_transaction_fee", 9.99),
        "rsu_selling_loss": st.session_state.get("rsu_selling_loss", 0.05),
        "rsu_blocks": st.session_state.get("rsu_blocks", []),
        "espp_enabled": st.session_state.get("espp_enabled", True),
        "espp_gross_income": st.session_state.get("espp_gross_income", 5000.0),
        "espp_contribution": st.session_state.get("espp_contribution", 10.0),
        "espp_start_offset": st.session_state.get("espp_start_offset", 0),
        "espp_vesting_interval": st.session_state.get("espp_vesting_interval", 6),
        "espp_discount": st.session_state.get("espp_discount", 15.0),
        "self_enabled": st.session_state.get("self_enabled", True),
        "self_net_income": st.session_state.get("self_net_income", 3500.0),
        "self_investment_type": st.session_state.get("self_investment_type", "Fixed Amount"),
        "self_investment_pct": st.session_state.get("self_investment_pct", 10.0),
        "self_investment_amt": st.session_state.get("self_investment_amt", 350.0),
    }

    filepath = os.path.join(SETTINGS_DIR, f"{name}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def load_settings(settings_name: str) -> None:
    """Load settings from a JSON file.

    Parameters
    ----------
    settings_name : str
        Name of the settings file to load.
    """
    if not settings_name or settings_name == "(no settings saved)":
        return

    filepath = os.path.join(SETTINGS_DIR, f"{settings_name}.json")
    if not os.path.exists(filepath):
        return

    with open(filepath, "r", encoding="utf-8") as f:
        saved_settings = json.load(f)

    # Load all settings into session state
    for key, value in saved_settings.items():
        if value is not None:
            st.session_state[key] = value

    # Mark that settings were loaded - rerun happens automatically after callback
    st.session_state["_settings_loaded"] = True


def delete_settings(settings_name: str) -> None:
    """Delete a saved settings file.

    Parameters
    ----------
    settings_name : str
        Name of the settings file to delete.
    """
    if not settings_name or settings_name == "(no settings saved)":
        return

    filepath = os.path.join(SETTINGS_DIR, f"{settings_name}.json")
    if os.path.exists(filepath):
        os.remove(filepath)


def get_stock_price_at_month(
    start_price: float,
    yearly_growth_rate: float,
    month: int,
) -> float:
    """Calculate stock price at a given month.

    Parameters
    ----------
    start_price : float
        Initial stock price.
    yearly_growth_rate : float
        Annual growth rate as decimal (e.g., 0.10 for 10%).
    month : int
        Number of months from start.

    Returns
    -------
    float
        Stock price at the given month.
    """
    monthly_rate = (1 + yearly_growth_rate) ** (1 / 12) - 1
    return start_price * ((1 + monthly_rate) ** month)


def calculate_rsu_vesting(
    total_stocks: int,
    vesting_period_months: int,
    stock_prices: list[float],
    start_offset: int = 0,
    delay_months: int = 0,
    usd_to_eur: float = 1.0,
    transaction_fee_usd: float = 9.99,
    selling_loss_usd: float = 0.05,
) -> pd.DataFrame:
    """Calculate RSU vesting schedule with quarterly payouts.

    RSU payouts happen every 3 months (quarterly). If there is a delay period,
    the first payout includes all accumulated quarterly intervals.

    Parameters
    ----------
    total_stocks : int
        Total number of RSU stocks granted.
    vesting_period_months : int
        Total vesting period in months (must be divisible by 3).
    stock_prices : list[float]
        Stock prices for each month (in USD).
    start_offset : int
        Number of months from now when RSU grant starts.
    delay_months : int
        Delay before first payout (e.g., 12 for cliff vesting).
        First payout includes all accumulated quarters.
    usd_to_eur : float
        USD to EUR conversion rate.
    transaction_fee_usd : float
        Transaction fee per vesting event (in USD).
    selling_loss_usd : float
        Fixed dollar amount lost per stock when E*Trade sells (in USD).

    Returns
    -------
    pd.DataFrame
        DataFrame with monthly RSU values (in EUR).
    """
    months = len(stock_prices)
    data = {
        "Month": list(range(1, months + 1)),
        "RSU_Stocks_Vested": [0.0] * months,
        "RSU_Stocks_Sold": [0.0] * months,
        "RSU_Stocks_Kept": [0.0] * months,
        "RSU_Tax_Due": [0.0] * months,
        "RSU_Sale_Proceeds": [0.0] * months,
        "RSU_Transaction_Fee": [0.0] * months,
        "RSU_Rest_Amount": [0.0] * months,
        "RSU_Value": [0.0] * months,
        "RSU_Cumulative_Stocks": [0.0] * months,
        "RSU_Cumulative_Value": [0.0] * months,
        "RSU_Cumulative_Rest": [0.0] * months,
    }

    if vesting_period_months <= 0:
        return pd.DataFrame(data)

    # Quarterly payouts (every 3 months)
    total_quarters = vesting_period_months // 3
    if total_quarters <= 0:
        return pd.DataFrame(data)

    # Stocks per quarter with remainder distribution
    base_stocks_per_quarter = total_stocks // total_quarters
    remainder = total_stocks % total_quarters

    # Calculate delayed quarters (accumulated in first payout)
    delayed_quarters = delay_months // 3

    cumulative_stocks = 0.0
    cumulative_rest = 0.0

    def process_vesting(vest_index: int, vested: int):
        """Process a single vesting event."""
        if vested <= 0 or vest_index < 0 or vest_index >= months:
            return

        stock_price_usd = stock_prices[vest_index]

        # Tax due = vested * stock_price / 2
        tax_due_usd = vested * stock_price_usd / 2

        # Sell half + 1 for taxes (e.g., 35->18 sold, 36->19 sold)
        stocks_sold = (vested // 2) + 1
        stocks_kept = vested - stocks_sold

        # Sale proceeds at E*Trade price (stock_price - selling_loss)
        etrade_price_usd = stock_price_usd - selling_loss_usd
        sale_proceeds_usd = stocks_sold * etrade_price_usd

        # Rest amount = sale proceeds - tax due - transaction fee
        rest_amount_usd = sale_proceeds_usd - tax_due_usd - transaction_fee_usd

        # Convert to EUR
        stock_price_eur = stock_price_usd * usd_to_eur
        tax_due_eur = tax_due_usd * usd_to_eur
        sale_proceeds_eur = sale_proceeds_usd * usd_to_eur
        transaction_fee_eur = transaction_fee_usd * usd_to_eur
        rest_amount_eur = rest_amount_usd * usd_to_eur

        # Value of kept stocks at real market price
        value_eur = stocks_kept * stock_price_eur

        data["RSU_Stocks_Vested"][vest_index] += vested
        data["RSU_Stocks_Sold"][vest_index] += stocks_sold
        data["RSU_Stocks_Kept"][vest_index] += stocks_kept
        data["RSU_Tax_Due"][vest_index] += tax_due_eur
        data["RSU_Sale_Proceeds"][vest_index] += sale_proceeds_eur
        data["RSU_Transaction_Fee"][vest_index] += transaction_fee_eur
        data["RSU_Rest_Amount"][vest_index] += rest_amount_eur
        data["RSU_Value"][vest_index] = max(0, data["RSU_Value"][vest_index] + value_eur)

    # Process each quarter
    stocks_distributed = 0
    for q in range(total_quarters):
        # Calculate stocks for this quarter (distribute remainder to first quarters)
        quarter_stocks = base_stocks_per_quarter + (1 if q < remainder else 0)
        stocks_distributed += quarter_stocks

        # Quarter month (1-indexed): q=0 -> month 3, q=1 -> month 6, etc.
        quarter_month = (q + 1) * 3

        if quarter_month <= delay_months:
            # This quarter is within delay period - will be paid at first payout
            continue

        # Determine payout month
        if q == delayed_quarters and delayed_quarters > 0:
            # First payout after delay - includes all delayed quarters
            payout_month = start_offset + delay_months + 3
            # Sum up all delayed quarters' stocks
            delayed_stocks = 0
            for dq in range(delayed_quarters):
                delayed_stocks += base_stocks_per_quarter + (1 if dq < remainder else 0)
            vested = delayed_stocks + quarter_stocks
        else:
            payout_month = start_offset + quarter_month
            vested = quarter_stocks

        vest_index = payout_month - 1
        process_vesting(vest_index, vested)

    # Calculate cumulative values
    for month in range(months):
        cumulative_stocks += data["RSU_Stocks_Kept"][month]
        cumulative_rest += data["RSU_Rest_Amount"][month]
        stock_price_eur = stock_prices[month] * usd_to_eur
        data["RSU_Cumulative_Stocks"][month] = cumulative_stocks
        data["RSU_Cumulative_Value"][month] = cumulative_stocks * stock_price_eur
        data["RSU_Cumulative_Rest"][month] = cumulative_rest

    return pd.DataFrame(data)


def calculate_espp_vesting(
    gross_income: float,
    contribution_percent: float,
    stock_prices: list[float],
    discount_rate: float = 0.15,
    vesting_interval_months: int = 6,
    start_offset: int = 0,
) -> pd.DataFrame:
    """Calculate ESPP vesting schedule.

    Parameters
    ----------
    gross_income : float
        Monthly gross income.
    contribution_percent : float
        Percentage of income contributed (as decimal).
    stock_prices : list[float]
        Stock prices for each month.
    discount_rate : float
        ESPP discount rate (default 15%).
    vesting_interval_months : int
        Months between purchases (default 6).
    start_offset : int
        Number of months from now when ESPP starts.

    Returns
    -------
    pd.DataFrame
        DataFrame with monthly ESPP values.
    """
    months = len(stock_prices)
    data = {
        "Month": list(range(1, months + 1)),
        "ESPP_Contribution": [0.0] * months,
        "ESPP_Stocks_Bought": [0.0] * months,
        "ESPP_Value": [0.0] * months,
        "ESPP_Cumulative_Stocks": [0.0] * months,
        "ESPP_Cumulative_Value": [0.0] * months,
    }

    monthly_contribution = gross_income * contribution_percent
    cumulative_stocks = 0.0
    accumulated_contribution = 0.0
    period_start_price = stock_prices[start_offset] if start_offset < months else 0.0

    for month in range(months):
        # Only contribute after start offset
        if month >= start_offset:
            data["ESPP_Contribution"][month] = monthly_contribution
            accumulated_contribution += monthly_contribution

            # Check if it's a vesting month (relative to start offset)
            months_since_start = month - start_offset + 1
            if months_since_start % vesting_interval_months == 0 and months_since_start > 0:
                current_price = stock_prices[month]
                # Buy at minimum of start or current price, with discount
                buy_price = min(period_start_price, current_price) * (1 - discount_rate)
                stocks_bought = accumulated_contribution / buy_price if buy_price > 0 else 0
                data["ESPP_Stocks_Bought"][month] = stocks_bought
                data["ESPP_Value"][month] = stocks_bought * current_price
                accumulated_contribution = 0.0
                # Reset period start price for next period
                period_start_price = current_price

        cumulative_stocks += data["ESPP_Stocks_Bought"][month]
        data["ESPP_Cumulative_Stocks"][month] = cumulative_stocks
        data["ESPP_Cumulative_Value"][month] = cumulative_stocks * stock_prices[month]

    return pd.DataFrame(data)


def calculate_self_buying(
    net_income: float,
    investment_amount: float,
    is_percentage: bool,
    stock_prices: list[float],
) -> pd.DataFrame:
    """Calculate self-buying stock accumulation.

    Parameters
    ----------
    net_income : float
        Monthly net income.
    investment_amount : float
        Amount or percentage to invest.
    is_percentage : bool
        If True, investment_amount is a percentage.
    stock_prices : list[float]
        Stock prices for each month.

    Returns
    -------
    pd.DataFrame
        DataFrame with monthly self-buying values.
    """
    months = len(stock_prices)
    data = {
        "Month": list(range(months)),
        "Self_Investment": [0.0] * months,
        "Self_Stocks_Bought": [0.0] * months,
        "Self_Value": [0.0] * months,
        "Self_Cumulative_Stocks": [0.0] * months,
        "Self_Cumulative_Value": [0.0] * months,
    }

    if is_percentage:
        monthly_investment = net_income * (investment_amount / 100)
    else:
        monthly_investment = investment_amount

    cumulative_stocks = 0.0

    for month in range(months):
        price = stock_prices[month]
        stocks_bought = monthly_investment / price if price > 0 else 0
        data["Self_Investment"][month] = monthly_investment
        data["Self_Stocks_Bought"][month] = stocks_bought
        data["Self_Value"][month] = stocks_bought * price

        cumulative_stocks += stocks_bought
        data["Self_Cumulative_Stocks"][month] = cumulative_stocks
        data["Self_Cumulative_Value"][month] = cumulative_stocks * price

    return pd.DataFrame(data)


def main() -> None:
    """Run the Stock Estimator page."""
    st.set_page_config(
        page_title="Stock Estimator",
        page_icon="📈",
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

    st.title("📈 Stock Estimator")

    # Initialize session state from defaults (only on first app init)
    init_session_state()

    # Sidebar inputs
    with st.sidebar:
        st.subheader("💾 Settings")
        settings_options = get_saved_settings()
        has_settings = len(settings_options) > 0
        select_options = settings_options if has_settings else ["(no settings saved)"]
        selected_settings = st.selectbox(
            "Load Settings",
            options=select_options,
            index=0,
            key="selected_settings",
        )
        col_load, col_delete = st.columns(2)
        with col_load:
            st.button(
                "Load",
                on_click=load_settings,
                args=(selected_settings,),
                disabled=not has_settings,
                use_container_width=True,
            )
        with col_delete:
            st.button(
                "Delete",
                on_click=delete_settings,
                args=(selected_settings,),
                disabled=not has_settings,
                use_container_width=True,
            )

        settings_name = st.text_input("Save Current Settings As", key="settings_name")
        if st.button("Save", key="save_settings_btn", use_container_width=True):
            save_current_settings(settings_name)

        st.divider()

        st.subheader("📊 Stock Price")
        c1, c2 = st.columns(2)
        with c1:
            stock_start_price = st.number_input(
                "Starting Stock Price ($)",
                min_value=0.01,
                value=st.session_state["stock_start_price"],
                step=1.0,
                key="stock_start_price_input",
            )
            st.session_state["stock_start_price"] = stock_start_price
        with c2:
            usd_to_eur = st.number_input(
                "USD to EUR",
                min_value=0.01,
                value=st.session_state["usd_to_eur"],
                step=0.01,
                format="%.2f",
                key="usd_to_eur_input",
                help="Conversion rate from USD to EUR",
            )
            st.session_state["usd_to_eur"] = usd_to_eur
        yearly_growth_rate = st.number_input(
            "Yearly Growth Rate (%)",
            min_value=-50.0,
            max_value=100.0,
            step=1.0,
            key="yearly_growth_rate",
        ) / 100

        st.markdown("**Visualization Range**")
        col_years, col_months = st.columns(2)
        with col_years:
            projection_years = st.number_input(
                "Years",
                min_value=0,
                max_value=10,
                step=1,
                key="projection_years",
            )
        with col_months:
            projection_extra_months = st.number_input(
                "Months",
                min_value=0,
                max_value=11,
                step=1,
                key="projection_extra_months",
            )
        projection_months = (projection_years * 12) + projection_extra_months
        if projection_months < 1:
            projection_months = 1

        st.divider()

        # RSU Settings - Multiple blocks
        # Use value from session state to persist across page changes
        if "rsu_enabled" not in st.session_state:
            st.session_state["rsu_enabled"] = True
        rsu_enabled = st.checkbox(
            "🎁 RSU (Restricted Stock Units)",
            value=st.session_state["rsu_enabled"],
            key="rsu_enabled_cb",
        )
        st.session_state["rsu_enabled"] = rsu_enabled
        rsu_blocks_data = []
        rsu_transaction_fee = 9.99
        rsu_selling_loss = 0.05

        if rsu_enabled:
            # RSU calculation info
            with st.expander("ℹ️ RSU Calculation Details"):
                st.markdown(
                    "**Vesting Schedule:**\n"
                    "- Payouts happen **quarterly** (every 3 months)\n"
                    "- If a **delay** (cliff) is set, the first payout includes all "
                    "accumulated quarters\n"
                    "- Example with **start=4, delay=0**: 480 stocks over 48m → first payout at month 5 "
                    "(4+0+1) with 30 stocks, then 15 more quarterly payouts of 30 stocks each\n"
                    "- Example with **start=2, delay=12**: 480 stocks over 48m → first payout at month 15 "
                    "(2+12+1) with 120 stocks (4 quarters), then 12 quarterly payouts of 30 stocks each\n\n"
                    "**Abbreviations:**\n"
                    "- V ... number of vested stocks\n"
                    "- P ... stock price (\\$)\n"
                    "- SL ... selling loss (\\$)\n"
                    "- TF ... transaction fee (\\$)\n\n"
                    "**Calculation steps:**\n"
                    "1. **Tax Due (T)** = V × P ÷ 2  "
                    "*(e.g., 35 stock units at 40\\$ each → 35 * 40 / 2 = 700\\$)*\n"
                    "2. **Stocks Sold (S)** = floor(V ÷ 2) + 1 *(e.g., 35 → 18, 36 → 19)*\n"
                    "3. **Sale Proceeds (SP)** = S × (P - SL) "
                    "*(e.g., 18 × (40 - 0.05) = 719.1\\$)*\n"
                    "4. **Rest Amount (R)** = SP - T - TF "
                    "*(e.g., 719.1 - 700 - 9.99 = 9.11\\$)*\n"
                    "5. **Value Held** = (V - S) × P "
                    "*(e.g., (35 - 18) × 40 = 520\\$)*\n\n"
                    "**Rest Amount** = leftover cash on E*Trade after taxes and fees.\n\n"
                    "⚠️ **Note:** The calculated rest value may diverge slightly from "
                    "reality due to:\n"
                    "- E*Trade may occasionally sell one more stock than expected\n"
                    "- This model uses a simplified stock price projection (constant growth "
                    "rate), while actual rest amounts depend on the real stock price at "
                    "vesting time — higher prices yield higher rest amounts, and vice versa\n"
                    "- The selling loss is not predictable (difference between market price "
                    "and E*Trade selling price varies)\n"
                    "- Additional transaction costs apply when selling stocks and "
                    "transferring money overseas"
                )

            # Transaction fee and selling loss settings
            c1, c2 = st.columns(2)
            with c1:
                rsu_transaction_fee = st.number_input(
                    "Transaction Fee ($)",
                    min_value=0.0,
                    value=st.session_state["rsu_transaction_fee"],
                    step=0.01,
                    format="%.2f",
                    key="rsu_transaction_fee_input",
                    help="Fee per vesting transaction (in USD)",
                )
                st.session_state["rsu_transaction_fee"] = rsu_transaction_fee
            with c2:
                rsu_selling_loss = st.number_input(
                    "Selling Loss ($)",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state["rsu_selling_loss"],
                    step=0.01,
                    format="%.2f",
                    key="rsu_selling_loss_input",
                    help="Fixed dollar amount lost per stock because E*Trade selling price is lower than market price",
                )
                st.session_state["rsu_selling_loss"] = rsu_selling_loss

            # Render each RSU block
            blocks_to_remove = []
            blocks_to_toggle = []

            for i, block in enumerate(st.session_state["rsu_blocks"]):
                is_hidden = block.get("hidden", False)
                with st.container():
                    col_title, col_eye, col_del = st.columns([5, 0.5, 0.5])
                    with col_title:
                        if is_hidden:
                            st.markdown(
                                f"<span style='color: #999; font-style: italic;'>"
                                f"Plan {i + 1}</span>",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(f"**Plan {i + 1}**")
                    with col_eye:
                        eye_icon = "🙈" if is_hidden else "👁️"
                        eye_help = "Show" if is_hidden else "Hide"
                        if st.button(eye_icon, key=f"rsu_toggle_{i}", help=eye_help):
                            blocks_to_toggle.append(i)
                    with col_del:
                        if st.button("🗑️", key=f"rsu_delete_{i}", help="Delete"):
                            blocks_to_remove.append(i)

                    # All fields in one row: Stocks, Start, Vest, Delay
                    # Migrate old blocks: convert intervals to delay_months
                    if "intervals" in block and "delay_months" not in block:
                        block["delay_months"] = 12  # Default cliff
                        del block["intervals"]
                    if "delay_months" not in block:
                        block["delay_months"] = 0

                    if is_hidden:
                        # Show greyed out values
                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            st.markdown(
                                f"<span style='color: #999;'>"
                                f"Stocks: {block['total_stocks']:,}</span>",
                                unsafe_allow_html=True,
                            )
                        with c2:
                            st.markdown(
                                f"<span style='color: #999;'>"
                                f"Start: {block['start_offset']}m</span>",
                                unsafe_allow_html=True,
                            )
                        with c3:
                            st.markdown(
                                f"<span style='color: #999;'>"
                                f"Vest: {block['vest_months']}m</span>",
                                unsafe_allow_html=True,
                            )
                        with c4:
                            st.markdown(
                                f"<span style='color: #999;'>"
                                f"Delay: {block['delay_months']}m</span>",
                                unsafe_allow_html=True,
                            )
                    else:
                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            block["total_stocks"] = st.number_input(
                                "Stocks",
                                min_value=0,
                                value=block["total_stocks"],
                                step=100,
                                key=f"rsu_total_{i}",
                            )
                        with c2:
                            block["start_offset"] = st.number_input(
                                "Start (m from now)",
                                min_value=0,
                                value=block["start_offset"],
                                step=1,
                                key=f"rsu_start_{i}",
                            )
                        with c3:
                            block["vest_months"] = st.number_input(
                                "Vesting period (m)",
                                min_value=3,
                                value=block["vest_months"],
                                step=3,
                                key=f"rsu_vest_m_{i}",
                                help="Total vesting period in months (quarterly payouts)",
                            )
                        with c4:
                            max_delay = max(0, block["vest_months"] - 3)
                            block["delay_months"] = st.number_input(
                                "Delay (m)",
                                min_value=0,
                                max_value=max_delay,
                                value=min(block["delay_months"], max_delay),
                                step=3,
                                key=f"rsu_delay_{i}",
                                help="Cliff period before first payout (first payout includes accumulated quarters)",
                            )

                    # Only add to calculation if not hidden
                    if not is_hidden:
                        rsu_blocks_data.append({
                            "total_stocks": block["total_stocks"],
                            "start_offset": block["start_offset"],
                            "vesting_period": block["vest_months"],
                            "delay_months": block["delay_months"],
                            "usd_to_eur": usd_to_eur,
                            "transaction_fee": rsu_transaction_fee,
                            "selling_loss": rsu_selling_loss,
                        })

                    if i < len(st.session_state["rsu_blocks"]) - 1:
                        st.markdown("---")

            # Handle toggles
            if blocks_to_toggle:
                for idx in blocks_to_toggle:
                    current_hidden = st.session_state["rsu_blocks"][idx].get("hidden", False)
                    st.session_state["rsu_blocks"][idx]["hidden"] = not current_hidden

            # Handle deletions
            if blocks_to_remove:
                for idx in reversed(blocks_to_remove):
                    st.session_state["rsu_blocks"].pop(idx)

            # Add new RSU block button
            if st.button("➕ Add RSU Plan", key="add_rsu_block"):
                st.session_state["rsu_blocks"].append({
                    "total_stocks": 1000,
                    "start_offset": 0,
                    "vest_months": 48,
                    "delay_months": 12,
                    "hidden": False,
                })

        st.divider()

        # ESPP Settings
        # Use value from session state to persist across page changes
        if "espp_enabled" not in st.session_state:
            st.session_state["espp_enabled"] = True
        espp_enabled = st.checkbox(
            "💼 ESPP (Employee Stock Purchase Plan)",
            value=st.session_state["espp_enabled"],
            key="espp_enabled_cb",
        )
        st.session_state["espp_enabled"] = espp_enabled

        if espp_enabled:
            c1, c2 = st.columns(2)
            with c1:
                espp_gross_income = st.number_input(
                    "Monthly Gross Income (€)",
                    min_value=0.0,
                    value=st.session_state["espp_gross_income"],
                    step=100.0,
                    key="espp_gross_income_input",
                )
                st.session_state["espp_gross_income"] = espp_gross_income
            with c2:
                espp_contribution_pct = st.number_input(
                    "Contribution Rate (%)",
                    min_value=0.0,
                    max_value=15.0,
                    value=st.session_state["espp_contribution"],
                    step=1.0,
                    key="espp_contribution_input",
                    help="Percentage of gross income contributed to ESPP",
                )
                st.session_state["espp_contribution"] = espp_contribution_pct
                espp_contribution = espp_contribution_pct / 100

            c1, c2, c3 = st.columns(3)
            with c1:
                espp_start_offset = st.number_input(
                    "Start (m from now)",
                    min_value=0,
                    value=st.session_state["espp_start_offset"],
                    step=1,
                    key="espp_start_offset_input",
                )
                st.session_state["espp_start_offset"] = espp_start_offset
            with c2:
                espp_vesting_interval = st.number_input(
                    "Vesting interval (M)",
                    min_value=1,
                    max_value=12,
                    value=st.session_state["espp_vesting_interval"],
                    step=1,
                    key="espp_vesting_interval_input",
                )
                st.session_state["espp_vesting_interval"] = espp_vesting_interval
            with c3:
                espp_discount_pct = st.number_input(
                    "Discount (%)",
                    min_value=0.0,
                    max_value=50.0,
                    value=st.session_state["espp_discount"],
                    step=1.0,
                    key="espp_discount_input",
                )
                st.session_state["espp_discount"] = espp_discount_pct
                espp_discount = espp_discount_pct / 100
        else:
            espp_gross_income = 0.0
            espp_contribution = 0.0
            espp_start_offset = 0
            espp_vesting_interval = 6
            espp_discount = 0.0

        st.divider()

        # Self Buying Settings
        # Use value from session state to persist across page changes
        if "self_enabled" not in st.session_state:
            st.session_state["self_enabled"] = True
        self_enabled = st.checkbox(
            "🛒 Self Buying",
            value=st.session_state["self_enabled"],
            key="self_enabled_cb",
        )
        st.session_state["self_enabled"] = self_enabled

        if self_enabled:
            self_net_income = st.number_input(
                "Monthly Net Income (€)",
                min_value=0.0,
                value=st.session_state["self_net_income"],
                step=100.0,
                key="self_net_income_input",
            )
            st.session_state["self_net_income"] = self_net_income

            self_investment_type = st.radio(
                "Investment Type",
                options=["Fixed Amount", "Percentage"],
                key="self_investment_type",
                horizontal=True,
            )
            if self_investment_type == "Percentage":
                self_investment = st.number_input(
                    "Investment (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=st.session_state["self_investment_pct"],
                    step=1.0,
                    key="self_investment_pct_input",
                )
                st.session_state["self_investment_pct"] = self_investment
                is_percentage = True
            else:
                self_investment = st.number_input(
                    "Investment Amount (€)",
                    min_value=0.0,
                    value=st.session_state["self_investment_amt"],
                    step=50.0,
                    key="self_investment_amt_input",
                )
                st.session_state["self_investment_amt"] = self_investment
                is_percentage = False
        else:
            self_net_income = 0.0
            self_investment = 0.0
            is_percentage = False

    # Calculate stock prices for projection period
    stock_prices = [
        get_stock_price_at_month(stock_start_price, yearly_growth_rate, m)
        for m in range(projection_months)
    ]

    # Calculate RSU for all blocks and combine
    rsu_dfs = []
    for block_data in rsu_blocks_data:
        block_df = calculate_rsu_vesting(
            block_data["total_stocks"],
            block_data["vesting_period"],
            stock_prices,
            block_data["start_offset"],
            block_data["delay_months"],
            block_data["usd_to_eur"],
            block_data["transaction_fee"],
            block_data["selling_loss"],
        )
        rsu_dfs.append(block_df)

    # Combine all RSU blocks
    if rsu_dfs:
        rsu_df = rsu_dfs[0].copy()
        for df in rsu_dfs[1:]:
            rsu_df["RSU_Stocks_Vested"] += df["RSU_Stocks_Vested"]
            rsu_df["RSU_Stocks_Sold"] += df["RSU_Stocks_Sold"]
            rsu_df["RSU_Stocks_Kept"] += df["RSU_Stocks_Kept"]
            rsu_df["RSU_Tax_Due"] += df["RSU_Tax_Due"]
            rsu_df["RSU_Sale_Proceeds"] += df["RSU_Sale_Proceeds"]
            rsu_df["RSU_Transaction_Fee"] += df["RSU_Transaction_Fee"]
            rsu_df["RSU_Rest_Amount"] += df["RSU_Rest_Amount"]
            rsu_df["RSU_Value"] += df["RSU_Value"]
            rsu_df["RSU_Cumulative_Stocks"] += df["RSU_Cumulative_Stocks"]
            rsu_df["RSU_Cumulative_Value"] += df["RSU_Cumulative_Value"]
            rsu_df["RSU_Cumulative_Rest"] += df["RSU_Cumulative_Rest"]
    else:
        rsu_df = pd.DataFrame({
            "Month": list(range(1, projection_months + 1)),
            "RSU_Stocks_Vested": [0.0] * projection_months,
            "RSU_Stocks_Sold": [0.0] * projection_months,
            "RSU_Stocks_Kept": [0.0] * projection_months,
            "RSU_Tax_Due": [0.0] * projection_months,
            "RSU_Sale_Proceeds": [0.0] * projection_months,
            "RSU_Transaction_Fee": [0.0] * projection_months,
            "RSU_Rest_Amount": [0.0] * projection_months,
            "RSU_Value": [0.0] * projection_months,
            "RSU_Cumulative_Stocks": [0.0] * projection_months,
            "RSU_Cumulative_Value": [0.0] * projection_months,
            "RSU_Cumulative_Rest": [0.0] * projection_months,
        })

    espp_df = calculate_espp_vesting(
        espp_gross_income,
        espp_contribution,
        stock_prices,
        espp_discount,
        espp_vesting_interval,
        espp_start_offset,
    )

    self_df = calculate_self_buying(
        self_net_income,
        self_investment,
        is_percentage,
        stock_prices,
    )

    # Convert stock prices to EUR for visualization
    stock_prices_eur = [p * usd_to_eur for p in stock_prices]

    # Combine data for visualization (all values in EUR)
    combined_df = pd.DataFrame({
        "Month": list(range(1, projection_months + 1)),
        "Stock_Price": stock_prices_eur,
        "RSU_Value": rsu_df["RSU_Cumulative_Value"],
        "ESPP_Value": espp_df["ESPP_Cumulative_Value"],
        "Self_Value": self_df["Self_Cumulative_Value"],
    })
    combined_df["Total_Value"] = (
        combined_df["RSU_Value"]
        + combined_df["ESPP_Value"]
        + combined_df["Self_Value"]
    )

    # Display summary metrics
    st.header("📊 Summary")
    col1, col2, col3, col4 = st.columns(4)

    final_month = projection_months - 1
    with col1:
        st.metric(
            "RSU Portfolio Value",
            format_currency(combined_df["RSU_Value"].iloc[final_month], symbol="€"),
            f"{rsu_df['RSU_Cumulative_Stocks'].iloc[final_month]:.1f} shares",
        )
    with col2:
        st.metric(
            "ESPP Portfolio Value",
            format_currency(combined_df["ESPP_Value"].iloc[final_month], symbol="€"),
            f"{espp_df['ESPP_Cumulative_Stocks'].iloc[final_month]:.1f} shares",
        )
    with col3:
        st.metric(
            "Self-Bought Value",
            format_currency(combined_df["Self_Value"].iloc[final_month], symbol="€"),
            f"{self_df['Self_Cumulative_Stocks'].iloc[final_month]:.1f} shares",
        )
    with col4:
        st.metric(
            "Total Portfolio Value",
            format_currency(combined_df["Total_Value"].iloc[final_month], symbol="€"),
            f"Stock: €{stock_prices_eur[final_month]:.2f}",
        )

    # Visualizations
    st.header("📈 Visualizations")

    # Stock price over time
    st.subheader("Stock Price Over Time")
    fig_price = px.line(
        combined_df,
        x="Month",
        y="Stock_Price",
        title="Stock Price Projection",
        labels={"Stock_Price": "Price (€)", "Month": "Month"},
    )
    fig_price.update_layout(hovermode="x unified")
    st.plotly_chart(fig_price, width="stretch")

    # Portfolio values over time (stacked area)
    st.subheader("Portfolio Value Over Time")
    fig_portfolio = go.Figure()

    fig_portfolio.add_trace(go.Scatter(
        x=combined_df["Month"],
        y=combined_df["RSU_Value"],
        mode="lines",
        name="RSU",
        stackgroup="one",
        fillcolor="rgba(99, 110, 250, 0.5)",
        line=dict(color="rgb(99, 110, 250)"),
    ))
    fig_portfolio.add_trace(go.Scatter(
        x=combined_df["Month"],
        y=combined_df["ESPP_Value"],
        mode="lines",
        name="ESPP",
        stackgroup="one",
        fillcolor="rgba(239, 85, 59, 0.5)",
        line=dict(color="rgb(239, 85, 59)"),
    ))
    fig_portfolio.add_trace(go.Scatter(
        x=combined_df["Month"],
        y=combined_df["Self_Value"],
        mode="lines",
        name="Self-Bought",
        stackgroup="one",
        fillcolor="rgba(0, 204, 150, 0.5)",
        line=dict(color="rgb(0, 204, 150)"),
    ))

    fig_portfolio.update_layout(
        title="Cumulative Portfolio Value by Category",
        xaxis_title="Month",
        yaxis_title="Value (€)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_portfolio, width="stretch")

    # Individual category breakdown
    st.subheader("Category Breakdown")
    tab1, tab2, tab3 = st.tabs(["🎁 RSU", "💼 ESPP", "🛒 Self Buying"])

    with tab1:
        st.markdown("**RSU Plans Summary**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"- **Tax Sell Rule:** floor(vested/2) + 1 stocks sold")
            st.markdown(f"- **Transaction Fee:** ${rsu_transaction_fee:.2f}")
            st.markdown(f"- **Selling Loss:** ${rsu_selling_loss:.2f}")
        with col2:
            st.markdown(f"- **Number of Plans:** {len(rsu_blocks_data)}")
            final_rest = rsu_df["RSU_Cumulative_Rest"].iloc[-1] if len(rsu_df) > 0 else 0
            st.markdown(f"- **Cumulative Rest Amount:** €{final_rest:.2f}")
            # Calculate RSU received wealth ratio
            if len(rsu_df) > 0 and rsu_blocks_data:
                final_stock_value = rsu_df["RSU_Cumulative_Value"].iloc[-1]
                total_granted = sum(b["total_stocks"] for b in rsu_blocks_data)
                final_stock_price_eur = stock_prices[-1] * usd_to_eur
                granted_value = total_granted * final_stock_price_eur
                total_wealth = final_stock_value + final_rest
                wealth_ratio = (total_wealth / granted_value * 100) if granted_value > 0 else 0
                st.markdown(
                    f"- **RSU Received Wealth Ratio:** {wealth_ratio:.1f}% "
                    f"*(= (stock value + rest) / granted value)*"
                )

        for idx, block_data in enumerate(rsu_blocks_data):
            delay_info = f", {block_data['delay_months']}m delay" if block_data['delay_months'] > 0 else ""
            st.markdown(f"**Plan {idx + 1}:** {block_data['total_stocks']:,} stocks, "
                        f"start month {block_data['start_offset']}, "
                        f"{block_data['vesting_period']}m vesting{delay_info}")

        # RSU vesting events
        vest_events = rsu_df[rsu_df["RSU_Stocks_Vested"] > 0][
            ["Month", "RSU_Stocks_Vested", "RSU_Stocks_Sold", "RSU_Stocks_Kept",
             "RSU_Tax_Due", "RSU_Sale_Proceeds", "RSU_Rest_Amount", "RSU_Value"]
        ].copy()
        vest_events.columns = ["Month", "Vested", "Sold", "Kept",
                               "Tax Due (€)", "Sale Proceeds (€)", "Rest (€)", "Value (€)"]
        if not vest_events.empty:
            st.dataframe(vest_events, width="stretch")

    with tab2:
        st.markdown("**ESPP Purchase Schedule**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"- **Gross Income:** {format_currency(espp_gross_income)}")
            st.markdown(f"- **Contribution Rate:** {espp_contribution * 100:.1f}%")
        with col2:
            monthly_contrib = espp_gross_income * espp_contribution
            st.markdown(f"- **Monthly Contribution:** {format_currency(monthly_contrib)}")
            st.markdown(f"- **ESPP Discount:** {espp_discount * 100:.0f}%")

        # ESPP purchase events
        espp_events = espp_df[espp_df["ESPP_Stocks_Bought"] > 0][
            ["Month", "ESPP_Stocks_Bought", "ESPP_Value"]
        ].copy()
        espp_events.columns = ["Month", "Stocks Bought", "Value at Purchase"]
        if not espp_events.empty:
            st.dataframe(espp_events, width="stretch")

    with tab3:
        st.markdown("**Self Buying Summary**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"- **Net Income:** {format_currency(self_net_income)}")
            if is_percentage:
                st.markdown(f"- **Investment Rate:** {self_investment:.1f}%")
            else:
                st.markdown(f"- **Fixed Investment:** {format_currency(self_investment)}")
        with col2:
            if is_percentage:
                monthly_inv = self_net_income * (self_investment / 100)
            else:
                monthly_inv = self_investment
            st.markdown(f"- **Monthly Investment:** {format_currency(monthly_inv)}")
            total_invested = monthly_inv * projection_months
            st.markdown(f"- **Total Invested:** {format_currency(total_invested)}")

    # Raw data
    if st.checkbox("Show Raw Data"):
        st.subheader("Combined Data")
        display_df = combined_df.copy()
        for col in ["Stock_Price", "RSU_Value", "ESPP_Value", "Self_Value", "Total_Value"]:
            display_df[col] = display_df[col].apply(lambda x: f"€{x:,.2f}")
        st.dataframe(display_df, width="stretch")


if __name__ == "__main__":
    main()
