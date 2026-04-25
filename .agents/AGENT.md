# Agent Notes - smarthome/vulnerabilities

Patterns, misunderstandings, and lessons learned while implementing the vulnerabilities module.

## Patterns

### Testing
- Use `unittest` (pytest is not available in this environment).
- When running tests from the `vulnerabilities/` directory, import directly from module names (e.g. `from database import ...`), **not** `from vulnerabilities.database import ...`.
- Tests should use temporary files for SQLite databases and clean them up in `tearDown`.

### Database
- `init_db()` creates tables if they don't exist — call it on every startup.
- For JOIN queries, get column names from the actual cursor's `description`, not from `SELECT * FROM table LIMIT 0` (which returns table schema, not query result schema).

### tree_parser
- Already copied into `vulnerabilities/tree_parser/` — it's a local dependency.
- Key public API: `tree_parser.merge_nix_trees(input_text: str) -> dict` (via `__init__.py`).
- Interfaces are defined in `tree_parser/interfaces/`, implementations in `tree_parser/core/`.

### Mock modules
- Mock modules replace real Nix tooling for development: `mock_derivation.py`, `mock_vulnix.py`, `mock_why_depends.py`.
- Each has a single public function that mirrors the real tool's interface.

## Misunderstandings

### 1. Column names for JOIN queries
**Wrong:** `conn.execute("SELECT * FROM vulnerability_events LIMIT 0").description`
**Right:** Get description from the actual query cursor after executing it.

### 2. Test import paths
**Wrong:** `from vulnerabilities.database import ...` (fails when running from `vulnerabilities/` directory)
**Right:** `from database import ...` (rely on current working directory in sys.path)

## Open Questions

- How should the Merger interface integrate with tree_parser's `merge_nix_trees`?
- What format does `tree_parser.merge_nix_trees` expect as input (raw text vs parsed dict)?
- Should `app.py` be in `vulnerabilities/` or at the project root?
