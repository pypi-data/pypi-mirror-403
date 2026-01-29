"""Status bar widget."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.widgets import Static

# Context-sensitive hint sets
HINT_SETS = {
    "list": "?:Help  /:Search  f:Filter  b:Board  Space:Select",
    "board": "?:Help  b:List  B:Config  h/l:Columns  j/k:Cards",
    "triage": "?:Help  a:Accept  d:Decline  s:Snooze  m:Mine",
    "detail": "?:Help  c:Comment  e:Edit  h/l:Tabs  p:Parent",
}

DEFAULT_HINTS = "?:Help  Ctrl-K:Commands  Ctrl-N:New  f:Filter  b:Board"


class StatusBar(Horizontal):
    """Status bar showing help hints, sync status, and info."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: $primary-darken-2;
        color: $text;
        dock: bottom;
    }

    StatusBar .help-hints {
        width: 1fr;
        padding: 0 1;
    }

    StatusBar .sync-status {
        width: auto;
        padding: 0 1;
    }

    StatusBar .notifications {
        width: auto;
        padding: 0 1;
        display: none;
    }

    StatusBar .notifications.visible {
        display: block;
    }

    StatusBar .notifications.has-new {
        color: $warning;
        text-style: bold;
    }

    StatusBar .workspace {
        width: auto;
        padding: 0 1;
        color: $text-muted;
    }

    StatusBar .pagination {
        width: auto;
        padding: 0 1;
        color: $text-muted;
    }

    StatusBar .error {
        color: $error;
    }

    StatusBar .warning {
        color: $warning;
    }

    StatusBar .success {
        color: $success;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._sync_status: str = "●"
        self._workspace: str = ""
        self._pagination: str = ""
        self._message: str = ""
        self._message_type: str = "info"
        self._new_comments: int = 0
        self._updated_issues: int = 0
        self._current_context: str = "list"

    def compose(self) -> ComposeResult:
        """Compose the status bar content."""
        yield Static(DEFAULT_HINTS, id="help-hints", classes="help-hints")
        yield Static("", id="notifications", classes="notifications")
        yield Static("●", id="sync-status", classes="sync-status success")
        yield Static("", id="workspace", classes="workspace")
        yield Static("", id="pagination", classes="pagination")

    def set_sync_status(self, syncing: bool, error: bool = False) -> None:
        """Update the sync status indicator."""
        try:
            status = self.query_one("#sync-status", Static)
        except NoMatches:
            return
        if error:
            status.update("⚠")
            status.remove_class("success", "warning")
            status.add_class("error")
        elif syncing:
            status.update("↻")
            status.remove_class("success", "error")
            status.add_class("warning")
        else:
            status.update("●")
            status.remove_class("warning", "error")
            status.add_class("success")

    def set_workspace(self, workspace: str) -> None:
        """Set the workspace name."""
        self._workspace = workspace
        try:
            ws = self.query_one("#workspace", Static)
            ws.update(workspace)
        except NoMatches:
            pass

    def set_pagination(self, current: int, total: int) -> None:
        """Set pagination info."""
        self._pagination = f"Viewing {current} of {total}"
        try:
            pag = self.query_one("#pagination", Static)
            pag.update(self._pagination)
        except NoMatches:
            pass

    def show_message(self, message: str, message_type: str = "info") -> None:
        """Show a temporary message in the help hints area."""
        try:
            hints = self.query_one("#help-hints", Static)
        except NoMatches:
            return
        hints.update(message)
        hints.remove_class("error", "warning", "success")
        if message_type in ("error", "warning", "success"):
            hints.add_class(message_type)

    def reset_hints(self) -> None:
        """Reset the help hints to context-appropriate defaults."""
        try:
            hints = self.query_one("#help-hints", Static)
        except NoMatches:
            return
        hint_text = HINT_SETS.get(self._current_context, DEFAULT_HINTS)
        hints.update(hint_text)
        hints.remove_class("error", "warning", "success")

    def set_view_context(self, context: str) -> None:
        """Update hints based on the current view context.

        Args:
            context: One of 'list', 'board', 'triage', or 'detail'
        """
        self._current_context = context
        self.reset_hints()

    def set_notifications(self, new_comments: int = 0, updated_issues: int = 0) -> None:
        """Set notification counts."""
        self._new_comments = new_comments
        self._updated_issues = updated_issues

        try:
            notif = self.query_one("#notifications", Static)
        except NoMatches:
            return

        total = new_comments + updated_issues
        if total > 0:
            parts = []
            if new_comments > 0:
                parts.append(f"{new_comments} comment{'s' if new_comments > 1 else ''}")
            if updated_issues > 0:
                parts.append(f"{updated_issues} update{'s' if updated_issues > 1 else ''}")
            notif.update(f"[{' + '.join(parts)}]")
            notif.add_class("visible", "has-new")
        else:
            notif.update("")
            notif.remove_class("visible", "has-new")

    def clear_notifications(self) -> None:
        """Clear all notifications."""
        self.set_notifications(0, 0)
