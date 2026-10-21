
import openpyxl

wb = openpyxl.load_workbook(
    "online_retail_II.xlsx",
    read_only=True,
    data_only=True
)

ws = wb.worksheets[1]
rows = ws.iter_rows(values_only=True)
next(rows)  # Skip header

total = 0
missing_names = 0
cancelled = 0
invalid_quantity = 0
invalid_price = 0
valid_sales = 0

for row in rows:
    invoice, code, name, quantity, date, price, customer, country = row
    total += 1

    if not name or not str(name).strip():
        missing_names += 1

    if str(invoice).upper().startswith("C"):
        cancelled += 1

    if not isinstance(quantity, (int, float)) or quantity <= 0:
        invalid_quantity += 1

    if not isinstance(price, (int, float)) or price <= 0:
        invalid_price += 1

    # Check whether this record is a valid completed sale
    if (
        name is not None
        and str(name).strip()
        and not str(invoice).upper().startswith("C")
        and isinstance(quantity, (int, float))
        and quantity > 0
        and isinstance(price, (int, float))
        and price > 0
    ):
        valid_sales += 1

wb.close()

print("\n===== DATA QUALITY REPORT =====")
print("Total records:", total)
print("Missing product names:", missing_names)
print("Cancelled invoices:", cancelled)
print("Invalid quantities:", invalid_quantity)
print("Invalid prices:", invalid_price)

print("\n===== CLEANING RESULTS =====")
print("Valid sales records:", valid_sales)
print("Excluded records:", total - valid_sales)
print("Valid sales percentage:", round(valid_sales / total * 100, 2), "%")
