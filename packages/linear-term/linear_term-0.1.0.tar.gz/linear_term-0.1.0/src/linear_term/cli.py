"""CLI interface for Linear TUI.

Provides standalone commands for quick interactions without the full TUI.

Usage:
    linear-term                    # Launch TUI
    linear-term create "Title"     # Create issue
    linear-term list               # List issues
    linear-term view ENG-123       # View issue
    linear-term search "query"     # Search issues
"""

import argparse
import asyncio
import json
import sys
from typing import Any

from linear_term.api.client import LinearClient, LinearClientError
from linear_term.api.models import Issue
from linear_term.config import load_config


def format_issue_short(issue: Issue) -> str:
    """Format issue for single line display."""
    status = issue.state.name if issue.state else "Unknown"
    priority = issue.priority_icon
    assignee = ""
    if issue.assignee:
        assignee = f" @{issue.assignee.name}"
    return f"{issue.identifier} [{status}] {priority} {issue.title}{assignee}"


def format_issue_detail(issue: Issue) -> str:
    """Format issue for detailed display."""
    lines = []
    lines.append(f"{'=' * 60}")
    lines.append(f"{issue.identifier}: {issue.title}")
    lines.append(f"{'=' * 60}")
    lines.append("")

    # Metadata
    if issue.state:
        lines.append(f"Status:    {issue.state.name}")
    lines.append(f"Priority:  {issue.priority_label}")
    if issue.assignee:
        lines.append(f"Assignee:  {issue.assignee.name}")
    if issue.project:
        lines.append(f"Project:   {issue.project.name}")
    if issue.cycle:
        lines.append(f"Cycle:     {issue.cycle.display_name}")
    if issue.due_date:
        lines.append(f"Due Date:  {issue.due_date}")
    if issue.estimate is not None:
        lines.append(f"Estimate:  {issue.estimate}")
    if issue.labels:
        label_names = ", ".join(lbl.name for lbl in issue.labels)
        lines.append(f"Labels:    {label_names}")
    if issue.url:
        lines.append(f"URL:       {issue.url}")

    lines.append("")

    # Description
    if issue.description:
        lines.append("Description:")
        lines.append("-" * 40)
        lines.append(issue.description)
    else:
        lines.append("No description")

    lines.append("")

    # Comments
    if issue.comments:
        lines.append(f"Comments ({len(issue.comments)}):")
        lines.append("-" * 40)
        for comment in issue.comments:
            author = comment.user.name if comment.user else "Unknown"
            time_str = comment.created_at.strftime("%Y-%m-%d %H:%M")
            lines.append(f"\n{author} ({time_str}):")
            lines.append(comment.body)

    return "\n".join(lines)


def format_issue_json(issue: Issue) -> dict[str, Any]:
    """Format issue as JSON-serializable dict."""
    return {
        "id": issue.id,
        "identifier": issue.identifier,
        "title": issue.title,
        "description": issue.description,
        "priority": issue.priority,
        "priority_label": issue.priority_label,
        "status": issue.state.name if issue.state else None,
        "assignee": issue.assignee.name if issue.assignee else None,
        "project": issue.project.name if issue.project else None,
        "url": issue.url,
        "due_date": str(issue.due_date) if issue.due_date else None,
        "created_at": issue.created_at.isoformat() if issue.created_at else None,
        "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
    }


async def cmd_list(args: argparse.Namespace, client: LinearClient) -> int:
    """List issues."""
    try:
        assignee_id = None
        if args.mine:
            viewer = await client.get_viewer()
            if viewer:
                assignee_id = viewer.id

        issues, _ = await client.get_issues(
            assignee_id=assignee_id,
            first=args.limit,
        )

        if args.json:
            output = [format_issue_json(issue) for issue in issues]
            print(json.dumps(output, indent=2))
        else:
            for issue in issues:
                print(format_issue_short(issue))

        return 0
    except LinearClientError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


