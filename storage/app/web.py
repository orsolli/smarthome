"""Entry point for the storage scanning service.

Ties together the scan database and serve results
via a Bottle web server.
"""

import os
from pathlib import Path

from bottle import Bottle, run  # type: ignore
from frontend import home
from core.database import Database


app = Bottle()


DB_PATH = os.environ["DATABASE_PATH"]
_DB_DIR = Path(DB_PATH).parent
_DB_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health_endpoint():
    """Health check endpoint.

    Returns:
        JSON health status.
    """
    return {"status": "ok"}


@app.get("/")
def home_endpoint():
    return home.root()


@app.get("/get_filesystems")
def get_filesystems_endpoint():
    return home.get_filesystems(Database(DB_PATH).get_filesystems())


@app.get("/get_usage_history/")
@app.get("/get_usage_history/<mounted_on:path>")
def get_usage_history_endpoint(mounted_on="/"):
    mounted_on = "/" + mounted_on.strip("/")  # Ensure it starts with "/"
    print(f"Received request for usage history of mounted_on: {mounted_on}")
    return home.get_usage_history(mounted_on, Database(DB_PATH).get_usage_history(mounted_on))


def main():
    """Run the Bottle server."""
    host, port = os.environ.get("BIND_ADDRESS", "localhost:8080").split(":")
    run(app, host=host, port=int(port), debug=True)


if __name__ == "__main__":
    main()
