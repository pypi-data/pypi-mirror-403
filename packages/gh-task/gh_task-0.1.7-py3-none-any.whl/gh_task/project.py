import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
from urllib.parse import quote

from .errors import (
    ApiError,
    ConfigError,
    CreateError,
    MoveError,
    NotFoundError,
    OwnershipError,
    ReleaseError,
    TakeError,
)
from .github import GitHubClient


PROJECT_QUERY_USER = """
query($login: String!, $number: Int!) {
  user(login: $login) {
    projectV2(number: $number) {
      id
      title
      fields(first: 100) {
        nodes {
          __typename
          ... on ProjectV2Field {
            id
            name
          }
          ... on ProjectV2IterationField {
            id
            name
          }
          ... on ProjectV2SingleSelectField {
            id
            name
            options {
              id
              name
            }
          }
        }
      }
    }
  }
}
"""

PROJECT_QUERY_ORG = """
query($login: String!, $number: Int!) {
  organization(login: $login) {
    projectV2(number: $number) {
      id
      title
      fields(first: 100) {
        nodes {
          __typename
          ... on ProjectV2Field {
            id
            name
          }
          ... on ProjectV2IterationField {
            id
            name
          }
          ... on ProjectV2SingleSelectField {
            id
            name
            options {
              id
              name
            }
          }
        }
      }
    }
  }
}
"""

VIEWER_QUERY = """
query {
  viewer { login }
}
"""

ITEMS_QUERY = """
query($projectId: ID!, $cursor: String, $statusField: String!) {
  node(id: $projectId) {
    ... on ProjectV2 {
      items(first: 100, after: $cursor) {
        nodes {
          id
          fieldValueByName(name: $statusField) {
            ... on ProjectV2ItemFieldSingleSelectValue {
              name
            }
          }
          content {
            __typename
            ... on Issue {
              number
              title
              url
              repository { nameWithOwner }
            }
            ... on PullRequest {
              number
              title
              url
              repository { nameWithOwner }
            }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

UPDATE_STATUS_MUTATION = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $projectId,
    itemId: $itemId,
    fieldId: $fieldId,
    value: { singleSelectOptionId: $optionId }
  }) {
    projectV2Item { id }
  }
}
"""

UPDATE_NUMBER_MUTATION = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $number: Float!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $projectId,
    itemId: $itemId,
    fieldId: $fieldId,
    value: { number: $number }
  }) {
    projectV2Item { id }
  }
}
"""

CLEAR_FIELD_MUTATION = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!) {
  clearProjectV2ItemFieldValue(input: {
    projectId: $projectId,
    itemId: $itemId,
    fieldId: $fieldId
  }) {
    projectV2Item { id }
  }
}
"""

ADD_ITEM_MUTATION = """
mutation($projectId: ID!, $contentId: ID!) {
  addProjectV2ItemById(input: { projectId: $projectId, contentId: $contentId }) {
    item { id }
  }
}
"""

COMMENT_VISIBILITY_TIMEOUT_SECONDS = 60.0


@dataclass(frozen=True)
class Issue:
    """Lightweight Issue model used by gh-task."""
    number: int
    repo: str
    title: Optional[str] = None
    url: Optional[str] = None
    body: Optional[str] = None
    status: Optional[str] = None
    project_item_id: Optional[str] = None
    labels: Optional[List[str]] = None


class IssueLease:
    """Context manager that releases an issue on exit."""
    def __init__(self, project: "Project", issue: Issue) -> None:
        self.project = project
        self.issue = issue

    def __enter__(self) -> Issue:
        return self.issue

    def __exit__(self, exc_type, exc, tb) -> bool:
        try:
            self.project.release(self.issue)
        except Exception:
            if exc_type is None:
                raise
        return False


