"""Detail panel widget for showing issue details."""

from datetime import datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Markdown, Static, TabbedContent, TabPane

from linear_term.api.models import Comment, Issue, IssueHistory


class CommentWidget(Vertical):
    """A focusable widget representing a single comment."""

    DEFAULT_CSS = """
    CommentWidget {
        height: auto;
        padding: 1 0;
        border-bottom: dashed $primary-darken-2;
    }

    CommentWidget:focus {
        background: $surface-lighten-1;
    }

    CommentWidget.selected {
        background: $primary-darken-1;
    }

    CommentWidget .comment-header {
        color: $text-muted;
    }

    CommentWidget .comment-body {
        padding-left: 0;
    }

    CommentWidget .comment-actions {
        height: auto;
        padding-top: 1;
        display: none;
    }

    CommentWidget:focus .comment-actions {
        display: block;
    }

    CommentWidget .action-hint {
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("r", "reply", "Reply", show=True),
        Binding("enter", "reply", "Reply", show=False),
    ]

    can_focus = True

    class ReplyRequested(Message):
        """Message when reply to comment is requested."""

        def __init__(self, comment: Comment, issue: Issue) -> None:
            self.comment = comment
            self.issue = issue
            super().__init__()

    def __init__(self, comment: Comment, issue: Issue, depth: int = 0, **kwargs) -> None:
        super().__init__(**kwargs)
        self.comment = comment
        self.issue = issue
        self.depth = depth

    def compose(self) -> ComposeResult:
        indent = "  " * self.depth
        author = self.comment.user.name if self.comment.user else "Unknown"
        time_str = self._format_time(self.comment.created_at)
        header = f"{indent}{author} · {time_str}"
        body = "\n".join(f"{indent}{line}" for line in self.comment.body.split("\n"))

        yield Static(header, classes="comment-header")
        yield Markdown(body, classes="comment-body")
        yield Static(f"{indent}[r] Reply", classes="action-hint comment-actions")

    def _format_time(self, dt: datetime) -> str:
        """Format datetime for display."""
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        delta = now - dt

        if delta.days > 365:
            return f"{delta.days // 365}y ago"
        elif delta.days > 30:
            return f"{delta.days // 30}mo ago"
        elif delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600}h ago"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60}m ago"
        else:
            return "just now"

    def action_reply(self) -> None:
        """Request to reply to this comment."""
        self.post_message(self.ReplyRequested(self.comment, self.issue))


class ActivityWidget(Vertical):
    """A focusable widget representing a single activity entry."""

    DEFAULT_CSS = """
    ActivityWidget {
        height: auto;
        padding: 1 0;
        border-bottom: dashed $primary-darken-2;
    }

    ActivityWidget:focus {
        background: $surface-lighten-1;
    }

    ActivityWidget .activity-header {
        color: $text-muted;
    }

    ActivityWidget .activity-body {
        padding-left: 2;
    }
    """

    can_focus = True

    def __init__(self, header: str, description: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._header = header
        self._description = description

    def compose(self) -> ComposeResult:
        yield Static(self._header, classes="activity-header")
        yield Static(self._description, classes="activity-body")


class ParentLinkWidget(Static):
    """A clickable widget to navigate to parent issue."""

    DEFAULT_CSS = """
    ParentLinkWidget {
        height: auto;
        padding: 0 0 1 0;
        color: $text;
        text-style: underline;
    }

    ParentLinkWidget:hover {
        color: $accent;
    }

    ParentLinkWidget:focus {
        background: $surface-lighten-1;
        color: $accent;
        text-style: bold underline;
    }
    """

    BINDINGS = [
        Binding("enter", "goto_parent", "Go to Parent", show=False),
    ]

    can_focus = True

    class ParentRequested(Message):
        """Message when parent navigation is requested."""

        def __init__(self, parent_issue: Issue) -> None:
            self.parent_issue = parent_issue
            super().__init__()

    def __init__(self, parent_issue: Issue, **kwargs) -> None:
        self._parent_issue = parent_issue
        parent_title = parent_issue.title or ""
        if len(parent_title) > 30:
            parent_title = parent_title[:29] + "…"
        label = f"Parent: {parent_issue.identifier} - {parent_title}"
        super().__init__(label, **kwargs)

    def action_goto_parent(self) -> None:
        """Navigate to parent issue."""
        self.post_message(self.ParentRequested(self._parent_issue))


class SubissueWidget(Vertical):
    """A focusable widget representing a single subissue."""

    DEFAULT_CSS = """
    SubissueWidget {
        height: auto;
        padding: 0 1;
        border-bottom: dashed $primary-darken-3;
    }

    SubissueWidget:focus {
        background: $surface-lighten-1;
    }

    SubissueWidget .subissue-row {
        height: auto;
    }

    SubissueWidget .subissue-status {
        width: 2;
    }

    SubissueWidget .subissue-priority {
        width: 2;
        color: $warning;
    }

    SubissueWidget .subissue-id {
        width: 10;
        color: $accent;
    }

    SubissueWidget .subissue-title {
        width: 1fr;
    }

    SubissueWidget .subissue-assignee {
        width: 10;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("enter", "open_subissue", "Open", show=True),
    ]

    can_focus = True

    class SubissueOpened(Message):
        """Message when a subissue is opened."""

        def __init__(self, issue: Issue) -> None:
            self.issue = issue
            super().__init__()

    def __init__(self, issue: Issue, **kwargs) -> None:
        super().__init__(**kwargs)
        self.issue = issue

    def compose(self) -> ComposeResult:
        status_icon = self.issue.status_icon
        priority_icon = self.issue.priority_icon
        identifier = self.issue.identifier

        title = self.issue.title or "(no title)"
        if len(title) > 25:
            title = title[:24] + "…"

        assignee = ""
        if self.issue.assignee:
            assignee = self.issue.assignee.display_name or self.issue.assignee.name
            if len(assignee) > 8:
                assignee = assignee[:7] + "…"

        with Horizontal(classes="subissue-row"):
            yield Static(status_icon, classes="subissue-status")
            yield Static(priority_icon, classes="subissue-priority")
            yield Static(identifier, classes="subissue-id")
            yield Static(title, classes="subissue-title")
            yield Static(assignee, classes="subissue-assignee")

    def action_open_subissue(self) -> None:
        """Open this subissue."""
        self.post_message(self.SubissueOpened(self.issue))


