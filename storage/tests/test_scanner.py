"""Tests for app module core logic."""

from datetime import datetime
import os
import tempfile
import unittest
import sys
sys.path.append(os.getcwd().split('/tests')[0])


class TestScanner(unittest.TestCase):
    """Tests for the scanner module."""

    def test_scanner_main(self):
        """Scanner main function runs without error."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as db_file:
            os.environ["DATABASE_PATH"] = db_file.name  # Use in-memory DB for testing
            from app import scanner
            scanner.main()
            from core.database import Database
            db = Database(db_file.name)
            db.cursor.execute("SELECT * FROM disk_usage")
            results = db.cursor.fetchall()
            self.assertIsInstance(results, list)
            self.assertEqual(results[0][0], 1)
            self.assertIsInstance(datetime.strptime(results[0][1], "%Y-%m-%d %H:%M:%S"), datetime)
            self.assertTrue(len(results[0][2]) > 0, 'filesystem name should be non-empty')
            self.assertTrue(results[0][3] >= results[0][4] + results[0][5], 'total_bytes should be at least used_bytes + available_bytes')
            if sys.version_info[:2] >= (3, 14):
                self.assertStartsWith(results[0][6], '/', 'mounted_on should start with "/"')

if __name__ == "__main__":
    unittest.main()
