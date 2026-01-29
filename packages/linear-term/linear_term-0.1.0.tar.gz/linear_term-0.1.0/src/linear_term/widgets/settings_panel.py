"""Settings panel widget for configuring the application."""

from __future__ import annotations

import copy

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, Select, Static

from linear_term.config import THEMES, Config
from linear_term.widgets.sidebar import Sidebar


class SettingsPanel(ModalScreen[Config | None]):
    """Settings panel modal for configuring application settings."""

    DEFAULT_CSS = """
    SettingsPanel {
        align: center middle;
    }

    SettingsPanel > Container {
        width: 70;
        height: auto;
        max-height: 85%;
        background: $surface;
        border: solid $accent;
        padding: 1 2;
    }

    SettingsPanel .settings-header {
        height: auto;
        padding-bottom: 1;
        border-bottom: solid $accent;
        margin-bottom: 1;
    }

    SettingsPanel .settings-title {
        text-style: bold;
        text-align: center;
    }

    SettingsPanel .settings-shortcuts {
        text-align: center;
        color: $text-muted;
    }

    SettingsPanel .section-title {
        text-style: bold;
        color: $accent;
        padding: 1 0 0 0;
    }

    SettingsPanel .setting-row {
        height: auto;
        padding: 0 0 1 0;
    }

    SettingsPanel .setting-label {
        width: 22;
        padding: 1 1 0 0;
    }

    SettingsPanel .setting-input {
        width: 1fr;
    }

    SettingsPanel Select {
        width: 100%;
    }

    SettingsPanel Input {
        width: 100%;
    }

    SettingsPanel .setting-hint {
        color: $text-muted;
        text-style: italic;
        padding: 0 0 0 23;
    }

    SettingsPanel .button-row {
        height: auto;
        padding-top: 1;
        border-top: solid $accent;
        margin-top: 1;
        align: center middle;
    }

    SettingsPanel Button {
        margin: 0 1;
    }

    SettingsPanel #btn-save {
        background: $success;
    }

    SettingsPanel #btn-cancel {
        background: $error;
    }

    SettingsPanel VerticalScroll {
        height: auto;
        max-height: 80%;
    }

    SettingsPanel .filter-checkbox {
        height: auto;
        margin: 0 0 0 2;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("ctrl+s", "save", "Save", show=False, priority=True),
    ]

    def __init__(self, config: Config, **kwargs) -> None:
        super().__init__(**kwargs)
        self._config = copy.deepcopy(config)

    def compose(self) -> ComposeResult:
        """Compose the settings panel content."""
        with Container():
            with Container(classes="settings-header"):
                yield Static("Settings", classes="settings-title")
                yield Static(
                    "Tab navigate · → expand · Space select · Ctrl+S save · Esc cancel",
                    classes="settings-shortcuts",
                )

            with VerticalScroll():
                # Appearance Section
                yield Static("Appearance", classes="section-title")

                with Horizontal(classes="setting-row"):
                    yield Label("Theme:", classes="setting-label")
                    yield Select(
                        [(name.replace("-", " ").title(), name) for name in THEMES.keys()],
                        value=self._config.theme,
                        id="theme-select",
                        classes="setting-input",
                    )

                # Layout Section
                yield Static("Layout", classes="section-title")

                with Horizontal(classes="setting-row"):
                    yield Label("Sidebar Width:", classes="setting-label")
                    yield Input(
                        str(self._config.layout.sidebar_width),
                        id="sidebar-width",
                        classes="setting-input",
                        type="integer",
                    )
                yield Static("Width in characters (16-60)", classes="setting-hint")

                with Horizontal(classes="setting-row"):
                    yield Label("Detail Panel Width:", classes="setting-label")
                    yield Input(
                        str(self._config.layout.detail_panel_width),
                        id="detail-width",
                        classes="setting-input",
                        type="integer",
                    )
                yield Static("Width in characters (20-80)", classes="setting-hint")

                # Defaults Section
                yield Static("Defaults", classes="section-title")

                with Horizontal(classes="setting-row"):
                    yield Label("Default View:", classes="setting-label")
                    yield Select(
                        [
                            ("My Issues", "my-issues"),
                            ("Triage", "triage"),
                            ("All Issues", "all-issues"),
                        ],
                        value=self._config.defaults.view,
                        id="default-view",
                        classes="setting-input",
                    )

                with Horizontal(classes="setting-row"):
                    yield Label("Sort By:", classes="setting-label")
                    yield Select(
                        [
                            ("Priority", "priority"),
                            ("ID", "identifier"),
                            ("Title", "title"),
                            ("Date Created", "created"),
                            ("Due Date", "due_date"),
                            ("Status", "status"),
                            ("Last Updated", "updated"),
                            ("Assignee", "assignee"),
                        ],
                        value=self._config.defaults.sort_by,
                        id="sort-by",
                        classes="setting-input",
                    )

                with Horizontal(classes="setting-row"):
                    yield Label("Sort Order:", classes="setting-label")
                    yield Select(
                        [
                            ("Ascending", "asc"),
                            ("Descending", "desc"),
                        ],
                        value=self._config.defaults.sort_order,
                        id="sort-order",
                        classes="setting-input",
                    )

                # Editor Section
                yield Static("Editor", classes="section-title")

                with Horizontal(classes="setting-row"):
                    yield Label("Editor Command:", classes="setting-label")
                    yield Input(
                        self._config.editor_command or "",
                        placeholder="vim (uses $EDITOR if empty)",
                        id="editor-command",
                        classes="setting-input",
                    )
                yield Static(
                    "Command to open external editor (e.g., vim, nvim, code)",
                    classes="setting-hint",
                )

                # Cache Section
                yield Static("Cache", classes="section-title")

                with Horizontal(classes="setting-row"):
                    yield Label("Cache TTL:", classes="setting-label")
                    yield Input(
                        str(self._config.cache.ttl_minutes),
                        id="cache-ttl",
                        classes="setting-input",
                        type="integer",
                    )
                yield Static(
                    "Minutes before cached data is considered stale (1-1440)",
                    classes="setting-hint",
                )

                with Horizontal(classes="setting-row"):
                    yield Label("Recent Issues:", classes="setting-label")
                    yield Input(
                        str(self._config.cache.recent_issues_limit),
                        id="recent-issues-limit",
                        classes="setting-input",
                        type="integer",
                    )
                yield Static(
                    "Number of recent issues to show in sidebar (1-25)",
                    classes="setting-hint",
                )

                # Default Filters Section
                yield Static("Default Filters", classes="section-title")
                for key, label in Sidebar.FILTER_DEFINITIONS:
                    yield Checkbox(
                        label,
                        value=key in self._config.defaults.filters,
                        id=f"filter-{key}",
                        classes="filter-checkbox",
                    )

            with Horizontal(classes="button-row"):
                yield Button("Save", variant="success", id="btn-save")
                yield Button("Cancel", variant="error", id="btn-cancel")

    def on_mount(self) -> None:
        """Focus the first input on mount."""
        self.query_one("#theme-select", Select).focus()

    def on_key(self, event: Key) -> None:
        """Handle key events for navigation."""
        if event.key == "right":
            focused = self.focused
            if isinstance(focused, Select) and not focused.expanded:
                focused.expanded = True
                event.stop()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-save":
            self.action_save()
        elif event.button.id == "btn-cancel":
            self.action_cancel()

    def action_save(self) -> None:
        """Save settings and dismiss."""
        try:
            # Get theme
            theme_select = self.query_one("#theme-select", Select)
            if theme_select.value and theme_select.value != Select.BLANK:
                self._config.theme = str(theme_select.value)

            # Get layout settings
            sidebar_width_input = self.query_one("#sidebar-width", Input)
            sidebar_width = int(sidebar_width_input.value or "28")
            self._config.layout.sidebar_width = max(16, min(60, sidebar_width))

            detail_width_input = self.query_one("#detail-width", Input)
            detail_width = int(detail_width_input.value or "40")
            self._config.layout.detail_panel_width = max(20, min(80, detail_width))

            # Get defaults
            view_select = self.query_one("#default-view", Select)
            if view_select.value and view_select.value != Select.BLANK:
                self._config.defaults.view = str(view_select.value)

            sort_by_select = self.query_one("#sort-by", Select)
            if sort_by_select.value and sort_by_select.value != Select.BLANK:
                self._config.defaults.sort_by = str(sort_by_select.value)

            sort_order_select = self.query_one("#sort-order", Select)
            if sort_order_select.value and sort_order_select.value != Select.BLANK:
                self._config.defaults.sort_order = str(sort_order_select.value)

            # Get editor
            editor_input = self.query_one("#editor-command", Input)
            editor_value = editor_input.value.strip()
            self._config.editor_command = editor_value if editor_value else None

            # Get cache TTL
            cache_ttl_input = self.query_one("#cache-ttl", Input)
            cache_ttl = int(cache_ttl_input.value or "30")
            self._config.cache.ttl_minutes = max(1, min(1440, cache_ttl))

            # Get recent issues limit
            recent_limit_input = self.query_one("#recent-issues-limit", Input)
            recent_limit = int(recent_limit_input.value or "5")
            self._config.cache.recent_issues_limit = max(1, min(25, recent_limit))

            # Get default filters
            selected_filters = []
            for key, _ in Sidebar.FILTER_DEFINITIONS:
                checkbox = self.query_one(f"#filter-{key}", Checkbox)
                if checkbox.value:
                    selected_filters.append(key)
            self._config.defaults.filters = selected_filters

            self.dismiss(self._config)

        except ValueError as e:
            self.app.notify(f"Invalid input: {e}", severity="error")

    def action_cancel(self) -> None:
        """Cancel and dismiss without saving."""
        self.dismiss(None)
