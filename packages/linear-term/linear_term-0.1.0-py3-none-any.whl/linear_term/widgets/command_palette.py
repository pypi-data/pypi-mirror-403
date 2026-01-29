"""Command palette widget."""

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Input, ListItem, ListView, Static


@dataclass
class Command:
    """A command in the palette."""

    name: str
    description: str
    shortcut: str
    action: str
    category: str = "Actions"


DEFAULT_COMMANDS = [
    Command("Create Issue", "Create a new issue", "Ctrl-N", "create_issue", "Actions"),
    Command("Quick Capture", "Quick capture new issue", "Ctrl-Shift-N", "quick_capture", "Actions"),
    Command("Refresh", "Refresh data from Linear", "Ctrl-R", "refresh", "Actions"),
    Command("Search", "Search issues", "/", "search", "Actions"),
    Command("My Issues", "Go to my issues", "g m", "goto_my_issues", "Navigation"),
    Command("Triage", "Go to triage view", "g t", "goto_triage", "Navigation"),
    Command("Sort By...", "Change sort order", "S", "change_sort", "Sort"),
    Command("Sort by Priority", "Sort issues by priority", "", "sort_priority", "Sort"),
    Command("Sort by ID", "Sort issues by identifier", "", "sort_identifier", "Sort"),
    Command("Sort by Title", "Sort issues alphabetically by title", "", "sort_title", "Sort"),
    Command("Sort by Created", "Sort issues by creation date", "", "sort_created", "Sort"),
    Command("Sort by Due Date", "Sort issues by due date", "", "sort_due_date", "Sort"),
    Command("Change Status", "Change issue status", "s", "change_status", "Issue"),
    Command("Change Assignee", "Change issue assignee", "a", "change_assignee", "Issue"),
    Command("Change Priority", "Change issue priority", "p", "change_priority", "Issue"),
    Command("Add Labels", "Add or remove labels", "l", "change_labels", "Issue"),
    Command("Add Comment", "Add a comment", "c", "add_comment", "Issue"),
    Command("Toggle Favorite", "Add/remove from favorites", "*", "toggle_favorite", "Issue"),
    Command("Copy URL", "Copy issue URL", "y", "copy_url", "Issue"),
    Command("Open in Browser", "Open issue in browser", "o", "open_browser", "Issue"),
    Command("Edit Issue", "Edit the issue", "e", "edit_issue", "Issue"),
    Command("Archive Issue", "Archive the issue", "Ctrl-A", "archive_issue", "Issue"),
    Command("Delete Issue", "Permanently delete the issue", "Del", "delete_issue", "Issue"),
    Command("Toggle Sidebar", "Show/hide sidebar", "Ctrl-B", "toggle_sidebar", "View"),
    Command("Toggle Detail Panel", "Show/hide detail panel", "Ctrl-D", "toggle_detail", "View"),
    Command("Settings", "Open settings panel", ",", "open_settings", "View"),
    Command("Help", "Show keyboard shortcuts", "?", "show_help", "Help"),
]


