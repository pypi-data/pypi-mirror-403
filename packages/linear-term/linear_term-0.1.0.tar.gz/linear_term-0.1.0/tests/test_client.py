"""Tests for the Linear API client."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from linear_term.api.client import (
    AuthenticationError,
    LinearClient,
    LinearClientError,
    RateLimitError,
)


class TestLinearClientInit:
    def test_init(self):
        client = LinearClient("test_key")
        assert client.api_key == "test_key"
        assert client._client is None

    def test_client_property_creates_client(self):
        client = LinearClient("test_key")
        http_client = client.client
        assert http_client is not None
        assert isinstance(http_client, httpx.AsyncClient)


class TestLinearClientContextManager:
    async def test_aenter_creates_client(self):
        client = LinearClient("test_key")
        async with client as c:
            assert c._client is not None
            assert c is client

    async def test_aexit_closes_client(self):
        client = LinearClient("test_key")
        async with client:
            pass
        assert client._client is None


class TestLinearClientExecute:
    async def test_execute_success(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"viewer": {"id": "user-1"}}}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            result = await client._execute("query { viewer { id } }")
            assert result == {"viewer": {"id": "user-1"}}

    async def test_execute_auth_error(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            with pytest.raises(AuthenticationError, match="Invalid API key"):
                await client._execute("query { viewer { id } }")

    async def test_execute_rate_limit_error(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.headers = {"Retry-After": "120"}
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            with pytest.raises(RateLimitError) as exc_info:
                await client._execute("query { viewer { id } }")
            assert exc_info.value.retry_after == 120

    async def test_execute_rate_limit_default_retry(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.headers = {}
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            with pytest.raises(RateLimitError) as exc_info:
                await client._execute("query { viewer { id } }")
            assert exc_info.value.retry_after == 60

    async def test_execute_bad_request(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"errors": [{"message": "Invalid field"}]}
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            with pytest.raises(LinearClientError, match="Bad Request"):
                await client._execute("query { viewer { id } }")

    async def test_execute_graphql_error(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"errors": [{"message": "Field not found"}]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            with pytest.raises(LinearClientError, match="GraphQL error"):
                await client._execute("query { viewer { id } }")


class TestLinearClientGetViewer:
    async def test_get_viewer(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "viewer": {
                        "id": "user-123",
                        "name": "Test User",
                        "email": "test@example.com",
                        "displayName": "Tester",
                        "active": True,
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            user = await client.get_viewer()
            assert user is not None
            assert user.id == "user-123"
            assert user.name == "Test User"

    async def test_get_viewer_none(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"viewer": None}}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            user = await client.get_viewer()
            assert user is None


class TestLinearClientGetTeams:
    async def test_get_teams(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "teams": {
                        "nodes": [
                            {"id": "team-1", "name": "Engineering", "key": "ENG"},
                            {"id": "team-2", "name": "Product", "key": "PRD"},
                        ]
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            teams = await client.get_teams()
            assert len(teams) == 2
            assert teams[0].id == "team-1"
            assert teams[0].key == "ENG"

    async def test_get_teams_empty(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"teams": {"nodes": []}}}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            teams = await client.get_teams()
            assert len(teams) == 0


class TestLinearClientGetProjects:
    async def test_get_projects(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "projects": {
                        "nodes": [
                            {"id": "proj-1", "name": "Project A", "state": "started"},
                            {"id": "proj-2", "name": "Project B", "state": "planned"},
                        ],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            projects, cursor = await client.get_projects()
            assert len(projects) == 2
            assert projects[0].name == "Project A"
            assert cursor is None

    async def test_get_projects_with_pagination(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "projects": {
                        "nodes": [{"id": "proj-1", "name": "Project A"}],
                        "pageInfo": {"hasNextPage": True, "endCursor": "cursor-123"},
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            projects, cursor = await client.get_projects()
            assert len(projects) == 1
            assert cursor == "cursor-123"


class TestLinearClientGetCycles:
    async def test_get_cycles(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "cycles": {
                        "nodes": [
                            {"id": "cycle-1", "name": "Sprint 1", "number": 1, "isActive": True},
                            {"id": "cycle-2", "name": "Sprint 2", "number": 2, "isActive": False},
                        ],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            cycles, cursor = await client.get_cycles("team-1")
            assert len(cycles) == 2
            assert cycles[0].is_active is True


class TestLinearClientGetIssues:
    async def test_get_issues(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "issues": {
                        "nodes": [
                            {
                                "id": "issue-1",
                                "identifier": "ENG-1",
                                "title": "Test Issue",
                                "priority": 2,
                                "state": {
                                    "id": "s1",
                                    "name": "Todo",
                                    "type": "unstarted",
                                    "color": "#888",
                                },
                            }
                        ],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            issues, cursor = await client.get_issues()
            assert len(issues) == 1
            assert issues[0].identifier == "ENG-1"

    async def test_get_issues_with_filters(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "issues": {
                        "nodes": [],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            issues, _ = await client.get_issues(
                team_id="team-1",
                project_id="proj-1",
                assignee_id="user-1",
                priority=2,
            )
            assert len(issues) == 0


class TestLinearClientGetIssue:
    async def test_get_issue(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "issue": {
                        "id": "issue-123",
                        "identifier": "ENG-123",
                        "title": "Test Issue",
                        "description": "A description",
                        "comments": {"nodes": []},
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            issue = await client.get_issue("issue-123")
            assert issue is not None
            assert issue.identifier == "ENG-123"

    async def test_get_issue_not_found(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"issue": None}}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            issue = await client.get_issue("nonexistent")
            assert issue is None


class TestLinearClientCreateIssue:
    async def test_create_issue(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "issueCreate": {
                        "success": True,
                        "issue": {
                            "id": "issue-new",
                            "identifier": "ENG-999",
                            "title": "New Issue",
                        },
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            issue = await client.create_issue(
                team_id="team-1",
                title="New Issue",
                description="Description",
                priority=2,
            )
            assert issue is not None
            assert issue.identifier == "ENG-999"

    async def test_create_issue_failure(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {"issueCreate": {"success": False, "issue": None}}
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            issue = await client.create_issue(team_id="team-1", title="Test")
            assert issue is None


class TestLinearClientUpdateIssue:
    async def test_update_issue(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "issueUpdate": {
                        "success": True,
                        "issue": {
                            "id": "issue-1",
                            "identifier": "ENG-1",
                            "title": "Updated Title",
                        },
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            issue = await client.update_issue(issue_id="issue-1", title="Updated Title")
            assert issue is not None
            assert issue.title == "Updated Title"

    async def test_update_issue_no_changes(self):
        client = LinearClient("test_key")
        issue = await client.update_issue(issue_id="issue-1")
        assert issue is None


class TestLinearClientArchiveDelete:
    async def test_archive_issue(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"issueArchive": {"success": True}}}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            success = await client.archive_issue("issue-1")
            assert success is True

    async def test_delete_issue(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"issueDelete": {"success": True}}}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            success = await client.delete_issue("issue-1")
            assert success is True


class TestLinearClientComments:
    async def test_create_comment(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "commentCreate": {
                        "success": True,
                        "comment": {
                            "id": "comment-1",
                            "body": "Test comment",
                            "createdAt": "2024-01-15T10:00:00Z",
                        },
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            comment = await client.create_comment("issue-1", "Test comment")
            assert comment is not None
            assert comment.body == "Test comment"

    async def test_create_comment_with_parent(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "commentCreate": {
                        "success": True,
                        "comment": {
                            "id": "comment-2",
                            "body": "Reply",
                            "createdAt": "2024-01-15T10:00:00Z",
                            "parent": {"id": "comment-1"},
                        },
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            comment = await client.create_comment("issue-1", "Reply", parent_id="comment-1")
            assert comment is not None
            assert comment.parent_id == "comment-1"

    async def test_get_comments(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "issue": {
                        "comments": {
                            "nodes": [
                                {
                                    "id": "c1",
                                    "body": "First",
                                    "createdAt": "2024-01-15T10:00:00Z",
                                },
                                {
                                    "id": "c2",
                                    "body": "Second",
                                    "createdAt": "2024-01-15T11:00:00Z",
                                },
                            ]
                        }
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            comments = await client.get_comments("issue-1")
            assert len(comments) == 2


class TestLinearClientSearch:
    async def test_search_issues(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "searchIssues": {
                        "nodes": [
                            {"id": "i1", "identifier": "ENG-1", "title": "Auth bug"},
                            {"id": "i2", "identifier": "ENG-2", "title": "Auth feature"},
                        ]
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            issues = await client.search_issues("auth")
            assert len(issues) == 2


class TestLinearClientWorkflowStates:
    async def test_get_workflow_states(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "workflowStates": {
                        "nodes": [
                            {
                                "id": "s1",
                                "name": "Backlog",
                                "color": "#888",
                                "type": "backlog",
                                "position": 0,
                            },
                            {
                                "id": "s2",
                                "name": "Todo",
                                "color": "#888",
                                "type": "unstarted",
                                "position": 1,
                            },
                            {
                                "id": "s3",
                                "name": "In Progress",
                                "color": "#0f0",
                                "type": "started",
                                "position": 2,
                            },
                        ]
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            states = await client.get_workflow_states("team-1")
            assert len(states) == 3
            assert states[0].name == "Backlog"
            assert states[2].position == 2


class TestLinearClientLabels:
    async def test_get_labels(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "issueLabels": {
                        "nodes": [
                            {"id": "l1", "name": "Bug", "color": "#f00"},
                            {"id": "l2", "name": "Feature", "color": "#0f0"},
                        ]
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            labels = await client.get_labels()
            assert len(labels) == 2
            assert labels[0].name == "Bug"


class TestLinearClientUsers:
    async def test_get_users(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "users": {
                        "nodes": [
                            {
                                "id": "u1",
                                "name": "Alice",
                                "email": "alice@test.com",
                                "active": True,
                            },
                            {"id": "u2", "name": "Bob", "email": "bob@test.com", "active": True},
                        ]
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            users = await client.get_users()
            assert len(users) == 2
            assert users[0].name == "Alice"


class TestLinearClientHistory:
    async def test_get_issue_history(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "issue": {
                        "history": {
                            "nodes": [
                                {
                                    "id": "h1",
                                    "createdAt": "2024-01-15T10:00:00Z",
                                    "fromPriority": 3,
                                    "toPriority": 1,
                                }
                            ]
                        }
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            history = await client.get_issue_history("issue-1")
            assert len(history) == 1
            assert history[0].changes is not None
            assert history[0].changes["priority"]["from"] == 3

    async def test_get_issue_history_error_returns_empty(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"errors": [{"message": "Error"}]}
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            history = await client.get_issue_history("issue-1")
            assert history == []


class TestLinearClientFavorites:
    async def test_get_favorites(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "favorites": {
                        "nodes": [
                            {
                                "id": "fav-1",
                                "type": "issue",
                                "issue": {
                                    "id": "issue-1",
                                    "identifier": "ENG-1",
                                    "title": "Test Issue",
                                },
                            },
                            {
                                "id": "fav-2",
                                "type": "issue",
                                "issue": {
                                    "id": "issue-2",
                                    "identifier": "ENG-2",
                                    "title": "Another Issue",
                                },
                            },
                        ]
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            favorites = await client.get_favorites()
            assert len(favorites) == 2
            assert favorites[0].id == "fav-1"
            assert favorites[0].issue_id == "issue-1"
            assert favorites[0].issue_identifier == "ENG-1"

    async def test_get_favorites_filters_non_issue_types(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {
                    "favorites": {
                        "nodes": [
                            {
                                "id": "fav-1",
                                "type": "issue",
                                "issue": {
                                    "id": "issue-1",
                                    "identifier": "ENG-1",
                                    "title": "Test Issue",
                                },
                            },
                            {
                                "id": "fav-2",
                                "type": "project",
                                "project": {"id": "proj-1", "name": "Project"},
                            },
                        ]
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            favorites = await client.get_favorites()
            assert len(favorites) == 1
            assert favorites[0].issue_identifier == "ENG-1"

    async def test_add_favorite(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {"favoriteCreate": {"success": True, "favorite": {"id": "fav-new"}}}
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            favorite_id = await client.add_favorite("issue-1")
            assert favorite_id == "fav-new"

    async def test_add_favorite_failure(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {"favoriteCreate": {"success": False, "favorite": None}}
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            favorite_id = await client.add_favorite("issue-1")
            assert favorite_id is None

    async def test_remove_favorite(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"favoriteDelete": {"success": True}}}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            success = await client.remove_favorite("fav-1")
            assert success is True

    async def test_remove_favorite_failure(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"favoriteDelete": {"success": False}}}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            client = LinearClient("test_key")
            success = await client.remove_favorite("fav-1")
            assert success is False


class TestLinearClientClose:
    async def test_close(self):
        client = LinearClient("test_key")
        _ = client.client
        assert client._client is not None
        await client.close()
        assert client._client is None

    async def test_close_no_client(self):
        client = LinearClient("test_key")
        await client.close()
        assert client._client is None
