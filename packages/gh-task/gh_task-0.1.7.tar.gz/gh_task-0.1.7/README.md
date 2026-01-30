# gh-task

Python + CLI helpers for taking, moving, and releasing GitHub Project (v2) issues using a lightweight ownership label protocol.

## Install (local)

```bash
pip install -e .
```

## Prerequisites

`gh` must be installed and authenticated (the library uses it to fetch a token if no `GH_TOKEN`/`GITHUB_TOKEN` is set).

## Auth

Uses `GH_TOKEN` or `GITHUB_TOKEN` if set, otherwise falls back to `gh auth token`. Ensure the token has the `project` scope for Project v2 access.

## Python usage

```python
from gh_task import Project

project = Project(
    project="https://github.com/users/yieldthought/projects/3/views/1",
    name="my-name",
    has_label=["bug", "help wanted"],
)

# list status columns (project can be a short ref or full URL)
print(project.list())

# list issue numbers in Backlog
print(project.list("Backlog"))

# take a specific issue (number, URL, or owner/repo#number)
issue_id = project.take(2)

# take the first available issue in Backlog that matches the label filter
issue_id = project.take("Backlog")

# move and release
project.move(2, "In review")
project.release(2)

# context-managed lease (auto-release on exit)
with project.lease("Backlog") as issue:
    print(issue.number)

# create a new issue and add it to the project
issue = project.create(
    title="Investigate latency spikes",
    description="See logs from Jan 24",
    status="Backlog",
    repo="yieldthought/gh-task",  # optional if the project has a single repo
    label="bug",
)
```

## CLI

```bash
# list status columns
 gh-task list -p yieldthought/projects/3 -n my-name

# list issues in Backlog
 gh-task list -p yieldthought/projects/3 -n my-name Backlog

# take a specific issue
 gh-task take -p yieldthought/projects/3 -n my-name -i 2

# take the first available issue in Backlog
 gh-task take -p yieldthought/projects/3 -n my-name -l "bug,help wanted" Backlog

# move and release
 gh-task move -p yieldthought/projects/3 -n my-name -i 2 -s "In review"
 gh-task release -p yieldthought/projects/3 -n my-name -i 2

# create a new issue and add it to the project (repo inferred if possible)
 gh-task create -p yieldthought/projects/3 -r yieldthought/gh-task -t "Fix retry logic" -d "Add jitter + cap"
 gh-task create -p yieldthought/projects/3 -t "Investigate latency spikes" -s Backlog --label bug
```

## Label filtering

`has_label` (or `--label/-l`) restricts `.list()` and `.take()` to issues that carry at least one of the provided labels.
When taking a specific issue, a `TakeError` is raised if it does not match the filter.

## Ownership protocol

`take()` performs the following:
1. Verify there is no label starting with `owner:`.
2. Add a comment `Taking: <name>`.
3. Wait 1s (configurable) and fetch all comments beginning with `Taking:`.
4. If the earliest `Taking:` comment is yours, add `owner: <name>` label.
5. Remove your `Taking:` comment (best-effort).

If any step fails, the comment is removed and a `TakeError` is raised.
