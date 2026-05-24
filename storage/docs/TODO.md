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

- [x] **Scaffold**:
    Establish the initial storage package scaffold
- [/] **Implement storage monitor**:
    Implement storage monitor that tracks the disk usage over time
    - [x] **Implement scanner**:
        Implement `storage-scanner`, parse the output, and append a row to the SQLite database at `DATABASE_PATH`.
    - [ ] **Implement frontend**:
        Implement an endpoint in `storage-web` that queries the database and returns historical disk usage data.
