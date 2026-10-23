# RetailAI — AI Retail Operations Analytics

A FastAPI + SQLite retail analytics portfolio prototype with an interactive dashboard and a Gemini-powered natural-language assistant.

## Features
- Revenue, order and units-sold KPIs
- Monthly revenue chart, top-selling products and top customers
- **Consistent date-range filtering** across all dashboard visualizations
- Gemini AI assistant with database-backed tools, formatted tables and a loading indicator
- Cached dashboard queries for repeat date ranges
- API and database tests using a small synthetic dataset

## Tech stack
Python, FastAPI, SQLite, Google Gemini API (`gemini-3.5-flash-lite`), HTML, CSS, JavaScript, Chart.js.

## Data notes
The `retail_sales` data comes from a historical online retail dataset (2009–2011), **not** live store transactions. The separate `products` table is a small demo inventory and is not synchronized with historical sales. Revenue is in GBP. This repository intentionally excludes the dataset/database, spreadsheet source and API credentials.

## Setup (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env` and insert your own `GEMINI_API_KEY`. Do not commit this file.

The dashboard analytics require a local `retail.db` populated with a `retail_sales` table. The expected columns are: `invoice`, `stock_code`, `description`, `quantity`, `invoice_date` (ISO date or datetime text), `unit_price`, `customer_id`, `country`. The source database is not included, so the historical dashboard will not work until the dataset is imported. To create the small demo inventory table, run `python database.py`.

Start the application:
```powershell
python -m uvicorn main:app --reload --port 8080
```
Open `http://127.0.0.1:8080/dashboard`. API docs: `http://127.0.0.1:8080/docs`.

## Testing
```powershell
python -m unittest -v test_project.py
```
The database tests use a temporary synthetic SQLite database and do not need the historical dataset. The API tests mock the dashboard data and do not call Gemini.

## Main endpoints
- `GET /analytics/dashboard` — complete dashboard data
- `GET /analytics/dashboard?start_date=2010-01-01&end_date=2010-12-31` — filtered data
- `POST /ai/chat` — `{ "message": "What are the top-selling products?" }`
- `GET /products`, `POST /products` — demo inventory

## Security and limitations
- Never publish `.env` or `retail.db` (may contain customer IDs).
- Chat requests use an external Gemini API and may incur charges or rate limits.
- Dashboard caching is process-local and assumes historical data is unchanged while the server runs. Restart the server if historical sales data is re-imported.
- The dashboard uses Chart.js via CDN, so charts need internet access.
- This is a portfolio prototype, not a production POS, live inventory system or authenticated multi-user platform.
