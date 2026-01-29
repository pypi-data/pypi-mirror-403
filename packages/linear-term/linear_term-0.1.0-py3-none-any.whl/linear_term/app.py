"""Main Linear TUI application."""

import subprocess
import webbrowser
from dataclasses import dataclass, field
from datetime import date, timedelta

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Header

from linear_term.api import LinearClient
from linear_term.api.client import AuthenticationError, LinearClientError, RateLimitError
from linear_term.api.models import (
    Comment,
    Cycle,
    Favorite,
    Issue,
    IssueLabel,
    Project,
    Team,
    User,
    WorkflowState,
)
from linear_term.cache import CacheStore
from linear_term.config import THEMES, Config, load_config, save_config
from linear_term.widgets.command_palette import (
    DEFAULT_COMMANDS,
    Command,
    CommandPalette,
    ConfirmDialog,
    QuickSelectDialog,
    SearchDialog,
    TextInputDialog,
)
from linear_term.widgets.detail_panel import DetailPanel
from linear_term.widgets.filter_bar import FilterBar, ParsedFilter
from linear_term.widgets.help_screen import HelpScreen
from linear_term.widgets.issue_form import CommentForm, IssueForm, IssueFormData, QuickCaptureForm
from linear_term.widgets.issue_list import IssueList
from linear_term.widgets.kanban_view import KanbanView
from linear_term.widgets.settings_panel import SettingsPanel
from linear_term.widgets.sidebar import Sidebar
from linear_term.widgets.status_bar import StatusBar


@dataclass
class FilterState:
    """State for toggleable filters."""

    exclude_done: bool = False
    in_progress_only: bool = False
    assignee_me: bool = False
    unassigned: bool = False
    priorities: set[int] = field(default_factory=set)
    due_overdue: bool = False
    due_today: bool = False
    due_this_week: bool = False
    due_this_month: bool = False

    def is_active(self) -> bool:
        """Check if any filter is active."""
        return (
            self.exclude_done
            or self.in_progress_only
            or self.assignee_me
            or self.unassigned
            or len(self.priorities) > 0
            or self.due_overdue
            or self.due_today
            or self.due_this_week
            or self.due_this_month
        )

    def active_count(self) -> int:
        """Count active filters."""
        count = 0
        if self.exclude_done:
            count += 1
        if self.in_progress_only:
            count += 1
        if self.assignee_me:
            count += 1
        if self.unassigned:
            count += 1
        count += len(self.priorities)
        if self.due_overdue:
            count += 1
        if self.due_today:
            count += 1
        if self.due_this_week:
            count += 1
        if self.due_this_month:
            count += 1
        return count