class CommandPalette(ModalScreen[str | None]):
    """Command palette modal for searching and executing commands."""

    DEFAULT_CSS = """
    CommandPalette {
        align: center middle;
    }

    CommandPalette > Container {
        width: 60;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: solid $accent;
        padding: 1;
    }

    CommandPalette Input {
        width: 100%;
        margin-bottom: 1;
    }

    CommandPalette ListView {
        height: auto;
        max-height: 20;
    }

    CommandPalette ListItem {
        padding: 0 1;
    }

    CommandPalette ListItem:hover {
        background: $surface-lighten-1;
    }

    CommandPalette .highlighted {
        background: $accent;
    }

    CommandPalette .command-name {
        width: 1fr;
    }

    CommandPalette .command-shortcut {
        width: auto;
        color: $text-muted;
    }

    CommandPalette .command-category {
        color: $text-muted;
        text-style: italic;
        padding: 1 0 0 0;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=False),
        Binding("enter", "select", "Select", show=False),
    ]

    class CommandSelected(Message):
        """Message when a command is selected."""

        def __init__(self, action: str) -> None:
            self.action = action
            super().__init__()

    def __init__(
        self,
        commands: list[Command] | None = None,
        issue_context: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._commands = commands or DEFAULT_COMMANDS
        self._filtered_commands: list[Command] = []
        self._issue_context = issue_context

    def compose(self) -> ComposeResult:
        """Compose the command palette content."""
        with Container():
            yield Input(placeholder="Type a command...", id="command-input")
            yield ListView(id="command-list")

    def on_mount(self) -> None:
        """Set up the command palette on mount."""
        self._filter_commands("")
        self.query_one("#command-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        self._filter_commands(event.value)

    def _filter_commands(self, query: str) -> None:
        """Filter commands based on query."""
        query_lower = query.lower()
        self._filtered_commands = []

        for cmd in self._commands:
            if cmd.category == "Issue" and not self._issue_context:
                continue

            matches_name = query_lower in cmd.name.lower()
            matches_desc = query_lower in cmd.description.lower()
            if not query or matches_name or matches_desc:
                self._filtered_commands.append(cmd)

        self._update_list()

    def _update_list(self) -> None:
        """Update the command list display."""
        list_view = self.query_one("#command-list", ListView)
        list_view.clear()

        current_category = ""
        for cmd in self._filtered_commands:
            if cmd.category != current_category:
                current_category = cmd.category
                list_view.append(
                    ListItem(
                        Static(f"── {current_category} ──", classes="command-category"),
                    )
                )

            item = ListItem(
                Static(f"{cmd.name}  \\[{cmd.shortcut}]"),
            )
            item.data = cmd
            list_view.append(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle list item selection."""
        if hasattr(event.item, "data") and event.item.data:
            cmd = event.item.data
            self.dismiss(cmd.action)

    def action_select(self) -> None:
        """Select the highlighted command."""
        list_view = self.query_one("#command-list", ListView)
        if list_view.highlighted_child:
            item = list_view.highlighted_child
            if hasattr(item, "data") and item.data:
                cmd = item.data
                self.dismiss(cmd.action)

    def action_dismiss(self) -> None:
        """Dismiss the palette."""
        self.dismiss(None)