async def cmd_view(args: argparse.Namespace, client: LinearClient) -> int:
    """View a specific issue."""
    try:
        # Handle both "ENG-123" format and raw ID
        identifier = args.identifier

        # Search for issue by identifier
        issues = await client.search_issues(identifier, first=5)

        # Find exact match
        issue = None
        for i in issues:
            if i.identifier.lower() == identifier.lower():
                issue = i
                break

        if not issue:
            # Try to get by ID directly
            issue = await client.get_issue(identifier)

        if not issue:
            print(f"Issue not found: {identifier}", file=sys.stderr)
            return 1

        # Get full details
        full_issue = await client.get_issue(issue.id)
        if not full_issue:
            print(f"Could not fetch issue details: {identifier}", file=sys.stderr)
            return 1

        if args.json:
            print(json.dumps(format_issue_json(full_issue), indent=2))
        else:
            print(format_issue_detail(full_issue))

        return 0
    except LinearClientError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


async def cmd_create(args: argparse.Namespace, client: LinearClient) -> int:
    """Create a new issue."""
    try:
        # Get teams to find default
        teams = await client.get_teams()
        if not teams:
            print("No teams available", file=sys.stderr)
            return 1

        team = teams[0]
        if args.team:
            # Find team by name or key
            for t in teams:
                if t.name.lower() == args.team.lower() or t.key.lower() == args.team.lower():
                    team = t
                    break

        # Map priority string to number
        priority = None
        if args.priority:
            priority_map = {
                "urgent": 1,
                "high": 2,
                "medium": 3,
                "low": 4,
                "none": 0,
            }
            priority = priority_map.get(args.priority.lower())

        issue = await client.create_issue(
            team_id=team.id,
            title=args.title,
            description=args.description,
            priority=priority,
        )

        if issue:
            if args.json:
                print(json.dumps(format_issue_json(issue), indent=2))
            else:
                print(f"Created: {issue.identifier} - {issue.title}")
                if issue.url:
                    print(f"URL: {issue.url}")
            return 0
        else:
            print("Failed to create issue", file=sys.stderr)
            return 1

    except LinearClientError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


async def cmd_search(args: argparse.Namespace, client: LinearClient) -> int:
    """Search issues."""
    try:
        issues = await client.search_issues(args.query, first=args.limit)

        if args.json:
            output = [format_issue_json(issue) for issue in issues]
            print(json.dumps(output, indent=2))
        else:
            if not issues:
                print("No issues found")
            else:
                for issue in issues:
                    print(format_issue_short(issue))

        return 0
    except LinearClientError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="linear-term",
        description="Terminal UI and CLI for Linear project management",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list command
    list_parser = subparsers.add_parser("list", aliases=["ls"], help="List issues")
    list_parser.add_argument("-m", "--mine", action="store_true", help="Only my issues")
    list_parser.add_argument("-l", "--limit", type=int, default=20, help="Max results")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # view command
    view_parser = subparsers.add_parser("view", aliases=["show"], help="View issue details")
    view_parser.add_argument("identifier", help="Issue identifier (e.g., ENG-123)")
    view_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # create command
    create_parser = subparsers.add_parser("create", aliases=["new"], help="Create new issue")
    create_parser.add_argument("title", help="Issue title")
    create_parser.add_argument("-d", "--description", help="Issue description")
    create_parser.add_argument("-t", "--team", help="Team name or key")
    create_parser.add_argument(
        "-p",
        "--priority",
        choices=["urgent", "high", "medium", "low", "none"],
        help="Issue priority",
    )
    create_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # search command
    search_parser = subparsers.add_parser("search", help="Search issues")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-l", "--limit", type=int, default=20, help="Max results")
    search_parser.add_argument("--json", action="store_true", help="Output as JSON")

    return parser


async def run_cli(args: argparse.Namespace) -> int:
    """Run CLI command."""
    config = load_config()

    if not config.api_key:
        print("Error: No API key configured.", file=sys.stderr)
        print("Set LINEAR_API_KEY environment variable or add to config file.", file=sys.stderr)
        return 1

    async with LinearClient(config.api_key) as client:
        if args.command in ("list", "ls"):
            return await cmd_list(args, client)
        elif args.command in ("view", "show"):
            return await cmd_view(args, client)
        elif args.command in ("create", "new"):
            return await cmd_create(args, client)
        elif args.command == "search":
            return await cmd_search(args, client)
        else:
            # No command specified, this shouldn't happen
            return 1


def cli_main() -> int:
    """CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        # No subcommand, run TUI
        from linear_term.app import main

        main()
        return 0

    # Run CLI command
    return asyncio.run(run_cli(args))


if __name__ == "__main__":
    sys.exit(cli_main())
