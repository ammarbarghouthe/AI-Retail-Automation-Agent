import sqlite3


def create_database():
    connection = sqlite3.connect("retail.db")
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    new_columns = {
        "category": "TEXT",
        "barcode": "TEXT",
        "cost_price": "REAL",
        "reorder_level": "INTEGER",
        "supplier": "TEXT"
    }

    cursor.execute("PRAGMA table_info(products)")
    existing_columns = {
        row[1] for row in cursor.fetchall()
    }

    for column, data_type in new_columns.items():
        if column not in existing_columns:
            cursor.execute(
                f"ALTER TABLE products ADD COLUMN {column} {data_type}"
            )
            print(f"Added column: {column}")

    connection.commit()
    connection.close()

    print("Database upgraded successfully!")


def add_product(name, price, stock):
    connection = sqlite3.connect("retail.db")
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
        (name, price, stock)
    )

    connection.commit()
    connection.close()

    print("Product added successfully!")

def get_products():
    connection = sqlite3.connect("retail.db")
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    connection.close()

    return products


def get_low_stock_products(threshold: int = 20) -> list[dict]:
    print(f"TOOL EXECUTED: get_low_stock_products(threshold={threshold})", flush=True)

    conn = sqlite3.connect("retail.db")
    cursor = conn.cursor()


    cursor.execute(
        "SELECT id, name, price, stock FROM products WHERE stock < ?",
        (threshold,)
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "stock": row[3]
        }
        for row in rows
    ]

if __name__ == "__main__":
    create_database()
    print(get_products())
    
def get_inventory_summary() -> dict:
    """Get total product records, stock units, and inventory value."""
    conn = sqlite3.connect("retail.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(stock), 0),
            COALESCE(SUM(price * stock), 0)
        FROM products
    """)

    row = cursor.fetchone()
    conn.close()

    return {
        "total_products": row[0],
        "total_stock_units": row[1],
        "total_inventory_value": round(row[2], 2)
    }

def create_retail_sales_table():
    """Create a table for historical retail transactions."""
    connection = sqlite3.connect("retail.db")
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS retail_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice TEXT,
            stock_code TEXT,
            description TEXT,
            quantity INTEGER,
            invoice_date TEXT,
            unit_price REAL,
            customer_id TEXT,
            country TEXT
        )
    """)

    connection.commit()
    connection.close()

    print("Retail sales table created successfully!")

