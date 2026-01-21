import streamlit as st


# Page definitions
overview_page = st.Page("pages/overview.py", title="Overview", icon="💰", default=True)
income_page = st.Page("pages/income_expenses.py", title="Income & Expenses", icon="💰")
stock_page = st.Page("pages/stock_estimator.py", title="Stock Estimator", icon="📈")
wealth_page = st.Page("pages/wealth_calculator.py", title="Wealth Calculator", icon="🏠")

pg = st.navigation([overview_page, income_page, stock_page, wealth_page])
pg.run()
