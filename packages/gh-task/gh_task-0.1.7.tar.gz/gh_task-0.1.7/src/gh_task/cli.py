import argparse
import sys
from typing import Optional

from .errors import GhTaskError
from .project import Project


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-p",
        "--project",
        required=True,
        help="Project reference (e.g. yieldthought/projects/3 or full URL)",
    )
    parser.add_argument("-n", "--name", required=True, help="Owner label name")
    parser.add_argument("--token", help="GitHub token (defaults to GH_TOKEN/GITHUB_TOKEN or gh auth)")
    parser.add_argument(
        "-l",
        "--label",
        help="Comma-separated list of labels to filter issues by",
    )


def _resolve_issue_or_status(
    issue: Optional[str], status: Optional[str], positional: Optional[str]
) -> tuple[Optional[str], Optional[str]]:
    if issue and status:
        raise ValueError("Provide either issue or status, not both")
    if issue:
        return issue, None
    if status:
        return None, status
    if positional:
        if positional.isdigit():
            return positional, None
        return None, positional
    return None, None


def _format_issue(issue) -> str:
    if getattr(issue, "repo", None):
        return f"{issue.repo}#{issue.number}"
    return str(issue.number)


def _parse_label_filter(value: Optional[str]) -> Optional[list[str]]:
    if not value:
        return None
    labels = [label.strip() for label in value.split(",") if label.strip()]
    if not labels:
        return None
    return labels


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="gh-task", description="GitHub Project task ownership helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    take_parser = subparsers.add_parser("take", help="Take an issue by id or by status")
    _add_common_args(take_parser)
    take_parser.add_argument("issue_or_status", nargs="?", help="Issue number or status name")
    take_parser.add_argument("-i", "--issue", help="Issue number or URL")
    take_parser.add_argument("-s", "--status", help="Status name")
    take_parser.add_argument("-r", "--repo", help="Repo name (owner/repo)")
    take_parser.add_argument("--wait", type=float, default=1.0, help="Seconds to wait before checking comments")

    move_parser = subparsers.add_parser("move", help="Move an issue to a new status")
    _add_common_args(move_parser)
    move_parser.add_argument("issue", nargs="?", help="Issue number or URL")
    move_parser.add_argument("status", nargs="?", help="Status name")
    move_parser.add_argument("-i", "--issue-id", help="Issue number or URL")
    move_parser.add_argument("-s", "--status-name", help="Status name")
    move_parser.add_argument("-r", "--repo", help="Repo name (owner/repo)")

    release_parser = subparsers.add_parser("release", help="Release an issue you own")
    _add_common_args(release_parser)
    release_parser.add_argument("issue", nargs="?", help="Issue number or URL")
    release_parser.add_argument("-i", "--issue-id", help="Issue number or URL")
    release_parser.add_argument("-r", "--repo", help="Repo name (owner/repo)")

    list_parser = subparsers.add_parser("list", help="List statuses or issues in a status")
    _add_common_args(list_parser)
    list_parser.add_argument("status", nargs="?", help="Status name to list issues for")
    list_parser.add_argument("-s", "--status-name", help="Status name to list issues for")

    create_parser = subparsers.add_parser("create", help="Create an issue and add it to the project")
    create_parser.add_argument(
        "-p",
        "--project",
        required=True,
        help="Project reference (e.g. yieldthought/projects/3 or full URL)",
    )
    create_parser.add_argument("--token", help="GitHub token (defaults to GH_TOKEN/GITHUB_TOKEN or gh auth)")
    create_parser.add_argument("-r", "--repo", help="Repo name (owner/repo)")
    create_parser.add_argument("-t", "--title", required=True, help="Issue title")
    create_parser.add_argument("-d", "--description", help="Issue description/body")
    create_parser.add_argument("-s", "--status", default="Backlog", help="Status name (default: Backlog)")
    create_parser.add_argument(
        "-l",
        "--label",
        help="Label to add to the issue (created if missing)",
    )

    args = parser.parse_args(argv)

    try:
        if args.command == "create":
            project = Project(project=args.project, token=args.token)
            result = project.create(
                title=args.title,
                description=args.description,
                status=args.status,
                repo=args.repo,
                label=args.label,
            )
            print(f"{_format_issue(result)} -> {result.status}")
            return 0

        labels = _parse_label_filter(args.label)
        project = Project(project=args.project, name=args.name, token=args.token, has_label=labels)

        if args.command == "take":
            issue, status = _resolve_issue_or_status(args.issue, args.status, args.issue_or_status)
            if not issue and not status:
                parser.error("take requires an issue id or a status name")
            result = project.take(
                issue_id=issue,
                status=status,
                repo=args.repo,
                wait_seconds=args.wait,
                return_issue=True,
            )
            print(_format_issue(result))
            return 0

        if args.command == "move":
            issue = args.issue_id or args.issue
            status = args.status_name or args.status
            if not issue or not status:
                parser.error("move requires an issue id and a status name")
            result = project.move(issue, status, repo=args.repo)
            print(f"{_format_issue(result)} -> {result.status}")
            return 0

        if args.command == "release":
            issue = args.issue_id or args.issue
            if not issue:
                parser.error("release requires an issue id")
            result = project.release(issue, repo=args.repo)
            print(_format_issue(result))
            return 0

        if args.command == "list":
            status = args.status_name or args.status
            if not status:
                for name in project.statuses():
                    print(name)
                return 0
            issues = project.list(status, return_issue=True)
            for issue in issues:
                if issue.title:
                    print(f"{_format_issue(issue)}\t{issue.title}")
                else:
                    print(_format_issue(issue))
            return 0

    except GhTaskError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
