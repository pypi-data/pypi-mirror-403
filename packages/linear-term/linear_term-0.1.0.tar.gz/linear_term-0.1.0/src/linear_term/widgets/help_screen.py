"""Help screen showing keyboard shortcuts."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static

HELP_TEXT = """
# Linear TUI Keyboard Shortcuts

## Global
  Ctrl-K        Command palette
  Ctrl-N        Create new issue
  Ctrl-Shift-N  Quick capture issue
  Ctrl-R        Refresh data
  /             Search issues
  ?             Show this help
  Tab           Cycle panel focus forward
  Shift-Tab     Cycle panel focus backward
  Ctrl-Q        Quit

## Navigation
  [             Previous page
  ]             Next page

## Issue Actions (when issue selected)
  Enter         Open issue detail
  e             Edit issue
  s             Change status
  a             Change assignee
  p             Change priority
  l             Add/remove labels
  c             Add comment
  y             Copy issue URL
  o             Open in browser
  r             Rename issue
  x             Advance to next status
  *             Toggle favorite
  Ctrl-A        Archive issue
  Ctrl-E        Edit in external editor

## Quick Priority (in issue list)
  1             Urgent
  2             High
  3             Medium
  4             Low
  0             No priority

## Bulk Selection
  Space         Toggle selection
  v             Enter select mode
  V             Select all
  Escape        Clear selection

## Board View (press b to toggle)
  b             Toggle board/list view
  B             Configure board columns
  h / ←         Previous column
  l / →         Next column
  j / ↓         Next card
  k / ↑         Previous card
  Enter         Open card

## Triage Mode
  a             Accept issue
  d             Decline issue
  s             Snooze
  m             Assign to me
  t             Toggle quick mode
  j / k         Next/prev issue
  1 / 2 / 3     Snooze tomorrow/week/month

## Detail Panel
  h / ←         Previous tab
  l / →         Next tab
  j / ↓         Focus content
  k / ↑         Focus tabs
  c             Add comment
  e             Edit issue
  p             Go to parent issue

## Panel Control
  Ctrl-B        Toggle sidebar
  Ctrl-D        Toggle detail panel
  F1            Focus sidebar
  F2            Focus issue list
  F3            Focus detail panel
  -             Shrink sidebar
  = / +         Grow sidebar
  ,             Open settings
  f             Show filter bar
  S             Change sort order

## Forms
  Ctrl-Enter    Submit form
  Escape        Cancel/close

## Context-Sensitive Keys
  Some keys change meaning by panel:
  p: Priority (list) / Parent (detail)
  l: Labels (list) / Next tab (detail)

Press any key to close this help.
"""


class HelpScreen(ModalScreen[None]):
    """Help screen showing keyboard shortcuts."""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }

    HelpScreen > Container {
        width: 60;
        height: 80%;
        background: $surface;
        border: solid $accent;
        padding: 1 2;
    }

    HelpScreen .help-title {
        text-style: bold;
        text-align: center;
        color: $accent;
        padding-bottom: 1;
    }

    HelpScreen VerticalScroll {
        height: 1fr;
    }

    HelpScreen .help-content {
        color: $text;
    }

    HelpScreen .hint {
        color: $text-muted;
        text-align: center;
        padding-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=False),
        Binding("any", "dismiss", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        with Container():
            yield Static("Help", classes="help-title")
            with VerticalScroll():
                yield Static(HELP_TEXT.strip(), classes="help-content")
            yield Static("Press Escape to close", classes="hint")

    def on_key(self, event) -> None:
        """Dismiss on any key press."""
        self.dismiss(None)

    def action_dismiss(self) -> None:
        """Dismiss the help screen."""
        self.dismiss(None)
