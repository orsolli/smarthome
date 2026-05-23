"""Entry point for the storage scanning service.

Ties together the scan database and serve results
via a Bottle web server.
"""

import os
from pathlib import Path

from bottle import Bottle, run  # type: ignore


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


def main():
    """Run the Bottle server."""
    host, port = os.environ.get("BIND_ADDRESS", "localhost:8080").split(":")
    run(app, host=host, port=int(port), debug=True)


if __name__ == "__main__":
    main()
