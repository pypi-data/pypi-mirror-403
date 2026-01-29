"""Sidebar widget for navigation."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widgets import Static, Tree
from textual.widgets.tree import TreeNode

from linear_term.api.models import Cycle, Favorite, Project
from linear_term.config import SavedFilter


class Sidebar(VerticalScroll):
    """Sidebar for navigation through projects, cycles, and views."""

    DEFAULT_CSS = """
    Sidebar {
        width: 28;
        background: $surface;
        border-right: solid $primary-darken-2;
        padding: 0 1;
    }

    Sidebar .sidebar-header {
        text-style: bold;
        color: $text-muted;
        padding: 1 0 0 0;
    }

    Sidebar Tree {
        padding: 0;
        background: transparent;
    }

    Sidebar Tree > .tree--guides {
        color: $text-muted;
    }

    Sidebar Tree:focus > .tree--cursor {
        background: $accent;
        color: $text;
    }
    """

    class ViewSelected(Message):
        """Message when a view is selected."""

        def __init__(self, view_type: str, view_id: str | None = None) -> None:
            self.view_type = view_type
            self.view_id = view_id
            super().__init__()

    class ProjectSelected(Message):
        """Message when a project is selected."""

        def __init__(self, project: Project) -> None:
            self.project = project
            super().__init__()

    class CycleSelected(Message):
        """Message when a cycle is selected."""

        def __init__(self, cycle: Cycle) -> None:
            self.cycle = cycle
            super().__init__()

    class FilterToggled(Message):
        """Message when a filter is toggled."""

        def __init__(self, filter_key: str, active: bool) -> None:
            self.filter_key = filter_key
            self.active = active
            super().__init__()

    class RecentIssueSelected(Message):
        """Message when a recent issue is selected."""

        def __init__(self, issue_id: str, identifier: str, title: str) -> None:
            self.issue_id = issue_id
            self.identifier = identifier
            self.title = title
            super().__init__()

    class FavoriteSelected(Message):
        """Message when a favorite is selected."""

        def __init__(self, favorite: Favorite) -> None:
            self.favorite = favorite
            super().__init__()

    class SavedFilterSelected(Message):
        """Message when a saved filter is selected."""

        def __init__(self, saved_filter: SavedFilter) -> None:
            self.saved_filter = saved_filter
            super().__init__()

    FILTER_DEFINITIONS = [
        ("not-done", "Not Done"),
        ("in-progress", "In Progress Only"),
        ("assignee-me", "Assigned to Me"),
        ("unassigned", "Unassigned"),
        ("priority-urgent", "Urgent Priority"),
        ("priority-high", "High Priority"),
        ("priority-medium", "Medium Priority"),
        ("priority-low", "Low Priority"),
        ("due-overdue", "Overdue"),
        ("due-today", "Due Today"),
        ("due-this-week", "Due This Week"),
        ("due-this-month", "Due This Month"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._projects: list[Project] = []
        self._cycles: list[Cycle] = []
        self._favorites: list[Favorite] = []
        self._saved_filters: list[SavedFilter] = []
        self._project_nodes: dict[str, TreeNode[str]] = {}
        self._cycle_nodes: dict[str, TreeNode[str]] = {}
        self._filter_nodes: dict[str, TreeNode[str]] = {}
        self._view_nodes: dict[str, TreeNode[str]] = {}
        self._recent_nodes: dict[str, TreeNode[str]] = {}
        self._favorite_nodes: dict[str, TreeNode[str]] = {}
        self._saved_filter_nodes: dict[str, TreeNode[str]] = {}
        self._active_filters: set[str] = set()
        self._view_counts: dict[str, int] = {}
        self._recent_issues: list[tuple[str, str, str]] = []

    def compose(self) -> ComposeResult:
        """Compose the sidebar content."""
        yield Static("Views", classes="sidebar-header")
        tree = Tree[str]("", id="nav-tree")
        tree.show_root = False

        # Favorites section at the top
        tree.root.add("★ Favorites", expand=True, data="section:favorites")

        views = tree.root.add("Quick Filters", expand=True)
        self._view_nodes["my-issues"] = views.add_leaf("My Issues", data="view:my-issues")
        self._view_nodes["created-by-me"] = views.add_leaf(
            "Created by Me", data="view:created-by-me"
        )
        self._view_nodes["all-issues"] = views.add_leaf("All Issues", data="view:all-issues")
        self._view_nodes["triage"] = views.add_leaf("Triage", data="view:triage")

        filters_node = tree.root.add("Filters", expand=True, data="section:filters")
        for filter_key, filter_label in self.FILTER_DEFINITIONS:
            checkbox = "☐"
            label = f"{checkbox} {filter_label}"
            node = filters_node.add_leaf(label, data=f"filter:{filter_key}")
            self._filter_nodes[filter_key] = node

        tree.root.add("Recent", expand=True, data="section:recent")
        tree.root.add("Projects", expand=True, data="section:projects")
        tree.root.add("Cycles", expand=True, data="section:cycles")

        yield tree

    def on_tree_node_selected(self, event: Tree.NodeSelected[str]) -> None:
        """Handle tree node selection."""
        data = event.node.data
        if not data:
            return

        if data.startswith("view:"):
            view_type = data.split(":", 1)[1]
            self.post_message(self.ViewSelected(view_type))
        elif data.startswith("filter:"):
            filter_key = data.split(":", 1)[1]
            self._toggle_filter(filter_key, event.node)
        elif data.startswith("project:"):
            project_id = data.split(":", 1)[1]
            for project in self._projects:
                if project.id == project_id:
                    self.post_message(self.ProjectSelected(project))
                    break
        elif data.startswith("cycle:"):
            cycle_id = data.split(":", 1)[1]
            for cycle in self._cycles:
                if cycle.id == cycle_id:
                    self.post_message(self.CycleSelected(cycle))
                    break
        elif data.startswith("recent:"):
            issue_id = data.split(":", 1)[1]
            for rid, identifier, title in self._recent_issues:
                if rid == issue_id:
                    self.post_message(self.RecentIssueSelected(rid, identifier, title))
                    break
        elif data.startswith("favorite:"):
            favorite_id = data.split(":", 1)[1]
            for favorite in self._favorites:
                if favorite.id == favorite_id:
                    self.post_message(self.FavoriteSelected(favorite))
                    break
        elif data.startswith("saved-filter:"):
            filter_name = data.split(":", 1)[1]
            for sf in self._saved_filters:
                if sf.name == filter_name:
                    self.post_message(self.SavedFilterSelected(sf))
                    break

    def _toggle_filter(self, filter_key: str, node: TreeNode[str]) -> None:
        """Toggle a filter and update its visual state."""
        is_active = filter_key in self._active_filters
        if is_active:
            self._active_filters.discard(filter_key)
        else:
            self._active_filters.add(filter_key)
        new_active = not is_active
        for key, label in self.FILTER_DEFINITIONS:
            if key == filter_key:
                checkbox = "☑" if new_active else "☐"
                node.set_label(f"{checkbox} {label}")
                break
        self.post_message(self.FilterToggled(filter_key, new_active))

    def update_projects(self, projects: list[Project]) -> None:
        """Update the projects in the sidebar."""
        self._projects = projects
        tree = self.query_one("#nav-tree", Tree)

        projects_node = None
        for node in tree.root.children:
            if node.data == "section:projects":
                projects_node = node
                break

        if projects_node:
            projects_node.remove_children()
            self._project_nodes.clear()
            for project in sorted(projects, key=lambda p: p.name):
                label = f"{project.name} ({project.issue_count})"
                node = projects_node.add_leaf(label, data=f"project:{project.id}")
                self._project_nodes[project.id] = node

    def update_cycles(self, cycles: list[Cycle]) -> None:
        """Update the cycles in the sidebar."""
        self._cycles = cycles
        tree = self.query_one("#nav-tree", Tree)

        cycles_node = None
        for node in tree.root.children:
            if node.data == "section:cycles":
                cycles_node = node
                break

        if cycles_node:
            cycles_node.remove_children()
            self._cycle_nodes.clear()

            active_cycles = [c for c in cycles if c.is_active]
            upcoming_cycles = [
                c
                for c in cycles
                if not c.is_active and c.starts_at and c.ends_at and c.starts_at > c.ends_at
            ]
            past_cycles = [c for c in cycles if not c.is_active and c not in upcoming_cycles]

            if active_cycles:
                for cycle in active_cycles:
                    label = f"● {cycle.display_name}"
                    node = cycles_node.add_leaf(label, data=f"cycle:{cycle.id}")
                    self._cycle_nodes[cycle.id] = node

            for cycle in sorted(
                past_cycles + upcoming_cycles,
                key=lambda c: c.number,
                reverse=True,
            )[:5]:
                label = f"○ {cycle.display_name}"
                node = cycles_node.add_leaf(label, data=f"cycle:{cycle.id}")
                self._cycle_nodes[cycle.id] = node

    def update_recent_issues(self, recent_issues: list[tuple[str, str, str]]) -> None:
        """Update the recent issues in the sidebar."""
        self._recent_issues = recent_issues
        tree = self.query_one("#nav-tree", Tree)

        recent_node = None
        for node in tree.root.children:
            if node.data == "section:recent":
                recent_node = node
                break

        if recent_node:
            recent_node.remove_children()
            self._recent_nodes.clear()

            if not recent_issues:
                recent_node.set_label("Recent")
            else:
                recent_node.set_label(f"Recent ({len(recent_issues)})")

            for issue_id, identifier, title in recent_issues:
                max_title_len = 15
                truncated_title = (
                    title[:max_title_len] + "..." if len(title) > max_title_len else title
                )
                label = f"{identifier} {truncated_title}"
                node = recent_node.add_leaf(label, data=f"recent:{issue_id}")
                self._recent_nodes[issue_id] = node

    def focus_recent_section(self) -> None:
        """Focus and expand the Recent section in the tree."""
        tree = self.query_one("#nav-tree", Tree)
        for node in tree.root.children:
            if node.data == "section:recent":
                node.expand()
                tree.select_node(node)
                tree.focus()
                break

    def update_favorites(self, favorites: list[Favorite]) -> None:
        """Update the favorites in the sidebar."""
        self._favorites = favorites
        tree = self.query_one("#nav-tree", Tree)

        favorites_node = None
        for node in tree.root.children:
            if node.data == "section:favorites":
                favorites_node = node
                break

        if favorites_node:
            favorites_node.remove_children()
            self._favorite_nodes.clear()
            for favorite in favorites:
                # Truncate title to fit sidebar
                title = favorite.issue_title
                if len(title) > 18:
                    title = title[:17] + "…"
                label = f"{favorite.issue_identifier} {title}"
                node = favorites_node.add_leaf(label, data=f"favorite:{favorite.id}")
                self._favorite_nodes[favorite.id] = node

    def set_active_filters(self, filters: list[str]) -> None:
        """Set active filters and update visual state."""
        self._active_filters = set(filters)
        for filter_key, filter_label in self.FILTER_DEFINITIONS:
            if filter_key in self._filter_nodes:
                node = self._filter_nodes[filter_key]
                checkbox = "☑" if filter_key in self._active_filters else "☐"
                node.set_label(f"{checkbox} {filter_label}")

    def update_view_counts(self, counts: dict[str, int]) -> None:
        """Update issue counts for views."""
        self._view_counts = counts

        view_labels = {
            "my-issues": "My Issues",
            "created-by-me": "Created by Me",
            "all-issues": "All Issues",
            "triage": "Triage",
        }

        for view_key, node in self._view_nodes.items():
            base_label = view_labels.get(view_key, view_key)
            count = counts.get(view_key)
            if count is not None and count > 0:
                node.set_label(f"{base_label} ({count})")
            else:
                node.set_label(base_label)

    def highlight_updated_view(self, view_key: str) -> None:
        """Mark a view as having updates (visual indicator)."""
        if view_key in self._view_nodes:
            node = self._view_nodes[view_key]
            current_label = str(node.label)
            if not current_label.startswith("●"):
                node.set_label(f"● {current_label}")

    def clear_view_highlight(self, view_key: str) -> None:
        """Clear the update indicator from a view."""
        if view_key in self._view_nodes:
            node = self._view_nodes[view_key]
            current_label = str(node.label)
            if current_label.startswith("● "):
                node.set_label(current_label[2:])

    def update_saved_filters(self, saved_filters: list[SavedFilter]) -> None:
        """Update the saved filters in the sidebar."""
        self._saved_filters = saved_filters
        tree = self.query_one("#nav-tree", Tree)

        saved_filters_node = None
        filters_node = None
        for node in tree.root.children:
            if node.data == "section:saved-filters":
                saved_filters_node = node
            elif node.data == "section:filters":
                filters_node = node

        if not saved_filters:
            if saved_filters_node:
                saved_filters_node.remove()
                self._saved_filter_nodes.clear()
            return

        if not saved_filters_node and filters_node:
            saved_filters_node = tree.root.add(
                "Saved Filters", expand=True, data="section:saved-filters", before=filters_node
            )

        if saved_filters_node:
            saved_filters_node.remove_children()
            self._saved_filter_nodes.clear()
            for sf in saved_filters:
                label = f"★ {sf.name}"
                node = saved_filters_node.add_leaf(label, data=f"saved-filter:{sf.name}")
                self._saved_filter_nodes[sf.name] = node
