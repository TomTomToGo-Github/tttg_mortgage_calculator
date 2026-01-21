import streamlit as st


st.set_page_config(
    page_title="Financial Calculator",
    page_icon="💰",
    layout="wide",
)

st.title("💰 Financial Calculator")
st.markdown("""
Welcome to the Financial Calculator app!

Use the sidebar to navigate between pages:

- **🏠 Mortgage Calculator**: Project mortgage payments and net worth over time
- **💰 Income & Expenses**: Track and visualize your income and expense streams
""")
