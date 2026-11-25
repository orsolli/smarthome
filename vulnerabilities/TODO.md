This plan follows a **top-down, abstract-to-concrete** structure. It begins with project foundations, moves to high-level architecture, defines visualization requirements, derives the database schema from those requirements, and concludes with concrete implementation steps.

### Phase 1: Project Foundation & Directory Management
**Goal:** Establish the project structure and handle existing directory conflicts.

1. [x] **Core Files**:
    * [x] Create `app.py` (Entry point).
    * [x] Create `pyproject.toml` (Dependencies: `bottle`).
    * [x] Create `default.nix` and `vulnerabilities.nix` (Standard NixOS module boilerplate).

### Phase 2: High-Level Technical Architecture
**Goal:** Define the data flow and component interactions abstractly.

The system consists of three logical layers:

1. [x] **Data Acquisition Layer**:
    * [x] Mock the nix commands so that the system can be tested on a non-nix environment.
2. [x] **Processing Layer**:
    * [x] **Merger**: Uses the local `tree_parser` to consolidate overlapping dependency paths into a single tree structure. The Merger assumes no cyclic dependencies in why-depends outputs. This is guaranteed by Nix's pure dependency graph.
    * [x] **Normalizer**: Converts the tree structure into a flat list of records suitable for database insertion.
3. [x] **Persistence & Serving Layer**:
    * [x] **Storage**: SQLite database stores scan history and current vulnerability states.
    * [x] **Server**: A Bottle web server exposes API endpoints to query the database and serve the visualization frontend.

### Phase 3: Visualization & Frontend Design
**Goal:** a historical status page showing vulnerability duration in a dependency structure.

**Current Requirements:**
* [x] **Frontend**: HTMX actions fetch tree nodes lazily on expand events.
* [x] **File Structure**: Display the dependency tree of vulnerable packages.
* [x] **Timeseries**: Visualize the frequency of specific package names becoming vulnerable over time.
* [x] **Timeseries aggregation**: If any child component is red, parent is red. Only green if all child components are green. Larger aggregation windows result in darker red (higher aggregate severity).

**Data Presentation (Time-Series):** A Timeline Bar Chart is necessary to show the history. This chart must render segmented bars, where the color and start/end points of a segment visually indicate:
* [x] **Color**: Gradient from light green (low severity) to dark red (critical). Severity mapping: Low → Medium → High → Critical, with lighter greens for cleaner states and darker reds for unmitigated.
* [x] **Interaction**: The tree must be collapsible, allowing users to drill down from the system root to specific packages and view their dependency relationships and their timeline bar chart.

### Phase 4: Database Schema Design (Derived from Visualization Needs)
**Goal:** The database schema must support the visualization requirements defined in Phase 3: historical status, structured dependency mapping, and granular vulnerability records.

**Table: `scans` (Scan Metadata)**
* `id` (INTEGER, PK): Unique scan ID.
* `timestamp` (TIMESTAMP, UNIQUE): When the scan occurred.
* `target` (TEXT): The derivation path scanned (e.g., `/nix/store/...-system`).

**Table: `vulnerability_events` (Time-Series Tracker)**
* `id` (INTEGER, PK): Unique event ID.
* `scan_id` (INTEGER, FK → `scans.id`): Links the event to a specific scan run.
* `package_name` (TEXT): The package name (e.g., `xdg-utils`).
* `drv_path` (TEXT): The unique Nix derivation path.
* `severity` (TEXT): e.g., 'CRITICAL', 'HIGH'.
* `timestamp` (TIMESTAMP): When this vulnerability was recorded.

**Table: `dependency_tree` (Structural Mapping)**
* `id` (INTEGER, PK): Unique node ID.
* `scan_id` (INTEGER, FK → `scans.id`): Link to `scans`.
* `vulnerability_event_id` (INTEGER, FK → `vulnerability_events.id`): Link to `vulnerability_events`.
* `package_name` (TEXT): The package name (e.g., `system-path`).
* `drv_path` (TEXT): The unique Nix derivation path.
* `parent_id` (INTEGER, FK → `dependency_tree.id`): Parent node reference. Null when this node is the target of the scan.
* `child_id` (INTEGER, FK → `dependency_tree.id`): Child node reference. Null for leaf nodes.

1. [x] **Initialize database**: Make sure the database is initialized upon startup of the service.
2. [x] **Query the database**: Create SELECT-queries with JOINS to get timeseries.
3. [x] **update_dependency_node**: Implemented for propagating most-critical-child up the tree during scan.

### Phase 5: Implementation Details
**Goal:** Concrete code structure and file contents.

