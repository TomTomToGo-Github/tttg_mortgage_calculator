import streamlit as st
import plotly.express as px

from formatting import format_currency, format_number, parse_formatted_number
from mortgage import calculate_amortization, calculate_mortgage
from net_worth import calculate_net_worth


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


def main() -> None:
    """Run the Streamlit mortgage and net worth calculator app."""
    st.set_page_config(
        page_title="Mortgage and Net Worth Calculator",
        layout="wide",
    )
    st.title("🏠 Mortgage and Net Worth Projection")

    # ------------------------------------------------------------------ Sidebar
    with st.sidebar:
        st.header("Financial Inputs")

        # Income
        st.subheader("💰 Monthly Income")
        col1, col2 = st.columns(2)
        with col1:
            income1 = currency_input("Primary Income (Net)", 3000.0, "income1")
        with col2:
            income2 = currency_input("Secondary Income (Net)", 1200.0, "income2")
        stock_income = currency_input(
            "Monthly Stock/Dividend Income", 600.0, "stock_income"
        )

        # Expenses
        st.subheader("💸 Expenses")
        monthly_expenses = currency_input(
            "Monthly Expenses", 1000.0, "monthly_expenses"
        )

        # Savings & Investments
        st.subheader("💼 Savings & Investments")
        initial_net_worth = currency_input(
            "Initial Net Worth", 50000.0, "initial_net_worth"
        )
        investment_return = st.number_input(
            "Expected Annual Investment Return (%)",
            min_value=0.0,
            value=3.0,
            step=0.1,
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
            value=2.5,
            step=0.1,
        )
        loan_term = st.number_input(
            "Loan Term (years)",
            min_value=1,
            max_value=40,
            value=30,
            step=1,
        )

        # Assumptions
        st.subheader("📈 Assumptions")
        home_appreciation = st.number_input(
            "Annual Home Appreciation (%)",
            min_value=-10.0,
            value=2.0,
            step=0.5,
        )
        projection_years = st.number_input(
            "Projection Years",
            min_value=1,
            max_value=50,
            value=30,
            step=1,
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
        initial_net_worth=initial_net_worth,
        monthly_income1=income1,
        monthly_income2=income2,
        stock_income=stock_income,
        monthly_expenses=monthly_expenses,
        years=projection_years,
        property_value=property_value,
        home_appreciation_rate=home_appreciation,
        investment_return_rate=investment_return,
        mortgage_rate=interest_rate,
        mortgage_years=loan_term,
        down_payment=down_payment,
    )

    # Add Year column for charting
    net_worth_df["Year"] = net_worth_df["Month"] / 12

    # ------------------------------------------------------------------- Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Monthly Mortgage Payment",
            format_currency(monthly_payment),
        )
    with col2:
        total_interest = amortization_schedule["Interest Payment"].sum()
        st.metric("Total Interest Paid", format_currency(total_interest))
    with col3:
        final_net_worth = net_worth_df["Net Worth"].iloc[-1]
        st.metric(
            f"Projected Net Worth in {projection_years} Years",
            format_currency(final_net_worth),
        )

    # -------------------------------------------------------------------- Charts
    st.subheader("Net Worth Projection")
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

    st.subheader("Wealth Composition")
    fig2 = px.area(
        net_worth_df,
        x="Year",
        y=["Liquid Assets", "Home Equity"],
        title="Wealth Composition Over Time",
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
            "Liquid Assets",
            "Home Equity",
            "Home Value",
            "Mortgage Balance",
        ]
        for col in numeric_cols:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(
                    lambda x: format_currency(x)
                )
        st.dataframe(display_df)


if __name__ == "__main__":
    main()
