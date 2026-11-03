
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date, timedelta

# ==========================================
# 1. DATABASE CONNECTION
# ==========================================

username = "postgres"
password = "data"
host = "localhost"
port = "5432"
database = "retail_company"

connection_string = (
    f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
)

engine = create_engine(connection_string)


# ==========================================
# 2. WEEKLY DATE RANGE
# ==========================================

today = date.today()

# Monday of the current week
current_monday = today - timedelta(days=today.weekday())

# Previous completed week
start_date = date(2026, 10, 1)
end_date = date(2026, 10, 18)

print("\nGenerating weekly report...")
print("Report period:", start_date, "to", end_date - timedelta(days=1))


# Parameters passed safely to SQL queries
parameters = {
    "start_date": start_date,
    "end_date": end_date
}

# ==========================================
# 3. QUERY 1: REVENUE OF EACH BRANCH
# ==========================================

revenue_query = """
SELECT
    b.branch_name,

    SUM(
        s.quantity * s.unit_price *
        (1 - s.discount_pct / 100.0)
    ) AS total_revenue

FROM sales s

JOIN branches b
    ON s.branch_id = b.branch_id

WHERE s.order_status = 'Completed'
AND s.sale_date >= :start_date
AND s.sale_date < :end_date

GROUP BY b.branch_name

ORDER BY total_revenue DESC;
"""


# ==========================================
# 4. QUERY 2: HIGHEST-SELLING PRODUCT
# ==========================================

top_products_query = """
WITH product_sales AS (

    SELECT
        b.branch_name,
        p.product_name,
        SUM(s.quantity) AS total_quantity_sold

    FROM sales s

    JOIN branches b
        ON s.branch_id = b.branch_id

    JOIN products p
        ON s.product_id = p.product_id

    WHERE s.order_status = 'Completed'
    AND s.sale_date >= :start_date
    AND s.sale_date < :end_date

    GROUP BY b.branch_name, p.product_name
),

ranked_products AS (

    SELECT
        *,
        RANK() OVER (
            PARTITION BY branch_name
            ORDER BY total_quantity_sold DESC
        ) AS product_rank

    FROM product_sales
)

SELECT
    branch_name,
    product_name,
    total_quantity_sold

FROM ranked_products

WHERE product_rank = 1

ORDER BY branch_name;
"""


# ==========================================
# 5. QUERY 3: HIGHEST-PRICED PRODUCT
# ==========================================

highest_prices_query = """
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
    AND s.sale_date < :end_date

    GROUP BY b.branch_name, p.product_name
),

ranked_products AS (

    SELECT
        *,
        RANK() OVER (
            PARTITION BY branch_name
            ORDER BY highest_unit_price DESC
        ) AS price_rank

    FROM product_prices
)

SELECT
    branch_name,
    product_name,
    highest_unit_price

FROM ranked_products

WHERE price_rank = 1

ORDER BY branch_name;
"""


# ==========================================
# 6. QUERY 4: TOTAL COMPANY REVENUE
# ==========================================

company_revenue_query = """
SELECT

    SUM(
        s.quantity * s.unit_price *
        (1 - s.discount_pct / 100.0)
    ) AS total_company_revenue

FROM sales s

WHERE s.order_status = 'Completed'
AND s.sale_date >= :start_date
AND s.sale_date < :end_date;
"""


# ==========================================
# 7. EXECUTE QUERIES
# ==========================================

try:

    with engine.connect() as connection:

        branch_revenue = pd.read_sql(
            sql=text(revenue_query),
            con=connection,
            params=parameters
        )

        highest_products = pd.read_sql(
            sql=text(top_products_query),
            con=connection,
            params=parameters
        )

        highest_prices = pd.read_sql(
            sql=text(highest_prices_query),
            con=connection,
            params=parameters
        )

        company_revenue = pd.read_sql(
            sql=text(company_revenue_query),
            con=connection,
            params=parameters
        )


    # ==========================================
    # 8. FORMAT NUMBERS
    # ==========================================

    branch_revenue["total_revenue"] = (
        branch_revenue["total_revenue"].round(2)
    )

    company_revenue["total_company_revenue"] = (
        company_revenue["total_company_revenue"].round(2)
    )

    highest_prices["highest_unit_price"] = (
        highest_prices["highest_unit_price"].round(2)
    )


    # ==========================================
    # 9. EXPORT TO EXCEL
    # ==========================================

    file_name = "weekly_retail_report.xlsx"

    with pd.ExcelWriter(file_name, engine="openpyxl") as writer:

        branch_revenue.to_excel(
            writer,
            sheet_name="Branch Revenue",
            index=False
        )

        highest_products.to_excel(
            writer,
            sheet_name="Top Products",
            index=False
        )

        highest_prices.to_excel(
            writer,
            sheet_name="Highest Prices",
            index=False
        )

        company_revenue.to_excel(
            writer,
            sheet_name="Company Revenue",
            index=False
        )


    # ==========================================
    # 10. DISPLAY RESULTS
    # ==========================================

    print("\n========== BRANCH REVENUE ==========")
    print(branch_revenue.to_string(index=False))

    print("\n========== HIGHEST-SELLING PRODUCTS ==========")
    print(highest_products.to_string(index=False))

    print("\n========== HIGHEST-PRICED PRODUCTS ==========")
    print(highest_prices.to_string(index=False))

    print("\n========== TOTAL COMPANY REVENUE ==========")
    print(company_revenue.to_string(index=False))

    print("\n====================================")
    print("REPORT GENERATED SUCCESSFULLY!")
    print("Excel file:", file_name)
    print("====================================")


finally:

    engine.dispose()
