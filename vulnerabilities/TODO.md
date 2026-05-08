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
* [ ] **Frontend**: HTMX actions fetch tree nodes lazily on expand events.
* [ ] **File Structure**: Display the dependency tree of vulnerable packages.
* [ ] **Timeseries**: Visualize the frequency of specific package names becoming vulnerable over time.
* [ ] **Timeseries aggregation**: If any child component is red, parent is red. Only green if all child components are green. Larger aggregation windows result in darker red (higher aggregate severity).

**Data Presentation (Time-Series):** A Timeline Bar Chart is necessary to show the history. This chart must render segmented bars, where the color and start/end points of a segment visually indicate:
* [ ] **Color**: Gradient from light green (low severity) to dark red (critical). Severity mapping: Low → Medium → High → Critical, with lighter greens for cleaner states and darker reds for unmitigated.
* [ ] **Interaction**: The tree must be collapsible, allowing users to drill down from the system root to specific packages and view their dependency relationships and their timeline bar chart.

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
            "/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv": {}
        }
        ```
2. [x] The `vulnix` scanner is replaced by a mock module for development.
    * **Input**: A target path (e.g., `/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv`).
    * **Output**: A tree-structured JSON object representing vulnerable packages.
    * *Reference*: 
        ```json
        [
            {
                "name": "Diff-1.0.2",
                "pname": "Diff",
                "version": "1.0.2",
                "derivation": "/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv",
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
                "name": "ShellCheck-0.11.0",
                "pname": "ShellCheck",
                "version": "0.11.0",
                "derivation": "/nix/store/b2cnc4mi1dvmcbsx1fnjfpwrc4srsisp-ShellCheck-0.11.0.drv",
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
    * **Input**: The system derivation (e.g., `/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv`) and the vulnerable derivation (e.g., `/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv`).
    * **Output**: A dependency graph tree representing which packages are affected by the vulnerable package.
    * *Reference*: 
        ```
        /nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv
        └───/nix/store/zq99dyzglrigchn618wkncr9fxcd5qsc-pre-switch-checks.drv
            └───/nix/store/b2cnc4mi1dvmcbsx1fnjfpwrc4srsisp-ShellCheck-0.11.0.drv
                └───/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv
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
        /nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv
        └───/nix/store/zq99dyzglrigchn618wkncr9fxcd5qsc-pre-switch-checks.drv
            └───/nix/store/b2cnc4mi1dvmcbsx1fnjfpwrc4srsisp-ShellCheck-0.11.0.drv
                └───/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv
        /nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv
        └───/nix/store/zq99dyzglrigchn618wkncr9fxcd5qsc-pre-switch-checks.drv
            └───/nix/store/b2cnc4mi1dvmcbsx1fnjfpwrc4srsisp-ShellCheck-0.11.0.drv
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
- `ed-1.22.5.drv` → `('ed', '1.22.5')` ✓ (works by accident)

#### Strategy
Split on the last dash **only if** the suffix starts with a digit (version pattern).
Strip any alphanumeric Nix hash prefix (any length).

#### Implementation Order (TDD)

1. [x] **Write tests first** in `tests/test_parser_version.py`:
    * `test_standard_version`: `/nix/store/xyz-ed-1.22.5.drv` → `('ed', '1.22.5')`
    * `test_version_with_rc`: `/nix/store/xyz-some-lib-1.0-rc1.drv` → `('some-lib', '1.0-rc1')`
    * `test_no_version`: `/nix/store/xyz-some-lib.drv` → `('some-lib', '')`
    * `test_no_version_dashes`: `/nix/store/xyz-some-lib-with-dashes.drv` → `('some-lib-with-dashes', '')`
    * `test_nix_hash_stripped`: `/nix/store/f8w6rdvahz02m1qlmv7fwvkljb1i1aq2-vulnerabilities-0.1.drv` → `('vulnerabilities', '0.1')`

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
