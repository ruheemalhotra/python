
import pandas as pd
from sqlalchemy import create_engine, text, URL
from datetime import date
from getpass import getpass


# ==========================================
# 1. DATABASE CONNECTION
# ==========================================

print("Connecting to PostgreSQL...")

password = getpass("Enter PostgreSQL password: ")

connection_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password=password,
    host="localhost",
    port=5432,
    database="retail_company"
)

engine = create_engine(connection_url)


# ==========================================
# 2. SELECT REPORTING PERIOD
# ==========================================

start_date = date(2026, 10, 1)
end_date = date(2026, 10, 18)

parameters = {
    "start_date": start_date,
    "end_date": end_date
}

print(f"Report period: {start_date} to {end_date}")


# ==========================================
# 3. DEFINE SQL QUERIES
# ==========================================

# A. EXECUTIVE SUMMARY

executive_summary_query = """
SELECT
    COUNT(s.sale_id) AS total_orders,
    COALESCE(SUM(s.quantity), 0) AS total_units_sold,
    COALESCE(
        SUM(s.quantity * s.unit_price *
        (1 - s.discount_pct / 100.0)), 0
    ) AS total_revenue,
    COALESCE(
        AVG(s.quantity * s.unit_price *
        (1 - s.discount_pct / 100.0)), 0
    ) AS average_order_value
FROM sales s
WHERE s.order_status = 'Completed'
AND s.sale_date >= :start_date
AND s.sale_date < :end_date + INTERVAL '1 day';
"""


# B. REVENUE BY BRANCH

branch_revenue_query = """
SELECT
    b.branch_name,
    COUNT(s.sale_id) AS total_orders,
    COALESCE(SUM(s.quantity), 0) AS units_sold,
    COALESCE(
        SUM(s.quantity * s.unit_price *
        (1 - s.discount_pct / 100.0)), 0
    ) AS total_revenue
FROM branches b
LEFT JOIN sales s
    ON b.branch_id = s.branch_id
    AND s.order_status = 'Completed'
    AND s.sale_date >= :start_date
    AND s.sale_date < :end_date + INTERVAL '1 day'
GROUP BY b.branch_name
ORDER BY total_revenue DESC;
"""


# C. DAILY REVENUE

daily_revenue_query = """
SELECT
    sale_date::date AS sale_day,
    COUNT(sale_id) AS total_orders,
    SUM(quantity) AS units_sold,
    SUM(
        quantity * unit_price *
        (1 - discount_pct / 100.0)
    ) AS daily_revenue
FROM sales
WHERE order_status = 'Completed'
AND sale_date >= :start_date
AND sale_date < :end_date + INTERVAL '1 day'
GROUP BY sale_date::date
ORDER BY sale_day;
"""


# D. PRODUCT PERFORMANCE

product_performance_query = """
SELECT
    p.product_name,
    p.category,
    SUM(s.quantity) AS units_sold,
    COUNT(s.sale_id) AS total_orders,
    SUM(
        s.quantity * s.unit_price *
        (1 - s.discount_pct / 100.0)
    ) AS total_revenue
FROM sales s
JOIN products p
    ON s.product_id = p.product_id
WHERE s.order_status = 'Completed'
AND s.sale_date >= :start_date
AND s.sale_date < :end_date + INTERVAL '1 day'
GROUP BY p.product_name, p.category
ORDER BY total_revenue DESC;
"""


# E. CATEGORY PERFORMANCE

category_performance_query = """
SELECT
    p.category,
    SUM(s.quantity) AS units_sold,
    SUM(
        s.quantity * s.unit_price *
        (1 - s.discount_pct / 100.0)
    ) AS total_revenue
FROM sales s
JOIN products p
    ON s.product_id = p.product_id
WHERE s.order_status = 'Completed'
AND s.sale_date >= :start_date
AND s.sale_date < :end_date + INTERVAL '1 day'
GROUP BY p.category
ORDER BY total_revenue DESC;
"""


# F. BEST-SELLING PRODUCT IN EACH BRANCH

