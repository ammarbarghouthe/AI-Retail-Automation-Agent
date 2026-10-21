
import sqlite3
import openpyxl

EXCEL_FILE = "online_retail_II.xlsx"
DATABASE_FILE = "retail.db"
BATCH_SIZE = 5000

connection = sqlite3.connect(DATABASE_FILE)
cursor = connection.cursor()

# Prevent accidental duplicate imports.
existing = cursor.execute(
    "SELECT COUNT(*) FROM retail_sales"
).fetchone()[0]

if existing > 0:
    connection.close()
    print(f"Import skipped: retail_sales already contains {existing} rows.")
    raise SystemExit

workbook = openpyxl.load_workbook(
    EXCEL_FILE,
    read_only=True,
    data_only=True
)

total_imported = 0
batch = []

try:
    for sheet in workbook.worksheets:
        print(f"Processing: {sheet.title}", flush=True)

        rows = sheet.iter_rows(values_only=True)
        next(rows)  # Skip column headers

        for row in rows:
            invoice, code, name, quantity, date, price, customer, country = row

            # Keep valid completed sales only.
            if (
                name is None
                or not str(name).strip()
                or str(invoice).upper().startswith("C")
                or not isinstance(quantity, (int, float))
                or quantity <= 0
                or not isinstance(price, (int, float))
                or price <= 0
            ):
                continue

            batch.append((
                str(invoice),
                str(code),
                str(name).strip(),
                int(quantity),
                date.isoformat() if date else None,
                float(price),
                str(customer) if customer is not None else None,
                str(country) if country is not None else None
            ))

            if len(batch) >= BATCH_SIZE:
                cursor.executemany("""
                    INSERT INTO retail_sales (
                        invoice, stock_code, description,
                        quantity, invoice_date, unit_price,
                        customer_id, country
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)

                total_imported += len(batch)
                batch.clear()

                print(f"Imported {total_imported:,} rows", flush=True)

    if batch:
        cursor.executemany("""
            INSERT INTO retail_sales (
                invoice, stock_code, description,
                quantity, invoice_date, unit_price,
                customer_id, country
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, batch)

        total_imported += len(batch)

    # Commit only after both worksheets finish successfully.
    connection.commit()
    print(f"\nSUCCESS! Imported {total_imported:,} sales records.")

except Exception:
    connection.rollback()
    print("Import failed. Changes rolled back.")
    raise

finally:
    workbook.close()
    connection.close()
