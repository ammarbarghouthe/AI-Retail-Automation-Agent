
"""Run with: python -m unittest -v test_project.py"""

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database


class DashboardDatabaseTests(unittest.TestCase):

    def setUp(self):
        # Create a temporary database for testing.
        # This does NOT modify your real retail.db file.
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp.name) / "sample.db")

        conn = sqlite3.connect(self.db_path)

        try:
            conn.execute("""
                CREATE TABLE retail_sales (
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

            conn.executemany(
                "INSERT INTO retail_sales VALUES (?,?,?,?,?,?,?,?)",
                [
                    (
                        "A", "P1", "Milk", 2,
                        "2010-01-15 10:00:00", 3, "C1", "UK"
                    ),
                    (
                        "B", "P2", "Bread", 4,
                        "2010-02-20 10:00:00", 2, "C2", "UK"
                    ),
                    (
                        "C", "P1", "Milk", 5,
                        "2011-01-10 10:00:00", 3, "C1", "UK"
                    ),
                ]
            )

            conn.commit()

        finally:
            # Explicitly release the SQLite file on Windows.
            conn.close()

        self.original_connect = sqlite3.connect

        database.get_dashboard_analytics.cache_clear()

        self.patcher = patch.object(
            database.sqlite3,
            "connect",
            side_effect=lambda path: self.original_connect(
                self.db_path
            )
        )

        self.patcher.start()

    def tearDown(self):
        # Restore the original SQLite connection function.
        self.patcher.stop()

        # Clear cached results between tests.
        database.get_dashboard_analytics.cache_clear()

        # Delete the temporary test database.
        self.temp.cleanup()

    def test_all_time_metrics(self):
        data = database.get_dashboard_analytics()

        self.assertEqual(
            data["summary"]["total_orders"], 3
        )

        self.assertEqual(
            data["summary"]["units_sold"], 11
        )

        self.assertEqual(
            data["summary"]["revenue_gbp"], 29
        )

        self.assertEqual(
            len(data["monthly_sales"]), 3
        )

    def test_date_range_updates_every_section(self):
        data = database.get_dashboard_analytics(
            "2010-01-01",
            "2010-01-31"
        )

        self.assertEqual(
            data["summary"]["total_orders"], 1
        )

        self.assertEqual(
            data["summary"]["revenue_gbp"], 6
        )

        self.assertEqual(
            [r["month"] for r in data["monthly_sales"]],
            ["2010-01"]
        )

        self.assertEqual(
            [r["product"] for r in data["top_products"]],
            ["Milk"]
        )

        self.assertEqual(
            [r["customer_id"] for r in data["top_customers"]],
            ["C1"]
        )

    def test_empty_date_range(self):
        data = database.get_dashboard_analytics(
            "2012-01-01",
            "2012-12-31"
        )

        self.assertEqual(
            data["summary"]["revenue_gbp"], 0
        )

        self.assertEqual(
            data["top_products"], []
        )


class DashboardApiTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault(
            "GEMINI_API_KEY",
            "test-key-not-used"
        )

        try:
            from fastapi.testclient import TestClient
            import main

        except ImportError as exc:
            raise unittest.SkipTest(
                f"Install requirements first: {exc}"
            )

        cls.client = TestClient(main.app)
        cls.main = main

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_invalid_date_order(self):
        result = self.client.get(
            "/analytics/dashboard"
            "?start_date=2011-01-01"
            "&end_date=2010-01-01"
        )

        self.assertEqual(
            result.status_code, 400
        )

    def test_missing_end_date(self):
        result = self.client.get(
            "/analytics/dashboard"
            "?start_date=2010-01-01"
        )

        self.assertEqual(
            result.status_code, 400
        )

    def test_invalid_date_format(self):
        result = self.client.get(
            "/analytics/dashboard"
            "?start_date=abc"
            "&end_date=2010-01-01"
        )

        self.assertEqual(
            result.status_code, 400
        )

    def test_dashboard_endpoint(self):
        with patch.object(
            self.main,
            "get_dashboard_analytics",
            return_value={
                "summary": {
                    "total_orders": 2
                }
            }
        ):
            result = self.client.get(
                "/analytics/dashboard"
            )

        self.assertEqual(
            result.status_code, 200
        )

        self.assertEqual(
            result.json()["summary"]["total_orders"],
            2
        )


if __name__ == "__main__":
    unittest.main()