top_products_query = """
WITH product_sales AS (
    SELECT
        b.branch_name,
        p.product_name,
        SUM(s.quantity) AS units_sold
    FROM sales s
    JOIN branches b
        ON s.branch_id = b.branch_id
    JOIN products p
        ON s.product_id = p.product_id
    WHERE s.order_status = 'Completed'
    AND s.sale_date >= :start_date
    AND s.sale_date < :end_date + INTERVAL '1 day'
    GROUP BY b.branch_name, p.product_name
),
ranked_products AS (
    SELECT *,
        RANK() OVER (
            PARTITION BY branch_name
            ORDER BY units_sold DESC
        ) AS product_rank
    FROM product_sales
)
SELECT branch_name, product_name, units_sold
FROM ranked_products
WHERE product_rank = 1
ORDER BY branch_name;
"""


# G. HIGHEST UNIT PRICE PRODUCT IN EACH BRANCH

highest_price_query = """
WITH product_prices AS (
    SELECT
        b.branch_name,
        p.product_name,
        MAX(s.unit_price) AS highest_unit_price
    FROM sales s
    JOIN branches b
        ON s.branch_id = b.branch_id
    JOIN products p
        ON s.product_id = p.product_id
    WHERE s.order_status = 'Completed'
    AND s.sale_date >= :start_date
    AND s.sale_date < :end_date + INTERVAL '1 day'
    GROUP BY b.branch_name, p.product_name
),
ranked_prices AS (
    SELECT *,
        RANK() OVER (
            PARTITION BY branch_name
            ORDER BY highest_unit_price DESC
        ) AS price_rank
    FROM product_prices
)
SELECT branch_name, product_name, highest_unit_price
FROM ranked_prices
WHERE price_rank = 1
ORDER BY branch_name;
"""


# H. CUSTOMER PERFORMANCE

customer_performance_query = """
WITH customer_sales AS (
    SELECT
        customer_id,
        COUNT(sale_id) AS total_orders,
        SUM(
            quantity * unit_price *
            (1 - discount_pct / 100.0)
        ) AS total_spent
    FROM sales
    WHERE order_status = 'Completed'
    AND sale_date >= :start_date
    AND sale_date < :end_date + INTERVAL '1 day'
    GROUP BY customer_id
)
SELECT
    c.*,
    COALESCE(cs.total_orders, 0) AS total_orders,
    COALESCE(cs.total_spent, 0) AS total_spent
FROM customers c
LEFT JOIN customer_sales cs
    ON c.customer_id = cs.customer_id
ORDER BY total_spent DESC;
"""


# I. EMPLOYEE PERFORMANCE

employee_performance_query = """
WITH employee_sales AS (
    SELECT
        employee_id,
        COUNT(sale_id) AS total_orders,
        SUM(
            quantity * unit_price *
            (1 - discount_pct / 100.0)
        ) AS total_revenue
    FROM sales
    WHERE order_status = 'Completed'
    AND sale_date >= :start_date
    AND sale_date < :end_date + INTERVAL '1 day'
    GROUP BY employee_id
)
SELECT
    e.*,
    COALESCE(es.total_orders, 0) AS total_orders,
    COALESCE(es.total_revenue, 0) AS total_revenue
FROM employees e
LEFT JOIN employee_sales es
    ON e.employee_id = es.employee_id
ORDER BY total_revenue DESC;
"""


# J. PAYMENT METHOD ANALYSIS

payment_analysis_query = """
SELECT
    payment_method,
    COUNT(sale_id) AS total_orders,
    SUM(
        quantity * unit_price *
        (1 - discount_pct / 100.0)
    ) AS total_revenue
FROM sales
WHERE order_status = 'Completed'
AND sale_date >= :start_date
AND sale_date < :end_date + INTERVAL '1 day'
GROUP BY payment_method
ORDER BY total_orders DESC;
"""


# K. ORDER STATUS ANALYSIS

order_status_query = """
SELECT
    order_status,
    COUNT(sale_id) AS total_orders
FROM sales
WHERE sale_date >= :start_date
AND sale_date < :end_date + INTERVAL '1 day'
GROUP BY order_status
ORDER BY total_orders DESC;
"""


# ==========================================
# 4. EXECUTE QUERIES
# ==========================================

print("\nRunning business analysis queries...")

