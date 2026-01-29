"""Configuration management for Linear TUI."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import platformdirs
import yaml
from textual.theme import Theme


@dataclass
class ThemeColors:
    """Color scheme for theming."""

    background: str = "#1e1e1e"
    foreground: str = "#eeffff"
    accent: str = "#82aaff"
    success: str = "#c3e88d"
    warning: str = "#ffcb6b"
    error: str = "#f07178"
    muted: str = "#546e7a"
    border: str = "#37474f"
    selection: str = "#264f78"
    priority_urgent: str = "#f07178"
    priority_high: str = "#ffcb6b"
    priority_medium: str = "#c3e88d"
    priority_low: str = "#82aaff"
    priority_none: str = "#546e7a"
    status_todo: str = "#546e7a"
    status_in_progress: str = "#82aaff"
    status_in_review: str = "#c792ea"
    status_done: str = "#c3e88d"
    status_canceled: str = "#f07178"

    def to_textual_theme(self, name: str) -> Theme:
        """Convert to a Textual Theme object."""
        return Theme(
            name=name,
            primary=self.accent,
            secondary=self.muted,
            accent=self.accent,
            background=self.background,
            surface=self.background,
            panel=self.border,
            foreground=self.foreground,
            success=self.success,
            warning=self.warning,
            error=self.error,
        )


THEMES = {
    "material-dark": ThemeColors(),
    "gruvbox-dark": ThemeColors(
        background="#282828",
        foreground="#ebdbb2",
        accent="#83a598",
        success="#b8bb26",
        warning="#fabd2f",
        error="#fb4934",
        muted="#928374",
        border="#504945",
        selection="#3c3836",
        priority_urgent="#fb4934",
        priority_high="#fabd2f",
        priority_medium="#b8bb26",
        priority_low="#83a598",
        priority_none="#928374",
        status_todo="#928374",
        status_in_progress="#83a598",
        status_in_review="#d3869b",
        status_done="#b8bb26",
        status_canceled="#fb4934",
    ),
    "linear": ThemeColors(
        background="#1a1a2e",
        foreground="#e4e4ef",
        accent="#5e6ad2",
        success="#4cb782",
        warning="#f2c94c",
        error="#eb5757",
        muted="#6b6f76",
        border="#2a2a3e",
        selection="#2e2e4a",
        priority_urgent="#eb5757",
        priority_high="#f2c94c",
        priority_medium="#4cb782",
        priority_low="#5e6ad2",
        priority_none="#6b6f76",
        status_todo="#6b6f76",
        status_in_progress="#5e6ad2",
        status_in_review="#9b8afb",
        status_done="#4cb782",
        status_canceled="#eb5757",
    ),
    "dracula": ThemeColors(
        background="#282a36",
        foreground="#f8f8f2",
        accent="#bd93f9",
        success="#50fa7b",
        warning="#f1fa8c",
        error="#ff5555",
        muted="#6272a4",
        border="#44475a",
        selection="#44475a",
        priority_urgent="#ff5555",
        priority_high="#ffb86c",
        priority_medium="#50fa7b",
        priority_low="#8be9fd",
        priority_none="#6272a4",
        status_todo="#6272a4",
        status_in_progress="#8be9fd",
        status_in_review="#ff79c6",
        status_done="#50fa7b",
        status_canceled="#ff5555",
    ),
    "nord": ThemeColors(
        background="#2e3440",
        foreground="#eceff4",
        accent="#88c0d0",
        success="#a3be8c",
        warning="#ebcb8b",
        error="#bf616a",
        muted="#4c566a",
        border="#3b4252",
        selection="#434c5e",
        priority_urgent="#bf616a",
        priority_high="#d08770",
        priority_medium="#a3be8c",
        priority_low="#81a1c1",
        priority_none="#4c566a",
        status_todo="#4c566a",
        status_in_progress="#81a1c1",
        status_in_review="#b48ead",
        status_done="#a3be8c",
        status_canceled="#bf616a",
    ),
    "solarized-dark": ThemeColors(
        background="#002b36",
        foreground="#839496",
        accent="#268bd2",
        success="#859900",
        warning="#b58900",
        error="#dc322f",
        muted="#586e75",
        border="#073642",
        selection="#073642",
        priority_urgent="#dc322f",
        priority_high="#cb4b16",
        priority_medium="#859900",
        priority_low="#268bd2",
        priority_none="#586e75",
        status_todo="#586e75",
        status_in_progress="#268bd2",
        status_in_review="#6c71c4",
        status_done="#859900",
        status_canceled="#dc322f",
    ),
    "catppuccin-mocha": ThemeColors(
        background="#1e1e2e",
        foreground="#cdd6f4",
        accent="#89b4fa",
        success="#a6e3a1",
        warning="#f9e2af",
        error="#f38ba8",
        muted="#6c7086",
        border="#313244",
        selection="#45475a",
        priority_urgent="#f38ba8",
        priority_high="#fab387",
        priority_medium="#a6e3a1",
        priority_low="#89dceb",
        priority_none="#6c7086",
        status_todo="#6c7086",
        status_in_progress="#89b4fa",
        status_in_review="#cba6f7",
        status_done="#a6e3a1",
        status_canceled="#f38ba8",
    ),
    "one-dark": ThemeColors(
        background="#282c34",
        foreground="#abb2bf",
        accent="#61afef",
        success="#98c379",
        warning="#e5c07b",
        error="#e06c75",
        muted="#5c6370",
        border="#3e4451",
        selection="#3e4451",
        priority_urgent="#e06c75",
        priority_high="#d19a66",
        priority_medium="#98c379",
        priority_low="#56b6c2",
        priority_none="#5c6370",
        status_todo="#5c6370",
        status_in_progress="#61afef",
        status_in_review="#c678dd",
        status_done="#98c379",
        status_canceled="#e06c75",
    ),
    "tokyo-night": ThemeColors(
        background="#1a1b26",
        foreground="#a9b1d6",
        accent="#7aa2f7",
        success="#9ece6a",
        warning="#e0af68",
        error="#f7768e",
        muted="#565f89",
        border="#292e42",
        selection="#33467c",
        priority_urgent="#f7768e",
        priority_high="#ff9e64",
        priority_medium="#9ece6a",
        priority_low="#7dcfff",
        priority_none="#565f89",
        status_todo="#565f89",
        status_in_progress="#7aa2f7",
        status_in_review="#bb9af7",
        status_done="#9ece6a",
        status_canceled="#f7768e",
    ),
}


@dataclass
class LayoutConfig:
    """Layout configuration."""

    sidebar_width: int = 28
    detail_panel_width: int = 40
    show_detail_panel: bool = True
    show_sidebar: bool = True


@dataclass
class DefaultsConfig:
    """Default view configuration."""

    view: str = "my-issues"
    sort_by: str = "priority"
    sort_order: str = "asc"
    filters: list[str] = field(default_factory=list)


@dataclass
class CacheConfig:
    """Cache configuration."""

    directory: str | None = None
    ttl_minutes: int = 30
    recent_issues_limit: int = 5


@dataclass
class KanbanConfig:
    """Kanban board configuration."""

    # List of state names to show, in order. Empty list = show all.
    columns: list[str] = field(default_factory=list)
    # Whether to hide completed/canceled states by default
    hide_done: bool = False


@dataclass
class SavedFilter:
    """A saved filter preset."""

    name: str
    filter_state: dict


@dataclass
class Config:
    """Main configuration class."""

    api_key: str | None = None
    workspace_id: str | None = None
    theme: str = "material-dark"
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    kanban: KanbanConfig = field(default_factory=KanbanConfig)
    columns: list[str] = field(
        default_factory=lambda: [
            "identifier",
            "title",
            "status",
            "priority",
            "assignee",
        ]
    )
    editor_command: str | None = None
    keybindings: dict[str, str] = field(default_factory=dict)
    saved_filters: list[SavedFilter] = field(default_factory=list)

    def get_theme_colors(self) -> ThemeColors:
        """Get the current theme colors."""
        return THEMES.get(self.theme, THEMES["material-dark"])

    def get_cache_directory(self) -> Path:
        """Get the cache directory path."""
        if self.cache.directory:
            return Path(self.cache.directory)
        return Path(platformdirs.user_cache_dir("linear-term"))

    def get_editor(self) -> str:
        """Get the editor command."""
        if self.editor_command:
            return self.editor_command
        return os.environ.get("EDITOR", "vim")

    def add_saved_filter(self, name: str, filter_state: dict) -> SavedFilter:
        """Add a saved filter preset."""
        self.saved_filters = [f for f in self.saved_filters if f.name != name]
        saved_filter = SavedFilter(name=name, filter_state=filter_state)
        self.saved_filters.append(saved_filter)
        return saved_filter

    def delete_saved_filter(self, name: str) -> bool:
        """Delete a saved filter by name. Returns True if deleted."""
        original_len = len(self.saved_filters)
        self.saved_filters = [f for f in self.saved_filters if f.name != name]
        return len(self.saved_filters) < original_len

    def get_saved_filter(self, name: str) -> SavedFilter | None:
        """Get a saved filter by name."""
        for f in self.saved_filters:
            if f.name == name:
                return f
        return None


def get_config_path() -> Path:
    """Get the configuration file path."""
    return Path(platformdirs.user_config_dir("linear-term")) / "config.yaml"


def load_config() -> Config:
    """Load configuration from file and environment."""
    config = Config()
    config_path = get_config_path()

    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
            config = _parse_config(data)

    if config.api_key is None or config.api_key == "$LINEAR_API_KEY":
        config.api_key = os.environ.get("LINEAR_API_KEY")

    return config


def _parse_config(data: dict[str, Any]) -> Config:
    """Parse configuration dictionary into Config object."""
    config = Config()

    if "api_key" in data:
        config.api_key = data["api_key"]

    if "workspace" in data and "id" in data["workspace"]:
        config.workspace_id = data["workspace"]["id"]

    if "appearance" in data and "theme" in data["appearance"]:
        config.theme = data["appearance"]["theme"]

    if "layout" in data:
        layout_data = data["layout"]
        config.layout = LayoutConfig(
            sidebar_width=layout_data.get("sidebar_width", 20),
            detail_panel_width=layout_data.get("detail_panel_width", 40),
            show_detail_panel=layout_data.get("show_detail_panel", True),
            show_sidebar=layout_data.get("show_sidebar", True),
        )

    if "defaults" in data:
        defaults_data = data["defaults"]
        config.defaults = DefaultsConfig(
            view=defaults_data.get("view", "my-issues"),
            sort_by=defaults_data.get("sort_by", "priority"),
            sort_order=defaults_data.get("sort_order", "asc"),
            filters=defaults_data.get("filters", []),
        )

    if "columns" in data:
        config.columns = data["columns"]

    if "kanban" in data:
        kanban_data = data["kanban"]
        config.kanban = KanbanConfig(
            columns=kanban_data.get("columns", []),
            hide_done=kanban_data.get("hide_done", False),
        )

    if "editor" in data and "command" in data["editor"]:
        config.editor_command = data["editor"]["command"]

    if "cache" in data:
        cache_data = data["cache"]
        config.cache = CacheConfig(
            directory=cache_data.get("directory"),
            ttl_minutes=cache_data.get("ttl_minutes", 30),
            recent_issues_limit=cache_data.get("recent_issues_limit", 5),
        )

    if "keybindings" in data:
        config.keybindings = data["keybindings"]

    if "saved_filters" in data:
        saved_filters = []
        for sf_data in data["saved_filters"]:
            if isinstance(sf_data, dict) and "name" in sf_data and "filter_state" in sf_data:
                saved_filters.append(
                    SavedFilter(name=sf_data["name"], filter_state=sf_data["filter_state"])
                )
        config.saved_filters = saved_filters

    return config


def save_config(config: Config) -> None:
    """Save configuration to file."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "api_key": config.api_key if config.api_key else "$LINEAR_API_KEY",
        "appearance": {"theme": config.theme},
        "layout": {
            "sidebar_width": config.layout.sidebar_width,
            "detail_panel_width": config.layout.detail_panel_width,
            "show_detail_panel": config.layout.show_detail_panel,
            "show_sidebar": config.layout.show_sidebar,
        },
        "defaults": {
            "view": config.defaults.view,
            "sort_by": config.defaults.sort_by,
            "sort_order": config.defaults.sort_order,
            "filters": config.defaults.filters,
        },
        "columns": config.columns,
        "cache": {
            "ttl_minutes": config.cache.ttl_minutes,
            "recent_issues_limit": config.cache.recent_issues_limit,
        },
    }

    if config.workspace_id:
        data["workspace"] = {"id": config.workspace_id}

    if config.editor_command:
        data["editor"] = {"command": config.editor_command}

    if config.cache.directory:
        data["cache"]["directory"] = config.cache.directory

    if config.keybindings:
        data["keybindings"] = config.keybindings

    if config.kanban.columns or config.kanban.hide_done:
        data["kanban"] = {
            "columns": config.kanban.columns,
            "hide_done": config.kanban.hide_done,
        }

    if config.saved_filters:
        data["saved_filters"] = [
            {"name": sf.name, "filter_state": sf.filter_state} for sf in config.saved_filters
        ]

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
