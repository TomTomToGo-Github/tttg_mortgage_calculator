"""Stock Estimator page for RSU, ESPP, and self-buying calculations."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.formatting import format_currency, format_number


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
    num_vesting_intervals: int,
    stock_prices: list[float],
    tax_sell_ratio: float = 0.5,
    start_offset: int = 0,
) -> pd.DataFrame:
    """Calculate RSU vesting schedule.

    Parameters
    ----------
    total_stocks : int
        Total number of RSU stocks granted.
    vesting_period_months : int
        Total vesting period in months.
    num_vesting_intervals : int
        Number of vesting events.
    stock_prices : list[float]
        Stock prices for each month.
    tax_sell_ratio : float
        Ratio of stocks sold for tax (default 0.5 + buffer).
    start_offset : int
        Number of months from now when RSU grant starts.

    Returns
    -------
    pd.DataFrame
        DataFrame with monthly RSU values.
    """
    months = len(stock_prices)
    data = {
        "Month": list(range(1, months + 1)),
        "RSU_Stocks_Vested": [0.0] * months,
        "RSU_Stocks_Kept": [0.0] * months,
        "RSU_Value": [0.0] * months,
        "RSU_Cumulative_Stocks": [0.0] * months,
        "RSU_Cumulative_Value": [0.0] * months,
    }

    if num_vesting_intervals <= 0 or vesting_period_months <= 0:
        return pd.DataFrame(data)

    stocks_per_vest = total_stocks / num_vesting_intervals
    interval_months = vesting_period_months / num_vesting_intervals

    cumulative_stocks = 0.0

    for i in range(num_vesting_intervals):
        # Vest at end of each interval, 0-indexed
        # E.g., interval 1 of 4 over 48 months = month 12 = index 11
        vest_month_1indexed = start_offset + int((i + 1) * interval_months)
        vest_index = vest_month_1indexed - 1
        if 0 <= vest_index < months:
            stocks_kept = stocks_per_vest * (1 - tax_sell_ratio)
            data["RSU_Stocks_Vested"][vest_index] = stocks_per_vest
            data["RSU_Stocks_Kept"][vest_index] = stocks_kept
            data["RSU_Value"][vest_index] = stocks_kept * stock_prices[vest_index]

    # Calculate cumulative values
    for month in range(months):
        cumulative_stocks += data["RSU_Stocks_Kept"][month]
        data["RSU_Cumulative_Stocks"][month] = cumulative_stocks
        data["RSU_Cumulative_Value"][month] = cumulative_stocks * stock_prices[month]

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
    st.title("📈 Stock Estimator")

    # Sidebar inputs
    with st.sidebar:
        st.header("Stock Settings")

        st.subheader("📊 Stock Price")
        stock_start_price = st.number_input(
            "Starting Stock Price ($)",
            min_value=0.01,
            value=100.0,
            step=1.0,
            key="stock_start_price",
        )
        yearly_growth_rate = st.number_input(
            "Yearly Growth Rate (%)",
            min_value=-50.0,
            max_value=100.0,
            value=10.0,
            step=1.0,
            key="yearly_growth_rate",
        ) / 100

        st.markdown("**Projection Period**")
        col_years, col_months = st.columns(2)
        with col_years:
            projection_years = st.number_input(
                "Years",
                min_value=0,
                max_value=10,
                value=4,
                step=1,
                key="projection_years",
            )
        with col_months:
            projection_extra_months = st.number_input(
                "Months",
                min_value=0,
                max_value=11,
                value=0,
                step=1,
                key="projection_extra_months",
            )
        projection_months = (projection_years * 12) + projection_extra_months
        if projection_months < 1:
            projection_months = 1

        st.divider()

        # RSU Settings - Multiple blocks
        st.subheader("🎁 RSU (Restricted Stock Units)")

        # Global tax ratio for all RSU plans
        rsu_tax_ratio = st.number_input(
            "Tax + Fees Sell Ratio (%)",
            min_value=0.0,
            max_value=100.0,
            value=50.0,
            step=1.0,
            key="rsu_tax_ratio",
            help="Applied to all RSU plans",
        ) / 100

        # Initialize RSU blocks in session state
        if "rsu_blocks" not in st.session_state:
            st.session_state["rsu_blocks"] = [
                {
                    "total_stocks": 1000,
                    "start_offset": 0,
                    "vest_months": 48,
                    "intervals": 4,
                }
            ]

        # Render each RSU block
        blocks_to_remove = []
        rsu_blocks_data = []

        for i, block in enumerate(st.session_state["rsu_blocks"]):
            with st.container():
                col_title, col_del = st.columns([5, 1])
                with col_title:
                    st.markdown(f"**Plan {i + 1}**")
                with col_del:
                    if st.button("🗑️", key=f"rsu_delete_{i}", help="Delete"):
                        blocks_to_remove.append(i)

                # All fields in one row: Stocks, Start, Vest, Intervals
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
                        "Vesting period (M)",
                        min_value=1,
                        value=block["vest_months"],
                        step=1,
                        key=f"rsu_vest_m_{i}",
                    )
                with c4:
                    block["intervals"] = st.number_input(
                        "Intervals",
                        min_value=1,
                        max_value=48,
                        value=block["intervals"],
                        step=1,
                        key=f"rsu_intervals_{i}",
                    )

                vesting_period = block["vest_months"]

                rsu_blocks_data.append({
                    "total_stocks": block["total_stocks"],
                    "start_offset": block["start_offset"],
                    "vesting_period": vesting_period,
                    "intervals": block["intervals"],
                    "tax_ratio": rsu_tax_ratio,
                })

                if i < len(st.session_state["rsu_blocks"]) - 1:
                    st.markdown("---")

        # Handle deletions
        for idx in reversed(blocks_to_remove):
            st.session_state["rsu_blocks"].pop(idx)
            st.rerun()

        # Add new RSU block button
        if st.button("➕ Add RSU Plan", key="add_rsu_block"):
            st.session_state["rsu_blocks"].append({
                "total_stocks": 1000,
                "start_offset": 0,
                "vest_months": 48,
                "intervals": 4,
            })
            st.rerun()

        st.divider()

        # ESPP Settings
        st.subheader("💼 ESPP (Employee Stock Purchase Plan)")
        c1, c2 = st.columns(2)
        with c1:
            espp_gross_income = st.number_input(
                "Monthly Gross Income (€)",
                min_value=0.0,
                value=5000.0,
                step=100.0,
                key="espp_gross_income",
            )
        with c2:
            espp_contribution = st.number_input(
                "Contribution Rate (%)",
                min_value=0.0,
                max_value=15.0,
                value=10.0,
                step=1.0,
                key="espp_contribution",
                help="Percentage of gross income contributed to ESPP",
            ) / 100

        c1, c2, c3 = st.columns(3)
        with c1:
            espp_start_offset = st.number_input(
                "Start (m from now)",
                min_value=0,
                value=0,
                step=1,
                key="espp_start_offset",
            )
        with c2:
            espp_vesting_interval = st.number_input(
                "Vesting interval (M)",
                min_value=1,
                max_value=12,
                value=6,
                step=1,
                key="espp_vesting_interval",
            )
        with c3:
            espp_discount = st.number_input(
                "Discount (%)",
                min_value=0.0,
                max_value=50.0,
                value=15.0,
                step=1.0,
                key="espp_discount",
            ) / 100

        st.divider()

        # Self Buying Settings
        st.subheader("🛒 Self Buying")
        self_net_income = st.number_input(
            "Monthly Net Income (€)",
            min_value=0.0,
            value=3500.0,
            step=100.0,
            key="self_net_income",
        )
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
                value=10.0,
                step=1.0,
                key="self_investment_pct",
            )
            is_percentage = True
        else:
            self_investment = st.number_input(
                "Investment Amount (€)",
                min_value=0.0,
                value=350.0,
                step=50.0,
                key="self_investment_amt",
            )
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
            block_data["intervals"],
            stock_prices,
            block_data["tax_ratio"],
            block_data["start_offset"],
        )
        rsu_dfs.append(block_df)

    # Combine all RSU blocks
    if rsu_dfs:
        rsu_df = rsu_dfs[0].copy()
        for df in rsu_dfs[1:]:
            rsu_df["RSU_Stocks_Vested"] += df["RSU_Stocks_Vested"]
            rsu_df["RSU_Stocks_Kept"] += df["RSU_Stocks_Kept"]
            rsu_df["RSU_Value"] += df["RSU_Value"]
            rsu_df["RSU_Cumulative_Stocks"] += df["RSU_Cumulative_Stocks"]
            rsu_df["RSU_Cumulative_Value"] += df["RSU_Cumulative_Value"]
    else:
        rsu_df = pd.DataFrame({
            "Month": list(range(projection_months)),
            "RSU_Stocks_Vested": [0.0] * projection_months,
            "RSU_Stocks_Kept": [0.0] * projection_months,
            "RSU_Value": [0.0] * projection_months,
            "RSU_Cumulative_Stocks": [0.0] * projection_months,
            "RSU_Cumulative_Value": [0.0] * projection_months,
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

    # Combine data for visualization
    combined_df = pd.DataFrame({
        "Month": list(range(1, projection_months + 1)),
        "Stock_Price": stock_prices,
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
            format_currency(combined_df["RSU_Value"].iloc[final_month], symbol="$"),
            f"{rsu_df['RSU_Cumulative_Stocks'].iloc[final_month]:.1f} shares",
        )
    with col2:
        st.metric(
            "ESPP Portfolio Value",
            format_currency(combined_df["ESPP_Value"].iloc[final_month], symbol="$"),
            f"{espp_df['ESPP_Cumulative_Stocks'].iloc[final_month]:.1f} shares",
        )
    with col3:
        st.metric(
            "Self-Bought Value",
            format_currency(combined_df["Self_Value"].iloc[final_month], symbol="$"),
            f"{self_df['Self_Cumulative_Stocks'].iloc[final_month]:.1f} shares",
        )
    with col4:
        st.metric(
            "Total Portfolio Value",
            format_currency(combined_df["Total_Value"].iloc[final_month], symbol="$"),
            f"Stock: ${stock_prices[final_month]:.2f}",
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
        labels={"Stock_Price": "Price ($)", "Month": "Month"},
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
        yaxis_title="Value ($)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_portfolio, width="stretch")

    # Individual category breakdown
    st.subheader("Category Breakdown")
    tab1, tab2, tab3 = st.tabs(["🎁 RSU", "💼 ESPP", "🛒 Self Buying"])

    with tab1:
        st.markdown("**RSU Plans Summary**")
        st.markdown(f"- **Tax/Fees Ratio:** {rsu_tax_ratio * 100:.0f}%")
        st.markdown(f"- **Number of Plans:** {len(rsu_blocks_data)}")

        for idx, block_data in enumerate(rsu_blocks_data):
            st.markdown(f"**Plan {idx + 1}:** {block_data['total_stocks']:,} stocks, "
                        f"start month {block_data['start_offset']}, "
                        f"{block_data['vesting_period']}m vesting, "
                        f"{block_data['intervals']} intervals")

        # RSU vesting events
        vest_events = rsu_df[rsu_df["RSU_Stocks_Vested"] > 0][
            ["Month", "RSU_Stocks_Vested", "RSU_Stocks_Kept", "RSU_Value"]
        ].copy()
        vest_events.columns = ["Month", "Stocks Vested", "Stocks Kept", "Value at Vest"]
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
            display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")
        st.dataframe(display_df, width="stretch")


if __name__ == "__main__":
    main()
