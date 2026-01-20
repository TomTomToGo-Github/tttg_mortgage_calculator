import streamlit as st
import plotly.express as px

from formatting import format_currency, format_number, parse_formatted_number
from income import convert_usd_to_eur
from mortgage import (
    calculate_amortization,
    calculate_mortgage,
    calculate_property_from_payment,
)
from net_worth import calculate_net_worth


# Default values for all inputs
CURRENCY_DEFAULTS = {
    "income1": 3000.0,
    "income2": 1200.0,
    "stock_income_usd": 600.0,
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
    "usd_eur_rate": 0.01,  # min_value constraint
    "transaction_fee": 0.0,
    "bank_return": 0.0,
    "stock_growth": 0.0,
    "bank_reserve_ratio": 0.0,
    "interest_rate": 0.1,  # min_value constraint
    "loan_term": 1,  # min_value constraint
    "home_appreciation": 0.0,
    "projection_years": 1,  # min_value constraint
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

    text_value = st.text_input(label, value=st.session_state[key], key=f"{key}_input")
    parsed = parse_formatted_number(text_value, default)

    # Update session state with formatted value for consistency
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


def main() -> None:
    """Run the Streamlit mortgage and net worth calculator app."""
    st.set_page_config(
        page_title="Mortgage and Net Worth Calculator",
        layout="wide",
    )
    st.title("🏠 Mortgage and Net Worth Projection")

    # Initialize session state for number inputs
    init_session_state()

    # Check if buffer was breached in previous run (for styling)
    buffer_breach = st.session_state.get("buffer_breach", False)

    # Inject warning CSS if buffer is breached
    if buffer_breach:
        st.markdown(get_warning_css(True), unsafe_allow_html=True)

    # ------------------------------------------------------------------ Sidebar
    with st.sidebar:
        st.header("Financial Inputs")

        # Zero and Reset buttons
        col1, col2 = st.columns(2)
        with col1:
            st.button("🔄 Reset", on_click=reset_all_fields, use_container_width=True)
        with col2:
            st.button("0️⃣ Zero", on_click=zero_all_fields, use_container_width=True)

        st.divider()

        # Income
        st.subheader("💰 Monthly Income")
        col1, col2 = st.columns(2)
        with col1:
            income1 = currency_input("Primary Income (Net)", 3000.0, "income1")
        with col2:
            income2 = currency_input("Secondary Income (Net)", 1200.0, "income2")

        # Stock income with USD to EUR conversion
        st.markdown("**Stock/Dividend Income (USD → EUR)**")
        stock_income_usd = currency_input(
            "Monthly Stock Income (USD)", 600.0, "stock_income_usd"
        )
        col1, col2 = st.columns(2)
        with col1:
            usd_eur_rate = st.number_input(
                "USD/EUR Rate",
                min_value=0.01,
                step=0.01,
                format="%.4f",
                key="usd_eur_rate",
            )
        with col2:
            transaction_fee = st.number_input(
                "Monthly Fee (€)",
                min_value=0.0,
                step=1.0,
                key="transaction_fee",
            )
        stock_income = convert_usd_to_eur(
            stock_income_usd, usd_eur_rate, transaction_fee
        )
        reinvest_dividends = st.checkbox(
            "Keep income in stocks",
            value=True,
            help="If checked, stock income goes directly to stock portfolio. "
                 "Otherwise treated as regular income (affected by savings ratio).",
        )
        st.caption(f"Net stock income: {format_currency(stock_income)}")

        # Expenses
        st.subheader("💸 Expenses")
        monthly_expenses = currency_input(
            "Monthly Expenses", 1000.0, "monthly_expenses"
        )

        # Savings & Investments
        st.subheader("💼 Savings & Investments")
        initial_bank_balance = currency_input(
            "Initial Bank Balance", 50000.0, "initial_bank_balance"
        )
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
        financial_buffer = currency_input(
            "Financial Buffer (Min Bank Reserve)", 10000.0, "financial_buffer"
        )

        # Property & Mortgage
        st.subheader("🏡 Property & Mortgage")
        property_value = currency_input(
            "Property Value", 800000.0, "property_value"
        )
        down_payment = currency_input("Down Payment", 200000.0, "down_payment")
        interest_rate = st.number_input(
            "Annual Interest Rate (%)",
            min_value=0.1,
            step=0.1,
            key="interest_rate",
        )
        loan_term = st.number_input(
            "Loan Term (years)",
            min_value=1,
            max_value=40,
            step=1,
            key="loan_term",
        )

        # Calculate and display monthly mortgage payment
        calc_monthly_payment = calculate_mortgage(
            property_value, interest_rate, loan_term, down_payment
        )

        # Initialize monthly payment in session state if needed
        if "monthly_payment" not in st.session_state:
            st.session_state["monthly_payment"] = format_number(calc_monthly_payment)

        # Check if property/mortgage inputs changed - update payment display
        if "last_calc_payment" not in st.session_state:
            st.session_state["last_calc_payment"] = calc_monthly_payment
        if abs(calc_monthly_payment - st.session_state["last_calc_payment"]) > 0.01:
            st.session_state["monthly_payment"] = format_number(calc_monthly_payment)
            st.session_state["last_calc_payment"] = calc_monthly_payment

        # Monthly payment input
        st.markdown("**Monthly Mortgage Payment**")
        payment_text = st.text_input(
            "Monthly Payment",
            value=st.session_state["monthly_payment"],
            key="monthly_payment_input",
            help="Edit to adjust property value to meet this payment",
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

        # Assumptions
        st.subheader("📈 Assumptions")
        home_appreciation = st.number_input(
            "Annual Home Appreciation (%)",
            min_value=-10.0,
            step=0.5,
            key="home_appreciation",
        )
        projection_years = st.number_input(
            "Projection Years",
            min_value=1,
            max_value=50,
            step=1,
            key="projection_years",
        )

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
    st.plotly_chart(fig_liquid, use_container_width=True)

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
    st.plotly_chart(fig_mortgage, use_container_width=True)

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
    st.plotly_chart(fig_property, use_container_width=True)

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
    st.plotly_chart(fig, use_container_width=True)

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
    st.plotly_chart(fig2, use_container_width=True)

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


if __name__ == "__main__":
    main()
