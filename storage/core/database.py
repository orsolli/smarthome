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

    def get_filesystems(self):
        """Fetch all filesystems from the database."""
        try:
            self.cursor.execute('SELECT DISTINCT mounted_on FROM disk_usage')
            rows = self.cursor.fetchall()
            filesystems = []
            for row in rows:
                filesystems.append({
                    "mounted_on": row[0],
                })
            return filesystems
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return {"error": str(e)}
        finally:
            self.conn.close()

    def get_usage_history(self, mounted_on, days=7):
        """Fetches raw usage history for high-res line chart (all measurements).
        
        Args:
            mounted_on: The mount point to query.
            days: Number of days of history to retrieve (default 7).
        """
        try:
            self.cursor.execute('''
                SELECT timestamp, total_bytes, used_bytes, available_bytes 
                FROM disk_usage 
                WHERE mounted_on = ?
                AND total_bytes > 0
                AND timestamp > datetime('now', ? || ' days')
                ORDER BY timestamp ASC
            ''', (mounted_on, f'-{days}'))
            rows = self.cursor.fetchall()
            usage_history = []
            for row in rows:
                usage_history.append({
                    "timestamp": row[0],
                    "total_bytes": row[1],
                    "used_bytes": row[2],
                    "available_bytes": row[3],
                })
            return usage_history
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []
        finally:
            self.conn.close()

    def get_usage_history_daily(self, mounted_on, days=365):
        """Fetches daily aggregated usage for candlestick charts (1 candle/day).
        
        Each candle represents one day:
        - Open: used_bytes at first scan of the day
        - High: max used_bytes during the day
        - Low: min used_bytes during the day
        - Close: used_bytes at last scan of the day
        
        Args:
            mounted_on: The mount point to query.
            days: Number of days of history to retrieve (default 365).
        """
        try:
            self.cursor.execute('''
                SELECT 
                    date(timestamp) as day,
                    MIN(timestamp) as first_ts,
                    MAX(timestamp) as last_ts,
                    (SELECT used_bytes FROM disk_usage 
                     WHERE mounted_on = ? AND date(timestamp) = date(d.timestamp)
                     ORDER BY timestamp ASC LIMIT 1) as open_val,
                    MAX(used_bytes) as high_val,
                    MIN(used_bytes) as low_val,
                    (SELECT used_bytes FROM disk_usage 
                     WHERE mounted_on = ? AND date(timestamp) = date(d.timestamp)
                     ORDER BY timestamp DESC LIMIT 1) as close_val,
                    MAX(total_bytes) as max_total
                FROM disk_usage d
                WHERE mounted_on = ?
                AND total_bytes > 0
                AND date(timestamp) >= date('now', ? || ' days')
                GROUP BY date(timestamp)
                ORDER BY day ASC
            ''', (mounted_on, mounted_on, mounted_on, f'-{days}'))
            rows = self.cursor.fetchall()
            usage_history = []
            for row in rows:
                usage_history.append({
                    "timestamp": row[0],  # day string YYYY-MM-DD
                    "open_bytes": row[3],
                    "high_bytes": row[4],
                    "low_bytes": row[5],
                    "close_bytes": row[6],
                    "total_bytes": row[7],
                })
            return usage_history
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []
        finally:
            self.conn.close()
