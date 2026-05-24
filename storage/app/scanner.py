import os
from pathlib import Path
import sys
from core.scanner import PsutilScannerBackend
from core.database import Database


def main() -> None:
    """Entry point for storage-scanner.
    """

    DB_PATH = os.environ["DATABASE_PATH"]
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    usage = PsutilScannerBackend().get_disk_usage()
    result = Database(DB_PATH).store(usage)

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)
