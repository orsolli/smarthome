import logging
import sqlite3

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str):
        """Initialize the SQLite database and return a connection."""
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS disk_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                filesystem TEXT NOT NULL,
                total_bytes INTEGER NOT NULL,
                used_bytes INTEGER NOT NULL,
                available_bytes INTEGER NOT NULL,
                mounted_on TEXT NOT NULL
            );
        ''')
        self.conn.commit()

    def store(self, records):
        """Insert into SQLite."""
        try:
            for record in records:
                self.cursor.execute('''
                    INSERT INTO disk_usage 
                    (filesystem, total_bytes, used_bytes, available_bytes, mounted_on)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    record["filesystem"],
                    record["total_bytes"],
                    record["used_bytes"],
                    record["available_bytes"],
                    record["mounted_on"],
                ))
            self.conn.commit()
            return {"success": self.cursor.rowcount}
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            self.conn.rollback()
            return {"error": str(e)}
        finally:
            self.conn.close()
