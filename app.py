import streamlit as st


# Redirect to Overview page
overview_page = st.Page("pages/overview.py", title="Overview", icon="💰", default=True)
wealth_page = st.Page("pages/wealth_calculator.py", title="Wealth Calculator", icon="🏠")
income_page = st.Page("pages/income_expenses.py", title="Income & Expenses", icon="💰")

pg = st.navigation([overview_page, income_page, wealth_page])
pg.run()
