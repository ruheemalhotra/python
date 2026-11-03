
import pandas as pd
from sqlalchemy import create_engine

# PART 1: Database connection details
username = "postgres"
password = "data"
host = "localhost"
port = "5432"
database = "retail_company"

# PART 2: Create the database connection
connection_string = (
    f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
)

engine = create_engine(connection_string)

# PART 3: Fetch data from PostgreSQL
query = "SELECT * FROM sales"

df = pd.read_sql(query, engine)

# PART 4: Display the data
print("\nFirst 5 rows:")
print(df.head())

print("\nDataset information:")
print(df.info())

# Fetch all tables

branches = pd.read_sql("SELECT * FROM branches", engine)
employees = pd.read_sql("SELECT * FROM employees", engine)
customers = pd.read_sql("SELECT * FROM customers", engine)
products = pd.read_sql("SELECT * FROM products", engine)
inventory = pd.read_sql("SELECT * FROM inventory", engine)

print("\nBranches:")
print(branches.head())

print("\nProducts:")
print(products.head())

print("\nInventory:")
print(inventory.head())


# Store all tables in one dictionary
tables = {
    "branches": branches,
    "employees": employees,
    "customers": customers,
    "products": products,
    "sales": df,
    "inventory": inventory
}

# Explore each table
for table_name, table_data in tables.items():

    print("\n" + "=" * 50)
    print("TABLE:", table_name.upper())
    print("=" * 50)

    # Number of rows and columns
    print("Shape:", table_data.shape)

    # Column names
    print("\nColumns:")
    print(table_data.columns.tolist())

    # Data types
    print("\nData types:")
    print(table_data.dtypes)

    # Missing values
    print("\nMissing values:")
    print(table_data.isnull().sum())

    # Duplicate records
    print("\nDuplicate rows:", table_data.duplicated().sum())


query = """
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

GROUP BY
    b.branch_name,
    p.product_name

ORDER BY
    b.branch_name,
    total_quantity_sold DESC;
"""

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

    GROUP BY
        b.branch_name,
        p.product_name
),

ranked_products AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
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
WHERE product_rank = 1;
"""

with engine.connect() as connection:
    top_products = pd.read_sql(top_products_query, connection)

print(top_products)

with engine.connect() as connection:
    product_sales = pd.read_sql(query, connection)

print(product_sales)


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

    GROUP BY
        b.branch_name,
        p.product_name
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

with engine.connect() as connection:
    highest_price_products = pd.read_sql(
        highest_price_query, connection
    )

print(highest_price_products)


# PART 5: Close the connection
engine.dispose()
print("\nDatabase connection closed.")
