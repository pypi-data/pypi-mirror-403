"""Tests for the cache store."""

import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from linear_term.api.models import (
    Cycle,
    Issue,
    IssueLabel,
    Project,
    Team,
    User,
    WorkflowState,
)
from linear_term.cache.store import CacheStore


@pytest.fixture
def cache_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def cache_store(cache_dir):
    return CacheStore(cache_dir, ttl_minutes=60)


class TestCacheStoreInit:
    def test_init_creates_directory(self, cache_dir):
        subdir = cache_dir / "subdir"
        _ = CacheStore(subdir)
        assert subdir.exists()

    def test_init_creates_database(self, cache_dir):
        _ = CacheStore(cache_dir)
        db_path = cache_dir / "cache.db"
        assert db_path.exists()

    def test_init_creates_table(self, cache_dir):
        _ = CacheStore(cache_dir)
        db_path = cache_dir / "cache.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='cache'"
            )
            result = cursor.fetchone()
            assert result is not None

    def test_custom_ttl(self, cache_dir):
        store = CacheStore(cache_dir, ttl_minutes=120)
        assert store.ttl == timedelta(minutes=120)


class TestCacheStoreTeams:
    def test_save_and_get_teams(self, cache_store):
        teams = [
            Team(id="t1", name="Engineering", key="ENG"),
            Team(id="t2", name="Product", key="PRD"),
        ]
        cache_store.save_teams(teams)

        loaded = cache_store.get_teams()
        assert len(loaded) == 2
        assert loaded[0].id == "t1"
        assert loaded[0].name == "Engineering"
        assert loaded[1].key == "PRD"

    def test_save_teams_replaces_old(self, cache_store):
        teams1 = [Team(id="t1", name="Old", key="OLD")]
        cache_store.save_teams(teams1)

        teams2 = [Team(id="t2", name="New", key="NEW")]
        cache_store.save_teams(teams2)

        loaded = cache_store.get_teams()
        assert len(loaded) == 1
        assert loaded[0].name == "New"


class TestCacheStoreProjects:
    def test_save_and_get_projects(self, cache_store):
        projects = [
            Project(id="p1", name="Alpha", state="started"),
            Project(id="p2", name="Beta", state="planned", progress=0.5),
        ]
        cache_store.save_projects(projects)

        loaded = cache_store.get_projects()
        assert len(loaded) == 2
        assert loaded[0].name == "Alpha"
        assert loaded[1].progress == 0.5

    def test_project_with_lead(self, cache_store):
        lead = User(id="u1", name="Alice")
        projects = [
            Project(id="p1", name="Project", lead=lead),
        ]
        cache_store.save_projects(projects)

        loaded = cache_store.get_projects()
        assert len(loaded) == 1
        assert loaded[0].lead is not None
        assert loaded[0].lead.name == "Alice"


class TestCacheStoreUsers:
    def test_save_and_get_users(self, cache_store):
        users = [
            User(id="u1", name="Alice", email="alice@test.com", active=True),
            User(id="u2", name="Bob", email="bob@test.com", active=False),
        ]
        cache_store.save_users(users)

        loaded = cache_store.get_users()
        assert len(loaded) == 2
        assert loaded[0].email == "alice@test.com"
        assert loaded[1].active is False


class TestCacheStoreLabels:
    def test_save_and_get_labels(self, cache_store):
        labels = [
            IssueLabel(id="l1", name="Bug", color="#ff0000"),
            IssueLabel(id="l2", name="Feature", color="#00ff00", description="New feature"),
        ]
        cache_store.save_labels(labels)

        loaded = cache_store.get_labels()
        assert len(loaded) == 2
        assert loaded[0].name == "Bug"
        assert loaded[1].description == "New feature"


class TestCacheStoreCycles:
    def test_save_and_get_cycles_with_team(self, cache_store):
        cycles = [
            Cycle(id="c1", name="Sprint 1", number=1, is_active=True),
            Cycle(id="c2", name="Sprint 2", number=2, is_active=False),
        ]
        cache_store.save_cycles(cycles, team_id="team-1")

        loaded = cache_store.get_cycles("team-1")
        assert len(loaded) == 2
        assert loaded[0].is_active is True

    def test_cycles_scoped_by_team(self, cache_store):
        cycles1 = [Cycle(id="c1", name="Team1 Sprint", number=1)]
        cycles2 = [Cycle(id="c2", name="Team2 Sprint", number=1)]

        cache_store.save_cycles(cycles1, team_id="team-1")
        cache_store.save_cycles(cycles2, team_id="team-2")

        loaded1 = cache_store.get_cycles("team-1")
        loaded2 = cache_store.get_cycles("team-2")

        assert len(loaded1) == 1
        assert loaded1[0].name == "Team1 Sprint"
        assert len(loaded2) == 1
        assert loaded2[0].name == "Team2 Sprint"


