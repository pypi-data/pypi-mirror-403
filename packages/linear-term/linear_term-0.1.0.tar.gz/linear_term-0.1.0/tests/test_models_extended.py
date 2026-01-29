"""Extended tests for data models."""

from linear_term.api.models import (
    Comment,
    Cycle,
    Issue,
    IssueHistory,
    IssueLabel,
    Project,
    Team,
    User,
    WorkflowState,
    _parse_datetime,
)


class TestParseDatetime:
    def test_parse_iso_format(self):
        result = _parse_datetime("2024-01-15T10:30:00+00:00")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_zulu_format(self):
        result = _parse_datetime("2024-01-15T10:30:00Z")
        assert result is not None
        assert result.year == 2024

    def test_parse_none(self):
        assert _parse_datetime(None) is None

    def test_parse_empty_string(self):
        assert _parse_datetime("") is None

    def test_parse_invalid_format(self):
        assert _parse_datetime("not-a-date") is None

    def test_parse_partial_date(self):
        assert _parse_datetime("2024-01-15") is not None


class TestUserModel:
    def test_from_dict_with_all_fields(self):
        data = {
            "id": "user-1",
            "name": "Test User",
            "email": "test@example.com",
            "displayName": "Tester",
            "avatarUrl": "https://example.com/avatar.png",
            "active": True,
        }
        user = User.from_dict(data)
        assert user is not None
        assert user.id == "user-1"
        assert user.avatar_url == "https://example.com/avatar.png"

    def test_from_dict_snake_case_fields(self):
        data = {
            "id": "user-1",
            "name": "Test",
            "display_name": "Tester",
            "avatar_url": "https://example.com/avatar.png",
        }
        user = User.from_dict(data)
        assert user is not None
        assert user.display_name == "Tester"
        assert user.avatar_url == "https://example.com/avatar.png"

    def test_from_dict_default_name(self):
        data = {"id": "user-1"}
        user = User.from_dict(data)
        assert user is not None
        assert user.name == "Unknown"

    def test_from_dict_inactive_user(self):
        data = {"id": "user-1", "name": "Test", "active": False}
        user = User.from_dict(data)
        assert user is not None
        assert user.active is False


class TestWorkflowStateModel:
    def test_from_dict_all_types(self):
        types = ["triage", "backlog", "unstarted", "started", "completed", "canceled"]
        for state_type in types:
            data = {
                "id": f"state-{state_type}",
                "name": state_type.title(),
                "color": "#888",
                "type": state_type,
            }
            state = WorkflowState.from_dict(data)
            assert state is not None
            assert state.type == state_type

    def test_from_dict_defaults(self):
        data = {"id": "state-1"}
        state = WorkflowState.from_dict(data)
        assert state is not None
        assert state.name == "Unknown"
        assert state.color == "#888888"
        assert state.type == "unstarted"
        assert state.position == 0

    def test_from_dict_with_position(self):
        data = {"id": "s1", "name": "State", "color": "#000", "type": "started", "position": 5.5}
        state = WorkflowState.from_dict(data)
        assert state is not None
        assert state.position == 5.5


class TestIssueLabelModel:
    def test_from_dict_with_description(self):
        data = {
            "id": "label-1",
            "name": "Bug",
            "color": "#ff0000",
            "description": "A bug report",
        }
        label = IssueLabel.from_dict(data)
        assert label is not None
        assert label.description == "A bug report"

    def test_from_dict_no_description(self):
        data = {"id": "label-1", "name": "Feature", "color": "#00ff00"}
        label = IssueLabel.from_dict(data)
        assert label is not None
        assert label.description is None


class TestTeamModel:
    def test_from_dict_with_all_fields(self):
        data = {
            "id": "team-1",
            "name": "Engineering",
            "key": "ENG",
            "description": "Engineering team",
            "color": "#0000ff",
            "icon": "rocket",
        }
        team = Team.from_dict(data)
        assert team is not None
        assert team.color == "#0000ff"
        assert team.icon == "rocket"

    def test_from_dict_defaults(self):
        data = {"id": "team-1"}
        team = Team.from_dict(data)
        assert team is not None
        assert team.name == "Unknown"
        assert team.key == "???"


