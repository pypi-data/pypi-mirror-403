"""Issue list widget."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widgets import DataTable, Static
from textual.widgets.data_table import RowKey

from linear_term.api.models import Issue


class IssueList(VerticalScroll):
    """Widget displaying a list of issues."""

    DEFAULT_CSS = """
    IssueList {
        background: $surface;
    }

    IssueList .filter-bar {
        height: 1;
        background: $surface-darken-1;
        color: $text-muted;
        padding: 0 1;
    }

    IssueList .selection-bar {
        height: 1;
        background: $warning-darken-2;
        color: $text;
        padding: 0 1;
        display: none;
    }

    IssueList .selection-bar.visible {
        display: block;
    }

    IssueList DataTable {
        height: 1fr;
    }

    IssueList DataTable > .datatable--header {
        background: $primary-darken-2;
        color: $text;
        text-style: bold;
    }

    IssueList DataTable > .datatable--cursor {
        background: $accent;
        color: $text;
    }

    IssueList DataTable > .datatable--hover {
        background: $surface-lighten-1;
    }
    """

    BINDINGS = [
        Binding("enter", "select_issue", "Open", show=True),
        Binding("e", "edit_issue", "Edit", show=True),
        Binding("s", "change_status", "Status", show=False),
        Binding("a", "change_assignee", "Assignee", show=False),
        Binding("p", "change_priority", "Priority", show=False),
        Binding("l", "change_labels", "Labels", show=False),
        Binding("c", "add_comment", "Comment", show=True),
        Binding("y", "copy_url", "Copy URL", show=True),
        Binding("o", "open_browser", "Open in Browser", show=True),
        Binding("S", "change_sort", "Sort", show=True),
        Binding("[", "prev_page", "Prev Page", show=False),
        Binding("]", "next_page", "Next Page", show=False),
        # Bulk selection
        Binding("space", "toggle_selection", "Select", show=True),
        Binding("v", "toggle_select_mode", "Select Mode", show=False),
        Binding("V", "select_all", "Select All", show=False),
        Binding("escape", "clear_selection", "Clear", show=False),
        # Quick priority keys
        Binding("1", "set_priority_urgent", "Urgent", show=False),
        Binding("2", "set_priority_high", "High", show=False),
        Binding("3", "set_priority_medium", "Medium", show=False),
        Binding("4", "set_priority_low", "Low", show=False),
        Binding("0", "set_priority_none", "No Priority", show=False),
        # Quick rename
        Binding("r", "rename_issue", "Rename", show=False),
        # Bulk archive
        Binding("ctrl+a", "archive_issues", "Archive", show=False),
        # Status advance
        Binding("x", "advance_status", "Next Status", show=False),
        # Favorite toggle
        Binding("*", "toggle_favorite", "Favorite", show=False),
    ]

    class IssueSelected(Message):
        """Message when an issue is selected."""

        def __init__(self, issue: Issue) -> None:
            self.issue = issue
            super().__init__()

    class IssueHighlighted(Message):
        """Message when an issue is highlighted (cursor moved)."""

        def __init__(self, issue: Issue | None) -> None:
            self.issue = issue
            super().__init__()

    class ActionRequested(Message):
        """Message when an action is requested on the selected issue."""

        def __init__(self, action: str, issue: Issue | None) -> None:
            self.action = action
            self.issue = issue
            super().__init__()

    class BulkActionRequested(Message):
        """Message when a bulk action is requested on selected issues."""

        def __init__(self, action: str, issues: list[Issue]) -> None:
            self.action = action
            self.issues = issues
            super().__init__()

    class SortChangeRequested(Message):
        """Message when sort change is requested."""

        def __init__(self, current_sort: str, sort_ascending: bool) -> None:
            self.current_sort = current_sort
            self.sort_ascending = sort_ascending
            super().__init__()

    class RenameRequested(Message):
        """Message when rename is requested."""

        def __init__(self, issue: Issue) -> None:
            self.issue = issue
            super().__init__()

    class QuickPriorityRequested(Message):
        """Message when quick priority change is requested."""

        def __init__(self, issues: list[Issue], priority: int) -> None:
            self.issues = issues
            self.priority = priority
            super().__init__()

    class StatusAdvanceRequested(Message):
        """Message when status advance is requested."""

        def __init__(self, issue: Issue) -> None:
            self.issue = issue
            super().__init__()

    class ToggleFavoriteRequested(Message):
        """Message when favorite toggle is requested."""

        def __init__(self, issue: Issue) -> None:
            self.issue = issue
            super().__init__()

    def __init__(
        self,
        default_sort: str = "priority",
        default_sort_order: str = "asc",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._issues: list[Issue] = []
        self._issue_map: dict[RowKey, Issue] = {}
        self._row_key_map: dict[str, RowKey] = {}  # issue.id -> RowKey
        self._current_filter: str = ""
        self._current_sort: str = default_sort
        self._sort_ascending: bool = default_sort_order == "asc"
        self._page: int = 0
        self._page_size: int = 50
        self._total_count: int = 0
        # Multi-selection support
        self._selected_ids: set[str] = set()
        self._select_mode: bool = False
        # Favorites tracking
        self._favorite_ids: set[str] = set()

    def compose(self) -> ComposeResult:
        """Compose the issue list content."""
        yield Static("", id="selection-bar", classes="selection-bar")
        yield Static("", id="filter-bar", classes="filter-bar")
        table = DataTable(id="issue-table", cursor_type="row")
        table.add_columns("", "★", "", "ID", "Title", "Status", "Pri", "Assignee")
        yield table

    def on_mount(self) -> None:
        """Set up the data table on mount."""
        table = self.query_one("#issue-table", DataTable)
        table.cursor_type = "row"

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        issue = self._issue_map.get(event.row_key)
        if issue:
            self.post_message(self.IssueSelected(issue))

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row highlight (cursor move)."""
        if event.row_key:
            issue = self._issue_map.get(event.row_key)
            self.post_message(self.IssueHighlighted(issue))
        else:
            self.post_message(self.IssueHighlighted(None))

    def update_issues(self, issues: list[Issue], total_count: int | None = None) -> None:
        """Update the issue list."""
        self._issues = issues
        self._total_count = total_count if total_count is not None else len(issues)
        self._refresh_table()
        self._update_filter_bar()

    def _refresh_table(self) -> None:
        """Refresh the data table with current issues."""
        table = self.query_one("#issue-table", DataTable)
        table.clear()
        self._issue_map.clear()
        self._row_key_map.clear()

        sorted_issues = self._sort_issues(self._issues)

        for issue in sorted_issues:
            selected = "●" if issue.id in self._selected_ids else " "
            star = "★" if issue.id in self._favorite_ids else " "
            status_icon = issue.status_icon
            status_name = issue.state.name if issue.state else "Unknown"
            priority_icon = issue.priority_icon
            assignee = ""
            if issue.assignee:
                assignee = issue.assignee.display_name or issue.assignee.name
                if len(assignee) > 12:
                    assignee = assignee[:11] + "…"

            title = issue.title
            if len(title) > 50:
                title = title[:49] + "…"

            hierarchy = ""
            if issue.children:
                hierarchy = f"[+{len(issue.children)}]"
            elif issue.parent:
                hierarchy = "└"
            identifier = issue.identifier
            if hierarchy:
                identifier = f"{issue.identifier} {hierarchy}"

            row_key = table.add_row(
                selected,
                star,
                status_icon,
                identifier,
                title,
                status_name,
                priority_icon,
                assignee,
            )
            self._issue_map[row_key] = issue
            self._row_key_map[issue.id] = row_key

        self._update_selection_bar()

    def _sort_issues(self, issues: list[Issue]) -> list[Issue]:
        """Sort issues by current sort criteria."""
        key_funcs = {
            "priority": lambda i: (i.priority if i.priority else 5, i.identifier),
            "identifier": lambda i: (i.identifier,),
            "title": lambda i: (i.title.lower(), i.identifier),
            "created": lambda i: (i.created_at or "", i.identifier),
            "due_date": lambda i: (i.due_date or "9999-99-99", i.identifier),
            "status": lambda i: (
                i.state.position if i.state else 999,
                i.identifier,
            ),
            "updated": lambda i: (i.updated_at or "", i.identifier),
            "assignee": lambda i: (
                i.assignee.name if i.assignee else "zzz",
                i.identifier,
            ),
        }
        key_func = key_funcs.get(self._current_sort, key_funcs["priority"])
        return sorted(issues, key=key_func, reverse=not self._sort_ascending)

    def _update_filter_bar(self) -> None:
        """Update the filter bar display."""
        filter_bar = self.query_one("#filter-bar", Static)
        parts = []
        if self._current_filter:
            parts.append(f"Filter: {self._current_filter}")

        sort_labels = {
            "priority": "Priority",
            "identifier": "ID",
            "title": "Title",
            "created": "Created",
            "due_date": "Due Date",
            "status": "Status",
            "updated": "Updated",
            "assignee": "Assignee",
        }
        sort_label = sort_labels.get(self._current_sort, self._current_sort)
        direction = "↑" if self._sort_ascending else "↓"
        parts.append(f"Sort: {sort_label} {direction} [S]")

        start = self._page * self._page_size + 1
        end = min((self._page + 1) * self._page_size, self._total_count)
        parts.append(f"Showing {start}-{end} of {self._total_count}")

        filter_bar.update(" | ".join(parts))

    def set_filter(self, filter_text: str) -> None:
        """Set the current filter text."""
        self._current_filter = filter_text
        self._update_filter_bar()

    def set_sort(self, sort_by: str, ascending: bool = True) -> None:
        """Set the sort criteria."""
        self._current_sort = sort_by
        self._sort_ascending = ascending
        self._refresh_table()
        self._update_filter_bar()

    def _update_selection_bar(self) -> None:
        """Update the selection bar display."""
        selection_bar = self.query_one("#selection-bar", Static)
        count = len(self._selected_ids)
        if count > 0:
            selection_bar.add_class("visible")
            actions = "[s] Status [a] Assign [p] Priority [l] Labels [Ctrl-A] Archive [Esc] Clear"
            selection_bar.update(f"  {count} selected  |  {actions}")
        else:
            selection_bar.remove_class("visible")

    def get_selected_issues(self) -> list[Issue]:
        """Get all selected issues."""
        return [i for i in self._issues if i.id in self._selected_ids]

    def clear_selection(self) -> None:
        """Clear all selections."""
        self._selected_ids.clear()
        self._select_mode = False
        self._refresh_table()

    def toggle_issue_selection(self, issue: Issue) -> None:
        """Toggle selection for a specific issue."""
        if issue.id in self._selected_ids:
            self._selected_ids.discard(issue.id)
        else:
            self._selected_ids.add(issue.id)
        self._refresh_table()

    def select_issue_by_id(self, issue_id: str) -> None:
        """Select an issue by ID."""
        self._selected_ids.add(issue_id)
        self._refresh_table()

    def select_all_issues(self) -> None:
        """Select all visible issues."""
        for issue in self._issues:
            self._selected_ids.add(issue.id)
        self._refresh_table()

    def has_selection(self) -> bool:
        """Check if any issues are selected."""
        return len(self._selected_ids) > 0

    def get_selected_issue(self) -> Issue | None:
        """Get the currently selected issue."""
        table = self.query_one("#issue-table", DataTable)
        if table.cursor_row is not None and table.row_count > 0:
            try:
                cursor_row = table.cursor_row
                for row_key in self._issue_map:
                    row_index = table.get_row_index(row_key)
                    if row_index == cursor_row:
                        return self._issue_map[row_key]
            except Exception:
                pass
        return None

    def action_select_issue(self) -> None:
        """Select the current issue."""
        issue = self.get_selected_issue()
        if issue:
            self.post_message(self.IssueSelected(issue))

    def action_edit_issue(self) -> None:
        """Request edit action."""
        self.post_message(self.ActionRequested("edit", self.get_selected_issue()))

    def action_change_status(self) -> None:
        """Request status change."""
        if self._selected_ids:
            issues = self.get_selected_issues()
            self.post_message(self.BulkActionRequested("status", issues))
        else:
            self.post_message(self.ActionRequested("status", self.get_selected_issue()))

    def action_change_assignee(self) -> None:
        """Request assignee change."""
        if self._selected_ids:
            issues = self.get_selected_issues()
            self.post_message(self.BulkActionRequested("assignee", issues))
        else:
            self.post_message(self.ActionRequested("assignee", self.get_selected_issue()))

    def action_change_priority(self) -> None:
        """Request priority change."""
        if self._selected_ids:
            issues = self.get_selected_issues()
            self.post_message(self.BulkActionRequested("priority", issues))
        else:
            self.post_message(self.ActionRequested("priority", self.get_selected_issue()))

    def action_change_labels(self) -> None:
        """Request labels change."""
        if self._selected_ids:
            issues = self.get_selected_issues()
            self.post_message(self.BulkActionRequested("labels", issues))
        else:
            self.post_message(self.ActionRequested("labels", self.get_selected_issue()))

    def action_add_comment(self) -> None:
        """Request add comment."""
        self.post_message(self.ActionRequested("comment", self.get_selected_issue()))

    def action_copy_url(self) -> None:
        """Request copy URL."""
        self.post_message(self.ActionRequested("copy_url", self.get_selected_issue()))

    def action_open_browser(self) -> None:
        """Request open in browser."""
        self.post_message(self.ActionRequested("open_browser", self.get_selected_issue()))

    def action_change_sort(self) -> None:
        """Request sort change."""
        self.post_message(self.SortChangeRequested(self._current_sort, self._sort_ascending))

    def action_prev_page(self) -> None:
        """Go to previous page."""
        if self._page > 0:
            self._page -= 1
            self.post_message(self.ActionRequested("prev_page", None))

    def action_next_page(self) -> None:
        """Go to next page."""
        if (self._page + 1) * self._page_size < self._total_count:
            self._page += 1
            self.post_message(self.ActionRequested("next_page", None))

    def action_toggle_selection(self) -> None:
        """Toggle selection of current issue."""
        issue = self.get_selected_issue()
        if issue:
            self.toggle_issue_selection(issue)
            # Move to next row after selecting
            table = self.query_one("#issue-table", DataTable)
            table.action_cursor_down()

    def action_toggle_select_mode(self) -> None:
        """Toggle visual select mode."""
        self._select_mode = not self._select_mode
        if self._select_mode:
            issue = self.get_selected_issue()
            if issue:
                self._selected_ids.add(issue.id)
                self._refresh_table()
        self.notify(f"Select mode: {'ON' if self._select_mode else 'OFF'}")

    def action_select_all(self) -> None:
        """Select all visible issues."""
        self.select_all_issues()

    def action_clear_selection(self) -> None:
        """Clear all selections."""
        if self._selected_ids:
            self.clear_selection()
        else:
            # If nothing selected, propagate escape
            pass

    def action_rename_issue(self) -> None:
        """Request to rename the current issue."""
        issue = self.get_selected_issue()
        if issue:
            self.post_message(self.RenameRequested(issue))

    def action_set_priority_urgent(self) -> None:
        """Set priority to urgent (1)."""
        self._request_priority_change(1)

    def action_set_priority_high(self) -> None:
        """Set priority to high (2)."""
        self._request_priority_change(2)

    def action_set_priority_medium(self) -> None:
        """Set priority to medium (3)."""
        self._request_priority_change(3)

    def action_set_priority_low(self) -> None:
        """Set priority to low (4)."""
        self._request_priority_change(4)

    def action_set_priority_none(self) -> None:
        """Set priority to none (0)."""
        self._request_priority_change(0)

    def _request_priority_change(self, priority: int) -> None:
        """Request priority change for selected or current issues."""
        if self._selected_ids:
            issues = self.get_selected_issues()
            self.post_message(self.QuickPriorityRequested(issues, priority))
        else:
            issue = self.get_selected_issue()
            if issue:
                self.post_message(self.QuickPriorityRequested([issue], priority))

    def _get_issues_for_action(self) -> list[Issue]:
        """Get issues for bulk or single action."""
        if self._selected_ids:
            return self.get_selected_issues()
        issue = self.get_selected_issue()
        return [issue] if issue else []

    def action_archive_issues(self) -> None:
        """Request archive for selected issues."""
        if self._selected_ids:
            issues = self.get_selected_issues()
            self.post_message(self.BulkActionRequested("archive", issues))
        else:
            issue = self.get_selected_issue()
            if issue:
                self.post_message(self.ActionRequested("archive", issue))

    def action_advance_status(self) -> None:
        """Request to advance status to next state."""
        issue = self.get_selected_issue()
        if issue:
            self.post_message(self.StatusAdvanceRequested(issue))

    def action_toggle_favorite(self) -> None:
        """Request to toggle favorite status."""
        issue = self.get_selected_issue()
        if issue:
            self.post_message(self.ToggleFavoriteRequested(issue))

    def set_favorite_ids(self, favorite_ids: set[str]) -> None:
        """Set the IDs of favorited issues for star display."""
        self._favorite_ids = favorite_ids
        self._refresh_table()
