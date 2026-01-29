"""Issue creation and editing forms."""

from dataclasses import dataclass, field

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static, TextArea

from linear_term.api.models import Cycle, Issue, IssueLabel, Project, Team, User, WorkflowState


@dataclass
class IssueFormData:
    """Data for issue creation/editing."""

    title: str = ""
    description: str = ""
    team_id: str | None = None
    project_id: str | None = None
    state_id: str | None = None
    priority: int | None = None
    assignee_id: str | None = None
    cycle_id: str | None = None
    label_ids: list[str] = field(default_factory=list)
    estimate: float | None = None
    due_date: str | None = None
    parent_id: str | None = None


class IssueForm(ModalScreen[IssueFormData | None]):
    """Form for creating or editing an issue."""

    DEFAULT_CSS = """
    IssueForm {
        align: center middle;
    }

    IssueForm > Container {
        width: 70;
        height: auto;
        max-height: 90%;
        background: $surface;
        border: solid $accent;
        padding: 1 2;
    }

    IssueForm .form-title {
        text-style: bold;
        text-align: center;
        padding-bottom: 1;
        color: $accent;
    }

    IssueForm VerticalScroll {
        height: auto;
        max-height: 70%;
    }

    IssueForm .form-row {
        height: auto;
        margin-bottom: 1;
    }

    IssueForm Label {
        width: 12;
        padding-top: 1;
    }

    IssueForm Input {
        width: 1fr;
    }

    IssueForm Select {
        width: 1fr;
    }

    IssueForm TextArea {
        height: 8;
        width: 1fr;
    }

    IssueForm .button-row {
        height: auto;
        padding-top: 1;
        align: center middle;
    }

    IssueForm Button {
        margin: 0 1;
    }

    IssueForm .hint {
        color: $text-muted;
        padding: 1 0;
        text-align: center;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("ctrl+enter", "submit", "Submit", show=False),
    ]

    def __init__(
        self,
        teams: list[Team],
        projects: list[Project],
        users: list[User],
        labels: list[IssueLabel],
        cycles: list[Cycle],
        workflow_states: list[WorkflowState],
        issue: Issue | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._teams = teams
        self._projects = projects
        self._users = users
        self._labels = labels
        self._cycles = cycles
        self._workflow_states = workflow_states
        self._issue = issue
        self._is_edit = issue is not None

    def compose(self) -> ComposeResult:
        """Compose the form content."""
        title = "Edit Issue" if self._is_edit else "Create Issue"

        with Container():
            yield Static(title, classes="form-title")
            with VerticalScroll():
                with Horizontal(classes="form-row"):
                    yield Label("Title:")
                    yield Input(
                        placeholder="Issue title",
                        value=self._issue.title if self._issue else "",
                        id="title-input",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Team:")
                    team_options = [(t.name, t.id) for t in self._teams]
                    team_ids = {t.id for t in self._teams}
                    default_team = None
                    if self._issue and self._issue.team and self._issue.team.id in team_ids:
                        default_team = self._issue.team.id
                    yield Select(
                        options=team_options,
                        value=default_team,
                        id="team-select",
                        prompt="Select team",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Status:")
                    state_options = [(s.name, s.id) for s in self._workflow_states]
                    state_ids = {s.id for s in self._workflow_states}
                    default_state = None
                    if self._issue and self._issue.state and self._issue.state.id in state_ids:
                        default_state = self._issue.state.id
                    yield Select(
                        options=state_options,
                        value=default_state,
                        id="state-select",
                        prompt="Select status",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Priority:")
                    priority_options = [
                        ("No Priority", "0"),
                        ("Urgent", "1"),
                        ("High", "2"),
                        ("Medium", "3"),
                        ("Low", "4"),
                    ]
                    default_priority = str(self._issue.priority) if self._issue else "0"
                    yield Select(
                        options=priority_options,
                        value=default_priority,
                        id="priority-select",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Assignee:")
                    active_users = [(u.name, u.id) for u in self._users if u.active]
                    user_options = [("Unassigned", "")] + active_users
                    user_ids = {u.id for u in self._users if u.active}
                    default_assignee = ""
                    if self._issue and self._issue.assignee and self._issue.assignee.id in user_ids:
                        default_assignee = self._issue.assignee.id
                    yield Select(
                        options=user_options,
                        value=default_assignee,
                        id="assignee-select",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Project:")
                    project_options = [("None", "")] + [(p.name, p.id) for p in self._projects]
                    project_ids = {p.id for p in self._projects}
                    default_project = ""
                    if self._issue and self._issue.project:
                        if self._issue.project.id in project_ids:
                            default_project = self._issue.project.id
                    yield Select(
                        options=project_options,
                        value=default_project,
                        id="project-select",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Cycle:")
                    cycle_opts = [(c.display_name, c.id) for c in self._cycles]
                    cycle_options = [("None", "")] + cycle_opts
                    cycle_ids = {c.id for c in self._cycles}
                    default_cycle = ""
                    if self._issue and self._issue.cycle and self._issue.cycle.id in cycle_ids:
                        default_cycle = self._issue.cycle.id
                    yield Select(
                        options=cycle_options,
                        value=default_cycle,
                        id="cycle-select",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Estimate:")
                    estimate_val = ""
                    if self._issue and self._issue.estimate:
                        estimate_val = str(self._issue.estimate)
                    yield Input(
                        placeholder="Story points",
                        value=estimate_val,
                        id="estimate-input",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Due Date:")
                    due_str = ""
                    if self._issue and self._issue.due_date:
                        due_str = self._issue.due_date.strftime("%Y-%m-%d")
                    yield Input(
                        placeholder="YYYY-MM-DD",
                        value=due_str,
                        id="due-date-input",
                    )

                with Vertical(classes="form-row"):
                    yield Label("Description:")
                    yield TextArea(
                        text=self._issue.description or "" if self._issue else "",
                        id="description-input",
                    )

            yield Static("Ctrl+Enter to submit, Escape to cancel", classes="hint")
            with Horizontal(classes="button-row"):
                yield Button("Submit", variant="primary", id="submit-btn")
                yield Button("Cancel", id="cancel-btn")

    def on_mount(self) -> None:
        """Focus title on mount."""
        self.query_one("#title-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "submit-btn":
            self._submit()
        elif event.button.id == "cancel-btn":
            self.dismiss(None)

    def action_submit(self) -> None:
        """Submit the form."""
        self._submit()

    def action_cancel(self) -> None:
        """Cancel the form."""
        self.dismiss(None)

    def _submit(self) -> None:
        """Collect form data and submit."""
        title = self.query_one("#title-input", Input).value.strip()
        if not title:
            return

        team_select = self.query_one("#team-select", Select)
        team_id = team_select.value if team_select.value != Select.BLANK else None

        state_select = self.query_one("#state-select", Select)
        state_id = state_select.value if state_select.value != Select.BLANK else None

        priority_select = self.query_one("#priority-select", Select)
        priority_str = priority_select.value if priority_select.value != Select.BLANK else "0"
        priority = int(priority_str) if priority_str else None

        assignee_select = self.query_one("#assignee-select", Select)
        assignee_val = assignee_select.value
        assignee_id = assignee_val if assignee_val not in (Select.BLANK, "") else None

        project_select = self.query_one("#project-select", Select)
        project_val = project_select.value
        project_id = project_val if project_val not in (Select.BLANK, "") else None

        cycle_select = self.query_one("#cycle-select", Select)
        cycle_id = cycle_select.value if cycle_select.value not in (Select.BLANK, "") else None

        estimate_str = self.query_one("#estimate-input", Input).value.strip()
        estimate = float(estimate_str) if estimate_str else None

        due_date = self.query_one("#due-date-input", Input).value.strip() or None

        description = self.query_one("#description-input", TextArea).text

        form_data = IssueFormData(
            title=title,
            description=description,
            team_id=team_id,
            project_id=project_id,
            state_id=state_id,
            priority=priority,
            assignee_id=assignee_id,
            cycle_id=cycle_id,
            estimate=estimate,
            due_date=due_date,
        )

        self.dismiss(form_data)


class QuickCaptureForm(ModalScreen[tuple[str, str] | None]):
    """Quick capture form for rapid issue creation."""

    DEFAULT_CSS = """
    QuickCaptureForm {
        align: center middle;
    }

    QuickCaptureForm > Container {
        width: 60;
        height: auto;
        background: $surface;
        border: solid $accent;
        padding: 1 2;
    }

    QuickCaptureForm .form-title {
        text-style: bold;
        text-align: center;
        padding-bottom: 1;
        color: $accent;
    }

    QuickCaptureForm Input {
        width: 100%;
        margin-bottom: 1;
    }

    QuickCaptureForm Select {
        width: 100%;
        margin-bottom: 1;
    }

    QuickCaptureForm .hint {
        color: $text-muted;
        text-align: center;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("enter", "submit", "Submit", show=False),
    ]

    def __init__(self, teams: list[Team], default_team_id: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._teams = teams
        self._default_team_id = default_team_id

    def compose(self) -> ComposeResult:
        """Compose the quick capture form."""
        with Container():
            yield Static("Quick Capture", classes="form-title")
            yield Input(placeholder="Issue title...", id="title-input")
            team_options = [(t.name, t.id) for t in self._teams]
            yield Select(
                options=team_options,
                value=self._default_team_id,
                id="team-select",
                prompt="Select team",
            )
            yield Static("Enter to create, Escape to cancel", classes="hint")

    def on_mount(self) -> None:
        """Focus title on mount."""
        self.query_one("#title-input", Input).focus()

    def action_submit(self) -> None:
        """Submit the quick capture."""
        title = self.query_one("#title-input", Input).value.strip()
        if not title:
            return

        team_select = self.query_one("#team-select", Select)
        team_id = team_select.value if team_select.value != Select.BLANK else None

        if title and team_id:
            self.dismiss((title, team_id))
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Cancel the quick capture."""
        self.dismiss(None)


class CommentForm(ModalScreen[str | None]):
    """Form for adding a comment."""

    DEFAULT_CSS = """
    CommentForm {
        align: center middle;
    }

    CommentForm > Container {
        width: 70;
        height: auto;
        background: $surface;
        border: solid $accent;
        padding: 1 2;
    }

    CommentForm .form-title {
        text-style: bold;
        text-align: center;
        padding-bottom: 1;
        color: $accent;
    }

    CommentForm TextArea {
        height: 10;
        width: 100%;
        margin-bottom: 1;
    }

    CommentForm .hint {
        color: $text-muted;
        text-align: center;
    }

    CommentForm .button-row {
        height: auto;
        padding-top: 1;
        align: center middle;
    }

    CommentForm Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("ctrl+enter", "submit", "Submit", show=False),
    ]

    def __init__(self, issue_identifier: str, title: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._issue_identifier = issue_identifier
        self._title = title or f"Add Comment to {issue_identifier}"

    def compose(self) -> ComposeResult:
        """Compose the comment form."""
        with Container():
            yield Static(self._title, classes="form-title")
            yield TextArea(id="comment-input")
            yield Static("Ctrl+Enter to submit, Escape to cancel", classes="hint")
            with Horizontal(classes="button-row"):
                yield Button("Submit", variant="primary", id="submit-btn")
                yield Button("Cancel", id="cancel-btn")

    def on_mount(self) -> None:
        """Focus the text area on mount."""
        self.query_one("#comment-input", TextArea).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "submit-btn":
            self._submit()
        elif event.button.id == "cancel-btn":
            self.dismiss(None)

    def action_submit(self) -> None:
        """Submit the comment."""
        self._submit()

    def action_cancel(self) -> None:
        """Cancel the form."""
        self.dismiss(None)

    def _submit(self) -> None:
        """Submit the comment."""
        text = self.query_one("#comment-input", TextArea).text.strip()
        if text:
            self.dismiss(text)
        else:
            self.dismiss(None)