class TestProjectModel:
    def test_from_dict_with_dates(self):
        data = {
            "id": "proj-1",
            "name": "Project",
            "targetDate": "2024-12-31T00:00:00Z",
            "startDate": "2024-01-01T00:00:00Z",
        }
        project = Project.from_dict(data)
        assert project is not None
        assert project.target_date is not None
        assert project.start_date is not None

    def test_from_dict_snake_case_dates(self):
        data = {
            "id": "proj-1",
            "name": "Project",
            "target_date": "2024-12-31T00:00:00Z",
            "start_date": "2024-01-01T00:00:00Z",
        }
        project = Project.from_dict(data)
        assert project is not None
        assert project.target_date is not None

    def test_from_dict_with_lead(self):
        data = {
            "id": "proj-1",
            "name": "Project",
            "lead": {"id": "user-1", "name": "Alice"},
        }
        project = Project.from_dict(data)
        assert project is not None
        assert project.lead is not None
        assert project.lead.name == "Alice"

    def test_from_dict_defaults(self):
        data = {"id": "proj-1"}
        project = Project.from_dict(data)
        assert project is not None
        assert project.state == "planned"
        assert project.progress == 0
        assert project.issue_count == 0


class TestCycleModel:
    def test_from_dict_with_all_fields(self):
        data = {
            "id": "cycle-1",
            "name": "Sprint 1",
            "number": 1,
            "startsAt": "2024-01-01T00:00:00Z",
            "endsAt": "2024-01-14T00:00:00Z",
            "progress": 0.75,
            "isActive": True,
        }
        cycle = Cycle.from_dict(data)
        assert cycle is not None
        assert cycle.starts_at is not None
        assert cycle.ends_at is not None
        assert cycle.progress == 0.75
        assert cycle.is_active is True

    def test_from_dict_snake_case(self):
        data = {
            "id": "cycle-1",
            "number": 1,
            "starts_at": "2024-01-01T00:00:00Z",
            "ends_at": "2024-01-14T00:00:00Z",
            "is_active": True,
        }
        cycle = Cycle.from_dict(data)
        assert cycle is not None
        assert cycle.is_active is True

    def test_display_name_with_name(self):
        data = {"id": "cycle-1", "name": "Sprint Alpha", "number": 1}
        cycle = Cycle.from_dict(data)
        assert cycle is not None
        assert cycle.display_name == "Sprint Alpha"

    def test_display_name_without_name(self):
        data = {"id": "cycle-1", "number": 5}
        cycle = Cycle.from_dict(data)
        assert cycle is not None
        assert cycle.display_name == "Cycle 5"

    def test_display_name_null_name(self):
        data = {"id": "cycle-1", "name": None, "number": 3}
        cycle = Cycle.from_dict(data)
        assert cycle is not None
        assert cycle.display_name == "Cycle 3"


class TestCommentModel:
    def test_from_dict_with_parent_dict(self):
        data = {
            "id": "comment-1",
            "body": "Test comment",
            "createdAt": "2024-01-15T10:00:00Z",
            "parent": {"id": "comment-0"},
        }
        comment = Comment.from_dict(data)
        assert comment is not None
        assert comment.parent_id == "comment-0"

    def test_from_dict_with_parent_id(self):
        data = {
            "id": "comment-1",
            "body": "Test comment",
            "createdAt": "2024-01-15T10:00:00Z",
            "parent_id": "comment-0",
        }
        comment = Comment.from_dict(data)
        assert comment is not None
        assert comment.parent_id == "comment-0"

    def test_from_dict_with_user(self):
        data = {
            "id": "comment-1",
            "body": "Test",
            "createdAt": "2024-01-15T10:00:00Z",
            "user": {"id": "user-1", "name": "Alice"},
        }
        comment = Comment.from_dict(data)
        assert comment is not None
        assert comment.user is not None
        assert comment.user.name == "Alice"

    def test_from_dict_no_created_at_uses_now(self):
        data = {"id": "comment-1", "body": "Test"}
        comment = Comment.from_dict(data)
        assert comment is not None
        assert comment.created_at is not None


