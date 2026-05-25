"""Entry point for the storage scanning service.

Ties together the scan database and serve results
via a Bottle web server.
"""

import json
import os
from pathlib import Path

from bottle import Bottle, request, run  # type: ignore
from frontend import home
from core.database import Database


app = Bottle()


Path(os.environ["DATABASE_PATH"]).parent.mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health_endpoint():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
def home_endpoint():
    return home.root()


@app.get("/get_filesystems")
def get_filesystems_endpoint():
    """Return filesystem cards as HTML for HTMX swap."""
    
    db = Database(os.environ["DATABASE_PATH"])
    filesystems = db.get_filesystems()
    return home.get_filesystems(filesystems)


@app.get("/get_usage_history/") # For mounted_on = "/"
@app.get("/get_usage_history/<mounted_on:path>")
def get_usage_history_endpoint(mounted_on="/"):
    """Return usage history as JSON.
    
    Query params:
        range: '1w' (high-res line chart, all measurements) or '1y' (low-res candlestick, daily)
    """
    mounted_on = "/" + mounted_on.strip("/")
    range_param = request.query.get("range", "1w")
    
    db = Database(os.environ["DATABASE_PATH"])
    
    if range_param == "1y":
        # Low-res: 1 candlestick per day over 1 year
        data = db.get_usage_history_daily(mounted_on, days=365)
    else:
        # High-res: all measurements over 1 week
        data = db.get_usage_history(mounted_on, days=7)
    
    return json.dumps(data)


def main():
    """Run the Bottle server."""
    host, port = os.environ.get("BIND_ADDRESS", "localhost:8080").split(":")
    run(app, host=host, port=int(port), debug=True)


if __name__ == "__main__":
    main()
