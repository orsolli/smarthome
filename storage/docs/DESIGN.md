**Relevant Files**
*   `storage/README.md` — Primary documentation entry point.
*   `storage/docs/DESIGN.md` — Dedicated file for architectural diagrams and deep dives.
*   `storage/app/web.py` — Source for API reference.
*   `storage/app/scanner.py` — Source for background process documentation.
*   `storage/default.nix` — Source for deployment and service lifecycle documentation.
*   `storage/pyproject.toml` — Source for dependency and package structure guidelines.

## API reference
*   `/health` — Health check endpoint

## Background process
timer -> df -> sqlite

## Deployment
Trigger bin/storage-scanner regularly providing environment variables for the df executable and a path to the database.
Start a service that executes bin/storage-web to host the web-server providing environment variables for the binding host and a path to the database.

## Package structure
*   `storage/tests/` — All tests should be stored in this test-folder
*   `storage/app/` — All python entrypoints should be stored inside this app-folder
*   `storage/docs/` — All documentation should be stored inside this docs-folder