try:

    with engine.connect() as connection:

        executive_summary = pd.read_sql(
            text(executive_summary_query),
            connection,
            params=parameters
        )

        branch_revenue = pd.read_sql(
            text(branch_revenue_query),
            connection,
            params=parameters
        )

        daily_revenue = pd.read_sql(
            text(daily_revenue_query),
            connection,
            params=parameters
        )

        product_performance = pd.read_sql(
            text(product_performance_query),
            connection,
            params=parameters
        )

        category_performance = pd.read_sql(
            text(category_performance_query),
            connection,
            params=parameters
        )

        top_products = pd.read_sql(
            text(top_products_query),
            connection,
            params=parameters
        )

        highest_prices = pd.read_sql(
            text(highest_price_query),
            connection,
            params=parameters
        )

        customer_performance = pd.read_sql(
            text(customer_performance_query),
            connection,
            params=parameters
        )

        employee_performance = pd.read_sql(
            text(employee_performance_query),
            connection,
            params=parameters
        )

        payment_analysis = pd.read_sql(
            text(payment_analysis_query),
            connection,
            params=parameters
        )

        order_status = pd.read_sql(
            text(order_status_query),
            connection,
            params=parameters
        )

        # Raw tables for detailed analysis and AI questions

        raw_sales = pd.read_sql(
            text("""
                SELECT *
                FROM sales
                WHERE sale_date >= :start_date
                AND sale_date < :end_date + INTERVAL '1 day'
                ORDER BY sale_date
            """),
            connection,
            params=parameters
        )

        raw_products = pd.read_sql(
            "SELECT * FROM products",
            connection
        )

        raw_branches = pd.read_sql(
            "SELECT * FROM branches",
            connection
        )

        raw_inventory = pd.read_sql(
            "SELECT * FROM inventory",
            connection
        )

        raw_customers = pd.read_sql(
            "SELECT * FROM customers",
            connection
        )

        raw_employees = pd.read_sql(
            "SELECT * FROM employees",
            connection
        )

    print("All queries executed successfully!")


    # ==========================================
    # 5. EXPORT EVERYTHING TO EXCEL
    # ==========================================

    print("\nCreating Excel workbook...")

    with pd.ExcelWriter(
        "retail_analysis.xlsx",
        engine="openpyxl"
    ) as writer:

        executive_summary.to_excel(
            writer, sheet_name="Executive Summary", index=False
        )

        branch_revenue.to_excel(
            writer, sheet_name="Branch Revenue", index=False
        )

        daily_revenue.to_excel(
            writer, sheet_name="Daily Revenue", index=False
        )

        product_performance.to_excel(
            writer, sheet_name="Product Performance", index=False
        )

        category_performance.to_excel(
            writer, sheet_name="Category Analysis", index=False
        )

        top_products.to_excel(
            writer, sheet_name="Top Products", index=False
        )

        highest_prices.to_excel(
            writer, sheet_name="Highest Prices", index=False
        )

        customer_performance.to_excel(
            writer, sheet_name="Customer Analysis", index=False
        )

        employee_performance.to_excel(
            writer, sheet_name="Employee Analysis", index=False
        )

        payment_analysis.to_excel(
            writer, sheet_name="Payment Analysis", index=False
        )

        order_status.to_excel(
            writer, sheet_name="Order Status", index=False
        )

        raw_sales.to_excel(
            writer, sheet_name="Raw Sales", index=False
        )

        raw_products.to_excel(
            writer, sheet_name="Raw Products", index=False
        )

        raw_branches.to_excel(
            writer, sheet_name="Raw Branches", index=False
        )

        raw_inventory.to_excel(
            writer, sheet_name="Raw Inventory", index=False
        )

        raw_customers.to_excel(
            writer, sheet_name="Raw Customers", index=False
        )

        raw_employees.to_excel(
            writer, sheet_name="Raw Employees", index=False
        )


    print("\n================================")
    print("RETAIL ANALYSIS COMPLETED")
    print("================================")

    print("\nExecutive Summary:")
    print(executive_summary.round(2).to_string(index=False))

    print("\nBranch Revenue:")
    print(branch_revenue.round(2).to_string(index=False))

    print("\nExcel file created: retail_analysis.xlsx")


except Exception as error:

    print("\nAn error occurred:")
    print(error)


finally:
    engine.dispose()