class Project:
    """Interact with a GitHub Project (v2) using the gh-task ownership protocol."""
    def __init__(
        self,
        project: str,
        name: Optional[str] = None,
        token: Optional[str] = None,
        has_label: Optional[Union[str, Iterable[str]]] = None,
    ) -> None:
        """Create a Project helper.

        Args:
            project: Project reference (e.g. "owner/projects/3" or full URL).
            name: Owner name used for the "owner: <name>" label (required for take/move/release).
            token: GitHub token; defaults to GH_TOKEN/GITHUB_TOKEN or gh auth token.
            has_label: Optional label filter (string or list). When set, only issues
                with at least one matching label are considered by list/take.
        """
        if not project:
            raise ConfigError("Project reference is required")
        self.client = GitHubClient(token=token)
        self.owner, self.number = _parse_project_ref(project)
        if self.owner == "@me":
            self.owner = self._viewer_login()
        self.name = name
        self.owner_label = f"owner: {self.name}" if self.name else None
        self._label_filter = _normalize_label_filter(has_label)
        self._project_id: Optional[str] = None
        self._status_field_id: Optional[str] = None
        self._status_field_name: Optional[str] = None
        self._status_options: List[Dict[str, str]] = []
        self._status_by_lower: Dict[str, Dict[str, str]] = {}
        self._number_fields_by_lower: Dict[str, Dict[str, str]] = {}
        self._owner_type: Optional[str] = None

    def __enter__(self) -> "Project":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def _require_owner_name(self) -> None:
        if not self.name:
            raise ConfigError("Owner name is required for this operation")

    def statuses(self) -> List[str]:
        """Return the available status column names."""
        self._ensure_project_loaded()
        return [opt["name"] for opt in self._status_options]

    def list(self, status: Optional[str] = None, *, return_issue: bool = False) -> List[Any]:
        """List statuses or issue numbers (or Issue objects) for a status column."""
        if status is None:
            return self.statuses()
        items = self._list_items()
        status_name = self._resolve_status_name(status)
        matches = [
            item
            for item in items
            if (item.status or "").lower() == status_name.lower() and self._issue_matches_label(item)
        ]
        if return_issue:
            return matches
        return [item.number for item in matches]

    def take(
        self,
        issue_id: Optional[Union[int, str, Issue]] = None,
        status: Optional[str] = None,
        *,
        repo: Optional[str] = None,
        wait_seconds: float = 1.0,
        return_issue: bool = False,
        lease: bool = False,
    ) -> Union[int, Issue, IssueLease]:
        """Take an issue by id or first available issue in a status column.

        If a label filter is set, only matching issues are eligible.
        """
        self._require_owner_name()
        if issue_id is None and status is None:
            raise TakeError("Provide an issue id or a status to take")
        if status is None and issue_id is not None and _looks_like_status(issue_id):
            status = str(issue_id)
            issue_id = None

        if issue_id is None:
            status_name = self._resolve_status_name(status)
            items = self.list(status_name, return_issue=True)
            for issue in items:
                if self._try_take(issue, wait_seconds=wait_seconds, strict=False):
                    return self._wrap_take_result(issue, return_issue, lease)
            label_hint = self._label_filter_hint()
            raise TakeError(f"No available issues to take in status '{status_name}'{label_hint}")

        issue = self._resolve_issue(issue_id, repo=repo)
        if not self._issue_matches_label(issue):
            raise TakeError(
                f"Issue {issue.repo}#{issue.number} does not match label filter{self._label_filter_hint()}"
            )
        if not self._try_take(issue, wait_seconds=wait_seconds, strict=True):
            raise TakeError(f"Failed to take issue {issue.repo}#{issue.number}")
        return self._wrap_take_result(issue, return_issue, lease)

    def lease(
        self,
        issue_id: Optional[Union[int, str, Issue]] = None,
        status: Optional[str] = None,
        *,
        repo: Optional[str] = None,
        wait_seconds: float = 1.0,
    ) -> IssueLease:
        """Context-managed variant of take() that releases on exit."""
        result = self.take(
            issue_id=issue_id,
            status=status,
            repo=repo,
            wait_seconds=wait_seconds,
            return_issue=True,
            lease=True,
        )
        if isinstance(result, IssueLease):
            return result
        return IssueLease(self, result)

    def move(self, issue_id: Union[int, str, Issue], status: str, *, repo: Optional[str] = None) -> Issue:
        """Move an owned issue to a new status column."""
        self._require_owner_name()
        issue = self._resolve_issue(issue_id, repo=repo, require_project_item=True)
        if not self._is_owned_by_me(issue):
            raise OwnershipError(f"You do not own issue {issue.repo}#{issue.number}")
        status_name, option_id = self._resolve_status(status)
        self._ensure_project_loaded()
        try:
            self.client.graphql(
                UPDATE_STATUS_MUTATION,
                {
                    "projectId": self._project_id,
                    "itemId": issue.project_item_id,
                    "fieldId": self._status_field_id,
                    "optionId": option_id,
                },
            )
        except Exception as exc:
            raise MoveError(f"Failed to move issue {issue.repo}#{issue.number} to '{status_name}'") from exc
        return Issue(
            number=issue.number,
            repo=issue.repo,
            title=issue.title,
            url=issue.url,
            body=issue.body,
            status=status_name,
            project_item_id=issue.project_item_id,
        )

    def set_number_field(
        self,
        issue_id: Union[int, str, Issue],
        field_name: str,
        value: Union[int, float],
        *,
        repo: Optional[str] = None,
    ) -> Issue:
        """Set a numeric project field value on an owned issue."""
        self._require_owner_name()
        issue = self._resolve_issue(issue_id, repo=repo, require_project_item=True)
        if not self._is_owned_by_me(issue):
            raise OwnershipError(f"You do not own issue {issue.repo}#{issue.number}")
        field = self._resolve_number_field(field_name)
        self._ensure_project_loaded()
        try:
            self.client.graphql(
                UPDATE_NUMBER_MUTATION,
                {
                    "projectId": self._project_id,
                    "itemId": issue.project_item_id,
                    "fieldId": field["id"],
                    "number": float(value),
                },
            )
        except Exception as exc:
            raise MoveError(
                f"Failed to set '{field_name}' for issue {issue.repo}#{issue.number}"
            ) from exc
        return issue

    def clear_number_field(
        self,
        issue_id: Union[int, str, Issue],
        field_name: str,
        *,
        repo: Optional[str] = None,
    ) -> Issue:
        """Clear a numeric project field value on an owned issue."""
        self._require_owner_name()
        issue = self._resolve_issue(issue_id, repo=repo, require_project_item=True)
        if not self._is_owned_by_me(issue):
            raise OwnershipError(f"You do not own issue {issue.repo}#{issue.number}")
        field = self._resolve_number_field(field_name)
        self._ensure_project_loaded()
        try:
            self.client.graphql(
                CLEAR_FIELD_MUTATION,
                {
                    "projectId": self._project_id,
                    "itemId": issue.project_item_id,
                    "fieldId": field["id"],
                },
            )
        except Exception as exc:
            raise MoveError(
                f"Failed to clear '{field_name}' for issue {issue.repo}#{issue.number}"
            ) from exc
        return issue

    def set_estimate(
        self,
        issue_id: Union[int, str, Issue],
        value: Optional[Union[int, float]],
        *,
        repo: Optional[str] = None,
        field_name: str = "Estimate",
    ) -> Issue:
        """Set the Estimate field for an owned issue. Pass None to clear it."""
        if value is None:
            return self.clear_number_field(issue_id, field_name, repo=repo)
        return self.set_number_field(issue_id, field_name, value, repo=repo)

    def get_issue_body(self, issue_id: Union[int, str, Issue], *, repo: Optional[str] = None) -> str:
        """Return the current issue body text."""
        issue = self._resolve_issue(issue_id, repo=repo)
        data = self._get_issue_data(issue.repo, issue.number)
        return data.get("body") or ""

    def set_issue_body(
        self,
        issue_id: Union[int, str, Issue],
        body: str,
        *,
        repo: Optional[str] = None,
    ) -> Issue:
        """Update the issue body text."""
        issue = self._resolve_issue(issue_id, repo=repo)
        owner, name = issue.repo.split("/", 1)
        self.client.rest(
            "PATCH",
            f"repos/{owner}/{name}/issues/{issue.number}",
            json_body={"body": body},
        )
        return issue

    def ensure_label(
        self,
        repo: str,
        label: str,
        *,
        color: str = "ededed",
        description: str = "Task owner",
    ) -> None:
        """Ensure a label exists in the repo."""
        self._ensure_label(repo, label, color=color, description=description)

    def add_label(self, issue_id: Union[int, str, Issue], label: str, *, repo: Optional[str] = None) -> None:
        """Add a label to an issue."""
        issue = self._resolve_issue(issue_id, repo=repo)
        self._add_label(issue, label)

    def get_issue(
        self,
        issue_id: Union[int, str, Issue],
        *,
        repo: Optional[str] = None,
        require_project_item: bool = False,
    ) -> Issue:
        """Return a fully populated Issue."""
        return self._resolve_issue(issue_id, repo=repo, require_project_item=require_project_item)

    def release(self, issue_id: Union[int, str, Issue], *, repo: Optional[str] = None) -> Issue:
        """Release an owned issue by removing the owner label."""
        self._require_owner_name()
        issue = self._resolve_issue(issue_id, repo=repo)
        if not self._is_owned_by_me(issue):
            raise OwnershipError(f"You do not own issue {issue.repo}#{issue.number}")
        try:
            self._remove_label(issue, self.owner_label)
        except Exception as exc:
            raise ReleaseError(f"Failed to release issue {issue.repo}#{issue.number}") from exc
        return issue

    def create(
        self,
        title: str,
        description: Optional[str] = None,
        status: str = "Backlog",
        *,
        repo: Optional[str] = None,
        label: Optional[str] = None,
    ) -> Issue:
        """Create an issue, add it to the project, and set its status."""
        if not title or not str(title).strip():
            raise ConfigError("Issue title is required")
        target_repo = repo or self._infer_repo()
        if not target_repo or "/" not in target_repo:
            raise ConfigError("Repo must be in owner/repo format")

        label_name = label.strip() if label is not None else None
        if label is not None and not label_name:
            raise ConfigError("Label must be non-empty")
        if label_name:
            self._ensure_label(target_repo, label_name, description="Created by gh-task")

        owner, name = target_repo.split("/", 1)
        payload: Dict[str, Any] = {"title": title, "body": description or ""}
        if label_name:
            payload["labels"] = [label_name]

        try:
            issue_data = self.client.rest("POST", f"repos/{owner}/{name}/issues", json_body=payload)
        except Exception as exc:
            raise CreateError(f"Failed to create issue in {target_repo}") from exc

        number = issue_data.get("number")
        content_id = issue_data.get("node_id")
        if not content_id:
            raise CreateError("Created issue is missing node id")

        self._ensure_project_loaded()
        status_name, option_id = self._resolve_status(status)
        item_id: Optional[str] = None
        try:
            item_data = self.client.graphql(
                ADD_ITEM_MUTATION,
                {"projectId": self._project_id, "contentId": content_id},
            )
            item_id = ((item_data.get("addProjectV2ItemById") or {}).get("item") or {}).get("id")
            if not item_id:
                raise CreateError("Failed to add issue to project")
            self.client.graphql(
                UPDATE_STATUS_MUTATION,
                {
                    "projectId": self._project_id,
                    "itemId": item_id,
                    "fieldId": self._status_field_id,
                    "optionId": option_id,
                },
            )
        except CreateError:
            raise
        except Exception as exc:
            raise CreateError(
                f"Created issue {target_repo}#{number} but failed to add to project"
            ) from exc

        return Issue(
            number=number,
            repo=target_repo,
            title=issue_data.get("title") or title,
            url=issue_data.get("html_url"),
            body=issue_data.get("body") if issue_data.get("body") is not None else (description or ""),
            status=status_name,
            project_item_id=item_id,
            labels=[label_name] if label_name else None,
        )

    def _wrap_take_result(self, issue: Issue, return_issue: bool, lease: bool):
        if lease:
            return IssueLease(self, issue)
        if return_issue:
            return issue
        return issue.number

    def _try_take(self, issue: Issue, *, wait_seconds: float, strict: bool) -> bool:
        labels = self._issue_labels(issue)
        if _has_owner_label(labels):
            if strict:
                raise TakeError(f"Issue already owned: {issue.repo}#{issue.number}")
            return False

        comment_id = None
        try:
            comment = self._add_comment(issue, f"Taking: {self.name}")
            comment_id = comment.get("id")
            deadline = time.monotonic() + COMMENT_VISIBILITY_TIMEOUT_SECONDS
            while True:
                if self._comment_visible(issue, comment_id):
                    break
                if time.monotonic() >= deadline:
                    raise TakeError(
                        f"Taking comment did not appear within {int(COMMENT_VISIBILITY_TIMEOUT_SECONDS)}s"
                    )
                time.sleep(min(wait_seconds, 1.0))
            time.sleep(wait_seconds)
            taking_comments = self._taking_comments(issue)
            if not taking_comments:
                return False
            first = min(taking_comments, key=_comment_sort_key)
            if first.get("id") != comment_id:
                return False
            labels = self._issue_labels(issue)
            if _has_owner_label(labels) and not self._label_matches_owner(labels):
                return False
            self._ensure_label(issue.repo, self.owner_label)
            self._add_label(issue, self.owner_label)
            return True
        finally:
            if comment_id:
                self._delete_comment(issue, comment_id)

    def _resolve_issue(
        self,
        issue_id: Union[int, str, Issue],
        *,
        repo: Optional[str] = None,
        require_project_item: bool = False,
    ) -> Issue:
        if isinstance(issue_id, Issue):
            issue = issue_id
            if require_project_item and not issue.project_item_id:
                issue = self._attach_project_item(issue)
            if issue.labels is None or issue.body is None or issue.title is None or issue.url is None:
                issue_data = self._get_issue_data(issue.repo, issue.number)
                labels = [label.get("name", "") for label in issue_data.get("labels") or []]
                return Issue(
                    number=issue.number,
                    repo=issue.repo,
                    title=issue.title or issue_data.get("title"),
                    url=issue.url or issue_data.get("html_url"),
                    body=issue.body if issue.body is not None else issue_data.get("body"),
                    status=issue.status,
                    project_item_id=issue.project_item_id,
                    labels=issue.labels or labels,
                )
            return issue

        parsed_repo, number = _parse_issue_ref(issue_id)
        if repo and parsed_repo and repo != parsed_repo:
            raise ConfigError("Conflicting repo supplied for issue")
        repo = repo or parsed_repo
        if number is None:
            raise ConfigError("Issue id is required")

        item = None
        if repo is None:
            item = self._find_issue_in_project(number)
            if not item:
                raise NotFoundError("Issue not found in project; provide repo to resolve it")
            repo = item.repo
        else:
            item = self._find_issue_in_project(number, repo)
        if require_project_item and not item:
            raise NotFoundError(f"Issue {repo}#{number} is not in project")

        issue_data = self._get_issue_data(repo, number)
        labels = [label.get("name", "") for label in issue_data.get("labels") or []]
        return Issue(
            number=number,
            repo=repo,
            title=issue_data.get("title"),
            url=issue_data.get("html_url"),
            body=issue_data.get("body"),
            status=item.status if item else None,
            project_item_id=item.project_item_id if item else None,
            labels=labels,
        )

    def _attach_project_item(self, issue: Issue) -> Issue:
        item = self._find_issue_in_project(issue.number, issue.repo)
        if not item:
            raise NotFoundError(f"Issue {issue.repo}#{issue.number} is not in project")
        return Issue(
            number=issue.number,
            repo=issue.repo,
            title=issue.title,
            url=issue.url,
            body=issue.body,
            status=item.status,
            project_item_id=item.project_item_id,
        )

    def _find_issue_in_project(self, number: int, repo: Optional[str] = None) -> Optional[Issue]:
        items = self._list_items()
        matches = [item for item in items if item.number == number]
        if repo:
            matches = [item for item in matches if item.repo == repo]
        if not matches:
            return None
        if len(matches) > 1:
            raise ConfigError("Multiple issues match that number; provide repo to disambiguate")
        return matches[0]

    def _list_items(self) -> List[Issue]:
        self._ensure_project_loaded()
        items: List[Issue] = []
        cursor = None
        while True:
            data = self.client.graphql(
                ITEMS_QUERY,
                {"projectId": self._project_id, "cursor": cursor, "statusField": self._status_field_name},
            )
            node = data.get("node") or {}
            project = node or {}
            item_block = project.get("items") or {}
            for raw in item_block.get("nodes") or []:
                content = raw.get("content") or {}
                if content.get("__typename") != "Issue":
                    continue
                repo_info = content.get("repository") or {}
                status_val = raw.get("fieldValueByName") or {}
                items.append(
                    Issue(
                        number=content.get("number"),
                        repo=repo_info.get("nameWithOwner"),
                        title=content.get("title"),
                        url=content.get("url"),
                        status=status_val.get("name"),
                        project_item_id=raw.get("id"),
                    )
                )
            page_info = item_block.get("pageInfo") or {}
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")
        return items

    def _project_repos(self) -> List[str]:
        self._ensure_project_loaded()
        repos: set[str] = set()
        cursor = None
        while True:
            data = self.client.graphql(
                ITEMS_QUERY,
                {"projectId": self._project_id, "cursor": cursor, "statusField": self._status_field_name},
            )
            node = data.get("node") or {}
            project = node or {}
            item_block = project.get("items") or {}
            for raw in item_block.get("nodes") or []:
                content = raw.get("content") or {}
                if content.get("__typename") not in {"Issue", "PullRequest"}:
                    continue
                repo_info = content.get("repository") or {}
                name_with_owner = repo_info.get("nameWithOwner")
                if name_with_owner:
                    repos.add(name_with_owner)
            page_info = item_block.get("pageInfo") or {}
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")
        return sorted(repos)

    def _infer_repo(self) -> str:
        repos = self._project_repos()
        if len(repos) == 1:
            return repos[0]
        raise ConfigError("-r/--repo must be specified")

    def _resolve_status(self, status: str) -> Tuple[str, str]:
        self._ensure_project_loaded()
        status_name = self._resolve_status_name(status)
        option = self._status_by_lower[status_name.lower()]
        return option["name"], option["id"]

    def _resolve_number_field(self, field_name: str) -> Dict[str, str]:
        if not field_name:
            raise ConfigError("Field name is required")
        self._ensure_project_loaded()
        key = field_name.strip().lower()
        field = self._number_fields_by_lower.get(key)
        if not field:
            raise ConfigError(f"Unknown field '{field_name}'")
        return field

    def _resolve_status_name(self, status: Optional[str]) -> str:
        if not status:
            raise ConfigError("Status name is required")
        self._ensure_project_loaded()
        key = status.strip().lower()
        if key not in self._status_by_lower:
            raise ConfigError(f"Unknown status '{status}'")
        return self._status_by_lower[key]["name"]

    def _ensure_project_loaded(self) -> None:
        if self._project_id:
            return
        owner_type = self._get_owner_type()
        query = PROJECT_QUERY_USER if owner_type == "user" else PROJECT_QUERY_ORG
        data = self.client.graphql(query, {"login": self.owner, "number": int(self.number)})
        project_key = "user" if owner_type == "user" else "organization"
        project = (data.get(project_key) or {}).get("projectV2")
        if not project:
            raise NotFoundError(f"Project {self.owner}/projects/{self.number} not found")
        fields = project.get("fields", {}).get("nodes", [])
        status_field = None
        single_selects = [field for field in fields if field.get("__typename") == "ProjectV2SingleSelectField"]
        for field in single_selects:
            if (field.get("name") or "").lower() == "status":
                status_field = field
                break
        if not status_field:
            if len(single_selects) == 1:
                status_field = single_selects[0]
            else:
                raise ConfigError("No Status field found in project")
        options = status_field.get("options") or []
        if not options:
            raise ConfigError("Status field has no options")
        self._project_id = project.get("id")
        self._status_field_id = status_field.get("id")
        self._status_field_name = status_field.get("name")
        self._status_options = list(options)
        self._status_by_lower = {opt["name"].lower(): opt for opt in options}
        self._number_fields_by_lower = {}
        for field in fields:
            if field.get("__typename") != "ProjectV2Field":
                continue
            name = field.get("name")
            if name:
                self._number_fields_by_lower[name.lower()] = field

    def _get_owner_type(self) -> str:
        if self._owner_type:
            return self._owner_type
        data = self.client.rest("GET", f"users/{self.owner}")
        owner_type = (data.get("type") or "").lower()
        if owner_type not in {"user", "organization"}:
            raise ConfigError(f"Unknown owner type for {self.owner}")
        self._owner_type = owner_type
        return owner_type

    def _viewer_login(self) -> str:
        data = self.client.graphql(VIEWER_QUERY)
        login = (data.get("viewer") or {}).get("login")
        if not login:
            raise ConfigError("Unable to resolve @me login")
        return login

    def _issue_labels(self, issue: Issue) -> List[str]:
        if issue.labels is not None:
            return issue.labels
        data = self._get_issue_data(issue.repo, issue.number)
        labels = data.get("labels") or []
        return [label.get("name", "") for label in labels]

    def _issue_matches_label(self, issue: Issue) -> bool:
        if not self._label_filter:
            return True
        labels = {label.lower() for label in self._issue_labels(issue)}
        return any(label in labels for label in self._label_filter)

    def _label_filter_hint(self) -> str:
        if not self._label_filter:
            return ""
        labels = ", ".join(sorted(self._label_filter))
        return f" (labels: {labels})"

    def _label_matches_owner(self, labels: Iterable[str]) -> bool:
        if not self.owner_label:
            return False
        needle = self.owner_label.lower()
        return any(label.lower() == needle for label in labels)

    def _is_owned_by_me(self, issue: Issue) -> bool:
        return self._label_matches_owner(self._issue_labels(issue))

    def _get_issue_data(self, repo: str, number: int) -> Dict[str, Any]:
        owner, name = repo.split("/", 1)
        return self.client.rest("GET", f"repos/{owner}/{name}/issues/{number}")

    def _ensure_label(
        self,
        repo: str,
        label: str,
        *,
        color: str = "ededed",
        description: str = "Task owner",
    ) -> None:
        owner, name = repo.split("/", 1)
        try:
            self.client.rest("GET", f"repos/{owner}/{name}/labels/{quote(label)}")
            return
        except ApiError as exc:
            if exc.status_code != 404:
                raise
        try:
            self.client.rest(
                "POST",
                f"repos/{owner}/{name}/labels",
                json_body={"name": label, "color": color, "description": description},
            )
        except ApiError as exc:
            if exc.status_code != 422:
                raise

    def _add_label(self, issue: Issue, label: str) -> None:
        owner, name = issue.repo.split("/", 1)
        self.client.rest(
            "POST",
            f"repos/{owner}/{name}/issues/{issue.number}/labels",
            json_body={"labels": [label]},
        )

    def _remove_label(self, issue: Issue, label: str) -> None:
        owner, name = issue.repo.split("/", 1)
        try:
            self.client.rest(
                "DELETE",
                f"repos/{owner}/{name}/issues/{issue.number}/labels/{quote(label)}",
            )
        except ApiError as exc:
            if exc.status_code != 404:
                raise

    def _add_comment(self, issue: Issue, body: str) -> Dict[str, Any]:
        owner, name = issue.repo.split("/", 1)
        return self.client.rest(
            "POST",
            f"repos/{owner}/{name}/issues/{issue.number}/comments",
            json_body={"body": body},
        )

    def _delete_comment(self, issue: Issue, comment_id: int) -> None:
        owner, name = issue.repo.split("/", 1)
        try:
            self.client.rest("DELETE", f"repos/{owner}/{name}/issues/comments/{comment_id}")
        except Exception:
            pass

    def _comment_visible(self, issue: Issue, comment_id: Optional[int]) -> bool:
        if not comment_id:
            return False
        for comment in self._taking_comments(issue):
            if comment.get("id") == comment_id:
                return True
        return False

    def _taking_comments(self, issue: Issue) -> List[Dict[str, Any]]:
        owner, name = issue.repo.split("/", 1)
        comments: List[Dict[str, Any]] = []
        page = 1
        while True:
            batch = self.client.rest(
                "GET",
                f"repos/{owner}/{name}/issues/{issue.number}/comments",
                params={"per_page": 100, "page": page},
            )
            if not batch:
                break
            comments.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return [c for c in comments if _is_taking_comment(c.get("body", ""))]