class SearchDialog(ModalScreen[str | None]):
    """Search dialog for searching issues with history support."""

    # Class-level search history (persists across dialogs)
    _search_history: list[str] = []
    _max_history: int = 20

    DEFAULT_CSS = """
    SearchDialog {
        align: center middle;
    }

    SearchDialog > Container {
        width: 60;
        height: auto;
        max-height: 70%;
        background: $surface;
        border: solid $accent;
        padding: 1;
    }

    SearchDialog Input {
        width: 100%;
    }

    SearchDialog .search-hint {
        color: $text-muted;
        padding-top: 1;
    }

    SearchDialog .history-section {
        padding-top: 1;
        max-height: 10;
    }

    SearchDialog .history-header {
        color: $text-muted;
        padding-bottom: 1;
    }

    SearchDialog ListView {
        height: auto;
        max-height: 8;
    }

    SearchDialog ListItem {
        padding: 0 1;
    }

    SearchDialog ListItem:hover {
        background: $surface-lighten-1;
    }

    SearchDialog ListView > ListItem.--highlight {
        background: $accent;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=False),
        Binding("enter", "search", "Search", show=False),
        Binding("up", "history_prev", "Previous", show=False),
        Binding("down", "history_next", "Next", show=False),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._history_index: int = -1

    def compose(self) -> ComposeResult:
        """Compose the search dialog content."""
        with Container():
            yield Input(
                placeholder="Search issues or type ID (e.g., ENG-123)...",
                id="search-input",
            )
            yield Static(
                "Enter to search | Up/Down for history | Type issue ID to jump",
                classes="search-hint",
            )
            if SearchDialog._search_history:
                with Container(classes="history-section"):
                    yield Static("Recent:", classes="history-header")
                    yield ListView(id="history-list")

    def on_mount(self) -> None:
        """Focus the input on mount."""
        self.query_one("#search-input", Input).focus()
        self._populate_history()

    def _populate_history(self) -> None:
        """Populate the history list."""
        try:
            history_list = self.query_one("#history-list", ListView)
            for query in reversed(SearchDialog._search_history[-5:]):
                item = ListItem(Static(query))
                item.data = query
                history_list.append(item)
        except Exception:
            pass

    def action_search(self) -> None:
        """Execute the search."""
        query = self.query_one("#search-input", Input).value.strip()
        if query:
            # Add to history
            if query in SearchDialog._search_history:
                SearchDialog._search_history.remove(query)
            SearchDialog._search_history.append(query)
            if len(SearchDialog._search_history) > SearchDialog._max_history:
                SearchDialog._search_history.pop(0)
        self.dismiss(query if query else None)

    def action_dismiss(self) -> None:
        """Dismiss the dialog."""
        self.dismiss(None)

    def action_history_prev(self) -> None:
        """Navigate to previous history entry."""
        if not SearchDialog._search_history:
            return
        if self._history_index == -1:
            self._history_index = len(SearchDialog._search_history) - 1
        elif self._history_index > 0:
            self._history_index -= 1

        self._apply_history_entry()

    def action_history_next(self) -> None:
        """Navigate to next history entry."""
        if not SearchDialog._search_history:
            return
        if self._history_index < len(SearchDialog._search_history) - 1:
            self._history_index += 1
            self._apply_history_entry()
        else:
            self._history_index = -1
            self.query_one("#search-input", Input).value = ""

    def _apply_history_entry(self) -> None:
        """Apply the current history entry to the input."""
        if 0 <= self._history_index < len(SearchDialog._search_history):
            query = SearchDialog._search_history[self._history_index]
            self.query_one("#search-input", Input).value = query

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle history item selection."""
        if hasattr(event.item, "data") and event.item.data:
            self.query_one("#search-input", Input).value = event.item.data
            self.action_search()