#### 1. Mock scripts
Simulates the output of `nix derivation show`, `vulnix` and `nix why-depends` by using hardcoded values as shown below.
1. [x] The `nix derivation show` command is replaced by a mock module for development.
    * **Input**: A target path (e.g., `/run/current-system`).
    * **Output**: A JSON object of the derivation path of the package /run/current-system.
    * *Reference*:
        ```json
        {
            "/nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv": {}
        }
        ```
2. [x] The `vulnix` scanner is replaced by a mock module for development.
    * **Input**: A target path (e.g., `/nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv`).
    * **Output**: A tree-structured JSON object representing vulnerable packages.
    * *Reference*: 
        ```json
        [
            {
                "name": "Diff-9.99.0",
                "pname": "Diff",
                "version": "9.99.0",
                "derivation": "/nix/store/diffdrv0000000000000000000000000000-Diff-9.99.0.drv",
                "affected_by": [
                    "CVE-2024-13278"
                ],
                "whitelisted": [],
                "cvssv3_basescore": {
                    "CVE-2024-13278": 9.1
                },
                "description": {
                    "CVE-2024-13278": "Incorrect Authorization vulnerability in Drupal Diff allows Functionality Misuse.This issue affects Diff: from 0.0.0 before 1.8.0."
                }
            },
            {
                "name": "ShellCheck-9.99.0",
                "pname": "ShellCheck",
                "version": "9.99.0",
                "derivation": "/nix/store/shcdrv00000000000000000000000000000-ShellCheck-9.99.0.drv",
                "affected_by": [
                    "CVE-2021-28794"
                ],
                "whitelisted": [],
                "cvssv3_basescore": {
                    "CVE-2021-28794": 9.8
                },
                "description": {
                    "CVE-2021-28794": "The unofficial ShellCheck extension before 0.13.4 for Visual Studio Code mishandles shellcheck.executablePath."
                }
            }
        ]
        ```
3. [x] The `nix why-depends` command is replaced by a mock module for development.
    * **Input**: The system derivation (e.g., `/nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv`) and the vulnerable derivation (e.g., `/nix/store/diffdrv0000000000000000000000000000-Diff-9.99.0.drv`).
    * **Output**: A dependency graph tree representing which packages are affected by the vulnerable package.
    * *Reference*: 
        ```
        /nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv
        └───/nix/store/chkdrv000000000000000000000000000000-pre-switch-checks.drv
            └───/nix/store/shcdrv00000000000000000000000000000-ShellCheck-9.99.0.drv
                └───/nix/store/diffdrv0000000000000000000000000000-Diff-9.99.0.drv
        ```
4. [x] A script that runs the `nix why-depends` for every vulnerability found upon calling `vulnix` with the input from `nix derivation show`. This single script will replace all the mocks and will provide the input for the parser.
    * **Input**: A target path (e.g., `/run/current-system`).
    * **Output**: Dependency graph trees that can be fed into the Merger.
    * *Reference*:
        ```bash
        SYSTEM_DERIVATION=$(nix derivation show /run/current-system | jq -r 'keys[0]')
        vulnix "$SYSTEM_DERIVATION" -j | jq -r '.[] | .derivation' | while read VULNERABLE_DERIVATION; do
            nix why-depends "$SYSTEM_DERIVATION" "$VULNERABLE_DERIVATION"
        done
        # Outputs:
        /nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv
        └───/nix/store/chkdrv000000000000000000000000000000-pre-switch-checks.drv
            └───/nix/store/shcdrv00000000000000000000000000000-ShellCheck-9.99.0.drv
                └───/nix/store/diffdrv0000000000000000000000000000-Diff-9.99.0.drv
        /nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv
        └───/nix/store/chkdrv000000000000000000000000000000-pre-switch-checks.drv
            └───/nix/store/shcdrv00000000000000000000000000000-ShellCheck-9.99.0.drv
        ```

#### 2. `app.py` (Server & Logic)
* **Imports**: `bottle`, `sqlite3`.
* **Implemented API routes**:
    * `GET /vulnerabilities?since=...&until=...&package=...` — Queries vulnerability events.
    * `GET /tree/<scan_id>` — Returns dependency tree nodes for a scan.
    * `GET /health` — Health check endpoint.
* **Scanner Module**:
    ```python
    def run_scan(target: str):
        # 1. Scann for vulnerabilities
        raw_output = get_vulnerabilities(target)
        
        # 2. Merge trees using local tree_parser
        merged_tree = tree_parser.merge_nix_trees(raw_output['tree_output'])
        
        # 3. Normalize and store in DB
        store_scan_results(target, merged_tree)
    ```