PROJECT_RE = re.compile(
    r"(?:(?:https?://)?(?:www\.)?github\.com/)?(?:users/|orgs/)?(?P<owner>[^/]+)/projects/(?P<number>\d+)",
    re.IGNORECASE,
)

ISSUE_URL_RE = re.compile(
    r"github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/issues/(?P<number>\d+)",
    re.IGNORECASE,
)

ISSUE_RE = re.compile(r"^(?P<owner>[^/]+)/(?P<repo>[^/#]+)[#/](?P<number>\d+)$")


def _normalize_label_filter(has_label: Optional[Union[str, Iterable[str]]]) -> Optional[set[str]]:
    if has_label is None:
        return None
    if isinstance(has_label, str):
        raw = [has_label]
    else:
        raw = list(has_label)
    cleaned = [label.strip() for label in raw if str(label).strip()]
    if not cleaned:
        raise ConfigError("has_label must contain at least one label")
    return {label.lower() for label in cleaned}


def _parse_project_ref(ref: str) -> Tuple[str, int]:
    text = str(ref).strip()
    match = PROJECT_RE.search(text)
    if not match:
        raise ConfigError(f"Could not parse project reference '{ref}'")
    owner = match.group("owner")
    number = int(match.group("number"))
    return owner, number


def _parse_issue_ref(issue_id: Union[int, str]) -> Tuple[Optional[str], Optional[int]]:
    if isinstance(issue_id, int):
        return None, issue_id
    text = str(issue_id).strip()
    if text.isdigit():
        return None, int(text)
    match = ISSUE_URL_RE.search(text)
    if match:
        repo = f"{match.group('owner')}/{match.group('repo')}"
        return repo, int(match.group("number"))
    match = ISSUE_RE.match(text)
    if match:
        repo = f"{match.group('owner')}/{match.group('repo')}"
        return repo, int(match.group("number"))
    return None, None


def _looks_like_status(issue_id: Union[int, str, Issue]) -> bool:
    if isinstance(issue_id, Issue):
        return False
    if isinstance(issue_id, int):
        return False
    repo, number = _parse_issue_ref(issue_id)
    return number is None


def _is_taking_comment(body: str) -> bool:
    return body.strip().startswith("Taking: ")


def _comment_sort_key(comment: Dict[str, Any]) -> Tuple[datetime, int]:
    created_at = comment.get("created_at") or comment.get("createdAt") or ""
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        created = datetime.now(timezone.utc)
    return created, int(comment.get("id") or 0)


def _has_owner_label(labels: Iterable[str]) -> bool:
    for label in labels:
        if label.lower().startswith("owner:"):
            return True
    return False