def search_product_sales(product_name: str) -> list[dict]:
    """Search historical sales by product name."""
    connection = sqlite3.connect("retail.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            stock_code,
            description,
            SUM(quantity) AS total_units_sold,
            ROUND(SUM(quantity * unit_price), 2) AS total_revenue
        FROM retail_sales
        WHERE description LIKE ? COLLATE NOCASE
        GROUP BY stock_code, description
        ORDER BY total_units_sold DESC
        LIMIT 10
    """, (f"%{product_name}%",))

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "stock_code": row[0],
            "product_name": row[1],
            "total_units_sold": row[2],
            "total_revenue_gbp": row[3]
        }
        for row in rows
    ]

def get_top_selling_products(limit: int = 10) -> list[dict]:
    """Return the best-selling products by units sold."""
    limit = max(1, min(limit, 50))

    with sqlite3.connect("retail.db") as conn:
        rows = conn.execute("""
            SELECT stock_code, description,
                   SUM(quantity) AS units,
                   ROUND(SUM(quantity * unit_price), 2) AS revenue
            FROM retail_sales
            GROUP BY stock_code, description
            ORDER BY units DESC
            LIMIT ?
        """, (limit,)).fetchall()

    return [
        {"stock_code": r[0], "product": r[1],
         "units_sold": r[2], "revenue_gbp": r[3]}
        for r in rows
    ]


def get_revenue_by_period(
    start_date: str,
    end_date: str
) -> dict:
    """Calculate sales revenue between two dates (YYYY-MM-DD)."""
    with sqlite3.connect("retail.db") as conn:
        row = conn.execute("""
            SELECT COUNT(DISTINCT invoice),
                   COALESCE(SUM(quantity), 0),
                   ROUND(COALESCE(SUM(quantity * unit_price), 0), 2)
            FROM retail_sales
            WHERE invoice_date >= ?
              AND invoice_date < date(?, '+1 day')
        """, (start_date, end_date)).fetchone()

    return {
        "start_date": start_date,
        "end_date": end_date,
        "orders": row[0],
        "units_sold": row[1],
        "revenue_gbp": row[2]
    }


def get_monthly_sales_trends() -> list[dict]:
    """Return monthly sales revenue and units sold."""
    with sqlite3.connect("retail.db") as conn:
        rows = conn.execute("""
            SELECT SUBSTR(invoice_date, 1, 7) AS month,
                   SUM(quantity),
                   ROUND(SUM(quantity * unit_price), 2)
            FROM retail_sales
            GROUP BY month
            ORDER BY month
        """).fetchall()

    return [
        {"month": r[0], "units_sold": r[1], "revenue_gbp": r[2]}
        for r in rows
    ]


def get_top_customers(limit: int = 10) -> list[dict]:
    """Find customers with the highest historical spending."""
    limit = max(1, min(limit, 50))

    with sqlite3.connect("retail.db") as conn:
        rows = conn.execute("""
            SELECT customer_id,
                   COUNT(DISTINCT invoice),
                   ROUND(SUM(quantity * unit_price), 2)
            FROM retail_sales
            WHERE customer_id IS NOT NULL
            GROUP BY customer_id
            ORDER BY SUM(quantity * unit_price) DESC
            LIMIT ?
        """, (limit,)).fetchall()

    return [
        {"customer_id": r[0], "orders": r[1],
         "total_spent_gbp": r[2]}
        for r in rows
    ]


def get_sales_by_country(limit: int = 10) -> list[dict]:
    """Rank countries by historical sales revenue."""
    limit = max(1, min(limit, 50))

    with sqlite3.connect("retail.db") as conn:
        rows = conn.execute("""
            SELECT country, COUNT(DISTINCT invoice),
                   ROUND(SUM(quantity * unit_price), 2)
            FROM retail_sales
            GROUP BY country
            ORDER BY SUM(quantity * unit_price) DESC
            LIMIT ?
        """, (limit,)).fetchall()

    return [
        {"country": r[0], "orders": r[1], "revenue_gbp": r[2]}
        for r in rows
    ]


def get_order_statistics() -> dict:
    """Return overall historical sales statistics."""
    with sqlite3.connect("retail.db") as conn:
        row = conn.execute("""
            SELECT COUNT(DISTINCT invoice),
                   COUNT(*),
                   SUM(quantity),
                   ROUND(SUM(quantity * unit_price), 2)
            FROM retail_sales
        """).fetchone()

    return {
        "total_orders": row[0],
        "sales_lines": row[1],
        "units_sold": row[2],
        "revenue_gbp": row[3]
    }


def get_slow_moving_products(limit: int = 10) -> list[dict]:
    """Find products with the fewest units sold historically."""
    limit = max(1, min(limit, 50))

    with sqlite3.connect("retail.db") as conn:
        rows = conn.execute("""
            SELECT stock_code, description,
                   SUM(quantity) AS units
            FROM retail_sales
            GROUP BY stock_code, description
            ORDER BY units ASC
            LIMIT ?
        """, (limit,)).fetchall()

    return [
        {"stock_code": r[0], "product": r[1], "units_sold": r[2]}
        for r in rows
    ]


def compare_product_sales(
    product_a: str,
    product_b: str
) -> list[dict]:
    """Compare historical sales for two product-name searches."""
    with sqlite3.connect("retail.db") as conn:
        results = []

        for product in [product_a, product_b]:
            row = conn.execute("""
                SELECT COALESCE(SUM(quantity), 0),
                       ROUND(COALESCE(SUM(quantity * unit_price), 0), 2)
                FROM retail_sales
                WHERE description LIKE ? COLLATE NOCASE
            """, (f"%{product}%",)).fetchone()

            results.append({
                "search_term": product,
                "units_sold": row[0],
                "revenue_gbp": row[1]
            })

    return results


from functools import lru_cache

@lru_cache(maxsize=32)
def get_dashboard_analytics(start_date: str | None = None, end_date: str | None = None) -> dict:
    """Consistent dashboard metrics using the same optional inclusive date range."""
    if (start_date is None) != (end_date is None):
        raise ValueError("Provide both dates or neither")
    condition = "WHERE invoice_date >= ? AND invoice_date < date(?, '+1 day')" if start_date else ""
    params = (start_date, end_date) if start_date else ()
    from contextlib import closing
    with closing(sqlite3.connect("retail.db")) as conn:
        conn.execute("PRAGMA temp_store = MEMORY")
        summary = conn.execute(f"""
            SELECT COUNT(DISTINCT invoice), COUNT(*),
                   COALESCE(SUM(quantity),0),
                   ROUND(COALESCE(SUM(quantity * unit_price),0),2)
            FROM retail_sales {condition}
        """, params).fetchone()
        months = conn.execute(f"""
            SELECT SUBSTR(invoice_date,1,7), SUM(quantity),
                   ROUND(SUM(quantity * unit_price),2)
            FROM retail_sales {condition}
            GROUP BY 1 ORDER BY 1
        """, params).fetchall()
        products = conn.execute(f"""
            SELECT stock_code, description, SUM(quantity) AS units,
                   ROUND(SUM(quantity * unit_price),2)
            FROM retail_sales {condition}
            GROUP BY stock_code, description ORDER BY units DESC LIMIT 10
        """, params).fetchall()
        customers_where = f"{condition} AND customer_id IS NOT NULL" if condition else "WHERE customer_id IS NOT NULL"
        customers = conn.execute(f"""
            SELECT customer_id, COUNT(DISTINCT invoice),
                   ROUND(SUM(quantity * unit_price),2) AS spend
            FROM retail_sales {customers_where}
            GROUP BY customer_id ORDER BY spend DESC LIMIT 10
        """, params).fetchall()
    return {
        "summary": {"total_orders": summary[0], "sales_lines": summary[1],
                    "units_sold": summary[2], "revenue_gbp": summary[3]},
        "monthly_sales": [{"month": r[0], "units_sold": r[1], "revenue_gbp": r[2]} for r in months],
        "top_products": [{"stock_code": r[0], "product": r[1], "units_sold": r[2],
                          "revenue_gbp": r[3]} for r in products],
        "top_customers": [{"customer_id": r[0], "orders": r[1],
                           "total_spent_gbp": r[2]} for r in customers],
        "start_date": start_date, "end_date": end_date,
    }