* **API Routes**:
    * `GET /vulnerabilities?since=2000-01-01&until=2001-01-01`: Return HTMX containing timeseries aggregation for each previously vulnerable package with a parent_id matching a `scans.target`.
    * `GET /vulnerabilities?since=2000-01-01&until=2001-01-01&package=vim`: Return HTMX containing timeseries (aggregation if not leaf-node) for each previously vulnerable package with a parent_id matching vim.

#### 3. `default.nix` (NixOS Module)
Standard NixOS module definition.
* **Options**: `enable`, `database_path`, `bind_address`.
* **Services**:
    * `smarthome-vulnerability-scan` (Systemd timer).
    * `smarthome-vulnerability-web` (Systemd service running the Bottle app).

#### 4. `pyproject.toml`
```toml
[project]
name = "vulnerabilities"
version = "0.1"
dependencies = [
    "bottle",
]
```


### Phase 6: Parser Fix — Version-Aware Package Name Extraction
**Goal:** Fix `_extract_name_from_path()` to handle package names with dashes and missing versions.

#### Problem
`rsplit('-', 2)` fails when the package name contains dashes:
- `some-lib-1.0-rc1.drv` → `('1.0', 'rc1')` ❌ (should be `('some-lib', '1.0-rc1')`)
- `ed-9.99.0.drv` → `('ed', '9.99.0')` ✓ (works by accident)

#### Strategy
Split on the last dash **only if** the suffix starts with a digit (version pattern).
Strip any alphanumeric Nix hash prefix (any length).

#### Implementation Order (TDD)

1. [x] **Write tests first** in `tests/test_parser_version.py`:
    * `test_standard_version`: `/nix/store/xyz-ed-9.99.0.drv` → `('ed', '9.99.0')`
    * `test_version_with_rc`: `/nix/store/xyz-some-lib-1.0-rc1.drv` → `('some-lib', '1.0-rc1')`
    * `test_no_version`: `/nix/store/xyz-some-lib.drv` → `('some-lib', '')`
    * `test_no_version_dashes`: `/nix/store/xyz-some-lib-with-dashes.drv` → `('some-lib-with-dashes', '')`
    * `test_nix_hash_stripped`: `/nix/store/vulndrv0000000000000000000000000000-vulnerabilities-0.1.drv` → `('vulnerabilities', '0.1')`

2. [x] **Implement** in `core/parser.py::_extract_name_from_path()`:
    ```python
    import re
    
    def _extract_name_from_path(path: str) -> tuple[str, str]:
        if '/nix/store/' in path:
            filename = path.rsplit('/nix/store/', 1)[-1]
        else:
            filename = path
        
        if filename.endswith('.drv'):
            filename = filename[:-4]
        
        # Split on last dash only if suffix is version-like (starts with digit)
        match = re.match(r'^(.+)-([0-9][\w.+-]*)$', filename)
        if match:
            name, version = match.group(1), match.group(2)
            # Strip Nix hash prefix (any alphanumeric, any length)
            hash_match = re.match(r'^[0-9a-zA-Z]+-', name)
            if hash_match:
                name = name[hash_match.end():]
            return name, version
        
        return filename, ""
    ```

3. [x] **Update existing tests** (`test_core_TestParser.py`):
    * `test_complex_tree`: root name `'root-1.0'` → `'root'`
    * `test_parse_tree_block`: child `'a-1.0'` → `'a'`, grandchildren `'a1-1.0'` → `'a1'`, `'a2-1.0'` → `'a2'`


#### 5. `vulnerabilities.nix`
```nix
{ pkgs ? import <nixpkgs> { } }:
pkgs.python3Packages.buildPythonApplication {
  pname = "vulnerabilities";
  version = "0.1";
  src = ./.;
  propagatedBuildInputs = with pkgs.python3Packages; [ bottle setuptools ];
}
```

### Phase 7: Target-Scoped Timelines and Time Windows
**Goal:** a bar should describe *one machine* across the generations of that machine, and be zoomable to the window the user cares about.

**Already done in Phase 3 (identity work)**
- [x] Store hash in `drv_path` changes every rebuild, so nodes are matched by name + version + compressed lineage (`core/identity.py`).
- [x] A generation link is a different derivation of the same machine: scan it with `--as-target` (the identity recorded in `scans.target`) and `--at` (its activation date). Vulnerability events inherit the scan timestamp.
- [x] Nodes that are clean in a scan emit an explicit `NONE` event, so a fixed vulnerability ends the bar.
- [x] `package_name` is the base pname and everything after the first dash followed by a digit is the version (`...-webkitgtk-9.99.0+abi=1.0.drv` → `webkitgtk` / `9.99.0+abi=1.0`). The old greedy split left the version inside the name whenever it contained a character outside `[0-9a-z]`, so every ABI or revision rebuild of `webkitgtk`, `glibc`, `go` or `texlive.infra` looked like a new package and its bar restarted.

