"""Tests for data models."""

from linear_term.api.models import (
    Comment,
    Cycle,
    Issue,
    IssueLabel,
    Project,
    Team,
    User,
    WorkflowState,
)


class TestUser:
    def test_from_dict(self):
        data = {
            "id": "user-123",
            "name": "Test User",
            "email": "test@example.com",
            "displayName": "Tester",
            "active": True,
        }
        user = User.from_dict(data)
        assert user is not None
        assert user.id == "user-123"
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.display_name == "Tester"
        assert user.active is True

    def test_from_dict_none(self):
        assert User.from_dict(None) is None

    def test_from_dict_minimal(self):
        data = {"id": "user-123", "name": "Test"}
        user = User.from_dict(data)
        assert user is not None
        assert user.id == "user-123"
        assert user.email is None


class TestWorkflowState:
    def test_from_dict(self):
        data = {
            "id": "state-123",
            "name": "In Progress",
            "color": "#ff0000",
            "type": "started",
            "position": 1.5,
        }
        state = WorkflowState.from_dict(data)
        assert state is not None
        assert state.id == "state-123"
        assert state.name == "In Progress"
        assert state.type == "started"


class TestIssueLabel:
    def test_from_dict(self):
        data = {
            "id": "label-123",
            "name": "Bug",
            "color": "#ff0000",
            "description": "A bug report",
        }
        label = IssueLabel.from_dict(data)
        assert label is not None
        assert label.id == "label-123"
        assert label.name == "Bug"
        assert label.color == "#ff0000"


class TestTeam:
    def test_from_dict(self):
        data = {
            "id": "team-123",
            "name": "Engineering",
            "key": "ENG",
            "description": "Engineering team",
        }
        team = Team.from_dict(data)
        assert team is not None
        assert team.id == "team-123"
        assert team.name == "Engineering"
        assert team.key == "ENG"


class TestProject:
    def test_from_dict(self):
        data = {
            "id": "proj-123",
            "name": "Project Alpha",
            "state": "started",
            "progress": 0.5,
        }
        project = Project.from_dict(data)
        assert project is not None
        assert project.id == "proj-123"
        assert project.name == "Project Alpha"
        assert project.issue_count == 0


class TestCycle:
    def test_from_dict(self):
        data = {
            "id": "cycle-123",
            "name": "Sprint 1",
            "number": 1,
            "progress": 0.75,
            "isActive": True,
        }
        cycle = Cycle.from_dict(data)
        assert cycle is not None
        assert cycle.id == "cycle-123"
        assert cycle.display_name == "Sprint 1"
        assert cycle.is_active is True

    def test_display_name_fallback(self):
        data = {"id": "cycle-123", "number": 5}
        cycle = Cycle.from_dict(data)
        assert cycle.display_name == "Cycle 5"


class TestIssue:
    def test_from_dict(self):
        data = {
            "id": "issue-123",
            "identifier": "ENG-123",
            "title": "Test Issue",
            "description": "A test issue",
            "priority": 2,
            "priorityLabel": "High",
            "state": {
                "id": "state-1",
                "name": "Todo",
                "type": "unstarted",
                "color": "#888",
            },
        }
        issue = Issue.from_dict(data)
        assert issue is not None
        assert issue.id == "issue-123"
        assert issue.identifier == "ENG-123"
        assert issue.title == "Test Issue"
        assert issue.priority == 2
        assert issue.state is not None
        assert issue.state.name == "Todo"

    def test_status_icon(self):
        data = {
            "id": "1",
            "identifier": "T-1",
            "title": "Test",
            "state": {"id": "s1", "name": "Done", "type": "completed", "color": "#0f0"},
        }
        issue = Issue.from_dict(data)
        assert issue.status_icon == "✓"

    def test_priority_icon(self):
        data = {"id": "1", "identifier": "T-1", "title": "Test", "priority": 1}
        issue = Issue.from_dict(data)
        assert issue.priority_icon == "!!!"

    def test_with_labels(self):
        data = {
            "id": "1",
            "identifier": "T-1",
            "title": "Test",
            "labels": {
                "nodes": [
                    {"id": "l1", "name": "Bug", "color": "#f00"},
                    {"id": "l2", "name": "Feature", "color": "#0f0"},
                ]
            },
        }
        issue = Issue.from_dict(data)
        assert len(issue.labels) == 2
        assert issue.labels[0].name == "Bug"


class TestComment:
    def test_from_dict(self):
        data = {
            "id": "comment-123",
            "body": "This is a comment",
            "createdAt": "2024-01-15T10:30:00Z",
            "user": {"id": "user-1", "name": "Test User"},
        }
        comment = Comment.from_dict(data)
        assert comment is not None
        assert comment.id == "comment-123"
        assert comment.body == "This is a comment"
        assert comment.user is not None
        assert comment.user.name == "Test User"