class TestIssueHistoryModel:
    def test_from_dict_title_change(self):
        data = {
            "id": "h1",
            "createdAt": "2024-01-15T10:00:00Z",
            "fromTitle": "Old Title",
            "toTitle": "New Title",
        }
        history = IssueHistory.from_dict(data)
        assert history is not None
        assert history.changes is not None
        assert "title" in history.changes
        assert history.changes["title"]["from"] == "Old Title"
        assert history.changes["title"]["to"] == "New Title"

    def test_from_dict_priority_change(self):
        data = {
            "id": "h1",
            "createdAt": "2024-01-15T10:00:00Z",
            "fromPriority": 3,
            "toPriority": 1,
        }
        history = IssueHistory.from_dict(data)
        assert history is not None
        assert history.changes is not None
        assert "priority" in history.changes
        assert history.from_priority == 3
        assert history.to_priority == 1

    def test_from_dict_estimate_change(self):
        data = {
            "id": "h1",
            "createdAt": "2024-01-15T10:00:00Z",
            "fromEstimate": 2,
            "toEstimate": 5,
        }
        history = IssueHistory.from_dict(data)
        assert history is not None
        assert history.changes is not None
        assert "estimate" in history.changes

    def test_from_dict_due_date_change(self):
        data = {
            "id": "h1",
            "createdAt": "2024-01-15T10:00:00Z",
            "fromDueDate": "2024-01-20",
            "toDueDate": "2024-01-25",
        }
        history = IssueHistory.from_dict(data)
        assert history is not None
        assert history.changes is not None
        assert "dueDate" in history.changes

    def test_from_dict_label_changes(self):
        data = {
            "id": "h1",
            "createdAt": "2024-01-15T10:00:00Z",
            "addedLabels": {"nodes": [{"name": "Bug"}]},
            "removedLabels": {"nodes": [{"name": "Feature"}]},
        }
        history = IssueHistory.from_dict(data)
        assert history is not None
        assert history.changes is not None
        assert "labels" in history.changes
        assert "Bug" in history.changes["labels"]["added"]
        assert "Feature" in history.changes["labels"]["removed"]

    def test_from_dict_no_changes(self):
        data = {
            "id": "h1",
            "createdAt": "2024-01-15T10:00:00Z",
        }
        history = IssueHistory.from_dict(data)
        assert history is not None
        assert history.changes is None

    def test_from_dict_with_actor(self):
        data = {
            "id": "h1",
            "createdAt": "2024-01-15T10:00:00Z",
            "actor": {"id": "user-1", "name": "Alice"},
            "fromPriority": 2,
            "toPriority": 1,
        }
        history = IssueHistory.from_dict(data)
        assert history is not None
        assert history.actor is not None
        assert history.actor.name == "Alice"

    def test_describe_title_change(self):
        data = {
            "id": "h1",
            "createdAt": "2024-01-15T10:00:00Z",
            "fromTitle": "Old",
            "toTitle": "New",
        }
        history = IssueHistory.from_dict(data)
        assert history is not None
        assert "Title changed" in history.describe()

    def test_describe_priority_change(self):
        data = {
            "id": "h1",
            "createdAt": "2024-01-15T10:00:00Z",
            "fromPriority": 3,
            "toPriority": 1,
        }
        history = IssueHistory.from_dict(data)
        assert history is not None
        desc = history.describe()
        assert "Priority" in desc
        assert "Medium" in desc
        assert "Urgent" in desc

    def test_describe_estimate_change(self):
        data = {
            "id": "h1",
            "createdAt": "2024-01-15T10:00:00Z",
            "fromEstimate": None,
            "toEstimate": 5,
        }
        history = IssueHistory.from_dict(data)
        assert history is not None
        desc = history.describe()
        assert "Estimate" in desc

    def test_describe_label_added(self):
        data = {
            "id": "h1",
            "createdAt": "2024-01-15T10:00:00Z",
            "addedLabels": {"nodes": [{"name": "Bug"}]},
            "removedLabels": {"nodes": []},
        }
        history = IssueHistory.from_dict(data)
        assert history is not None
        assert "Added labels: Bug" in history.describe()

    def test_describe_no_changes(self):
        data = {"id": "h1", "createdAt": "2024-01-15T10:00:00Z"}
        history = IssueHistory.from_dict(data)
        assert history is not None
        assert history.describe() == "Updated"