**Resolved**

1. [x] **The generation actually scanned was not recorded.** `scans.target` is `/run/current-system` while `scans.scanned_path` is the generation link handed to `vulnix` (`/nix/var/nix/profiles/system-3-link`), and the scan page shows it.
2. [x] **The window was global.** `get_zoom_window(conn, scan_id, days)` takes MIN/MAX over the scans of *that scan's target*, so a `/run/current-system` bar never stretches across the unrelated `~/.dotfiles/result-example` scan.
3. [x] **`/` listed scans, not identities.** It now lists targets (`list_targets`): one row per machine, with its scan count, first/last scan and worst severity; `/scan/<id>` is the generation view.
4. [x] **No zoom.** The sidebar has `7d / 30d / 90d / all` chips; `?days=N` narrows the timeline and re-requests the bars.
5. [x] **Tooltip semantics were mixed.** The bar colour is still the *subtree* maximum, but the tooltip now says whose severity it is:

    ```
    CRITICAL from 2024-11-16T14:03:16 to 2024-11-17T19:16:29
    pipewire 9.99.0
    via go 1.0.0-linux-386-bootstrap
    ```

    `subtree_worst` returns `(severity, driving descendant)`, so the cause travels with every timeline entry.

**Schema (`core/database.py`)**
- `scans.scanned_path` (TEXT, nullable): the path handed to `vulnix`. Add with a guarded `ALTER TABLE` so existing databases upgrade in place.

**Queries (`core/timeseries.py`)**
- `get_zoom_window(conn, scan_id, days)` → `(since, start, end)` over the target's scans only, padded by `pad_days`.
- `get_tree_subtree_timelines(conn, scan_id, since=None)` and `subtree_worst` take the same window.
- `list_targets(conn)` → `target, scan_count, first_scan, last_scan, latest_scan_id, worst_severity`.

**Frontend (`app/api.py`, `app/chart.py`)**
- [x] `/` renders the target list; `/scan/<id>` stays the generation view, reached from it, with a header naming the target, the generation link and the date.
- [x] `?days=30` (or `?since=`) on the tree page; chips `all / 90 / 30 / 7` that re-request the bars with the narrower window.
- [x] A node first seen inside the window keeps its leading `NONE` segment; scans outside the window are not bar boundaries.
- [x] Bars are only generated for nodes that are rendered: the bootstrap fills the roots and the first `MAX_VISIBLE_CHILDREN` children of each root, and deeper bars arrive on expansion.

**Tests (TDD order)**
1. Fixture DB with two targets and a scan outside the window; assert the window excludes the other target's scan.
2. Assert a bar for a target never spans another target's timestamp.
3. Assert `scanned_path` survives insert and is shown on the scan page.
4. Assert `?days=7` on a backfilled DB drops the segments before the cutoff but keeps the count of segments equal to the in-window scans.

**Backfill recipe** — `scripts/backfill.sh` does this; the trap to avoid is deriving
the timestamp from the wrong field: `${pair##*:}` on `3:2024-11-01T15:48:40` yields
`40`, which is how five scans ended up dated 1970.

```bash
nix-shell -p python3 python3Packages.bottle \
  --command "scripts/backfill.sh --gens 1 2 3 4 5 --db $DB"
scripts/backfill.sh --dry-run       # print the commands, scan nothing
```

Each generation is scanned through its profile link and dated with that link's own
mtime (`stat -c %Y` on a symlink does not follow it), recorded under `--as-target`
so all generations of one machine share a timeline.

**Verification checklist**
- Coverage query: `len(t) > 1` for most nodes in `get_tree_subtree_timelines(conn, scan_id)`.
- Known movers to eyeball: `ruby` (HIGH → CRITICAL → HIGH), `pipewire` (1.6.3 → 1.6.9 → 9.99.0), `cups` (HIGH 2.4.16 → MEDIUM 2.4.19), `wai-extra` (oscillating CRITICAL/LOW), `webkitgtk` (one bar across the 2.54.1/2.54.2 abi=4.1/abi=6.0 rebuilds).
- Bars only fill after a *real* click on a node header: HTMX `node-expanded` is fired by `toggleNode`, and an `eval`-based fake expansion or a class toggle never triggers the `/api/bars/...` fetch.
