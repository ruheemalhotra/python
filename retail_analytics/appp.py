
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.write("App has started successfully!")
# =====================================
# 1. PAGE CONFIGURATION
# =====================================

st.set_page_config(
    page_title="Retail Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("Retail Business Analytics")
st.caption("Business performance and sales analysis")


# =====================================
# 2. LOAD EXCEL WORKBOOK
# =====================================
FILE_PATH = Path(__file__).parent.parent / "retail_analysis.xlsx"


@st.cache_data
def load_data(file_path):
    return pd.read_excel(file_path, sheet_name=None)


if not FILE_PATH.exists():
    st.error("Excel file not found. Run analysis.py first.")
    st.stop()

try:
    data = load_data(str(FILE_PATH))

except Exception as error:
    st.error(f"Unable to read Excel file: {error}")
    st.stop()


# Access individual sheets

summary = data["Executive Summary"]
branch = data["Branch Revenue"]
daily = data["Daily Revenue"]
products = data["Product Performance"]
categories = data["Category Analysis"]
top_products = data["Top Products"]
highest_prices = data["Highest Prices"]
customers = data["Customer Analysis"]
employees = data["Employee Analysis"]
payments = data["Payment Analysis"]
orders = data["Order Status"]


# =====================================
# 3. SIDEBAR FILTERS
# =====================================

st.sidebar.title("Dashboard Filters")

start_date = st.sidebar.date_input(
    "Report start date",
    value=pd.to_datetime("2026-10-01")
)

end_date = st.sidebar.date_input(
    "Report end date",
    value=pd.to_datetime("2026-10-18")
)

st.sidebar.info(
    "The displayed data comes from the Excel workbook. "
    "Run analysis.py to generate a new reporting period."
)


# =====================================
# 4. VALIDATE REPORT PERIOD
# =====================================

st.subheader(
    f"Reporting Period: {start_date} to {end_date}"
)

st.caption("The dates shown here describe the generated report. "
           "Changing them does not recalculate the Excel data.")


# =====================================
# 5. OVERVIEW
# =====================================

st.header("Business Overview")

revenue = float(
    summary["total_revenue"].iloc[0]
)

total_orders = int(
    summary["total_orders"].iloc[0]
)

total_units = int(
    summary["total_units_sold"].iloc[0]
)

average_order_value = float(
    summary["average_order_value"].iloc[0]
)


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Revenue",
    f"₹{revenue:,.2f}"
)

col2.metric(
    "Total Orders",
    f"{total_orders:,}"
)

col3.metric(
    "Units Sold",
    f"{total_units:,}"
)

col4.metric(
    "Average Order Value",
    f"₹{average_order_value:,.2f}"
)


# =====================================
# 6. BRANCH ANALYSIS
# =====================================

st.divider()
st.header("Branch Performance")

col1, col2 = st.columns(2)

with col1:

    st.subheader("Revenue by Branch")

    fig = px.bar(
        branch,
        x="branch_name",
        y="total_revenue",
        color="total_revenue",
        text_auto=".2s",
        title="Branch-wise Revenue",
        labels={
            "branch_name": "Branch",
            "total_revenue": "Revenue"
        }
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with col2:

    st.subheader("Branch Revenue Share")

    fig = px.pie(
        branch,
        names="branch_name",
        values="total_revenue",
        hole=0.45
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


st.subheader("Branch Revenue Details")

st.dataframe(
    branch,
    use_container_width=True,
    hide_index=True
)


# =====================================
# 7. DAILY REVENUE ANALYSIS
# =====================================

st.divider()
st.header("Daily Sales Trend")

if not daily.empty:

    daily["sale_day"] = pd.to_datetime(
        daily["sale_day"]
    )

    fig = px.line(
        daily,
        x="sale_day",
        y="daily_revenue",
        markers=True,
        title="Daily Revenue Trend",
        labels={
            "sale_day": "Date",
            "daily_revenue": "Revenue"
        }
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:
    st.info("No completed sales found in this period.")


# =====================================
# 8. PRODUCT ANALYSIS
# =====================================

st.divider()
st.header("Product Performance")

col1, col2 = st.columns(2)

with col1:

    st.subheader("Top Products by Revenue")

    top_revenue = products.head(10)

    fig = px.bar(
        top_revenue,
        x="total_revenue",
        y="product_name",
        orientation="h",
        title="Top 10 Products"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with col2:

    st.subheader("Category Performance")

    fig = px.pie(
        categories,
        names="category",
        values="total_revenue",
        hole=0.4
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


st.subheader("Best-selling Products by Branch")

st.dataframe(
    top_products,
    use_container_width=True,
    hide_index=True
)


st.subheader("Highest-priced Products by Branch")

st.dataframe(
    highest_prices,
    use_container_width=True,
    hide_index=True
)


# =====================================
# 9. CUSTOMER ANALYSIS
# =====================================

st.divider()
st.header("Customer Analysis")

active_customers = customers[
    customers["total_orders"] > 0
]

col1, col2 = st.columns(2)

with col1:

    st.metric(
        "Customers with Purchases",
        len(active_customers)
    )

    st.subheader("Top Customers by Spending")

    st.dataframe(
        active_customers.head(10),
        use_container_width=True,
        hide_index=True
    )


with col2:

    if not active_customers.empty:

        fig = px.bar(
            active_customers.head(10),
            x="total_spent",
            y="customer_id",
            orientation="h",
            title="Customer Spending"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# =====================================
# 10. EMPLOYEE ANALYSIS
# =====================================

st.divider()
st.header("Employee Performance")

st.dataframe(
    employees,
    use_container_width=True,
    hide_index=True
)


# =====================================
# 11. PAYMENT ANALYSIS
# =====================================

st.divider()
st.header("Payment Analysis")

col1, col2 = st.columns(2)

with col1:

    fig = px.pie(
        payments,
        names="payment_method",
        values="total_orders",
        title="Orders by Payment Method"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with col2:

    st.dataframe(
        payments,
        use_container_width=True,
        hide_index=True
    )


# =====================================
# 12. ORDER STATUS
# =====================================

st.divider()
st.header("Order Status Analysis")

fig = px.bar(
    orders,
    x="order_status",
    y="total_orders",
    color="order_status",
    title="Order Status Distribution"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# =====================================
# 13. DATA REFRESH INSTRUCTIONS
# =====================================

st.divider()

st.subheader("Data Management")

st.write(
    "To refresh the dashboard with new database data, "
    "run analysis.py again and then reload this application."
)

if st.button("Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()


st.success("Retail Analytics Dashboard Loaded Successfully!")
