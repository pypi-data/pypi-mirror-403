"""Triage view for processing untriaged issues."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Button, DataTable, Static
from textual.widgets.data_table import RowKey

from linear_term.api.models import Issue


class TriageView(VerticalScroll):
    """View for triaging issues."""

    DEFAULT_CSS = """
    TriageView {
        background: $surface;
        padding: 1;
    }

    TriageView .triage-header {
        text-style: bold;
        color: $accent;
        padding-bottom: 1;
    }

    TriageView .triage-stats {
        color: $text-muted;
        padding-bottom: 1;
    }

    TriageView .inbox-zero {
        display: none;
        text-align: center;
        padding: 4;
    }

    TriageView .inbox-zero.visible {
        display: block;
    }

    TriageView .inbox-zero-icon {
        color: $success;
        text-style: bold;
    }

    TriageView .inbox-zero-text {
        color: $text;
        padding-top: 1;
    }

    TriageView .quick-triage {
        display: none;
        padding: 2;
        border: solid $accent;
        margin: 1;
    }

    TriageView .quick-triage.visible {
        display: block;
    }

    TriageView .quick-triage-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        padding-bottom: 1;
    }

    TriageView .quick-triage-issue {
        text-style: bold;
        padding: 1;
    }

    TriageView .quick-triage-desc {
        padding: 1;
        max-height: 10;
    }

    TriageView .quick-triage-actions {
        text-align: center;
        padding-top: 1;
        color: $text-muted;
    }

    TriageView DataTable {
        height: 1fr;
        min-height: 10;
    }

    TriageView .action-bar {
        height: 3;
        padding: 1 0;
        align: center middle;
    }

    TriageView Button {
        margin: 0 1;
    }

    TriageView .issue-preview {
        height: auto;
        max-height: 20;
        padding: 1;
        border: solid $border;
        margin-top: 1;
    }

    TriageView .preview-title {
        text-style: bold;
        padding-bottom: 1;
    }

    TriageView .preview-meta {
        color: $text-muted;
        padding-bottom: 1;
    }

    TriageView .mode-toggle {
        padding: 0 1;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("a", "accept", "Accept", show=True),
        Binding("d", "decline", "Decline", show=True),
        Binding("s", "snooze", "Snooze", show=True),
        Binding("m", "assign_to_me", "Assign to Me", show=True),
        Binding("j", "next_issue", "Next", show=True),
        Binding("k", "prev_issue", "Previous", show=True),
        Binding("t", "toggle_quick_mode", "Quick Mode", show=True),
        Binding("1", "snooze_tomorrow", "Tomorrow", show=False),
        Binding("2", "snooze_next_week", "Next Week", show=False),
        Binding("3", "snooze_next_month", "Next Month", show=False),
    ]

    class TriageAction(Message):
        """Message when a triage action is taken."""

        def __init__(self, action: str, issue: Issue, snooze_days: int = 0) -> None:
            self.action = action
            self.issue = issue
            self.snooze_days = snooze_days
            super().__init__()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._issues: list[Issue] = []
        self._issue_map: dict[RowKey, Issue] = {}
        self._selected_issue: Issue | None = None
        self._quick_mode: bool = False
        self._triaged_count: int = 0

    def compose(self) -> ComposeResult:
        """Compose the triage view."""
        yield Static("Triage Queue", classes="triage-header")
        yield Static("0 issues to triage", id="triage-stats", classes="triage-stats")
        yield Static("[t] Toggle Quick Mode", classes="mode-toggle")

        # Inbox zero celebration
        with Vertical(classes="inbox-zero", id="inbox-zero"):
            yield Static("✓", classes="inbox-zero-icon")
            yield Static("Inbox Zero!", classes="inbox-zero-text")
            yield Static("All issues have been triaged.", classes="inbox-zero-text")

        # Quick triage mode (single issue focus)
        with Vertical(classes="quick-triage", id="quick-triage"):
            yield Static("Quick Triage Mode", classes="quick-triage-title")
            yield Static("", id="quick-issue-id", classes="quick-triage-issue")
            yield Static("", id="quick-issue-desc", classes="quick-triage-desc")
            yield Static(
                "[a] Accept  [d] Decline  [m] Assign  [1] Tomorrow  [2] Next Week  [3] Next Month",
                classes="quick-triage-actions",
            )

        table = DataTable(id="triage-table", cursor_type="row")
        table.add_columns("ID", "Title", "Created", "Creator")
        yield table

        with Horizontal(classes="action-bar"):
            yield Button("Accept (a)", id="accept-btn", variant="success")
            yield Button("Decline (d)", id="decline-btn", variant="error")
            yield Button("Snooze (s)", id="snooze-btn")
            yield Button("Assign to Me (m)", id="assign-btn", variant="primary")

        with Vertical(classes="issue-preview", id="issue-preview"):
            yield Static("", id="preview-title", classes="preview-title")
            yield Static("", id="preview-meta", classes="preview-meta")
            yield Static("", id="preview-description")

    def update_issues(self, issues: list[Issue]) -> None:
        """Update the triage queue."""
        self._issues = issues
        self._refresh_table()
        self._update_stats()

    def _refresh_table(self) -> None:
        """Refresh the data table."""
        table = self.query_one("#triage-table", DataTable)
        table.clear()
        self._issue_map.clear()

        for issue in self._issues:
            created = ""
            if issue.created_at:
                created = issue.created_at.strftime("%Y-%m-%d")

            creator = ""
            if issue.creator:
                creator = issue.creator.name

            title = issue.title
            if len(title) > 50:
                title = title[:49] + "…"

            row_key = table.add_row(
                issue.identifier,
                title,
                created,
                creator,
            )
            self._issue_map[row_key] = issue

    def _update_stats(self) -> None:
        """Update the stats display."""
        stats = self.query_one("#triage-stats", Static)
        count = len(self._issues)
        triaged_text = f" ({self._triaged_count} triaged)" if self._triaged_count > 0 else ""
        stats.update(f"{count} issue{'s' if count != 1 else ''} to triage{triaged_text}")

        # Show/hide inbox zero
        inbox_zero = self.query_one("#inbox-zero")
        if count == 0:
            inbox_zero.add_class("visible")
        else:
            inbox_zero.remove_class("visible")

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row highlight."""
        if event.row_key:
            issue = self._issue_map.get(event.row_key)
            if issue:
                self._selected_issue = issue
                self._update_preview(issue)

    def _update_preview(self, issue: Issue) -> None:
        """Update the issue preview."""
        title = self.query_one("#preview-title", Static)
        title.update(f"{issue.identifier}: {issue.title}")

        meta_parts = []
        if issue.priority_label:
            meta_parts.append(f"Priority: {issue.priority_label}")
        if issue.team:
            meta_parts.append(f"Team: {issue.team.name}")
        if issue.project:
            meta_parts.append(f"Project: {issue.project.name}")

        meta = self.query_one("#preview-meta", Static)
        meta.update(" | ".join(meta_parts) if meta_parts else "No metadata")

        desc = self.query_one("#preview-description", Static)
        description = issue.description or "No description"
        if len(description) > 300:
            description = description[:297] + "..."
        desc.update(description)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if not self._selected_issue:
            return

        button_actions = {
            "accept-btn": "accept",
            "decline-btn": "decline",
            "snooze-btn": "snooze",
            "assign-btn": "assign_to_me",
        }

        action = button_actions.get(event.button.id)
        if action:
            self.post_message(self.TriageAction(action, self._selected_issue))

    def action_accept(self) -> None:
        """Accept the current issue."""
        if self._selected_issue:
            self.post_message(self.TriageAction("accept", self._selected_issue))

    def action_decline(self) -> None:
        """Decline the current issue."""
        if self._selected_issue:
            self.post_message(self.TriageAction("decline", self._selected_issue))

    def action_snooze(self) -> None:
        """Snooze the current issue (default: 1 day)."""
        if self._selected_issue:
            self.post_message(self.TriageAction("snooze", self._selected_issue, snooze_days=1))

    def action_snooze_tomorrow(self) -> None:
        """Snooze the current issue until tomorrow."""
        if self._selected_issue:
            self.post_message(self.TriageAction("snooze", self._selected_issue, snooze_days=1))
            self._advance_to_next()

    def action_snooze_next_week(self) -> None:
        """Snooze the current issue for a week."""
        if self._selected_issue:
            self.post_message(self.TriageAction("snooze", self._selected_issue, snooze_days=7))
            self._advance_to_next()

    def action_snooze_next_month(self) -> None:
        """Snooze the current issue for a month."""
        if self._selected_issue:
            self.post_message(self.TriageAction("snooze", self._selected_issue, snooze_days=30))
            self._advance_to_next()

    def action_assign_to_me(self) -> None:
        """Assign the current issue to self."""
        if self._selected_issue:
            self.post_message(self.TriageAction("assign_to_me", self._selected_issue))

    def action_toggle_quick_mode(self) -> None:
        """Toggle quick triage mode."""
        self._quick_mode = not self._quick_mode
        self._update_quick_mode_display()

    def _update_quick_mode_display(self) -> None:
        """Update display based on quick mode state."""
        quick_triage = self.query_one("#quick-triage")
        table = self.query_one("#triage-table", DataTable)
        preview = self.query_one("#issue-preview")

        if self._quick_mode and self._issues:
            quick_triage.add_class("visible")
            table.display = False
            preview.display = False
            self._update_quick_issue_display()
        else:
            quick_triage.remove_class("visible")
            table.display = True
            preview.display = True

    def _update_quick_issue_display(self) -> None:
        """Update quick mode issue display."""
        if not self._selected_issue:
            return

        issue = self._selected_issue
        issue_id = self.query_one("#quick-issue-id", Static)
        issue_desc = self.query_one("#quick-issue-desc", Static)

        issue_id.update(f"{issue.identifier}: {issue.title}")

        desc = issue.description or "No description"
        if len(desc) > 500:
            desc = desc[:497] + "..."
        issue_desc.update(desc)

    def _advance_to_next(self) -> None:
        """Advance to next issue in quick mode."""
        self._triaged_count += 1
        if self._quick_mode:
            # Will be updated when remove_issue is called
            pass

    def action_next_issue(self) -> None:
        """Move to next issue."""
        table = self.query_one("#triage-table", DataTable)
        table.action_cursor_down()

    def action_prev_issue(self) -> None:
        """Move to previous issue."""
        table = self.query_one("#triage-table", DataTable)
        table.action_cursor_up()

    def get_selected_issue(self) -> Issue | None:
        """Get the currently selected issue."""
        return self._selected_issue

    def remove_issue(self, issue_id: str) -> None:
        """Remove an issue from the triage queue."""
        self._issues = [i for i in self._issues if i.id != issue_id]
        self._triaged_count += 1
        self._refresh_table()
        self._update_stats()

        if self._issues:
            table = self.query_one("#triage-table", DataTable)
            if table.row_count > 0:
                for _row_key, issue in self._issue_map.items():
                    self._selected_issue = issue
                    self._update_preview(issue)
                    if self._quick_mode:
                        self._update_quick_issue_display()
                    break
        else:
            self._selected_issue = None
            if self._quick_mode:
                self._update_quick_mode_display()
