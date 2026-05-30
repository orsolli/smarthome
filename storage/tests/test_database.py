"""Tests for app module core logic."""

from datetime import datetime, timedelta
import os
import tempfile
from time import sleep
import unittest
import sys
sys.path.append(os.getcwd().split('/tests')[0])


class TestDatabase(unittest.TestCase):
    """Tests for the database module."""

    def test_database_store(self):
        """Database store function updates correctly."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as db_file:
            from core.database import Database
            for _ in range(3):
                result = Database(db_file.name).store([{
                    "filesystem": "/dev/sda1",
                    "total_bytes": 1000000,
                    "used_bytes": 500000,
                    "available_bytes": 500000,
                    "mounted_on": "/"
                }]*5)
                assert result["success"] == 1, 'Store should return success for valid record'
                sleep(1)  # Ensure timestamp difference
            results = Database(db_file.name).get_usage_history("/")
            self.assertIsInstance(results, list)
            self.assertEqual(len(results), 2, 'Should compress equal records into 2 entries')
            self.assertEqual(timedelta(seconds=2) + datetime.strptime(results[0]["timestamp"], "%Y-%m-%d %H:%M:%S"), datetime.strptime(results[1]["timestamp"], "%Y-%m-%d %H:%M:%S"))
            self.assertTrue(results[0], results[1])

if __name__ == "__main__":
    unittest.main()
