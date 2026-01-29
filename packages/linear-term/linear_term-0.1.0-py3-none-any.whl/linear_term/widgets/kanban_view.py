"""Kanban board view widget."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Static

from linear_term.api.models import Issue, WorkflowState
from linear_term.config import KanbanConfig


class KanbanCard(Vertical):
    """A single issue card in the Kanban board."""

    DEFAULT_CSS = """
    KanbanCard {
        height: auto;
        margin: 0 0 1 0;
        padding: 1;
        background: $surface-lighten-1;
        border: solid $primary-darken-2;
    }

    KanbanCard:focus {
        border: solid $accent;
        background: $surface-lighten-2;
    }

    KanbanCard .card-id {
        color: $text-muted;
    }

    KanbanCard .card-title {
        text-style: bold;
    }

    KanbanCard .card-meta {
        color: $text-muted;
        padding-top: 1;
    }
    """

    can_focus = True

    class CardSelected(Message):
        """Message when card is selected."""

        def __init__(self, issue: Issue) -> None:
            self.issue = issue
            super().__init__()

    def __init__(self, issue: Issue, **kwargs) -> None:
        super().__init__(**kwargs)
        self.issue = issue

    def compose(self) -> ComposeResult:
        yield Static(self.issue.identifier, classes="card-id")
        title = self.issue.title
        if len(title) > 40:
            title = title[:37] + "..."
        yield Static(title, classes="card-title")

        meta_parts = []
        if self.issue.priority:
            meta_parts.append(self.issue.priority_icon)
        if self.issue.assignee:
            name = self.issue.assignee.display_name or self.issue.assignee.name
            if len(name) > 10:
                name = name[:9] + "..."
            meta_parts.append(name)
        if meta_parts:
            yield Static(" ".join(meta_parts), classes="card-meta")

    def on_click(self) -> None:
        """Handle click on card."""
        self.post_message(self.CardSelected(self.issue))


class KanbanColumn(Vertical):
    """A column in the Kanban board representing a workflow state."""

    DEFAULT_CSS = """
    KanbanColumn {
        width: 30;
        height: 1fr;
        border-right: solid $primary-darken-2;
        padding: 0 1;
    }

    KanbanColumn:last-of-type {
        border-right: none;
    }

    KanbanColumn .column-header {
        text-style: bold;
        padding: 1 0;
        border-bottom: solid $primary-darken-2;
        margin-bottom: 1;
        height: auto;
    }

    KanbanColumn .column-cards {
        height: 1fr;
    }

    KanbanColumn .empty-column {
        color: $text-muted;
        text-align: center;
        padding: 2;
    }
    """

    def __init__(self, state: WorkflowState, issues: list[Issue], **kwargs) -> None:
        super().__init__(**kwargs)
        self.state = state
        self.issues = issues

    def compose(self) -> ComposeResult:
        header_text = f"{self.state.name} ({len(self.issues)})"
        yield Static(header_text, classes="column-header")

        with VerticalScroll(classes="column-cards"):
            if self.issues:
                for issue in self.issues:
                    yield KanbanCard(issue)
            else:
                yield Static("No issues", classes="empty-column")


class KanbanView(Horizontal):
    """Kanban board view showing issues grouped by status."""

    can_focus = True

    DEFAULT_CSS = """
    KanbanView {
        height: 100%;
        width: 1fr;
        background: $surface;
    }
    """

    BINDINGS = [
        Binding("h", "prev_column", "Prev Column", show=False),
        Binding("l", "next_column", "Next Column", show=False),
        Binding("left", "prev_column", "Prev Column", show=False),
        Binding("right", "next_column", "Next Column", show=False),
        Binding("j", "next_card", "Next Card", show=False),
        Binding("k", "prev_card", "Prev Card", show=False),
        Binding("down", "next_card", "Next Card", show=False),
        Binding("up", "prev_card", "Prev Card", show=False),
        Binding("enter", "select_card", "Open", show=True),
        Binding("B", "app.configure_board", "Config Columns", show=True),
        Binding("b", "app.toggle_board_view", "List View", show=True),
    ]

    class IssueSelected(Message):
        """Message when an issue is selected from the board."""

        def __init__(self, issue: Issue) -> None:
            self.issue = issue
            super().__init__()

    def __init__(self, kanban_config: KanbanConfig | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._states: list[WorkflowState] = []
        self._issues: list[Issue] = []
        self._current_column: int = 0
        self._current_row: int = 0
        self._config = kanban_config or KanbanConfig()

    def compose(self) -> ComposeResult:
        yield Static("Loading board...", classes="board-placeholder")

    def update_board(self, states: list[WorkflowState], issues: list[Issue]) -> None:
        """Update the board with new data."""
        self._states = sorted(states, key=lambda s: s.position)
        self._issues = issues
        self._rebuild_board()

    def _rebuild_board(self) -> None:
        """Rebuild the board columns."""
        self.remove_children()

        if not self._issues:
            self.mount(Static("No issues to display"))
            return

        # Group issues by state NAME (not ID) to merge same-named states across teams
        states_by_name: dict[str, WorkflowState] = {}
        issues_by_name: dict[str, list[Issue]] = {}

        for issue in self._issues:
            if issue.state:
                state_name = issue.state.name

                # Skip done/canceled if configured
                if self._config.hide_done:
                    if issue.state.type in ("completed", "canceled"):
                        continue

                if state_name not in states_by_name:
                    states_by_name[state_name] = issue.state
                    issues_by_name[state_name] = []
                issues_by_name[state_name].append(issue)

        if not states_by_name:
            self.mount(Static("No issues with workflow states"))
            return

        # Determine column order
        if self._config.columns:
            # Use configured order, only showing configured columns
            ordered_names = [n for n in self._config.columns if n in states_by_name]
        else:
            # Default: sort by workflow position
            sorted_states = sorted(states_by_name.values(), key=lambda s: s.position)
            ordered_names = [s.name for s in sorted_states]

        # Create columns in order
        for state_name in ordered_names:
            state = states_by_name[state_name]
            state_issues = issues_by_name.get(state_name, [])
            state_issues.sort(key=lambda i: (i.priority or 5, i.identifier))
            column = KanbanColumn(state, state_issues)
            self.mount(column)

    def set_config(self, config: KanbanConfig) -> None:
        """Update the kanban configuration."""
        self._config = config

    def get_visible_columns(self) -> list[str]:
        """Get list of currently visible column names."""
        return [col.state.name for col in self.query(KanbanColumn)]

    def on_kanban_card_card_selected(self, event: KanbanCard.CardSelected) -> None:
        """Handle card selection."""
        self.post_message(self.IssueSelected(event.issue))

    def action_prev_column(self) -> None:
        """Move to previous column."""
        if self._current_column > 0:
            self._current_column -= 1
            self._current_row = 0
            self._focus_current_card()

    def action_next_column(self) -> None:
        """Move to next column."""
        columns = list(self.query(KanbanColumn))
        if self._current_column < len(columns) - 1:
            self._current_column += 1
            self._current_row = 0
            self._focus_current_card()

    def action_next_card(self) -> None:
        """Move to next card in column."""
        self._current_row += 1
        self._focus_current_card()

    def action_prev_card(self) -> None:
        """Move to previous card in column."""
        if self._current_row > 0:
            self._current_row -= 1
            self._focus_current_card()

    def action_select_card(self) -> None:
        """Select the current card."""
        card = self._get_current_card()
        if card:
            self.post_message(self.IssueSelected(card.issue))

    def _focus_current_card(self) -> None:
        """Focus the card at current position."""
        card = self._get_current_card()
        if card:
            card.focus()

    def _get_current_card(self) -> KanbanCard | None:
        """Get the card at current position."""
        try:
            columns = list(self.query(KanbanColumn))
            if not columns or self._current_column >= len(columns):
                return None
            column = columns[self._current_column]
            cards = list(column.query(KanbanCard))
            if cards:
                # Clamp row to valid range
                self._current_row = max(0, min(self._current_row, len(cards) - 1))
                return cards[self._current_row]
        except Exception:
            pass
        return None