class TestIssueModel:
    def test_from_dict_with_all_nested(self):
        data = {
            "id": "issue-1",
            "identifier": "ENG-1",
            "title": "Test Issue",
            "state": {"id": "s1", "name": "Todo", "color": "#888", "type": "unstarted"},
            "assignee": {"id": "u1", "name": "Alice"},
            "creator": {"id": "u2", "name": "Bob"},
            "team": {"id": "t1", "name": "Engineering", "key": "ENG"},
            "project": {"id": "p1", "name": "Project"},
            "cycle": {"id": "c1", "name": "Sprint 1", "number": 1},
        }
        issue = Issue.from_dict(data)
        assert issue is not None
        assert issue.assignee is not None
        assert issue.creator is not None
        assert issue.team is not None
        assert issue.project is not None
        assert issue.cycle is not None

    def test_from_dict_with_parent(self):
        data = {
            "id": "issue-2",
            "identifier": "ENG-2",
            "title": "Sub-issue",
            "parent": {
                "id": "issue-1",
                "identifier": "ENG-1",
                "title": "Parent Issue",
            },
        }
        issue = Issue.from_dict(data)
        assert issue is not None
        assert issue.parent is not None
        assert issue.parent.identifier == "ENG-1"

    def test_from_dict_with_children(self):
        data = {
            "id": "issue-1",
            "identifier": "ENG-1",
            "title": "Parent",
            "children": {
                "nodes": [
                    {"id": "i2", "identifier": "ENG-2", "title": "Child 1"},
                    {"id": "i3", "identifier": "ENG-3", "title": "Child 2"},
                ]
            },
        }
        issue = Issue.from_dict(data)
        assert issue is not None
        assert len(issue.children) == 2
        assert issue.children[0].identifier == "ENG-2"

    def test_from_dict_with_labels_as_nodes(self):
        data = {
            "id": "issue-1",
            "identifier": "ENG-1",
            "title": "Test",
            "labels": {
                "nodes": [
                    {"id": "l1", "name": "Bug", "color": "#f00"},
                    {"id": "l2", "name": "Feature", "color": "#0f0"},
                ]
            },
        }
        issue = Issue.from_dict(data)
        assert issue is not None
        assert len(issue.labels) == 2

    def test_from_dict_with_labels_as_list(self):
        data = {
            "id": "issue-1",
            "identifier": "ENG-1",
            "title": "Test",
            "labels": [
                {"id": "l1", "name": "Bug", "color": "#f00"},
            ],
        }
        issue = Issue.from_dict(data)
        assert issue is not None
        assert len(issue.labels) == 1

    def test_from_dict_with_comments_as_nodes(self):
        data = {
            "id": "issue-1",
            "identifier": "ENG-1",
            "title": "Test",
            "comments": {
                "nodes": [
                    {"id": "c1", "body": "Comment 1", "createdAt": "2024-01-15T10:00:00Z"},
                    {"id": "c2", "body": "Comment 2", "createdAt": "2024-01-15T11:00:00Z"},
                ]
            },
        }
        issue = Issue.from_dict(data)
        assert issue is not None
        assert len(issue.comments) == 2

    def test_from_dict_with_url_and_branch(self):
        data = {
            "id": "issue-1",
            "identifier": "ENG-1",
            "title": "Test",
            "url": "https://linear.app/team/issue/ENG-1",
            "branchName": "tburch/eng-1-test",
        }
        issue = Issue.from_dict(data)
        assert issue is not None
        assert issue.url == "https://linear.app/team/issue/ENG-1"
        assert issue.branch_name == "tburch/eng-1-test"

    def test_from_dict_snake_case_branch(self):
        data = {
            "id": "issue-1",
            "identifier": "ENG-1",
            "title": "Test",
            "branch_name": "feature/test",
        }
        issue = Issue.from_dict(data)
        assert issue is not None
        assert issue.branch_name == "feature/test"

    def test_status_icon_all_types(self):
        types_icons = {
            "triage": "◇",
            "backlog": "○",
            "unstarted": "○",
            "started": "●",
            "completed": "✓",
            "canceled": "⊗",
        }
        for state_type, expected_icon in types_icons.items():
            data = {
                "id": "i1",
                "identifier": "T-1",
                "title": "Test",
                "state": {"id": "s1", "name": "State", "type": state_type, "color": "#888"},
            }
            issue = Issue.from_dict(data)
            assert issue is not None
            assert issue.status_icon == expected_icon

    def test_status_icon_no_state(self):
        data = {"id": "i1", "identifier": "T-1", "title": "Test"}
        issue = Issue.from_dict(data)
        assert issue is not None
        assert issue.status_icon == "○"

    def test_status_icon_unknown_type(self):
        data = {
            "id": "i1",
            "identifier": "T-1",
            "title": "Test",
            "state": {"id": "s1", "name": "Custom", "type": "custom", "color": "#888"},
        }
        issue = Issue.from_dict(data)
        assert issue is not None
        assert issue.status_icon == "○"

    def test_priority_icon_all_levels(self):
        priorities_icons = {
            0: "---",
            1: "!!!",
            2: "!!",
            3: "!",
            4: "-",
        }
        for priority, expected_icon in priorities_icons.items():
            data = {
                "id": "i1",
                "identifier": "T-1",
                "title": "Test",
                "priority": priority,
            }
            issue = Issue.from_dict(data)
            assert issue is not None
            assert issue.priority_icon == expected_icon

    def test_priority_icon_unknown_level(self):
        data = {"id": "i1", "identifier": "T-1", "title": "Test", "priority": 99}
        issue = Issue.from_dict(data)
        assert issue is not None
        assert issue.priority_icon == "---"

    def test_from_dict_defaults(self):
        data = {"id": "i1"}
        issue = Issue.from_dict(data)
        assert issue is not None
        assert issue.identifier == "???"
        assert issue.title == "Untitled"
        assert issue.priority == 0
        assert issue.priority_label == "No Priority"
        assert issue.labels == []
        assert issue.children == []
        assert issue.comments == []

    def test_from_dict_with_dates(self):
        data = {
            "id": "i1",
            "identifier": "T-1",
            "title": "Test",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-16T10:00:00Z",
            "completedAt": "2024-01-17T10:00:00Z",
            "canceledAt": None,
            "startedAt": "2024-01-15T12:00:00Z",
            "dueDate": "2024-01-20",
        }
        issue = Issue.from_dict(data)
        assert issue is not None
        assert issue.created_at is not None
        assert issue.updated_at is not None
        assert issue.completed_at is not None
        assert issue.canceled_at is None
        assert issue.started_at is not None
        assert issue.due_date is not None

    def test_from_dict_snake_case_dates(self):
        data = {
            "id": "i1",
            "identifier": "T-1",
            "title": "Test",
            "created_at": "2024-01-15T10:00:00Z",
            "due_date": "2024-01-20",
        }
        issue = Issue.from_dict(data)
        assert issue is not None
        assert issue.created_at is not None
        assert issue.due_date is not None