class DetailPanel(VerticalScroll):
    """Panel showing issue details, description, and comments."""

    DEFAULT_CSS = """
    DetailPanel {
        width: 45;
        background: $surface;
        border-left: solid $primary-darken-2;
        padding: 1;
    }

    DetailPanel .detail-header {
        text-style: bold;
        color: $accent;
        padding-bottom: 1;
    }

    DetailPanel .detail-title {
        text-style: bold;
        padding-bottom: 1;
    }

    DetailPanel .detail-meta {
        color: $text-muted;
        padding-bottom: 1;
    }

    DetailPanel .meta-row {
        height: auto;
        padding: 0 0 0 0;
    }

    DetailPanel .meta-label {
        color: $text-muted;
        width: 12;
    }

    DetailPanel .meta-value {
        color: $text;
    }

    DetailPanel .section-header {
        text-style: bold;
        color: $text;
        padding: 1 0 0 0;
        border-top: solid $primary-darken-2;
        margin-top: 1;
    }

    DetailPanel .comment {
        padding: 1 0;
        border-bottom: dashed $primary-darken-2;
    }

    DetailPanel .comment-header {
        color: $text-muted;
    }

    DetailPanel .comment-body {
        padding-left: 0;
    }

    DetailPanel .label-tag {
        padding: 0 1;
        margin-right: 1;
    }

    DetailPanel .empty-state {
        color: $text-muted;
        text-align: center;
        padding: 2;
    }

    DetailPanel TabbedContent {
        height: auto;
    }

    DetailPanel .subissue-summary {
        color: $text-muted;
        padding: 0 0 1 0;
    }

    DetailPanel #parent-link-container {
        height: auto;
        padding: 0;
    }
    """

    BINDINGS = [
        Binding("c", "add_comment", "Comment", show=True),
        Binding("e", "edit_issue", "Edit", show=True),
        Binding("p", "goto_parent", "Parent", show=False),
        Binding("left", "prev_tab", "Prev Tab", show=False),
        Binding("right", "next_tab", "Next Tab", show=False),
        Binding("h", "prev_tab", "Prev Tab", show=False),
        Binding("l", "next_tab", "Next Tab", show=False),
        Binding("down", "focus_content", "Focus Content", show=False),
        Binding("j", "focus_content", "Focus Content", show=False),
        Binding("up", "focus_tabs", "Focus Tabs", show=False),
        Binding("k", "focus_tabs", "Focus Tabs", show=False),
    ]

    class CommentRequested(Message):
        """Message when comment is requested."""

        def __init__(self, issue: Issue, parent_comment: Comment | None = None) -> None:
            self.issue = issue
            self.parent_comment = parent_comment
            super().__init__()

    class EditRequested(Message):
        """Message when edit is requested."""

        def __init__(self, issue: Issue) -> None:
            self.issue = issue
            super().__init__()

    class SubissueSelected(Message):
        """Message when navigating to a subissue."""

        def __init__(self, issue: Issue) -> None:
            self.issue = issue
            super().__init__()

    class ParentSelected(Message):
        """Message when navigating to parent issue."""

        def __init__(self, issue: Issue) -> None:
            self.issue = issue
            super().__init__()

    # Tab IDs for navigation
    TAB_IDS = ["tab-details", "tab-subissues", "tab-comments", "tab-activity"]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._issue: Issue | None = None

    def compose(self) -> ComposeResult:
        """Compose the detail panel content."""
        yield Static("Select an issue to view details", classes="empty-state", id="empty-state")
        yield Static("", id="detail-header", classes="detail-header")
        yield Static("", id="detail-title", classes="detail-title")
        yield Static("", id="detail-meta", classes="detail-meta")
        with TabbedContent(id="detail-tabs"):
            with TabPane("Details", id="tab-details"):
                yield Vertical(id="parent-link-container")
                yield Static("", id="meta-section")
                yield Static("Description", classes="section-header", id="desc-header")
                yield Markdown("", id="description")
            with TabPane("Sub-issues", id="tab-subissues"):
                yield VerticalScroll(id="subissues-container")
            with TabPane("Comments", id="tab-comments"):
                yield VerticalScroll(id="comments-container")
            with TabPane("Activity", id="tab-activity"):
                yield VerticalScroll(id="activity-container")

    def on_mount(self) -> None:
        """Hide content on mount."""
        self._hide_content()

    def _hide_content(self) -> None:
        """Hide all content and show empty state."""
        self.query_one("#empty-state").display = True
        self.query_one("#detail-header").display = False
        self.query_one("#detail-title").display = False
        self.query_one("#detail-meta").display = False
        self.query_one("#detail-tabs").display = False

    def _show_content(self) -> None:
        """Show all content and hide empty state."""
        self.query_one("#empty-state").display = False
        self.query_one("#detail-header").display = True
        self.query_one("#detail-title").display = True
        self.query_one("#detail-meta").display = True
        self.query_one("#detail-tabs").display = True

    def show_issue(self, issue: Issue) -> None:
        """Display issue details."""
        self._issue = issue
        self._show_content()

        header = self.query_one("#detail-header", Static)
        header.update(f"{issue.status_icon} {issue.identifier}")

        title = self.query_one("#detail-title", Static)
        title.update(issue.title)

        meta_parts = []
        if issue.state:
            meta_parts.append(f"Status: {issue.state.name}")
        meta_parts.append(f"Priority: {issue.priority_label}")
        if issue.assignee:
            name = issue.assignee.display_name or issue.assignee.name
            meta_parts.append(f"Assignee: {name}")

        meta = self.query_one("#detail-meta", Static)
        meta.update(" | ".join(meta_parts))

        self._update_details_tab(issue)
        self._update_subissues_tab(issue)
        self._update_comments_tab(issue)

    def _update_details_tab(self, issue: Issue) -> None:
        """Update the details tab."""
        parent_container = self.query_one("#parent-link-container", Vertical)
        parent_container.remove_children()
        if issue.parent:
            parent_container.display = True
            parent_container.mount(ParentLinkWidget(issue.parent))
        else:
            parent_container.display = False

        meta_lines = []

        if issue.project:
            meta_lines.append(f"Project: {issue.project.name}")
        if issue.cycle:
            meta_lines.append(f"Cycle: {issue.cycle.display_name}")
        if issue.estimate is not None:
            meta_lines.append(f"Estimate: {issue.estimate}")
        if issue.due_date:
            meta_lines.append(f"Due: {issue.due_date.strftime('%Y-%m-%d')}")
        if issue.labels:
            label_names = [label.name for label in issue.labels]
            meta_lines.append(f"Labels: {', '.join(label_names)}")
        if issue.children:
            completed = sum(
                1 for c in issue.children if c.state and c.state.type in ("completed", "canceled")
            )
            meta_lines.append(f"Sub-issues: {completed}/{len(issue.children)} completed")

        meta_section = self.query_one("#meta-section", Static)
        meta_section.update("\n".join(meta_lines) if meta_lines else "No additional metadata")

        description = self.query_one("#description", Markdown)
        if issue.description:
            description.update(issue.description)
        else:
            description.update("*No description*")

    def _update_subissues_tab(self, issue: Issue) -> None:
        """Update the sub-issues tab."""
        container = self.query_one("#subissues-container", VerticalScroll)
        container.remove_children()

        if not issue.children:
            container.mount(Static("No sub-issues", classes="empty-state"))
            return

        completed = sum(
            1 for c in issue.children if c.state and c.state.type in ("completed", "canceled")
        )
        summary = f"{completed}/{len(issue.children)} completed"
        container.mount(Static(summary, classes="subissue-summary"))

        sorted_children = sorted(
            issue.children,
            key=lambda c: c.created_at or datetime.min,
        )
        for child in sorted_children:
            widget = SubissueWidget(child)
            container.mount(widget)

    def _update_comments_tab(self, issue: Issue) -> None:
        """Update the comments tab."""
        container = self.query_one("#comments-container", VerticalScroll)
        container.remove_children()

        if not issue.comments:
            container.mount(Static("No comments yet", classes="empty-state"))
            return

        threaded = self._thread_comments(issue.comments)
        for comment, depth in threaded:
            widget = CommentWidget(comment, issue, depth, id=f"comment-{comment.id}")
            container.mount(widget)

    def _thread_comments(self, comments: list[Comment]) -> list[tuple[Comment, int]]:
        """Organize comments into threads with depth."""
        result: list[tuple[Comment, int]] = []
        root_comments = [c for c in comments if not c.parent_id]
        child_map: dict[str, list[Comment]] = {}

        for comment in comments:
            if comment.parent_id:
                if comment.parent_id not in child_map:
                    child_map[comment.parent_id] = []
                child_map[comment.parent_id].append(comment)

        for root in sorted(root_comments, key=lambda c: c.created_at):
            self._add_comment_tree(root, 0, child_map, result)

        return result

    def _add_comment_tree(
        self,
        comment: Comment,
        depth: int,
        child_map: dict[str, list[Comment]],
        result: list[tuple[Comment, int]],
    ) -> None:
        """Recursively add comment and its children."""
        result.append((comment, depth))
        children = child_map.get(comment.id, [])
        for child in sorted(children, key=lambda c: c.created_at):
            self._add_comment_tree(child, depth + 1, child_map, result)

    def _format_time(self, dt: datetime) -> str:
        """Format datetime for display."""
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        delta = now - dt

        if delta.days > 365:
            return f"{delta.days // 365}y ago"
        elif delta.days > 30:
            return f"{delta.days // 30}mo ago"
        elif delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600}h ago"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60}m ago"
        else:
            return "just now"

    def action_add_comment(self) -> None:
        """Request to add a comment."""
        if self._issue:
            self.post_message(self.CommentRequested(self._issue))

    def action_edit_issue(self) -> None:
        """Request to edit the issue."""
        if self._issue:
            self.post_message(self.EditRequested(self._issue))

    def update_activity(self, history: list[IssueHistory]) -> None:
        """Update the activity tab with history entries."""
        container = self.query_one("#activity-container", VerticalScroll)
        container.remove_children()

        if not history:
            container.mount(Static("No activity recorded", classes="empty-state"))
            return

        for i, entry in enumerate(history):
            actor = entry.actor.name if entry.actor else "Unknown"
            time_str = self._format_time(entry.created_at)
            description = entry.describe()
            header = f"{actor} · {time_str}"

            widget = ActivityWidget(header, description, id=f"activity-{i}")
            container.mount(widget)

    def action_prev_tab(self) -> None:
        """Switch to previous tab."""
        tabs = self.query_one("#detail-tabs", TabbedContent)
        current = tabs.active
        if current in self.TAB_IDS:
            current_idx = self.TAB_IDS.index(current)
            new_idx = (current_idx - 1) % len(self.TAB_IDS)
            tabs.active = self.TAB_IDS[new_idx]

    def action_next_tab(self) -> None:
        """Switch to next tab."""
        tabs = self.query_one("#detail-tabs", TabbedContent)
        current = tabs.active
        if current in self.TAB_IDS:
            current_idx = self.TAB_IDS.index(current)
            new_idx = (current_idx + 1) % len(self.TAB_IDS)
            tabs.active = self.TAB_IDS[new_idx]

    def action_focus_content(self) -> None:
        """Focus first focusable item in current tab content."""
        tabs = self.query_one("#detail-tabs", TabbedContent)
        current = tabs.active

        if current == "tab-comments":
            container = self.query_one("#comments-container", VerticalScroll)
            comment_widgets = container.query(CommentWidget)
            if comment_widgets:
                comment_widgets.first().focus()
        elif current == "tab-subissues":
            container = self.query_one("#subissues-container", VerticalScroll)
            subissue_widgets = container.query(SubissueWidget)
            if subissue_widgets:
                subissue_widgets.first().focus()
        elif current == "tab-activity":
            container = self.query_one("#activity-container", VerticalScroll)
            activity_widgets = container.query(ActivityWidget)
            if activity_widgets:
                activity_widgets.first().focus()
        elif current == "tab-details":
            # Details tab - focus parent link if present, otherwise scroll
            parent_links = self.query(ParentLinkWidget)
            if parent_links:
                parent_links.first().focus()
            else:
                container = self.query_one("#tab-details", TabPane)
                container.scroll_down()

    def action_focus_tabs(self) -> None:
        """Return focus to the tabs."""
        tabs = self.query_one("#detail-tabs", TabbedContent)
        tabs.focus()

    def on_comment_widget_reply_requested(self, event: CommentWidget.ReplyRequested) -> None:
        """Handle reply request from comment widget."""
        self.post_message(self.CommentRequested(event.issue, event.comment))

    def on_subissue_widget_subissue_opened(self, event: SubissueWidget.SubissueOpened) -> None:
        """Handle subissue opened from subissue widget."""
        self.post_message(self.SubissueSelected(event.issue))

    def on_parent_link_widget_parent_requested(
        self, event: ParentLinkWidget.ParentRequested
    ) -> None:
        """Handle parent navigation from parent link widget."""
        self.post_message(self.ParentSelected(event.parent_issue))

    def action_goto_parent(self) -> None:
        """Navigate to parent issue."""
        if self._issue and self._issue.parent:
            self.post_message(self.ParentSelected(self._issue.parent))

    def clear(self) -> None:
        """Clear the panel."""
        self._issue = None
        self._hide_content()
