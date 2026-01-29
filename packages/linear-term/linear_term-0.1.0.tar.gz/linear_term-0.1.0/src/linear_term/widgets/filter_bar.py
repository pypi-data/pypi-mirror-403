"""Filter bar widget with syntax parsing."""

import re
from dataclasses import dataclass, field
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Input, Static


@dataclass
class ParsedFilter:
    """Parsed filter criteria."""

    text: str = ""
    assignee: str | None = None
    status: str | None = None
    priority: str | None = None
    project: str | None = None
    label: str | None = None
    is_unassigned: bool = False
    exclude_labels: list[str] = field(default_factory=list)
    due: str | None = None  # overdue, today, week, month

    def is_empty(self) -> bool:
        """Check if filter is empty."""
        return (
            not self.text
            and not self.assignee
            and not self.status
            and not self.priority
            and not self.project
            and not self.label
            and not self.is_unassigned
            and not self.exclude_labels
            and not self.due
        )

    def to_display(self) -> str:
        """Convert to display string."""
        parts = []
        if self.text:
            parts.append(f'"{self.text}"')
        if self.assignee:
            parts.append(f"assignee:{self.assignee}")
        if self.is_unassigned:
            parts.append("unassigned")
        if self.status:
            parts.append(f"status:{self.status}")
        if self.priority:
            parts.append(f"priority:{self.priority}")
        if self.project:
            parts.append(f"project:{self.project}")
        if self.label:
            parts.append(f"label:{self.label}")
        for lbl in self.exclude_labels:
            parts.append(f"-label:{lbl}")
        if self.due:
            parts.append(f"due:{self.due}")
        return " ".join(parts) if parts else ""

    def to_dict(self) -> dict:
        """Serialize to dictionary for storage."""
        return {
            "text": self.text,
            "assignee": self.assignee,
            "status": self.status,
            "priority": self.priority,
            "project": self.project,
            "label": self.label,
            "is_unassigned": self.is_unassigned,
            "exclude_labels": self.exclude_labels,
            "due": self.due,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ParsedFilter":
        """Deserialize from dictionary."""
        return cls(
            text=data.get("text", ""),
            assignee=data.get("assignee"),
            status=data.get("status"),
            priority=data.get("priority"),
            project=data.get("project"),
            label=data.get("label"),
            is_unassigned=data.get("is_unassigned", False),
            exclude_labels=data.get("exclude_labels", []),
            due=data.get("due"),
        )


def parse_filter_query(query: str) -> ParsedFilter:
    """Parse a filter query string into structured filter."""
    result = ParsedFilter()
    remaining_text = []

    # Pattern for key:value pairs
    kv_pattern = re.compile(r"(-?)(\w+):(\S+)")

    # Split by spaces but preserve quoted strings
    parts = re.findall(r'"[^"]*"|\S+', query)

    for part in parts:
        # Handle quoted text
        if part.startswith('"') and part.endswith('"'):
            result.text = part[1:-1]
            continue

        # Handle key:value pairs
        match = kv_pattern.match(part)
        if match:
            negate, key, value = match.groups()
            key_lower = key.lower()

            if key_lower in ("assignee", "assign", "a"):
                if value.lower() == "me":
                    result.assignee = "me"
                else:
                    result.assignee = value
            elif key_lower in ("status", "state", "s"):
                result.status = value.lower()
            elif key_lower in ("priority", "pri", "p"):
                result.priority = value.lower()
            elif key_lower in ("project", "proj"):
                result.project = value
            elif key_lower in ("label", "l", "tag"):
                if negate:
                    result.exclude_labels.append(value)
                else:
                    result.label = value
            elif key_lower in ("due", "d"):
                result.due = value.lower()
        elif part.lower() == "unassigned":
            result.is_unassigned = True
        elif part.lower() in ("overdue", "today", "week", "month"):
            result.due = part.lower()
        else:
            # Plain text search
            remaining_text.append(part)

    if remaining_text:
        result.text = " ".join(remaining_text)

    return result


class FilterBar(Horizontal):
    """Interactive filter bar with syntax support."""

    DEFAULT_CSS = """
    FilterBar {
        height: 3;
        background: $surface-darken-1;
        padding: 0 1;
        display: none;
    }

    FilterBar.visible {
        display: block;
    }

    FilterBar Input {
        width: 1fr;
    }

    FilterBar .filter-hint {
        width: auto;
        color: $text-muted;
        padding: 0 1;
    }

    FilterBar .filter-icon {
        width: 3;
        color: $accent;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close", show=False),
        Binding("enter", "apply", "Apply", show=False),
    ]

    class FilterApplied(Message):
        """Message when filter is applied."""

        def __init__(self, parsed: ParsedFilter, raw_query: str) -> None:
            self.parsed = parsed
            self.raw_query = raw_query
            super().__init__()

    class FilterCleared(Message):
        """Message when filter is cleared."""

        pass

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._history: list[str] = []
        self._history_index: int = -1

    def compose(self) -> ComposeResult:
        """Compose the filter bar."""
        yield Static("/", classes="filter-icon")
        yield Input(
            placeholder="Filter: assignee:me status:started priority:high label:bug -label:wontfix",
            id="filter-input",
        )
        yield Static("Enter to apply, Esc to close", classes="filter-hint")

    def show(self, initial_value: str = "") -> None:
        """Show the filter bar and focus input."""
        self.add_class("visible")
        inp = self.query_one("#filter-input", Input)
        inp.value = initial_value
        inp.focus()

    def hide(self) -> None:
        """Hide the filter bar."""
        self.remove_class("visible")

    def is_visible(self) -> bool:
        """Check if filter bar is visible."""
        return self.has_class("visible")

    def action_close(self) -> None:
        """Close the filter bar."""
        self.hide()
        self.post_message(self.FilterCleared())

    def action_apply(self) -> None:
        """Apply the filter."""
        inp = self.query_one("#filter-input", Input)
        query = inp.value.strip()

        if query:
            # Add to history
            if not self._history or self._history[-1] != query:
                self._history.append(query)
            self._history_index = -1

            parsed = parse_filter_query(query)
            self.post_message(self.FilterApplied(parsed, query))
        else:
            self.post_message(self.FilterCleared())

        self.hide()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle enter in input."""
        event.stop()
        self.action_apply()

    def get_current_filter(self) -> str:
        """Get current filter text."""
        return self.query_one("#filter-input", Input).value

    def clear(self) -> None:
        """Clear the filter input."""
        self.query_one("#filter-input", Input).value = ""