class TestCacheStoreWorkflowStates:
    def test_save_and_get_workflow_states(self, cache_store):
        states = [
            WorkflowState(id="s1", name="Backlog", color="#888", type="backlog", position=0),
            WorkflowState(id="s2", name="In Progress", color="#0f0", type="started", position=1),
        ]
        cache_store.save_workflow_states(states, team_id="team-1")

        loaded = cache_store.get_workflow_states("team-1")
        assert len(loaded) == 2
        assert loaded[0].type == "backlog"

    def test_workflow_states_scoped_by_team(self, cache_store):
        states1 = [WorkflowState(id="s1", name="Todo", color="#888", type="unstarted")]
        states2 = [WorkflowState(id="s2", name="Doing", color="#0f0", type="started")]

        cache_store.save_workflow_states(states1, team_id="team-1")
        cache_store.save_workflow_states(states2, team_id="team-2")

        loaded1 = cache_store.get_workflow_states("team-1")
        loaded2 = cache_store.get_workflow_states("team-2")

        assert len(loaded1) == 1
        assert loaded1[0].name == "Todo"
        assert loaded2[0].name == "Doing"


class TestCacheStoreIssues:
    def test_save_and_get_issues(self, cache_store):
        issues = [
            Issue(id="i1", identifier="ENG-1", title="Issue 1", priority=2),
            Issue(id="i2", identifier="ENG-2", title="Issue 2", priority=3),
        ]
        cache_store.save_issues(issues)

        loaded = cache_store.get_issues()
        assert len(loaded) == 2
        assert loaded[0].identifier == "ENG-1"

    def test_issue_with_nested_objects(self, cache_store):
        state = WorkflowState(id="s1", name="Todo", color="#888", type="unstarted")
        assignee = User(id="u1", name="Alice")
        team = Team(id="t1", name="Engineering", key="ENG")
        labels = [IssueLabel(id="l1", name="Bug", color="#f00")]

        issues = [
            Issue(
                id="i1",
                identifier="ENG-1",
                title="Issue",
                state=state,
                assignee=assignee,
                team=team,
                labels=labels,
            )
        ]
        cache_store.save_issues(issues)

        loaded = cache_store.get_issues()
        assert len(loaded) == 1
        assert loaded[0].state is not None
        assert loaded[0].state.name == "Todo"
        assert loaded[0].assignee is not None
        assert loaded[0].assignee.name == "Alice"
        assert loaded[0].team is not None
        assert len(loaded[0].labels) == 1

    def test_delete_issue(self, cache_store):
        issues = [
            Issue(id="i1", identifier="ENG-1", title="Issue 1"),
            Issue(id="i2", identifier="ENG-2", title="Issue 2"),
        ]
        cache_store.save_issues(issues)

        cache_store.delete_issue("i1")

        loaded = cache_store.get_issues()
        assert len(loaded) == 1
        assert loaded[0].id == "i2"

    def test_issue_with_dates(self, cache_store):
        now = datetime.now()
        issues = [
            Issue(
                id="i1",
                identifier="ENG-1",
                title="Issue",
                created_at=now,
                updated_at=now,
                due_date=now,
            )
        ]
        cache_store.save_issues(issues)

        loaded = cache_store.get_issues()
        assert len(loaded) == 1
        assert loaded[0].created_at is not None


class TestCacheStoreStaleness:
    def test_stale_entries_not_returned(self, cache_dir):
        store = CacheStore(cache_dir, ttl_minutes=1)

        teams = [Team(id="t1", name="Old", key="OLD")]
        store.save_teams(teams)

        db_path = cache_dir / "cache.db"
        old_time = (datetime.now() - timedelta(minutes=10)).isoformat()
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "UPDATE cache SET updated_at = ? WHERE entity_type = 'teams'",
                (old_time,),
            )
            conn.commit()

        loaded = store.get_teams()
        assert len(loaded) == 0

    def test_fresh_entries_returned(self, cache_store):
        teams = [Team(id="t1", name="Fresh", key="FRE")]
        cache_store.save_teams(teams)

        loaded = cache_store.get_teams()
        assert len(loaded) == 1

    def test_is_stale_invalid_timestamp(self, cache_store):
        assert cache_store._is_stale("invalid-timestamp") is True
        assert cache_store._is_stale(None) is True


class TestCacheStoreClear:
    def test_clear(self, cache_store):
        teams = [Team(id="t1", name="Team", key="TEM")]
        projects = [Project(id="p1", name="Project")]

        cache_store.save_teams(teams)
        cache_store.save_projects(projects)

        cache_store.clear()

        assert len(cache_store.get_teams()) == 0
        assert len(cache_store.get_projects()) == 0