class QuickSelectDialog(ModalScreen[str | None]):
    """Quick select dialog for choosing from a list of options."""

    DEFAULT_CSS = """
    QuickSelectDialog {
        align: center middle;
    }

    QuickSelectDialog > Container {
        width: 50;
        height: auto;
        max-height: 60%;
        background: $surface;
        border: solid $accent;
        padding: 1;
    }

    QuickSelectDialog .dialog-title {
        text-style: bold;
        padding-bottom: 1;
    }

    QuickSelectDialog Input {
        width: 100%;
        margin-bottom: 1;
    }

    QuickSelectDialog ListView {
        height: auto;
        max-height: 15;
    }

    QuickSelectDialog ListItem {
        padding: 0 1;
    }

    QuickSelectDialog ListItem:hover {
        background: $surface-lighten-1;
    }

    QuickSelectDialog ListView > ListItem.--highlight {
        background: $accent;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=False),
        Binding("enter", "select", "Select", show=False, priority=True),
        Binding("up", "cursor_up", "Up", show=False, priority=True),
        Binding("down", "cursor_down", "Down", show=False, priority=True),
    ]

    def __init__(
        self,
        title: str,
        options: list[tuple[str, str]],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._options = options
        self._filtered_options: list[tuple[str, str]] = options.copy()
        self._highlighted_index: int = 0

    def compose(self) -> ComposeResult:
        """Compose the dialog content."""
        with Container():
            yield Static(self._title, classes="dialog-title")
            yield Input(placeholder="Filter...", id="filter-input")
            yield ListView(id="options-list")

    def on_mount(self) -> None:
        """Set up the dialog on mount."""
        self._update_list()
        self.query_one("#filter-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        query = event.value.lower()
        self._filtered_options = [
            (value, label) for value, label in self._options if query in label.lower()
        ]
        self._highlighted_index = 0
        self._update_list()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input field."""
        event.stop()
        self.action_select()

    def _update_list(self) -> None:
        """Update the options list."""
        list_view = self.query_one("#options-list", ListView)
        list_view.clear()

        for value, label in self._filtered_options:
            item = ListItem(Static(label))
            item.data = value
            list_view.append(item)

        if self._filtered_options:
            self._highlighted_index = min(self._highlighted_index, len(self._filtered_options) - 1)
            list_view.index = self._highlighted_index

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection."""
        if hasattr(event.item, "data"):
            self.dismiss(event.item.data)

    def action_cursor_up(self) -> None:
        """Move selection up."""
        if self._filtered_options and self._highlighted_index > 0:
            self._highlighted_index -= 1
            list_view = self.query_one("#options-list", ListView)
            list_view.index = self._highlighted_index

    def action_cursor_down(self) -> None:
        """Move selection down."""
        if self._filtered_options and self._highlighted_index < len(self._filtered_options) - 1:
            self._highlighted_index += 1
            list_view = self.query_one("#options-list", ListView)
            list_view.index = self._highlighted_index

    def action_select(self) -> None:
        """Select the highlighted option."""
        if self._filtered_options and 0 <= self._highlighted_index < len(self._filtered_options):
            value, _ = self._filtered_options[self._highlighted_index]
            self.dismiss(value)

    def action_dismiss(self) -> None:
        """Dismiss the dialog."""
        self.dismiss(None)


class TextInputDialog(ModalScreen[str | None]):
    """Dialog for text input."""

    DEFAULT_CSS = """
    TextInputDialog {
        align: center middle;
    }

    TextInputDialog > Container {
        width: 60;
        height: auto;
        background: $surface;
        border: solid $accent;
        padding: 1;
    }

    TextInputDialog .dialog-title {
        text-style: bold;
        padding-bottom: 1;
    }

    TextInputDialog Input {
        width: 100%;
    }

    TextInputDialog .hint {
        color: $text-muted;
        padding-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=False),
        Binding("enter", "submit", "Submit", show=False),
    ]

    def __init__(
        self,
        title: str,
        placeholder: str = "",
        initial_value: str = "",
        hint: str = "Press Enter to submit, Escape to cancel",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._placeholder = placeholder
        self._initial_value = initial_value
        self._hint = hint

    def compose(self) -> ComposeResult:
        """Compose the dialog content."""
        with Container():
            yield Static(self._title, classes="dialog-title")
            yield Input(
                placeholder=self._placeholder,
                value=self._initial_value,
                id="text-input",
            )
            yield Static(self._hint, classes="hint")

    def on_mount(self) -> None:
        """Focus the input on mount."""
        self.query_one("#text-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        event.stop()
        self.action_submit()

    def action_submit(self) -> None:
        """Submit the input."""
        value = self.query_one("#text-input", Input).value
        self.dismiss(value)

    def action_dismiss(self) -> None:
        """Dismiss the dialog."""
        self.dismiss(None)


class ConfirmDialog(ModalScreen[bool]):
    """Confirmation dialog."""

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }

    ConfirmDialog > Container {
        width: 50;
        height: auto;
        background: $surface;
        border: solid $warning;
        padding: 1;
    }

    ConfirmDialog .dialog-title {
        text-style: bold;
        padding-bottom: 1;
    }

    ConfirmDialog .dialog-message {
        padding-bottom: 1;
    }

    ConfirmDialog .dialog-buttons {
        text-align: center;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("enter", "confirm", "Confirm", show=False),
        Binding("y", "confirm", "Yes", show=False),
        Binding("n", "cancel", "No", show=False),
    ]

    def __init__(
        self,
        title: str,
        message: str,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._message = message

    def compose(self) -> ComposeResult:
        """Compose the dialog content."""
        with Container():
            yield Static(self._title, classes="dialog-title")
            yield Static(self._message, classes="dialog-message")
            yield Static("Press Y to confirm, N or Escape to cancel", classes="dialog-buttons")

    def action_confirm(self) -> None:
        """Confirm the action."""
        self.dismiss(True)

    def action_cancel(self) -> None:
        """Cancel the action."""
        self.dismiss(False)
