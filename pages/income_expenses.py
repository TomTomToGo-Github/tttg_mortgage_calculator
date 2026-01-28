import json
import os

import streamlit as st
import pandas as pd
import plotly.express as px

from src.formatting import format_currency, format_number, parse_formatted_number


SETTINGS_DIR = os.path.join("saved_settings", "income_expenses")


def get_saved_settings() -> list[str]:
    """Get list of saved settings files.

    Returns
    -------
    list[str]
        List of saved setting names (without .json extension).
    """
    if not os.path.exists(SETTINGS_DIR):
        return []
    files = [f[:-5] for f in os.listdir(SETTINGS_DIR) if f.endswith(".json")]
    return sorted(files)


def save_settings(name: str) -> None:
    """Save current settings to a JSON file.

    Parameters
    ----------
    name : str
        Name for the settings file.
    """
    if not name:
        return

    os.makedirs(SETTINGS_DIR, exist_ok=True)

    settings = {
        "income_monthly_items": st.session_state.get("income_monthly_items", []),
        "income_yearly_items": st.session_state.get("income_yearly_items", []),
        "expense_monthly_items": st.session_state.get("expense_monthly_items", []),
        "expense_yearly_items": st.session_state.get("expense_yearly_items", []),
        "calc_mode": st.session_state.get("calc_mode", "separate"),
    }

    # Remove internal tracking keys from items
    for key in ["income_monthly_items", "expense_monthly_items"]:
        settings[key] = [
            {k: v for k, v in item.items() if k != "original_yearly"}
            for item in settings[key]
        ]

    filepath = os.path.join(SETTINGS_DIR, f"{name}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def load_settings(name: str) -> None:
    """Load settings from a JSON file.

    Parameters
    ----------
    name : str
        Name of the settings file to load.
    """
    if not name:
        return

    filepath = os.path.join(SETTINGS_DIR, f"{name}.json")
    if not os.path.exists(filepath):
        return

    with open(filepath, "r", encoding="utf-8") as f:
        settings = json.load(f)

    st.session_state["income_monthly_items"] = settings.get(
        "income_monthly_items", []
    )
    st.session_state["income_yearly_items"] = settings.get(
        "income_yearly_items", []
    )
    st.session_state["expense_monthly_items"] = settings.get(
        "expense_monthly_items", []
    )
    st.session_state["expense_yearly_items"] = settings.get(
        "expense_yearly_items", []
    )
    st.session_state["calc_mode"] = settings.get("calc_mode", "separate")


def delete_settings(name: str) -> None:
    """Delete a saved settings file.

    Parameters
    ----------
    name : str
        Name of the settings file to delete.
    """
    if not name:
        return

    filepath = os.path.join(SETTINGS_DIR, f"{name}.json")
    if os.path.exists(filepath):
        os.remove(filepath)


# Initialize session state for income and expenses
def init_finance_state() -> None:
    """Initialize session state for income and expense tracking."""
    if "income_monthly_items" not in st.session_state:
        st.session_state["income_monthly_items"] = [
            {"name": "Primary Salary", "amount": 3000.0},
            {"name": "Secondary Salary", "amount": 1200.0},
        ]
    if "income_yearly_items" not in st.session_state:
        st.session_state["income_yearly_items"] = [
            {"name": "Bonus", "amount": 5000.0},
            {"name": "Tax Return", "amount": 1200.0},
        ]
    if "expense_monthly_items" not in st.session_state:
        st.session_state["expense_monthly_items"] = [
            {"name": "Rent/Mortgage", "amount": 1500.0},
            {"name": "Groceries", "amount": 400.0},
            {"name": "Utilities", "amount": 150.0},
            {"name": "Transport", "amount": 100.0},
        ]
    if "expense_yearly_items" not in st.session_state:
        st.session_state["expense_yearly_items"] = [
            {"name": "Insurance", "amount": 1200.0},
            {"name": "Vacation", "amount": 3000.0},
        ]


def add_item(category: str) -> None:
    """Add a new item to the specified category.

    Parameters
    ----------
    category : str
        The session state key for the category list.
    """
    st.session_state[category].append({"name": "New Item", "amount": 0.0})


def remove_item(category: str, index: int) -> None:
    """Remove an item from the specified category.

    Parameters
    ----------
    category : str
        The session state key for the category list.
    index : int
        Index of the item to remove.
    """
    if len(st.session_state[category]) > 0:
        st.session_state[category].pop(index)


def render_item_list(
    category: str,
    title: str,
    emoji: str,
    is_income: bool = True,
    is_yearly: bool = False,
) -> float:
    """Render an editable list of income/expense items.

    Parameters
    ----------
    category : str
        The session state key for the category list.
    title : str
        Display title for the section.
    emoji : str
        Emoji to display with the title.
    is_income : bool
        True for income items (green), False for expense items (red).
    is_yearly : bool
        True for yearly items, False for monthly items.

    Returns
    -------
    float
        Total amount for this category.
    """
    # Color based on income/expense (only for totals, not subheaders)
    color = "#228B22" if is_income else "#DC143C"  # Dark green / Crimson red

    # Subheader in normal black font
    st.subheader(f"{emoji} {title}")

    total = 0.0
    items_to_remove = []
    items_to_toggle = []

    for i, item in enumerate(st.session_state[category]):
        is_hidden = item.get("hidden", False)
        col1, col2, col3, col4 = st.columns([3, 2, 0.4, 0.4])

        with col1:
            if is_hidden:
                st.markdown(
                    f"<span style='color: #999; font-style: italic;'>"
                    f"{item['name']}</span>",
                    unsafe_allow_html=True,
                )
            else:
                new_name = st.text_input(
                    "Name",
                    value=item["name"],
                    key=f"{category}_name_{i}",
                    label_visibility="collapsed",
                )
                st.session_state[category][i]["name"] = new_name

        with col2:
            if is_hidden:
                st.markdown(
                    f"<span style='color: #999; font-style: italic;'>"
                    f"{format_number(item['amount'])}</span>",
                    unsafe_allow_html=True,
                )
            else:
                amount_str = st.text_input(
                    "Amount",
                    value=format_number(item["amount"]),
                    key=f"{category}_amount_{i}",
                    label_visibility="collapsed",
                )
                new_amount = parse_formatted_number(amount_str, item["amount"])
                st.session_state[category][i]["amount"] = new_amount

        # Only add to total if not hidden
        if not is_hidden:
            total += item["amount"]

        with col3:
            # Eye icon: 👁️ for visible, � for hidden
            eye_icon = "🙈" if is_hidden else "👁️"
            eye_help = "Show" if is_hidden else "Hide"
            if st.button(eye_icon, key=f"{category}_toggle_{i}", help=eye_help):
                items_to_toggle.append(i)

        with col4:
            if st.button("🗑️", key=f"{category}_remove_{i}", help="Delete"):
                items_to_remove.append(i)

    # Toggle hidden state
    for idx in items_to_toggle:
        current_hidden = st.session_state[category][idx].get("hidden", False)
        st.session_state[category][idx]["hidden"] = not current_hidden
        st.rerun()

    # Remove items after iteration
    for idx in reversed(items_to_remove):
        st.session_state[category].pop(idx)
        st.rerun()

    col1, col2 = st.columns([3, 1])
    with col1:
        # Show total and the equivalent in the other period
        if is_yearly:
            monthly_equiv = total / 12
            st.markdown(
                f"<span style='color: {color};'>**Total: {format_currency(total)}**</span>"
                f"<br><span style='color: {color}; font-size: 0.9em;'>"
                f"(Monthly: {format_currency(monthly_equiv)})</span>",
                unsafe_allow_html=True,
            )
        else:
            yearly_equiv = total * 12
            st.markdown(
                f"<span style='color: {color};'>**Total: {format_currency(total)}**</span>"
                f"<br><span style='color: {color}; font-size: 0.9em;'>"
                f"(Yearly: {format_currency(yearly_equiv)})</span>",
                unsafe_allow_html=True,
            )
    with col2:
        if st.button("➕ Add", key=f"{category}_add"):
            add_item(category)
            st.rerun()

    return total


def clear_item_widget_keys() -> None:
    """Clear widget keys for item lists to force refresh."""
    keys_to_remove = [
        key for key in st.session_state.keys()
        if any(key.startswith(prefix) for prefix in [
            "income_monthly_items_name_",
            "income_monthly_items_amount_",
            "income_yearly_items_name_",
            "income_yearly_items_amount_",
            "expense_monthly_items_name_",
            "expense_monthly_items_amount_",
            "expense_yearly_items_name_",
            "expense_yearly_items_amount_",
        ])
    ]
    for key in keys_to_remove:
        del st.session_state[key]


def toggle_calculation_mode() -> None:
    """Toggle between monthly and yearly calculation modes."""
    if st.session_state.get("calc_mode", "separate") == "separate":
        # Convert yearly items to monthly by dividing by 12
        for item in st.session_state["income_yearly_items"]:
            monthly_amount = item["amount"] / 12
            st.session_state["income_monthly_items"].append({
                "name": f"{item['name']} (yearly/12)",
                "amount": monthly_amount,
                "original_yearly": item["amount"],
                "original_name": item["name"],
                "hidden": item.get("hidden", False),
            })

        for item in st.session_state["expense_yearly_items"]:
            monthly_amount = item["amount"] / 12
            st.session_state["expense_monthly_items"].append({
                "name": f"{item['name']} (yearly/12)",
                "amount": monthly_amount,
                "original_yearly": item["amount"],
                "original_name": item["name"],
                "hidden": item.get("hidden", False),
            })

        # Clear yearly items (they are now in monthly)
        st.session_state["income_yearly_items"] = []
        st.session_state["expense_yearly_items"] = []

        st.session_state["calc_mode"] = "monthly"
    else:
        # Move converted items back to yearly
        for item in st.session_state["income_monthly_items"]:
            if "original_yearly" in item:
                st.session_state["income_yearly_items"].append({
                    "name": item["original_name"],
                    "amount": item["amount"] * 12,
                    "hidden": item.get("hidden", False),
                })

        for item in st.session_state["expense_monthly_items"]:
            if "original_yearly" in item:
                st.session_state["expense_yearly_items"].append({
                    "name": item["original_name"],
                    "amount": item["amount"] * 12,
                    "hidden": item.get("hidden", False),
                })

        # Remove converted items from monthly
        st.session_state["income_monthly_items"] = [
            item for item in st.session_state["income_monthly_items"]
            if "original_yearly" not in item
        ]
        st.session_state["expense_monthly_items"] = [
            item for item in st.session_state["expense_monthly_items"]
            if "original_yearly" not in item
        ]

        st.session_state["calc_mode"] = "separate"

    # Clear widget keys to force UI refresh
    clear_item_widget_keys()


def main() -> None:
    """Run the Income & Expenses page."""
    st.set_page_config(
        page_title="Income & Expenses",
        page_icon="💰",
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

    st.title("💰 Income & Expenses Tracker")

    init_finance_state()

    # Settings management in sidebar
    with st.sidebar:
        st.header("Settings")

        # Load settings dropdown
        saved_settings = get_saved_settings()
        if saved_settings:
            selected_setting = st.selectbox(
                "Load Settings",
                options=[""] + saved_settings,
                format_func=lambda x: "Select..." if x == "" else x,
                key="selected_setting",
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Load", disabled=not selected_setting):
                    load_settings(selected_setting)
                    st.rerun()
            with col2:
                if st.button("Delete", disabled=not selected_setting):
                    delete_settings(selected_setting)
                    st.rerun()
        else:
            st.caption("No saved settings yet")

        st.divider()

        # Save settings
        new_setting_name = st.text_input(
            "Save Current Settings As",
            placeholder="Enter name...",
            key="new_setting_name",
        )
        if st.button("Save", disabled=not new_setting_name):
            save_settings(new_setting_name)
            st.success(f"Saved as '{new_setting_name}'")
            st.rerun()

    # Toggle button for calculation mode
    calc_mode = st.session_state.get("calc_mode", "separate")
    button_label = (
        "📊 Include Yearly in Monthly Calculation" if calc_mode == "separate"
        else "📆 Exclude Yearly from Monthly Calculation"
    )
    button_help = (
        "Divide yearly items by 12 and add to monthly totals"
        if calc_mode == "separate"
        else "Restore yearly items as separate entries"
    )
    st.button(
        button_label,
        on_click=toggle_calculation_mode,
        help=button_help,
        type="primary",
    )

    st.divider()

    # Income section - monthly left, yearly right
    st.markdown(
        "<h2 style='color: #228B22;'>\U0001F4B5 Income</h2>",
        unsafe_allow_html=True,
    )
    col_income_monthly, col_income_yearly = st.columns(2)

    with col_income_monthly:
        monthly_income_total = render_item_list(
            "income_monthly_items",
            "Monthly",
            "\U0001F4B5",
            is_income=True,
        )

    with col_income_yearly:
        yearly_income_total = render_item_list(
            "income_yearly_items",
            "Once a year",
            "\U0001F4B0",
            is_income=True,
            is_yearly=True,
        )

    st.divider()

    # Expenses section - monthly left, yearly right
    st.markdown(
        "<h2 style='color: #DC143C;'>\U0001F4B8 Expenses</h2>",
        unsafe_allow_html=True,
    )
    col_expense_monthly, col_expense_yearly = st.columns(2)

    with col_expense_monthly:
        monthly_expenses_total = render_item_list(
            "expense_monthly_items",
            "Monthly",
            "\U0001F4B8",
            is_income=False,
        )

    with col_expense_yearly:
        yearly_expenses_total = render_item_list(
            "expense_yearly_items",
            "Once a year",
            "\U0001F5D3",
            is_income=False,
            is_yearly=True,
        )

    # Summary section
    st.divider()
    st.header("📊 Summary")

    # Calculate totals directly from session state for accuracy
    calc_mode = st.session_state.get("calc_mode", "separate")

    # Get raw totals from session state (excluding hidden items)
    raw_monthly_income = sum(
        item["amount"] for item in st.session_state["income_monthly_items"]
        if "original_yearly" not in item and not item.get("hidden", False)
    )
    raw_monthly_expenses = sum(
        item["amount"] for item in st.session_state["expense_monthly_items"]
        if "original_yearly" not in item and not item.get("hidden", False)
    )
    converted_yearly_income = sum(
        item["amount"] for item in st.session_state["income_monthly_items"]
        if "original_yearly" in item and not item.get("hidden", False)
    )
    converted_yearly_expenses = sum(
        item["amount"] for item in st.session_state["expense_monthly_items"]
        if "original_yearly" in item and not item.get("hidden", False)
    )
    raw_yearly_income = sum(
        item["amount"] for item in st.session_state["income_yearly_items"]
        if not item.get("hidden", False)
    )
    raw_yearly_expenses = sum(
        item["amount"] for item in st.session_state["expense_yearly_items"]
        if not item.get("hidden", False)
    )

    if calc_mode == "monthly":
        # In monthly mode, yearly items are converted and included in monthly
        total_monthly_income = raw_monthly_income + converted_yearly_income
        total_monthly_expenses = raw_monthly_expenses + converted_yearly_expenses
        total_yearly_income = total_monthly_income * 12
        total_yearly_expenses = total_monthly_expenses * 12
    else:
        # In separate mode, monthly shows ONLY monthly values
        total_monthly_income = raw_monthly_income
        total_monthly_expenses = raw_monthly_expenses
        # Yearly always shows the total (monthly*12 + yearly)
        total_yearly_income = (raw_monthly_income * 12) + raw_yearly_income
        total_yearly_expenses = (raw_monthly_expenses * 12) + raw_yearly_expenses

    monthly_net = total_monthly_income - total_monthly_expenses
    yearly_net = total_yearly_income - total_yearly_expenses

    # Store summary values in session state for cross-page access
    st.session_state["summary_monthly_income"] = total_monthly_income
    st.session_state["summary_monthly_expenses"] = total_monthly_expenses

    # Summary metrics - Monthly on left, separator, Yearly on right
    col_monthly, col_sep, col_yearly = st.columns([10, 1, 10])

    # Title suffix based on mode
    monthly_suffix = (
        " (including 'once a year' items)" if calc_mode == "monthly"
        else " (excluding 'once a year' items)"
    )

    # Colors for income/expenses
    income_color = "#228B22"  # Dark green
    expense_color = "#DC143C"  # Crimson red

    with col_monthly:
        st.subheader(f"Monthly{monthly_suffix}")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(
                f"<p style='font-size: 14px; margin-bottom: 0;'>Income</p>"
                f"<p style='font-size: 24px; font-weight: bold; color: {income_color}; "
                f"margin-top: 0;'>{format_currency(total_monthly_income)}</p>",
                unsafe_allow_html=True,
            )
        with m2:
            st.markdown(
                f"<p style='font-size: 14px; margin-bottom: 0;'>Expenses</p>"
                f"<p style='font-size: 24px; font-weight: bold; color: {expense_color}; "
                f"margin-top: 0;'>{format_currency(total_monthly_expenses)}</p>",
                unsafe_allow_html=True,
            )
        with m3:
            net_color = income_color if monthly_net >= 0 else expense_color
            st.markdown(
                f"<p style='font-size: 14px; margin-bottom: 0;'>Net</p>"
                f"<p style='font-size: 24px; font-weight: bold; color: {net_color}; "
                f"margin-top: 0;'>{format_currency(monthly_net)}</p>",
                unsafe_allow_html=True,
            )
        with m4:
            monthly_savings_rate = (
                (monthly_net / total_monthly_income * 100)
                if total_monthly_income > 0 else 0
            )
            savings_color = income_color if monthly_savings_rate >= 0 else expense_color
            st.markdown(
                f"<p style='font-size: 14px; margin-bottom: 0;'>Savings Rate</p>"
                f"<p style='font-size: 24px; font-weight: bold; color: {savings_color}; "
                f"margin-top: 0;'>{monthly_savings_rate:.1f}%</p>",
                unsafe_allow_html=True,
            )

    with col_sep:
        st.markdown(
            "<div style='border-left: 2px solid #e0e0e0; height: 150px; "
            "margin: 0 auto;'></div>",
            unsafe_allow_html=True,
        )

    with col_yearly:
        st.subheader("Yearly")
        y1, y2, y3, y4 = st.columns(4)
        with y1:
            st.markdown(
                f"<p style='font-size: 14px; margin-bottom: 0;'>Income</p>"
                f"<p style='font-size: 24px; font-weight: bold; color: {income_color}; "
                f"margin-top: 0;'>{format_currency(total_yearly_income)}</p>",
                unsafe_allow_html=True,
            )
        with y2:
            st.markdown(
                f"<p style='font-size: 14px; margin-bottom: 0;'>Expenses</p>"
                f"<p style='font-size: 24px; font-weight: bold; color: {expense_color}; "
                f"margin-top: 0;'>{format_currency(total_yearly_expenses)}</p>",
                unsafe_allow_html=True,
            )
        with y3:
            yearly_net_color = income_color if yearly_net >= 0 else expense_color
            st.markdown(
                f"<p style='font-size: 14px; margin-bottom: 0;'>Net</p>"
                f"<p style='font-size: 24px; font-weight: bold; color: {yearly_net_color}; "
                f"margin-top: 0;'>{format_currency(yearly_net)}</p>",
                unsafe_allow_html=True,
            )
        with y4:
            yearly_savings_rate = (
                (yearly_net / total_yearly_income * 100)
                if total_yearly_income > 0 else 0
            )
            yearly_savings_color = income_color if yearly_savings_rate >= 0 else expense_color
            st.markdown(
                f"<p style='font-size: 14px; margin-bottom: 0;'>Savings Rate</p>"
                f"<p style='font-size: 24px; font-weight: bold; color: {yearly_savings_color}; "
                f"margin-top: 0;'>{yearly_savings_rate:.1f}%</p>",
                unsafe_allow_html=True,
            )

    # Visualizations
    st.divider()
    st.header("📈 Visualizations")

    viz_col1, viz_col2 = st.columns(2)

    with viz_col1:
        # Monthly breakdown pie chart
        st.subheader(f"Monthly Income vs Expenses{monthly_suffix}")
        monthly_data = pd.DataFrame({
            "Category": ["Income", "Expenses"],
            "Amount": [total_monthly_income, total_monthly_expenses],
        })
        fig_monthly = px.pie(
            monthly_data,
            values="Amount",
            names="Category",
            color="Category",
            color_discrete_map={"Income": "#28A745", "Expenses": "#DC3545"},
            hole=0.4,
        )
        fig_monthly.update_traces(textinfo="label+value")
        fig_monthly.update_layout(
            showlegend=False,
            annotations=[{
                "text": f"Net<br>{format_currency(monthly_net)}",
                "x": 0.5,
                "y": 0.5,
                "font_size": 14,
                "showarrow": False,
            }],
        )
        st.plotly_chart(fig_monthly, width="stretch", key="monthly_pie")

    with viz_col2:
        # Yearly breakdown pie chart
        st.subheader("Yearly Income vs Expenses")
        yearly_data = pd.DataFrame({
            "Category": ["Income", "Expenses"],
            "Amount": [total_yearly_income, total_yearly_expenses],
        })
        fig_yearly = px.pie(
            yearly_data,
            values="Amount",
            names="Category",
            color="Category",
            color_discrete_map={"Income": "#28A745", "Expenses": "#DC3545"},
            hole=0.4,
        )
        fig_yearly.update_traces(textinfo="label+value")
        fig_yearly.update_layout(
            showlegend=False,
            annotations=[{
                "text": f"Net<br>{format_currency(yearly_net)}",
                "x": 0.5,
                "y": 0.5,
                "font_size": 14,
                "showarrow": False,
            }],
        )
        st.plotly_chart(fig_yearly, width="stretch", key="yearly_pie")

    # Detailed breakdown bar charts
    st.subheader("Detailed Breakdown")

    breakdown_col1, breakdown_col2 = st.columns(2)

    with breakdown_col1:
        # Income breakdown (excluding hidden items)
        income_items = []
        for item in st.session_state["income_monthly_items"]:
            if item.get("hidden", False):
                continue
            # Skip items converted from yearly (they have original_yearly marker)
            if "original_yearly" not in item:
                income_items.append({
                    "Name": item["name"],
                    "Amount": item["amount"],
                    "Type": "Monthly",
                })
            else:
                # Show converted yearly items only in monthly mode
                income_items.append({
                    "Name": item["name"],
                    "Amount": item["amount"],
                    "Type": "Yearly (monthly equiv.)",
                })
        # Only show yearly items in separate mode
        if calc_mode == "separate":
            for item in st.session_state["income_yearly_items"]:
                if item.get("hidden", False):
                    continue
                income_items.append({
                    "Name": item["name"],
                    "Amount": item["amount"] / 12,
                    "Type": "Yearly (monthly equiv.)",
                })

        if income_items:
            income_df = pd.DataFrame(income_items)
            fig_income = px.bar(
                income_df,
                x="Name",
                y="Amount",
                color="Type",
                title="Income Sources (Monthly Equivalent)",
                color_discrete_map={
                    "Monthly": "#28A745",
                    "Yearly (monthly equiv.)": "#6FCF97",
                },
            )
            fig_income.update_layout(
                xaxis_tickangle=-45,
                yaxis_tickformat=",.0f",
            )
            st.plotly_chart(fig_income, width="stretch", key="income_bar")

    with breakdown_col2:
        # Expenses breakdown (excluding hidden items)
        expense_items = []
        for item in st.session_state["expense_monthly_items"]:
            if item.get("hidden", False):
                continue
            # Skip items converted from yearly (they have original_yearly marker)
            if "original_yearly" not in item:
                expense_items.append({
                    "Name": item["name"],
                    "Amount": item["amount"],
                    "Type": "Monthly",
                })
            else:
                # Show converted yearly items only in monthly mode
                expense_items.append({
                    "Name": item["name"],
                    "Amount": item["amount"],
                    "Type": "Yearly (monthly equiv.)",
                })
        # Only show yearly items in separate mode
        if calc_mode == "separate":
            for item in st.session_state["expense_yearly_items"]:
                if item.get("hidden", False):
                    continue
                expense_items.append({
                    "Name": item["name"],
                    "Amount": item["amount"] / 12,
                    "Type": "Yearly (monthly equiv.)",
                })

        if expense_items:
            expense_df = pd.DataFrame(expense_items)
            fig_expenses = px.bar(
                expense_df,
                x="Name",
                y="Amount",
                color="Type",
                title="Expense Categories (Monthly Equivalent)",
                color_discrete_map={
                    "Monthly": "#DC3545",
                    "Yearly (monthly equiv.)": "#F2994A",
                },
            )
            fig_expenses.update_layout(
                xaxis_tickangle=-45,
                yaxis_tickformat=",.0f",
            )
            st.plotly_chart(fig_expenses, width="stretch", key="expenses_bar")


if __name__ == "__main__":
    main()
