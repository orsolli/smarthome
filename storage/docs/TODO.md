# TODO task list
Use this list to figure out what to do next.

## Format
Every task starts with `- [ ] **title**:` followed by an indented description on the next line. Sub-tasks are indented relative to their parent task.
Use `- [ ]` for incomplete tasks, `- [x]` for completed tasks, `- [/]` for in-progress tasks.

## Operations
Find the last in-progress task by searching for `- [/]` and reading the surrounding lines to get the full picture of what that task is about.

Add sub-tasks to tasks that are not completed, but is too big or vague to complete.

A task that does not require any more work must be marked as completed. The sub-tasks must be removed from this file and the parent task must be marked as in-progress if there are incomplete siblings.

## Tasks

- [/] **Scaffold**:
    Establish the initial storage package scaffold
    - [x] **Add TODO.md**:
        Add a TODO.md file to describe what needs to be done
    - [x] **Entrypoint scaffold**:
        Add executable entrypoints `storage-web` and `storage-scanner` in `pyproject.toml` and provide initial implementations in `app/web.py` and `app/scanner.py`.
    - [x] **Test scaffold**:
        Add baseline automated test coverage: create `tests/test_app.py` to verify `GET /health` returns HTTP 200 and `{"status":"ok"}`.
    - [/] **Nix scaffold**:
        Define packaging and deployment wiring
        - [x] **storage.nix**:
            Add `storage.nix` to build the python application
        - [x] **default.nix**:
            Add `default.nix` with `storage-web` service + `storage-scan` timer configuration and required environment variables.
        - [ ] **root module**:
            Include the storage module to the smarthome repository root module at `../default.nix` (relative to storage/default.nix)
- [ ] **Implement storage monitor**:
    Implement storage monitor that tracks the disk usage over time
    - [ ] **Implement scanner**:
        Implement `storage-scanner` to call `df` (via `DF_PATH` env var), parse the output, and append a row to the SQLite database at `DATABASE_PATH`.
    - [ ] **Implement frontend**:
        Implement an endpoint in `storage-web` that queries the database and returns historical disk usage data.