class LinearTUI(App):
    """The main Linear TUI application."""

    TITLE = "Linear TUI"

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 1fr;
    }

    #sidebar {
        display: block;
    }

    #sidebar.hidden {
        display: none;
    }

    #detail-panel {
        display: block;
    }

    #detail-panel.hidden {
        display: none;
    }

    #issue-list {
        width: 1fr;
    }

    #kanban-view {
        width: 1fr;
    }
    """

    BINDINGS = [
        Binding("ctrl+k", "command_palette", "Commands", show=True, priority=True),
        Binding("ctrl+n", "create_issue", "New Issue", show=True, priority=True),
        Binding("ctrl+shift+n", "quick_capture", "Quick Capture", show=False, priority=True),
        Binding("ctrl+r", "refresh", "Refresh", show=True, priority=True),
        Binding("/", "search", "Search", show=True, priority=True),
        Binding("?", "show_help", "Help", show=False),
        Binding("comma", "open_settings", "Settings", show=True),
        Binding("tab", "focus_next_panel", "Next Panel", show=False),
        Binding("shift+tab", "focus_prev_panel", "Prev Panel", show=False),
        Binding("ctrl+b", "toggle_sidebar", "Toggle Sidebar", show=False),
        Binding("ctrl+d", "toggle_detail", "Toggle Detail", show=False),
        Binding("f1", "focus_sidebar", "Focus Sidebar", show=False),
        Binding("f2", "focus_list", "Focus List", show=False),
        Binding("f3", "focus_detail", "Focus Detail", show=False),
        Binding("minus", "shrink_sidebar", "Shrink Sidebar", show=False),
        Binding("equal", "grow_sidebar", "Grow Sidebar", show=False),
        Binding("f", "show_filter", "Filter", show=False),
        Binding("b", "toggle_board_view", "Board View", show=False),
        Binding("B", "configure_board", "Configure Board", show=False),
        Binding("ctrl+e", "edit_in_editor", "External Editor", show=False),
        Binding("ctrl+q", "quit", "Quit", show=False, priority=True),
    ]

    def __init__(self, config: Config | None = None):
        super().__init__()
        self.config = config or load_config()
        self._client: LinearClient | None = None
        self._cache: CacheStore | None = None
        self._viewer: User | None = None
        self._teams: list[Team] = []
        self._current_team: Team | None = None
        self._projects: list[Project] = []
        self._cycles: list[Cycle] = []
        self._users: list[User] = []
        self._labels: list[IssueLabel] = []
        self._workflow_states: list[WorkflowState] = []
        self._issues: list[Issue] = []
        self._favorites: list[Favorite] = []
        self._current_view: str = "my-issues"
        self._current_filter_project: Project | None = None
        self._current_filter_cycle: Cycle | None = None
        self._filter_state: FilterState = FilterState()
        self._parsed_filter: ParsedFilter | None = None
        self._focused_panel: str = "list"
        self._panels = ["sidebar", "list", "detail"]
        self._board_view_active: bool = False

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()
        yield FilterBar(id="filter-bar-input")
        with Horizontal(id="main-container"):
            yield Sidebar(id="sidebar")
            yield IssueList(
                id="issue-list",
                default_sort=self.config.defaults.sort_by,
                default_sort_order=self.config.defaults.sort_order,
            )
            yield KanbanView(kanban_config=self.config.kanban, id="kanban-view")
            yield DetailPanel(id="detail-panel")
        yield StatusBar(id="status-bar")

    async def on_mount(self) -> None:
        """Initialize the application on mount."""
        for theme_name, theme_colors in THEMES.items():
            textual_theme = theme_colors.to_textual_theme(theme_name)
            self.register_theme(textual_theme)

        if self.config.theme in THEMES:
            self.theme = self.config.theme

        if not self.config.api_key:
            self.notify(
                "No API key configured. Set LINEAR_API_KEY or add to config.", severity="error"
            )
            return

        self._cache = CacheStore(
            self.config.get_cache_directory(),
            self.config.cache.ttl_minutes,
        )

        self._client = LinearClient(self.config.api_key)

        self._load_from_cache()
        self._sync_data()

        if not self.config.layout.show_sidebar:
            self.query_one("#sidebar").add_class("hidden")
        if not self.config.layout.show_detail_panel:
            self.query_one("#detail-panel").add_class("hidden")

        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.styles.width = self.config.layout.sidebar_width

        if self.config.defaults.filters:
            self._apply_default_filters()

        self.query_one("#kanban-view", KanbanView).display = False
        issue_list = self.query_one("#issue-list", IssueList)
        issue_list.query_one("#issue-table").focus()

        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.set_view_context("list")

    def _load_from_cache(self) -> None:
        """Load data from cache for instant display."""
        if not self._cache:
            return

        self._teams = self._cache.get_teams()
        if self._teams:
            self._current_team = self._teams[0]

        self._projects = self._cache.get_projects()
        self._users = self._cache.get_users()
        self._labels = self._cache.get_labels()

        if self._current_team:
            self._cycles = self._cache.get_cycles(self._current_team.id)
            self._workflow_states = self._cache.get_workflow_states(self._current_team.id)

        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.update_projects(self._projects)
        sidebar.update_cycles(self._cycles)
        sidebar.update_saved_filters(self.config.saved_filters)

        recent_issues = self._cache.get_recent_issues(limit=self.config.cache.recent_issues_limit)
        sidebar.update_recent_issues(recent_issues)

        self._issues = self._cache.get_issues()
        self._update_issue_list()

    @work(exclusive=True, thread=False)
    async def _sync_data(self) -> None:
        """Sync data from Linear API in background."""
        if not self._client:
            return

        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.set_sync_status(syncing=True)

        try:
            self._viewer = await self._client.get_viewer()
            if self._viewer:
                status_bar.set_workspace(self._viewer.name)

            self._teams = await self._client.get_teams()
            if self._teams and self._cache:
                self._cache.save_teams(self._teams)
                self._current_team = self._teams[0]

            for team in self._teams:
                team_states = await self._client.get_workflow_states(team.id)
                if self._cache:
                    self._cache.save_workflow_states(team_states, team.id)
                if self._current_team and team.id == self._current_team.id:
                    self._workflow_states = team_states

            if self._current_team:
                cycles, _ = await self._client.get_cycles(self._current_team.id)
                self._cycles = cycles
                if self._cache:
                    self._cache.save_cycles(cycles, self._current_team.id)

            projects, _ = await self._client.get_projects()
            self._projects = projects
            if self._cache:
                self._cache.save_projects(projects)

            self._users = await self._client.get_users()
            if self._cache:
                self._cache.save_users(self._users)

            self._labels = await self._client.get_labels()
            if self._cache:
                self._cache.save_labels(self._labels)

            sidebar = self.query_one("#sidebar", Sidebar)
            sidebar.update_projects(self._projects)
            sidebar.update_cycles(self._cycles)
            sidebar.update_saved_filters(self.config.saved_filters)

            await self._refresh_issues()
            await self._refresh_favorites()

            status_bar.set_sync_status(syncing=False)

        except AuthenticationError:
            status_bar.set_sync_status(syncing=False, error=True)
            self.notify("Authentication failed. Check your API key.", severity="error")
        except RateLimitError as e:
            status_bar.set_sync_status(syncing=False, error=True)
            self.notify(f"Rate limited. Retry in {e.retry_after}s", severity="warning")
        except LinearClientError as e:
            status_bar.set_sync_status(syncing=False, error=True)
            self.notify(f"API error: {e}", severity="error")
        except Exception as e:
            status_bar.set_sync_status(syncing=False, error=True)
            self.notify(f"Sync error: {e}", severity="error")

    async def _refresh_issues(self) -> None:
        """Refresh issues based on current view and filters."""
        if not self._client:
            return

        assignee_id = None
        state_type = None
        project_id = None
        cycle_id = None

        if self._current_view == "my-issues" and self._viewer:
            assignee_id = self._viewer.id
        elif self._current_view == "triage":
            state_type = "triage"

        if self._filter_state.assignee_me and self._viewer:
            assignee_id = self._viewer.id

        if self._current_filter_project:
            project_id = self._current_filter_project.id
        if self._current_filter_cycle:
            cycle_id = self._current_filter_cycle.id

        issues, _ = await self._client.get_issues(
            assignee_id=assignee_id,
            state_type=state_type,
            project_id=project_id,
            cycle_id=cycle_id,
            first=100,
        )

        issues = self._apply_client_filters(issues)

        self._issues = issues
        if self._cache:
            self._cache.save_issues(issues)

        self._update_issue_list()

    def _apply_client_filters(self, issues: list[Issue]) -> list[Issue]:
        """Apply client-side filters to issues."""
        fs = self._filter_state
        if not fs.is_active():
            return issues

        filtered = []
        today = date.today()
        week_end = today + timedelta(days=7)
        month_end = today + timedelta(days=30)

        for issue in issues:
            if fs.exclude_done and issue.state:
                if issue.state.type in ("completed", "canceled"):
                    continue

            if fs.in_progress_only and issue.state:
                if issue.state.type != "started":
                    continue

            if fs.unassigned and issue.assignee:
                continue

            if fs.priorities and issue.priority not in fs.priorities:
                continue

            if fs.due_overdue or fs.due_today or fs.due_this_week or fs.due_this_month:
                if not issue.due_date:
                    continue
                due = issue.due_date.date() if hasattr(issue.due_date, "date") else issue.due_date
                passes_due_filter = False
                if fs.due_overdue and due < today:
                    passes_due_filter = True
                if fs.due_today and due == today:
                    passes_due_filter = True
                if fs.due_this_week and today <= due <= week_end:
                    passes_due_filter = True
                if fs.due_this_month and today <= due <= month_end:
                    passes_due_filter = True
                if not passes_due_filter:
                    continue

            filtered.append(issue)

        return filtered

    def _update_issue_list(self) -> None:
        """Update the issue list widget."""
        issue_list = self.query_one("#issue-list", IssueList)
        issue_list.update_issues(self._issues, len(self._issues))

        # Also update board view if active
        if self._board_view_active:
            kanban_view = self.query_one("#kanban-view", KanbanView)
            kanban_view.update_board(self._workflow_states, self._issues)

        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.set_pagination(len(self._issues), len(self._issues))

    def on_sidebar_view_selected(self, event: Sidebar.ViewSelected) -> None:
        """Handle view selection from sidebar."""
        self._current_view = event.view_type
        self._current_filter_project = None
        self._current_filter_cycle = None
        self._sync_issues()

    def on_sidebar_project_selected(self, event: Sidebar.ProjectSelected) -> None:
        """Handle project selection from sidebar."""
        self._current_filter_project = event.project
        self._current_filter_cycle = None
        self._sync_issues()

    def on_sidebar_cycle_selected(self, event: Sidebar.CycleSelected) -> None:
        """Handle cycle selection from sidebar."""
        self._current_filter_cycle = event.cycle
        self._current_filter_project = None
        self._sync_issues()

    def on_sidebar_saved_filter_selected(self, event: Sidebar.SavedFilterSelected) -> None:
        """Handle saved filter selection from sidebar."""
        saved_filter = event.saved_filter
        parsed = ParsedFilter.from_dict(saved_filter.filter_state)
        self._parsed_filter = parsed
        self._apply_parsed_filter(parsed)

        issue_list = self.query_one("#issue-list", IssueList)
        issue_list.set_filter(parsed.to_display())
        self.notify(f"Applied filter: {saved_filter.name}")

    def on_sidebar_recent_issue_selected(self, event: Sidebar.RecentIssueSelected) -> None:
        """Handle recent issue selection from sidebar."""
        self._load_recent_issue(event.issue_id, event.identifier, event.title)

    def on_sidebar_favorite_selected(self, event: Sidebar.FavoriteSelected) -> None:
        """Handle favorite selection from sidebar."""
        self._load_favorite_issue(event.favorite)

    @work(thread=False)
    async def _load_recent_issue(self, issue_id: str, identifier: str, title: str) -> None:
        """Load a recent issue and display it in the detail panel."""
        if not self._client:
            return

        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.set_sync_status(syncing=True)

        try:
            full_issue = await self._client.get_issue(issue_id)
            if full_issue:
                detail_panel = self.query_one("#detail-panel", DetailPanel)
                detail_panel.show_issue(full_issue)
                if detail_panel.has_class("hidden"):
                    detail_panel.remove_class("hidden")

                history = await self._client.get_issue_history(issue_id)
                detail_panel.update_activity(history)

                self._track_issue_view(full_issue)

                self.notify(f"Loaded {identifier}")
            else:
                self.notify(f"Issue {identifier} not found", severity="warning")
            status_bar.set_sync_status(syncing=False)
        except Exception as e:
            status_bar.set_sync_status(syncing=False, error=True)
            self.notify(f"Error loading {identifier}: {e}", severity="error")

    def on_sidebar_filter_toggled(self, event: Sidebar.FilterToggled) -> None:
        """Handle filter toggle from sidebar."""
        key = event.filter_key
        active = event.active
        if key == "not-done":
            self._filter_state.exclude_done = active
        elif key == "in-progress":
            self._filter_state.in_progress_only = active
        elif key == "assignee-me":
            self._filter_state.assignee_me = active
        elif key == "unassigned":
            self._filter_state.unassigned = active
        elif key == "priority-urgent":
            if active:
                self._filter_state.priorities.add(1)
            else:
                self._filter_state.priorities.discard(1)
        elif key == "priority-high":
            if active:
                self._filter_state.priorities.add(2)
            else:
                self._filter_state.priorities.discard(2)
        elif key == "priority-medium":
            if active:
                self._filter_state.priorities.add(3)
            else:
                self._filter_state.priorities.discard(3)
        elif key == "priority-low":
            if active:
                self._filter_state.priorities.add(4)
            else:
                self._filter_state.priorities.discard(4)
        elif key == "due-overdue":
            self._filter_state.due_overdue = active
        elif key == "due-today":
            self._filter_state.due_today = active
        elif key == "due-this-week":
            self._filter_state.due_this_week = active
        elif key == "due-this-month":
            self._filter_state.due_this_month = active
        self._sync_issues()

    @work(exclusive=True, thread=False)
    async def _sync_issues(self) -> None:
        """Sync issues with current filters."""
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.set_sync_status(syncing=True)

        try:
            await self._refresh_issues()
            status_bar.set_sync_status(syncing=False)
        except Exception as e:
            status_bar.set_sync_status(syncing=False, error=True)
            self.notify(f"Error loading issues: {e}", severity="error")

    def on_issue_list_issue_highlighted(self, event: IssueList.IssueHighlighted) -> None:
        """Handle issue highlight (cursor move)."""
        detail_panel = self.query_one("#detail-panel", DetailPanel)
        if event.issue:
            detail_panel.show_issue(event.issue)
            self._load_issue_details(event.issue)
        else:
            detail_panel.clear()

    def on_issue_list_issue_selected(self, event: IssueList.IssueSelected) -> None:
        """Handle issue selection."""
        detail_panel = self.query_one("#detail-panel", DetailPanel)
        detail_panel.show_issue(event.issue)
        self._load_issue_details(event.issue)
        self._track_issue_view(event.issue)

        if detail_panel.has_class("hidden"):
            detail_panel.remove_class("hidden")

    def _track_issue_view(self, issue: Issue) -> None:
        """Track that an issue was viewed in recent history."""
        if not self._cache:
            return
        limit = self.config.cache.recent_issues_limit
        self._cache.add_recent_issue(issue.id, issue.identifier, issue.title, limit=limit)
        recent_issues = self._cache.get_recent_issues(limit=limit)
        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.update_recent_issues(recent_issues)

    @work(thread=False)
    async def _load_issue_details(self, issue: Issue) -> None:
        """Load full issue details including comments and activity."""
        if not self._client:
            return
        detail_panel = self.query_one("#detail-panel", DetailPanel)
        try:
            full_issue = await self._client.get_issue(issue.id)
            if full_issue:
                detail_panel.show_issue(full_issue)
        except Exception:
            pass
        try:
            history = await self._client.get_issue_history(issue.id)
            detail_panel.update_activity(history)
        except Exception:
            pass

    def on_issue_list_action_requested(self, event: IssueList.ActionRequested) -> None:
        """Handle action requests from issue list."""
        self._handle_issue_action(event.action, event.issue)

    def on_issue_list_sort_change_requested(self, event: IssueList.SortChangeRequested) -> None:
        """Handle sort change request from issue list."""
        self._show_sort_picker(event.current_sort, event.sort_ascending)

    def on_issue_list_bulk_action_requested(self, event: IssueList.BulkActionRequested) -> None:
        """Handle bulk action requests from issue list."""
        if not event.issues:
            return
        if event.action == "status":
            self._show_bulk_status_picker(event.issues)
        elif event.action == "assignee":
            self._show_bulk_assignee_picker(event.issues)
        elif event.action == "priority":
            self._show_bulk_priority_picker(event.issues)
        elif event.action == "labels":
            self._show_bulk_labels_picker(event.issues)
        elif event.action == "archive":
            self._confirm_bulk_archive(event.issues)

    def on_issue_list_rename_requested(self, event: IssueList.RenameRequested) -> None:
        """Handle rename request."""
        self._show_rename_dialog(event.issue)

    def on_issue_list_quick_priority_requested(
        self, event: IssueList.QuickPriorityRequested
    ) -> None:
        """Handle quick priority change request."""
        self._apply_quick_priority(event.issues, event.priority)

    def on_issue_list_status_advance_requested(
        self, event: IssueList.StatusAdvanceRequested
    ) -> None:
        """Handle status advance request."""
        self._advance_issue_status(event.issue)

    def on_issue_list_toggle_favorite_requested(
        self, event: IssueList.ToggleFavoriteRequested
    ) -> None:
        """Handle toggle favorite request."""
        self._toggle_favorite(event.issue)

    def on_detail_panel_comment_requested(self, event: DetailPanel.CommentRequested) -> None:
        """Handle comment request from detail panel."""
        self._show_comment_form(event.issue, event.parent_comment)

    def on_detail_panel_edit_requested(self, event: DetailPanel.EditRequested) -> None:
        """Handle edit request from detail panel."""
        self._show_edit_form(event.issue)

    def on_detail_panel_subissue_selected(self, event: DetailPanel.SubissueSelected) -> None:
        """Navigate to view subissue details."""
        self._navigate_to_issue(event.issue)

    def on_detail_panel_parent_selected(self, event: DetailPanel.ParentSelected) -> None:
        """Navigate to parent issue."""
        self._navigate_to_issue(event.issue)

    def _navigate_to_issue(self, issue: Issue) -> None:
        """Navigate to a specific issue, loading full details."""
        detail_panel = self.query_one("#detail-panel", DetailPanel)
        detail_panel.show_issue(issue)
        self._load_issue_details(issue)
        self._track_issue_view(issue)

    @work(thread=False)
    async def _load_favorite_issue(self, favorite: Favorite) -> None:
        """Load a favorite issue and display it in the detail panel."""
        if not self._client:
            return

        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.set_sync_status(syncing=True)

        try:
            full_issue = await self._client.get_issue(favorite.issue_id)
            if full_issue:
                detail_panel = self.query_one("#detail-panel", DetailPanel)
                detail_panel.show_issue(full_issue)
                if detail_panel.has_class("hidden"):
                    detail_panel.remove_class("hidden")

                history = await self._client.get_issue_history(favorite.issue_id)
                detail_panel.update_activity(history)

                self._track_issue_view(full_issue)

                self.notify(f"Loaded {favorite.issue_identifier}")
            else:
                self.notify(
                    f"Issue {favorite.issue_identifier} not found",
                    severity="warning",
                )
            status_bar.set_sync_status(syncing=False)
        except Exception as e:
            status_bar.set_sync_status(syncing=False, error=True)
            self.notify(
                f"Error loading {favorite.issue_identifier}: {e}",
                severity="error",
            )

    async def _refresh_favorites(self) -> None:
        """Refresh favorites from Linear API."""
        if not self._client:
            return

        self._favorites = await self._client.get_favorites()
        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.update_favorites(self._favorites)

        # Update issue list star indicators
        favorite_ids = {f.issue_id for f in self._favorites}
        issue_list = self.query_one("#issue-list", IssueList)
        issue_list.set_favorite_ids(favorite_ids)

    @work(thread=False)
    async def _toggle_favorite(self, issue: Issue) -> None:
        """Toggle favorite status for an issue."""
        if not self._client:
            return

        # Check if already favorited
        existing = None
        for fav in self._favorites:
            if fav.issue_id == issue.id:
                existing = fav
                break

        if existing:
            # Remove favorite
            success = await self._client.remove_favorite(existing.id)
            if success:
                self.notify(f"Removed {issue.identifier} from favorites")
                await self._refresh_favorites()
        else:
            # Add favorite
            favorite_id = await self._client.add_favorite(issue.id)
            if favorite_id:
                self.notify(f"Added {issue.identifier} to favorites")
                await self._refresh_favorites()

    def _handle_issue_action(self, action: str, issue: Issue | None) -> None:
        """Handle an action on an issue."""
        if action == "edit" and issue:
            self._show_edit_form(issue)
        elif action == "status" and issue:
            self._show_status_picker(issue)
        elif action == "assignee" and issue:
            self._show_assignee_picker(issue)
        elif action == "priority" and issue:
            self._show_priority_picker(issue)
        elif action == "labels" and issue:
            self._show_labels_picker(issue)
        elif action == "comment" and issue:
            self._show_comment_form(issue)
        elif action == "copy_url" and issue:
            self._copy_url(issue)
        elif action == "open_browser" and issue:
            self._open_in_browser(issue)
        elif action == "archive" and issue:
            self._confirm_archive(issue)
        elif action == "toggle_favorite" and issue:
            self._toggle_favorite(issue)

    def _show_edit_form(self, issue: Issue) -> None:
        """Show the issue edit form."""
        if issue.team and self._cache:
            states = self._cache.get_workflow_states(issue.team.id)
            if not states:
                states = self._workflow_states
        else:
            states = self._workflow_states
        form = IssueForm(
            teams=self._teams,
            projects=self._projects,
            users=self._users,
            labels=self._labels,
            cycles=self._cycles,
            workflow_states=states,
            issue=issue,
        )
        self.push_screen(form, self._handle_edit_result(issue))

    def _handle_edit_result(self, issue: Issue):
        """Create callback for edit form result."""

        async def callback(result: IssueFormData | None) -> None:
            if result and self._client:
                try:
                    updated = await self._client.update_issue(
                        issue_id=issue.id,
                        title=result.title,
                        description=result.description,
                        priority=result.priority,
                        state_id=result.state_id,
                        assignee_id=result.assignee_id,
                        project_id=result.project_id,
                        cycle_id=result.cycle_id,
                        estimate=result.estimate,
                        due_date=result.due_date,
                    )
                    if updated:
                        self.notify(f"Updated {updated.identifier}")
                        self._sync_issues()
                except Exception as e:
                    self.notify(f"Error updating issue: {e}", severity="error")

        return callback

    def _show_status_picker(self, issue: Issue) -> None:
        """Show status picker dialog."""
        if issue.team and self._cache:
            states = self._cache.get_workflow_states(issue.team.id)
            if not states:
                states = self._workflow_states
        else:
            states = self._workflow_states
        options = [(s.id, s.name) for s in states]
        dialog = QuickSelectDialog("Change Status", options)
        self.push_screen(dialog, self._handle_status_change(issue))

    def _handle_status_change(self, issue: Issue):
        """Create callback for status change."""

        async def callback(state_id: str | None) -> None:
            if state_id and self._client:
                try:
                    updated = await self._client.update_issue(issue.id, state_id=state_id)
                    if updated:
                        state_name = updated.state.name if updated.state else "Unknown"
                        self.notify(f"Status changed to {state_name}")
                        self._sync_issues()
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

        return callback

    def _show_assignee_picker(self, issue: Issue) -> None:
        """Show assignee picker dialog."""
        options = [("", "Unassigned")] + [(u.id, u.name) for u in self._users if u.active]
        dialog = QuickSelectDialog("Change Assignee", options)
        self.push_screen(dialog, self._handle_assignee_change(issue))

    def _handle_assignee_change(self, issue: Issue):
        """Create callback for assignee change."""

        async def callback(assignee_id: str | None) -> None:
            if self._client:
                try:
                    updated = await self._client.update_issue(
                        issue.id, assignee_id=assignee_id if assignee_id else None
                    )
                    if updated:
                        name = updated.assignee.name if updated.assignee else "Unassigned"
                        self.notify(f"Assigned to {name}")
                        self._sync_issues()
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

        return callback

    def _show_priority_picker(self, issue: Issue) -> None:
        """Show priority picker dialog."""
        options = [
            ("0", "No Priority"),
            ("1", "Urgent"),
            ("2", "High"),
            ("3", "Medium"),
            ("4", "Low"),
        ]
        dialog = QuickSelectDialog("Change Priority", options)
        self.push_screen(dialog, self._handle_priority_change(issue))

    def _handle_priority_change(self, issue: Issue):
        """Create callback for priority change."""

        async def callback(priority_str: str | None) -> None:
            if priority_str is not None and self._client:
                try:
                    updated = await self._client.update_issue(issue.id, priority=int(priority_str))
                    if updated:
                        self.notify(f"Priority changed to {updated.priority_label}")
                        self._sync_issues()
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

        return callback

    def _show_labels_picker(self, issue: Issue) -> None:
        """Show labels picker dialog."""
        options = [(lbl.id, lbl.name) for lbl in self._labels]
        dialog = QuickSelectDialog("Add Label", options)
        self.push_screen(dialog, self._handle_label_change(issue))

    def _handle_label_change(self, issue: Issue):
        """Create callback for label change."""

        async def callback(label_id: str | None) -> None:
            if label_id and self._client:
                try:
                    current_labels = [lbl.id for lbl in issue.labels]
                    if label_id not in current_labels:
                        current_labels.append(label_id)
                    updated = await self._client.update_issue(issue.id, label_ids=current_labels)
                    if updated:
                        self.notify("Labels updated")
                        self._sync_issues()
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

        return callback

    # --- Bulk Actions ---

    def _show_bulk_status_picker(self, issues: list[Issue]) -> None:
        """Show status picker for bulk update."""
        states = self._workflow_states
        options = [(s.id, s.name) for s in states]
        dialog = QuickSelectDialog(f"Change Status ({len(issues)} issues)", options)
        self.push_screen(dialog, self._handle_bulk_status_change(issues))

    def _handle_bulk_status_change(self, issues: list[Issue]):
        """Create callback for bulk status change."""

        async def callback(state_id: str | None) -> None:
            if state_id and self._client:
                success_count = 0
                for issue in issues:
                    try:
                        await self._client.update_issue(issue.id, state_id=state_id)
                        success_count += 1
                    except Exception:
                        pass
                self.notify(f"Updated status for {success_count}/{len(issues)} issues")
                self._clear_issue_selection()
                self._sync_issues()

        return callback

    def _show_bulk_assignee_picker(self, issues: list[Issue]) -> None:
        """Show assignee picker for bulk update."""
        options = [("", "Unassigned")] + [(u.id, u.name) for u in self._users if u.active]
        dialog = QuickSelectDialog(f"Change Assignee ({len(issues)} issues)", options)
        self.push_screen(dialog, self._handle_bulk_assignee_change(issues))

    def _handle_bulk_assignee_change(self, issues: list[Issue]):
        """Create callback for bulk assignee change."""

        async def callback(assignee_id: str | None) -> None:
            if self._client:
                success_count = 0
                for issue in issues:
                    try:
                        await self._client.update_issue(
                            issue.id, assignee_id=assignee_id if assignee_id else None
                        )
                        success_count += 1
                    except Exception:
                        pass
                self.notify(f"Updated assignee for {success_count}/{len(issues)} issues")
                self._clear_issue_selection()
                self._sync_issues()

        return callback

    def _show_bulk_priority_picker(self, issues: list[Issue]) -> None:
        """Show priority picker for bulk update."""
        options = [
            ("0", "No Priority"),
            ("1", "Urgent"),
            ("2", "High"),
            ("3", "Medium"),
            ("4", "Low"),
        ]
        dialog = QuickSelectDialog(f"Change Priority ({len(issues)} issues)", options)
        self.push_screen(dialog, self._handle_bulk_priority_change(issues))

    def _handle_bulk_priority_change(self, issues: list[Issue]):
        """Create callback for bulk priority change."""

        async def callback(priority_str: str | None) -> None:
            if priority_str is not None and self._client:
                priority = int(priority_str)
                success_count = 0
                for issue in issues:
                    try:
                        await self._client.update_issue(issue.id, priority=priority)
                        success_count += 1
                    except Exception:
                        pass
                self.notify(f"Updated priority for {success_count}/{len(issues)} issues")
                self._clear_issue_selection()
                self._sync_issues()

        return callback

    def _show_bulk_labels_picker(self, issues: list[Issue]) -> None:
        """Show labels picker for bulk update."""
        options = [(lbl.id, lbl.name) for lbl in self._labels]
        dialog = QuickSelectDialog(f"Add Label ({len(issues)} issues)", options)
        self.push_screen(dialog, self._handle_bulk_label_change(issues))

    def _handle_bulk_label_change(self, issues: list[Issue]):
        """Create callback for bulk label change."""

        async def callback(label_id: str | None) -> None:
            if label_id and self._client:
                success_count = 0
                for issue in issues:
                    try:
                        current_labels = [lbl.id for lbl in issue.labels]
                        if label_id not in current_labels:
                            current_labels.append(label_id)
                        await self._client.update_issue(issue.id, label_ids=current_labels)
                        success_count += 1
                    except Exception:
                        pass
                self.notify(f"Added label to {success_count}/{len(issues)} issues")
                self._clear_issue_selection()
                self._sync_issues()

        return callback

    def _confirm_bulk_archive(self, issues: list[Issue]) -> None:
        """Show confirmation for bulk archive."""
        msg = f"Are you sure you want to archive {len(issues)} issues?"
        dialog = ConfirmDialog("Archive Issues", msg)
        self.push_screen(dialog, self._handle_bulk_archive(issues))

    def _handle_bulk_archive(self, issues: list[Issue]):
        """Create callback for bulk archive confirmation."""

        async def callback(confirmed: bool) -> None:
            if confirmed and self._client:
                success_count = 0
                for issue in issues:
                    try:
                        await self._client.archive_issue(issue.id)
                        success_count += 1
                    except Exception:
                        pass
                self.notify(f"Archived {success_count}/{len(issues)} issues")
                self._clear_issue_selection()
                self._sync_issues()

        return callback

    def _clear_issue_selection(self) -> None:
        """Clear issue list selection."""
        issue_list = self.query_one("#issue-list", IssueList)
        issue_list.clear_selection()

    # --- Quick Actions ---

    def _show_rename_dialog(self, issue: Issue) -> None:
        """Show rename dialog for an issue."""
        dialog = TextInputDialog(
            f"Rename {issue.identifier}",
            placeholder="Enter new title",
            initial_value=issue.title,
        )
        self.push_screen(dialog, self._handle_rename_result(issue))

    def _handle_rename_result(self, issue: Issue):
        """Create callback for rename result."""

        async def callback(new_title: str | None) -> None:
            if new_title and new_title.strip() and self._client:
                try:
                    updated = await self._client.update_issue(issue.id, title=new_title.strip())
                    if updated:
                        self.notify(f"Renamed to: {new_title[:30]}...")
                        self._sync_issues()
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

        return callback

    @work(thread=False)
    async def _apply_quick_priority(self, issues: list[Issue], priority: int) -> None:
        """Apply priority change to issues."""
        if not self._client:
            return

        priority_names = {0: "None", 1: "Urgent", 2: "High", 3: "Medium", 4: "Low"}
        priority_name = priority_names.get(priority, "Unknown")

        success_count = 0
        for issue in issues:
            try:
                await self._client.update_issue(issue.id, priority=priority)
                success_count += 1
            except Exception:
                pass

        if len(issues) == 1:
            self.notify(f"Priority set to {priority_name}")
        else:
            self.notify(f"Set priority to {priority_name} for {success_count}/{len(issues)} issues")

        self._clear_issue_selection()
        self._sync_issues()

    @work(thread=False)
    async def _advance_issue_status(self, issue: Issue) -> None:
        """Advance issue to next workflow state."""
        if not self._client or not issue.state:
            return

        # Get workflow states for the issue's team
        if issue.team and self._cache:
            states = self._cache.get_workflow_states(issue.team.id)
            if not states:
                states = self._workflow_states
        else:
            states = self._workflow_states

        if not states:
            self.notify("No workflow states available", severity="warning")
            return

        # Sort by position
        sorted_states = sorted(states, key=lambda s: s.position)

        # Find current state and get next
        current_idx = -1
        for i, state in enumerate(sorted_states):
            if state.id == issue.state.id:
                current_idx = i
                break

        if current_idx == -1:
            self.notify("Current state not found", severity="warning")
            return

        # Get next state (wrap around or stay at end)
        if current_idx < len(sorted_states) - 1:
            next_state = sorted_states[current_idx + 1]
        else:
            self.notify(f"Already at final state: {issue.state.name}")
            return

        try:
            updated = await self._client.update_issue(issue.id, state_id=next_state.id)
            if updated:
                self.notify(f"Status: {issue.state.name} → {next_state.name}")
                self._sync_issues()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def _show_sort_picker(self, current_sort: str, sort_ascending: bool) -> None:
        """Show sort picker dialog."""
        options = [
            ("priority", "Priority"),
            ("identifier", "ID (e.g., ENG-1511)"),
            ("title", "Title"),
            ("created", "Date Created"),
            ("due_date", "Due Date"),
            ("status", "Status"),
            ("updated", "Last Updated"),
            ("assignee", "Assignee"),
        ]
        dialog = QuickSelectDialog("Sort Issues By", options)
        self.push_screen(dialog, self._handle_sort_change(current_sort, sort_ascending))

    def _handle_sort_change(self, current_sort: str, current_ascending: bool):
        """Create callback for sort change."""

        def callback(sort_by: str | None) -> None:
            if sort_by:
                issue_list = self.query_one("#issue-list", IssueList)
                if sort_by == current_sort:
                    issue_list.set_sort(sort_by, not current_ascending)
                else:
                    issue_list.set_sort(sort_by, True)

        return callback

    def _show_comment_form(self, issue: Issue, parent_comment: Comment | None = None) -> None:
        """Show comment form."""
        if parent_comment:
            author = parent_comment.user.name if parent_comment.user else "Unknown"
            form = CommentForm(issue.identifier, title=f"Reply to {author}")
        else:
            form = CommentForm(issue.identifier)
        self.push_screen(form, self._handle_comment_result(issue, parent_comment))

    def _handle_comment_result(self, issue: Issue, parent_comment: Comment | None = None):
        """Create callback for comment form result."""

        async def callback(comment_text: str | None) -> None:
            if comment_text and self._client:
                try:
                    parent_id = parent_comment.id if parent_comment else None
                    comment = await self._client.create_comment(
                        issue.id, comment_text, parent_id=parent_id
                    )
                    if comment:
                        msg = "Reply added" if parent_comment else "Comment added"
                        self.notify(msg)
                        full_issue = await self._client.get_issue(issue.id)
                        if full_issue:
                            detail_panel = self.query_one("#detail-panel", DetailPanel)
                            detail_panel.show_issue(full_issue)
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

        return callback

    def _copy_url(self, issue: Issue) -> None:
        """Copy issue URL to clipboard."""
        if issue.url:
            try:
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=issue.url.encode(),
                    check=True,
                )
                self.notify(f"Copied {issue.identifier} URL")
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    subprocess.run(
                        ["wl-copy"],
                        input=issue.url.encode(),
                        check=True,
                    )
                    self.notify(f"Copied {issue.identifier} URL")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    self.notify("Could not copy to clipboard", severity="warning")

    def _open_in_browser(self, issue: Issue) -> None:
        """Open issue in browser."""
        if issue.url:
            webbrowser.open(issue.url)
            self.notify(f"Opened {issue.identifier} in browser")

    def action_command_palette(self) -> None:
        """Show command palette."""
        issue_list = self.query_one("#issue-list", IssueList)
        has_issue = issue_list.get_selected_issue() is not None

        commands = list(DEFAULT_COMMANDS)

        commands.append(
            Command(
                "Save Current Filter...",
                "Save the current filter as a preset",
                "",
                "save_filter",
                "Filters",
            )
        )

        if self.config.saved_filters:
            commands.append(
                Command(
                    "Delete Saved Filter...",
                    "Remove a saved filter preset",
                    "",
                    "delete_saved_filter",
                    "Filters",
                )
            )

            for sf in self.config.saved_filters:
                commands.append(
                    Command(
                        f"Apply: {sf.name}",
                        f"Apply saved filter '{sf.name}'",
                        "",
                        f"apply_saved_filter:{sf.name}",
                        "Saved Filters",
                    )
                )

        palette = CommandPalette(commands=commands, issue_context=has_issue)
        self.push_screen(palette, self._handle_command)

    async def _handle_command(self, action: str | None) -> None:
        """Handle command palette selection."""
        if not action:
            return

        issue_list = self.query_one("#issue-list", IssueList)
        issue = issue_list.get_selected_issue()

        if action == "save_filter":
            self._show_save_filter_dialog()
            return
        elif action == "delete_saved_filter":
            self._show_delete_saved_filter_dialog()
            return
        elif action.startswith("apply_saved_filter:"):
            filter_name = action.split(":", 1)[1]
            sf = self.config.get_saved_filter(filter_name)
            if sf:
                parsed = ParsedFilter.from_dict(sf.filter_state)
                self._parsed_filter = parsed
                self._apply_parsed_filter(parsed)
                issue_list.set_filter(parsed.to_display())
                self.notify(f"Applied filter: {sf.name}")
            return

        command_map = {
            "create_issue": self.action_create_issue,
            "quick_capture": self.action_quick_capture,
            "refresh": self.action_refresh,
            "search": self.action_search,
            "goto_my_issues": self.action_goto_my_issues,
            "goto_triage": self.action_goto_triage,
            "toggle_sidebar": self.action_toggle_sidebar,
            "toggle_detail": self.action_toggle_detail,
            "show_help": self.action_show_help,
            "change_sort": self.action_change_sort,
            "open_settings": self.action_open_settings,
        }

        sort_commands = {
            "sort_priority": "priority",
            "sort_identifier": "identifier",
            "sort_title": "title",
            "sort_created": "created",
            "sort_due_date": "due_date",
        }
        if action in sort_commands:
            issue_list = self.query_one("#issue-list", IssueList)
            sort_key = sort_commands[action]
            if issue_list._current_sort == sort_key:
                issue_list.set_sort(sort_key, not issue_list._sort_ascending)
            else:
                issue_list.set_sort(sort_key, True)
            return

        if action in command_map:
            command_map[action]()
        elif issue:
            issue_actions = {
                "change_status": ("status", issue),
                "change_assignee": ("assignee", issue),
                "change_priority": ("priority", issue),
                "change_labels": ("labels", issue),
                "add_comment": ("comment", issue),
                "copy_url": ("copy_url", issue),
                "open_browser": ("open_browser", issue),
                "edit_issue": ("edit", issue),
                "archive_issue": ("archive", issue),
                "delete_issue": ("delete", issue),
                "toggle_favorite": ("toggle_favorite", issue),
            }
            if action in issue_actions:
                act, iss = issue_actions[action]
                if act == "archive":
                    self._confirm_archive(iss)
                elif act == "delete":
                    self._confirm_delete(iss)
                else:
                    self._handle_issue_action(act, iss)

    def _confirm_archive(self, issue: Issue) -> None:
        """Show confirmation for archiving."""
        dialog = ConfirmDialog(
            "Archive Issue", f"Are you sure you want to archive {issue.identifier}?"
        )
        self.push_screen(dialog, self._handle_archive(issue))

    def _handle_archive(self, issue: Issue):
        """Create callback for archive confirmation."""

        async def callback(confirmed: bool) -> None:
            if confirmed and self._client:
                try:
                    success = await self._client.archive_issue(issue.id)
                    if success:
                        self.notify(f"Archived {issue.identifier}")
                        self._sync_issues()
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

        return callback

    def _confirm_delete(self, issue: Issue) -> None:
        """Show confirmation for deleting."""
        msg = f"Are you sure you want to permanently delete {issue.identifier}?"
        dialog = ConfirmDialog("Delete Issue", f"{msg} This cannot be undone.")
        self.push_screen(dialog, self._handle_delete(issue))

    def _handle_delete(self, issue: Issue):
        """Create callback for delete confirmation."""

        async def callback(confirmed: bool) -> None:
            if confirmed and self._client:
                try:
                    success = await self._client.delete_issue(issue.id)
                    if success:
                        self.notify(f"Deleted {issue.identifier}")
                        if self._cache:
                            self._cache.delete_issue(issue.id)
                        self._sync_issues()
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

        return callback

    def action_create_issue(self) -> None:
        """Show create issue form."""
        form = IssueForm(
            teams=self._teams,
            projects=self._projects,
            users=self._users,
            labels=self._labels,
            cycles=self._cycles,
            workflow_states=self._workflow_states,
        )
        self.push_screen(form, self._handle_create_result)

    async def _handle_create_result(self, result: IssueFormData | None) -> None:
        """Handle create form result."""
        if result and self._client and result.team_id:
            try:
                issue = await self._client.create_issue(
                    team_id=result.team_id,
                    title=result.title,
                    description=result.description,
                    priority=result.priority,
                    state_id=result.state_id,
                    assignee_id=result.assignee_id,
                    project_id=result.project_id,
                    cycle_id=result.cycle_id,
                    label_ids=result.label_ids,
                    estimate=result.estimate,
                    due_date=result.due_date,
                )
                if issue:
                    self.notify(f"Created {issue.identifier}")
                    self._sync_issues()
            except Exception as e:
                self.notify(f"Error creating issue: {e}", severity="error")

    def action_quick_capture(self) -> None:
        """Show quick capture form."""
        default_team = self._current_team.id if self._current_team else None
        form = QuickCaptureForm(self._teams, default_team)
        self.push_screen(form, self._handle_quick_capture)

    async def _handle_quick_capture(self, result: tuple[str, str] | None) -> None:
        """Handle quick capture result."""
        if result and self._client:
            title, team_id = result
            try:
                issue = await self._client.create_issue(team_id=team_id, title=title)
                if issue:
                    self.notify(f"Created {issue.identifier}")
                    self._sync_issues()
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")

    def action_refresh(self) -> None:
        """Refresh data from Linear."""
        self._sync_data()

    def action_search(self) -> None:
        """Show search dialog."""
        dialog = SearchDialog()
        self.push_screen(dialog, self._handle_search)

    @work(exclusive=True, thread=False)
    async def _handle_search(self, query: str | None) -> None:
        """Handle search query."""
        if not query or not self._client:
            return

        try:
            import re

            # Check if query looks like an issue ID (e.g., ENG-123)
            id_pattern = re.compile(r"^[A-Za-z]+-\d+$")
            if id_pattern.match(query.strip()):
                # Jump to specific issue
                issues = await self._client.search_issues(query.strip(), first=5)
                for issue in issues:
                    if issue.identifier.lower() == query.strip().lower():
                        # Found exact match - show in detail panel
                        self._issues = [issue]
                        self._update_issue_list()
                        detail_panel = self.query_one("#detail-panel", DetailPanel)
                        detail_panel.show_issue(issue)
                        self._load_issue_activity(issue)
                        self._track_issue_view(issue)
                        self.notify(f"Jumped to {issue.identifier}")
                        return

                # No exact match found
                self.notify(f"Issue {query} not found", severity="warning")
                return

            # Regular search
            issues = await self._client.search_issues(query)
            self._issues = issues
            self._update_issue_list()

            issue_list = self.query_one("#issue-list", IssueList)
            issue_list.set_filter(f'"{query}"')

            if not issues:
                self.notify("No results found")
            else:
                self.notify(f"Found {len(issues)} result{'s' if len(issues) != 1 else ''}")

        except Exception as e:
            self.notify(f"Search error: {e}", severity="error")

    def action_goto_my_issues(self) -> None:
        """Go to my issues view."""
        self._current_view = "my-issues"
        self._current_filter_project = None
        self._current_filter_cycle = None
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.set_view_context("list")
        self._sync_issues()

    def action_goto_triage(self) -> None:
        """Go to triage view."""
        self._current_view = "triage"
        self._current_filter_project = None
        self._current_filter_cycle = None
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.set_view_context("triage")
        self._sync_issues()

    def action_goto_recent(self) -> None:
        """Go to recent issues section in sidebar."""
        sidebar = self.query_one("#sidebar", Sidebar)
        if sidebar.has_class("hidden"):
            sidebar.remove_class("hidden")
        sidebar.focus_recent_section()

    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        sidebar = self.query_one("#sidebar")
        sidebar.toggle_class("hidden")

    def action_toggle_detail(self) -> None:
        """Toggle detail panel visibility."""
        detail = self.query_one("#detail-panel")
        detail.toggle_class("hidden")

    def action_change_sort(self) -> None:
        """Show sort picker dialog."""
        issue_list = self.query_one("#issue-list", IssueList)
        self._show_sort_picker(issue_list._current_sort, issue_list._sort_ascending)

    def action_focus_next_panel(self) -> None:
        """Focus the next panel."""
        current_idx = self._panels.index(self._focused_panel)
        next_idx = (current_idx + 1) % len(self._panels)
        self._focus_panel(self._panels[next_idx])

    def action_focus_prev_panel(self) -> None:
        """Focus the previous panel."""
        current_idx = self._panels.index(self._focused_panel)
        prev_idx = (current_idx - 1) % len(self._panels)
        self._focus_panel(self._panels[prev_idx])

    def action_focus_sidebar(self) -> None:
        """Focus the sidebar panel."""
        self._focus_panel("sidebar")

    def action_focus_list(self) -> None:
        """Focus the issue list panel."""
        self._focus_panel("list")

    def action_focus_detail(self) -> None:
        """Focus the detail panel."""
        self._focus_panel("detail")

    def action_shrink_sidebar(self) -> None:
        """Shrink sidebar width."""
        self._resize_sidebar(-4)

    def action_grow_sidebar(self) -> None:
        """Grow sidebar width."""
        self._resize_sidebar(4)

    def _resize_sidebar(self, delta: int) -> None:
        """Resize the sidebar by delta units."""
        new_width = max(16, min(60, self.config.layout.sidebar_width + delta))
        self.config.layout.sidebar_width = new_width
        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.styles.width = new_width
        save_config(self.config)
        self.notify(f"Sidebar width: {new_width}", timeout=1)

    def _focus_panel(self, panel: str) -> None:
        """Focus a specific panel."""
        self._focused_panel = panel
        status_bar = self.query_one("#status-bar", StatusBar)

        if panel == "sidebar":
            sidebar = self.query_one("#sidebar", Sidebar)
            if not sidebar.has_class("hidden"):
                tree = sidebar.query_one("#nav-tree")
                tree.focus()
            status_bar.set_view_context("list")
        elif panel == "list":
            issue_list = self.query_one("#issue-list", IssueList)
            table = issue_list.query_one("#issue-table")
            table.focus()
            if self._current_view == "triage":
                status_bar.set_view_context("triage")
            else:
                status_bar.set_view_context("list")
        elif panel == "detail":
            detail = self.query_one("#detail-panel", DetailPanel)
            if not detail.has_class("hidden"):
                tabs = detail.query_one("#detail-tabs")
                tabs.focus()
            status_bar.set_view_context("detail")

    def action_show_help(self) -> None:
        """Show help screen."""
        self.push_screen(HelpScreen())

    def action_open_settings(self) -> None:
        """Open settings panel."""
        panel = SettingsPanel(self.config)
        self.push_screen(panel, self._handle_settings_result)

    def action_show_filter(self) -> None:
        """Show the filter bar."""
        filter_bar = self.query_one("#filter-bar-input", FilterBar)
        current_query = ""
        if self._parsed_filter:
            current_query = self._parsed_filter.to_display()
        filter_bar.show(current_query)

    def _show_save_filter_dialog(self) -> None:
        """Show dialog to save current filter."""
        if not self._parsed_filter or self._parsed_filter.is_empty():
            self.notify("No active filter to save", severity="warning")
            return

        dialog = TextInputDialog(
            title="Save Current Filter",
            placeholder="Enter a name for this filter...",
            hint="Press Enter to save, Escape to cancel",
        )
        self.push_screen(dialog, self._handle_save_filter_result)

    def _handle_save_filter_result(self, name: str | None) -> None:
        """Handle save filter dialog result."""
        if not name or not name.strip():
            return

        if not self._parsed_filter:
            return

        name = name.strip()
        filter_state = self._parsed_filter.to_dict()
        self.config.add_saved_filter(name, filter_state)
        save_config(self.config)

        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.update_saved_filters(self.config.saved_filters)

        self.notify(f"Saved filter: {name}")

    def _show_delete_saved_filter_dialog(self) -> None:
        """Show dialog to delete a saved filter."""
        if not self.config.saved_filters:
            self.notify("No saved filters to delete", severity="warning")
            return

        options = [(sf.name, sf.name) for sf in self.config.saved_filters]
        dialog = QuickSelectDialog("Delete Saved Filter", options)
        self.push_screen(dialog, self._handle_delete_saved_filter_result)

    def _handle_delete_saved_filter_result(self, name: str | None) -> None:
        """Handle delete saved filter dialog result."""
        if not name:
            return

        if self.config.delete_saved_filter(name):
            save_config(self.config)

            sidebar = self.query_one("#sidebar", Sidebar)
            sidebar.update_saved_filters(self.config.saved_filters)

            self.notify(f"Deleted filter: {name}")

    def action_toggle_board_view(self) -> None:
        """Toggle between list and board view."""
        self._board_view_active = not self._board_view_active

        issue_list = self.query_one("#issue-list", IssueList)
        kanban_view = self.query_one("#kanban-view", KanbanView)
        sidebar = self.query_one("#sidebar")
        detail_panel = self.query_one("#detail-panel")
        status_bar = self.query_one("#status-bar", StatusBar)

        if self._board_view_active:
            issue_list.display = False
            sidebar.add_class("hidden")
            detail_panel.add_class("hidden")
            kanban_view.display = True
            kanban_view.update_board(self._workflow_states, self._issues)
            kanban_view.focus()
            status_bar.set_view_context("board")
            self.notify("Board view")
        else:
            kanban_view.display = False
            issue_list.display = True
            sidebar.remove_class("hidden")
            detail_panel.remove_class("hidden")
            issue_list.focus()
            status_bar.set_view_context("list")
            self.notify("List view")

    async def _load_issue_activity(self, issue: Issue) -> None:
        """Load activity history for an issue."""
        if not self._client:
            return
        try:
            history = await self._client.get_issue_history(issue.id)
            detail_panel = self.query_one("#detail-panel", DetailPanel)
            detail_panel.update_activity(history)
        except Exception:
            pass

    def on_kanban_view_issue_selected(self, event: KanbanView.IssueSelected) -> None:
        """Handle issue selection from Kanban view."""
        detail_panel = self.query_one("#detail-panel", DetailPanel)
        detail_panel.remove_class("hidden")
        detail_panel.show_issue(event.issue)
        self._load_issue_activity(event.issue)
        detail_panel.focus()

    def action_configure_board(self) -> None:
        """Configure kanban board columns."""
        if not self._board_view_active:
            self.notify("Enter board view first (press 'b')", severity="warning")
            return

        kanban_view = self.query_one("#kanban-view", KanbanView)
        current_columns = kanban_view.get_visible_columns()
        current_value = ", ".join(current_columns)

        # Get all available column names from issues
        available = set()
        for issue in self._issues:
            if issue.state:
                available.add(issue.state.name)
        available_list = sorted(available)

        hint = f"Available: {', '.join(available_list)}\n\nEnter to submit, Escape to cancel"

        dialog = TextInputDialog(
            title="Configure Board Columns",
            placeholder="e.g., Backlog, In Progress, In Review, Done",
            initial_value=current_value,
            hint=hint,
        )
        self.push_screen(dialog, self._handle_board_config)

    def _handle_board_config(self, result: str | None) -> None:
        """Handle board configuration result."""
        if result is None:
            return

        # Parse comma-separated column names
        columns = [c.strip() for c in result.split(",") if c.strip()]

        # Update config
        self.config.kanban.columns = columns
        save_config(self.config)

        # Update kanban view
        kanban_view = self.query_one("#kanban-view", KanbanView)
        kanban_view.set_config(self.config.kanban)
        kanban_view.update_board(self._workflow_states, self._issues)

        self.notify(f"Board configured with {len(columns)} columns")

    def action_edit_in_editor(self) -> None:
        """Edit current issue description in external editor."""
        issue_list = self.query_one("#issue-list", IssueList)
        issue = issue_list.get_selected_issue()
        if not issue:
            self.notify("No issue selected", severity="warning")
            return

        self._open_external_editor(issue)

    @work(thread=True, exclusive=True)
    async def _open_external_editor(self, issue: Issue) -> None:
        """Open external editor for issue description."""
        from linear_term.utils.editor import edit_description_with_template

        current_desc = issue.description or ""
        edited = edit_description_with_template(current_desc, issue.identifier)

        if edited is None:
            self.notify("Edit cancelled")
            return

        if edited == current_desc:
            self.notify("No changes made")
            return

        # Update the issue
        if self._client:
            try:
                updated = await self._client.update_issue(issue.id, description=edited)
                if updated:
                    self.notify(f"Updated description for {issue.identifier}")
                    self._sync_issues()
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")

    def on_filter_bar_filter_applied(self, event: FilterBar.FilterApplied) -> None:
        """Handle filter applied from filter bar."""
        self._parsed_filter = event.parsed
        self._apply_parsed_filter(event.parsed)

        # Update the issue list filter display
        issue_list = self.query_one("#issue-list", IssueList)
        issue_list.set_filter(event.raw_query)

    def on_filter_bar_filter_cleared(self, event: FilterBar.FilterCleared) -> None:
        """Handle filter cleared."""
        self._parsed_filter = None
        self._sync_issues()

        issue_list = self.query_one("#issue-list", IssueList)
        issue_list.set_filter("")

    def _apply_parsed_filter(self, parsed: ParsedFilter) -> None:
        """Apply parsed filter to issue list."""
        # Reset filter state
        self._filter_state = FilterState()

        # Apply parsed filter to filter state
        if parsed.is_unassigned:
            self._filter_state.unassigned = True

        if parsed.priority:
            pri_map = {"urgent": 1, "high": 2, "medium": 3, "low": 4, "none": 0}
            pri_val = pri_map.get(parsed.priority)
            if pri_val is not None:
                self._filter_state.priorities.add(pri_val)

        if parsed.due:
            if parsed.due == "overdue":
                self._filter_state.due_overdue = True
            elif parsed.due == "today":
                self._filter_state.due_today = True
            elif parsed.due == "week":
                self._filter_state.due_this_week = True
            elif parsed.due == "month":
                self._filter_state.due_this_month = True

        if parsed.assignee == "me":
            self._filter_state.assignee_me = True

        if parsed.status:
            status_lower = parsed.status.lower()
            if status_lower in ("started", "in_progress", "inprogress"):
                self._filter_state.in_progress_only = True
            elif status_lower in ("done", "completed", "closed"):
                pass  # Could add completed filter
            else:
                self._filter_state.exclude_done = True

        # Store additional filter info for client-side filtering
        self._sync_issues_with_parsed_filter(parsed)

    @work(exclusive=True, thread=False)
    async def _sync_issues_with_parsed_filter(self, parsed: ParsedFilter) -> None:
        """Sync issues with parsed filter applied."""
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.set_sync_status(syncing=True)

        try:
            await self._refresh_issues()

            # Apply additional client-side filtering
            if parsed.text or parsed.project or parsed.label or parsed.exclude_labels:
                filtered = []
                for issue in self._issues:
                    # Text search
                    if parsed.text:
                        text_lower = parsed.text.lower()
                        if (
                            text_lower not in issue.title.lower()
                            and text_lower not in (issue.description or "").lower()
                            and text_lower not in issue.identifier.lower()
                        ):
                            continue

                    # Project filter
                    if parsed.project:
                        proj_name = issue.project.name.lower() if issue.project else ""
                        if not issue.project or parsed.project.lower() not in proj_name:
                            continue

                    # Label filter
                    if parsed.label:
                        label_names = [lbl.name.lower() for lbl in issue.labels]
                        if parsed.label.lower() not in label_names:
                            continue

                    # Exclude labels
                    if parsed.exclude_labels:
                        label_names = [lbl.name.lower() for lbl in issue.labels]
                        skip = False
                        for excl in parsed.exclude_labels:
                            if excl.lower() in label_names:
                                skip = True
                                break
                        if skip:
                            continue

                    filtered.append(issue)

                self._issues = filtered
                self._update_issue_list()

            status_bar.set_sync_status(syncing=False)
        except Exception as e:
            status_bar.set_sync_status(syncing=False, error=True)
            self.notify(f"Error applying filter: {e}", severity="error")

    async def _handle_settings_result(self, result: Config | None) -> None:
        """Handle settings panel result."""
        if result is None:
            return

        theme_changed = result.theme != self.config.theme
        filters_changed = result.defaults.filters != self.config.defaults.filters

        self.config = result
        save_config(self.config)

        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.styles.width = self.config.layout.sidebar_width

        if theme_changed and self.config.theme in THEMES:
            self.theme = self.config.theme

        if filters_changed:
            self._filter_state = FilterState()
            self._apply_default_filters()
            self._sync_issues()

        self.notify("Settings saved", timeout=2)

    def _apply_default_filters(self) -> None:
        """Apply default filters from config."""
        sidebar = self.query_one("#sidebar", Sidebar)
        for filter_key in self.config.defaults.filters:
            if filter_key == "not-done":
                self._filter_state.exclude_done = True
            elif filter_key == "in-progress":
                self._filter_state.in_progress_only = True
            elif filter_key == "assignee-me":
                self._filter_state.assignee_me = True
            elif filter_key == "unassigned":
                self._filter_state.unassigned = True
            elif filter_key == "priority-urgent":
                self._filter_state.priorities.add(1)
            elif filter_key == "priority-high":
                self._filter_state.priorities.add(2)
            elif filter_key == "priority-medium":
                self._filter_state.priorities.add(3)
            elif filter_key == "priority-low":
                self._filter_state.priorities.add(4)
            elif filter_key == "due-overdue":
                self._filter_state.due_overdue = True
            elif filter_key == "due-today":
                self._filter_state.due_today = True
            elif filter_key == "due-this-week":
                self._filter_state.due_this_week = True
            elif filter_key == "due-this-month":
                self._filter_state.due_this_month = True
        sidebar.set_active_filters(self.config.defaults.filters)


def main() -> None:
    """Main entry point."""
    config = load_config()
    app = LinearTUI(config)
    app.run()


if __name__ == "__main__":
    main()
