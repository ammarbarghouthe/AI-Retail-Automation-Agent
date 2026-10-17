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

    connection.commit()
    connection.close()

    print("Database and products table created successfully!")


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
if __name__ == "__main__":
    create_database()
    print(get_products())