class TestCacheStoreEntityToDict:
    def test_entity_to_dict_simple(self, cache_store):
        user = User(id="u1", name="Test", email="test@test.com")
        result = cache_store._entity_to_dict(user)

        assert result["id"] == "u1"
        assert result["name"] == "Test"
        assert result["email"] == "test@test.com"

    def test_entity_to_dict_with_datetime(self, cache_store):
        now = datetime.now()
        project = Project(id="p1", name="Project", start_date=now)
        result = cache_store._entity_to_dict(project)

        assert "start_date" in result
        assert isinstance(result["start_date"], str)

    def test_entity_to_dict_with_nested(self, cache_store):
        lead = User(id="u1", name="Lead")
        project = Project(id="p1", name="Project", lead=lead)
        result = cache_store._entity_to_dict(project)

        assert "lead" in result
        assert result["lead"]["name"] == "Lead"

    def test_entity_to_dict_with_list(self, cache_store):
        labels = [
            IssueLabel(id="l1", name="Bug", color="#f00"),
            IssueLabel(id="l2", name="Feature", color="#0f0"),
        ]
        issue = Issue(id="i1", identifier="ENG-1", title="Test", labels=labels)
        result = cache_store._entity_to_dict(issue)

        assert "labels" in result
        assert len(result["labels"]) == 2
        assert result["labels"][0]["name"] == "Bug"

    def test_entity_to_dict_primitive(self, cache_store):
        assert cache_store._entity_to_dict("string") == "string"
        assert cache_store._entity_to_dict(123) == 123
        assert cache_store._entity_to_dict(None) is None


class TestCacheStoreLoadEntities:
    def test_load_entities_json_error(self, cache_store, cache_dir):
        db_path = cache_dir / "cache.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT INTO cache (entity_type, entity_id, parent_id, data, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("test", "1", "", "invalid json", datetime.now().isoformat()),
            )
            conn.commit()

        loaded = cache_store._load_entities("test", Team.from_dict)
        assert len(loaded) == 0

    def test_load_entities_key_error(self, cache_store, cache_dir):
        db_path = cache_dir / "cache.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT INTO cache (entity_type, entity_id, parent_id, data, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("test", "1", "", "{}", datetime.now().isoformat()),
            )
            conn.commit()

        loaded = cache_store._load_entities("test", Team.from_dict)
        assert len(loaded) == 0


class TestCacheStoreEdgeCases:
    def test_empty_list(self, cache_store):
        cache_store.save_teams([])
        loaded = cache_store.get_teams()
        assert len(loaded) == 0

    def test_special_characters_in_data(self, cache_store):
        teams = [Team(id="t1", name="Team with 'quotes' and \"double quotes\"", key="TEM")]
        cache_store.save_teams(teams)

        loaded = cache_store.get_teams()
        assert len(loaded) == 1
        assert "quotes" in loaded[0].name

    def test_unicode_in_data(self, cache_store):
        teams = [Team(id="t1", name="Team with unicode: \u00e9\u00e8\u00ea\u4e2d\u6587", key="UNI")]
        cache_store.save_teams(teams)

        loaded = cache_store.get_teams()
        assert len(loaded) == 1
        assert "\u00e9" in loaded[0].name


class TestRecentIssues:
    def test_add_and_get_recent_issues(self, cache_store):
        cache_store.add_recent_issue("i1", "ENG-1", "First issue")
        cache_store.add_recent_issue("i2", "ENG-2", "Second issue")

        recent = cache_store.get_recent_issues()
        assert len(recent) == 2
        assert recent[0] == ("i2", "ENG-2", "Second issue")
        assert recent[1] == ("i1", "ENG-1", "First issue")

    def test_recent_issues_update_timestamp(self, cache_store):
        cache_store.add_recent_issue("i1", "ENG-1", "First issue")
        cache_store.add_recent_issue("i2", "ENG-2", "Second issue")
        cache_store.add_recent_issue("i1", "ENG-1", "First issue updated")

        recent = cache_store.get_recent_issues()
        assert len(recent) == 2
        assert recent[0][0] == "i1"
        assert recent[0][2] == "First issue updated"

    def test_recent_issues_limit(self, cache_store):
        for i in range(20):
            cache_store.add_recent_issue(f"i{i}", f"ENG-{i}", f"Issue {i}", limit=5)

        recent = cache_store.get_recent_issues()
        assert len(recent) == 5
        assert recent[0][0] == "i19"

    def test_recent_issues_get_limit(self, cache_store):
        for i in range(10):
            cache_store.add_recent_issue(f"i{i}", f"ENG-{i}", f"Issue {i}", limit=10)

        recent = cache_store.get_recent_issues(limit=3)
        assert len(recent) == 3
        assert recent[0][0] == "i9"

    def test_clear_recent_issues(self, cache_store):
        cache_store.add_recent_issue("i1", "ENG-1", "First issue")
        cache_store.add_recent_issue("i2", "ENG-2", "Second issue")

        cache_store.clear_recent_issues()

        recent = cache_store.get_recent_issues()
        assert len(recent) == 0

    def test_recent_issues_empty(self, cache_store):
        recent = cache_store.get_recent_issues()
        assert len(recent) == 0

    def test_recent_issues_special_characters(self, cache_store):
        cache_store.add_recent_issue("i1", "ENG-1", "Issue with 'quotes' and \"double quotes\"")
        cache_store.add_recent_issue("i2", "ENG-2", "Issue with unicode: \u00e9\u4e2d\u6587")

        recent = cache_store.get_recent_issues()
        assert len(recent) == 2
        assert "quotes" in recent[1][2]
        assert "\u00e9" in recent[0][2]

    def test_recent_issues_table_created(self, cache_dir):
        import sqlite3

        _ = CacheStore(cache_dir)
        db_path = cache_dir / "cache.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='recent_issues'"
            )
            result = cursor.fetchone()
            assert result is not None
