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
