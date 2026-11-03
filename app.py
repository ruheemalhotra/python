
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from datetime import date

# -------------------------------
# 1. PAGE SETTINGS
# -------------------------------

st.set_page_config(
    page_title="Retail Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("Retail Business Dashboard")
st.write("Analyse sales performance across your branches.")

# -------------------------------
# 2. DATABASE CONNECTION
# -------------------------------

@st.cache_resource
def get_engine():
    username = "postgres"
    password = "data"
    host = "localhost"
    port = "5432"
    database = "retail_company"

    connection_string = (
        f"postgresql+psycopg2://{username}:{password}"
        f"@{host}:{port}/{database}"
    )

    return create_engine(connection_string)


# -------------------------------
# 3. SQL QUERIES
# -------------------------------

revenue_query = """
SELECT
    b.branch_name,
    COALESCE(
        SUM(s.quantity * s.unit_price *
            (1 - s.discount_pct / 100.0)), 0
    ) AS total_revenue
FROM branches b
LEFT JOIN sales s
    ON b.branch_id = s.branch_id
    AND s.order_status = 'Completed'
    AND s.sale_date >= :start_date
    AND s.sale_date <= :end_date
GROUP BY b.branch_name
ORDER BY total_revenue DESC;
"""

top_products_query = """
WITH product_sales AS (
    SELECT
        b.branch_name,
        p.product_name,
        SUM(s.quantity) AS total_quantity_sold
    FROM sales s
    JOIN branches b ON s.branch_id = b.branch_id
    JOIN products p ON s.product_id = p.product_id
    WHERE s.order_status = 'Completed'
      AND s.sale_date >= :start_date
      AND s.sale_date <= :end_date
    GROUP BY b.branch_name, p.product_name
),
ranked AS (
    SELECT *,
        RANK() OVER (
            PARTITION BY branch_name
            ORDER BY total_quantity_sold DESC
        ) AS product_rank
    FROM product_sales
)
SELECT branch_name, product_name, total_quantity_sold
FROM ranked
WHERE product_rank = 1
ORDER BY branch_name;
"""

highest_prices_query = """
WITH product_prices AS (
    SELECT
        b.branch_name,
        p.product_name,
        MAX(s.unit_price) AS highest_unit_price
    FROM sales s
    JOIN branches b ON s.branch_id = b.branch_id
    JOIN products p ON s.product_id = p.product_id
    WHERE s.order_status = 'Completed'
      AND s.sale_date >= :start_date
      AND s.sale_date <= :end_date
    GROUP BY b.branch_name, p.product_name
),
ranked AS (
    SELECT *,
        RANK() OVER (
            PARTITION BY branch_name
            ORDER BY highest_unit_price DESC
        ) AS price_rank
    FROM product_prices
)
SELECT branch_name, product_name, highest_unit_price
FROM ranked
WHERE price_rank = 1
ORDER BY branch_name;
"""

company_revenue_query = """
SELECT COALESCE(
    SUM(quantity * unit_price *
        (1 - discount_pct / 100.0)), 0
) AS total_company_revenue
FROM sales
WHERE order_status = 'Completed'
  AND sale_date >= :start_date
  AND sale_date <= :end_date;
"""


# -------------------------------
# 4. DATE FILTER
# -------------------------------

with st.form("report_filters"):
    st.subheader("Select reporting period")

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Start date",
            value=date(2026, 10, 1)
        )

    with col2:
        end_date = st.date_input(
            "End date",
            value=date(2026, 10, 18)
        )

    generate = st.form_submit_button("Generate Dashboard")

# -------------------------------
# 5. FETCH AND DISPLAY DATA
# -------------------------------

if generate:

    if start_date > end_date:
        st.error("Start date cannot be after end date.")

    else:
        try:
            engine = get_engine()

            parameters = {
                "start_date": start_date,
                "end_date": end_date
            }

            with engine.connect() as connection:

                branch_revenue = pd.read_sql(
                    text(revenue_query),
                    connection,
                    params=parameters
                )

                top_products = pd.read_sql(
                    text(top_products_query),
                    connection,
                    params=parameters
                )

                highest_prices = pd.read_sql(
                    text(highest_prices_query),
                    connection,
                    params=parameters
                )

                company_revenue = pd.read_sql(
                    text(company_revenue_query),
                    connection,
                    params=parameters
                )

            total_revenue = float(
                company_revenue["total_company_revenue"].iloc[0]
            )

            total_branches = len(branch_revenue)

            st.success("Dashboard generated successfully!")

            # KPI CARDS
            st.subheader("Business Overview")

            col1, col2 = st.columns(2)

            col1.metric(
                "Total Company Revenue",
                f"₹{total_revenue:,.2f}"
            )

            col2.metric(
                "Branches Analysed",
                total_branches
            )

            # REVENUE CHART
            st.subheader("Revenue by Branch")

            fig = px.bar(
                branch_revenue,
                x="branch_name",
                y="total_revenue",
                title="Branch-wise Revenue",
                labels={
                    "branch_name": "Branch",
                    "total_revenue": "Revenue (₹)"
                },
                text_auto=".2s"
            )

            st.plotly_chart(fig, use_container_width=True)

            # TABLES
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Best-selling Products")
                st.dataframe(
                    top_products,
                    use_container_width=True,
                    hide_index=True
                )

            with col2:
                st.subheader("Highest-priced Products")
                st.dataframe(
                    highest_prices,
                    use_container_width=True,
                    hide_index=True
                )

            st.subheader("Complete Branch Revenue")
            st.dataframe(
                branch_revenue,
                use_container_width=True,
                hide_index=True
            )

            # EXCEL DOWNLOAD
            import io

            output = io.BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                branch_revenue.to_excel(
                    writer, sheet_name="Branch Revenue", index=False
                )
                top_products.to_excel(
                    writer, sheet_name="Top Products", index=False
                )
                highest_prices.to_excel(
                    writer, sheet_name="Highest Prices", index=False
                )
                company_revenue.to_excel(
                    writer, sheet_name="Company Revenue", index=False
                )

            st.download_button(
                "Download Excel Report",
                data=output.getvalue(),
                file_name="retail_dashboard_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as error:
            st.error(f"Something went wrong: {error}")
