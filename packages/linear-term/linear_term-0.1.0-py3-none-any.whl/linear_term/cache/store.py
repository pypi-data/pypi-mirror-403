"""SQLite-based cache for Linear data."""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from linear_term.api.models import (
    Cycle,
    Issue,
    IssueLabel,
    Project,
    Team,
    User,
    WorkflowState,
)


class CacheStore:
    """SQLite cache for storing Linear entities."""

    def __init__(self, cache_dir: Path, ttl_minutes: int = 60):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "cache.db"
        self.ttl = timedelta(minutes=ttl_minutes)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    parent_id TEXT,
                    data TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (entity_type, entity_id, parent_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_type
                ON cache(entity_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_parent
                ON cache(entity_type, parent_id)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recent_issues (
                    issue_id TEXT PRIMARY KEY,
                    identifier TEXT NOT NULL,
                    title TEXT NOT NULL,
                    accessed_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_recent_accessed
                ON recent_issues(accessed_at DESC)
            """)
            conn.commit()

    def _is_stale(self, updated_at: str) -> bool:
        """Check if a cache entry is stale."""
        try:
            updated = datetime.fromisoformat(updated_at)
            return datetime.now() - updated > self.ttl
        except (ValueError, TypeError):
            return True

    def _save_entities(
        self,
        entity_type: str,
        entities: list[Any],
        parent_id: str | None = None,
    ) -> None:
        """Save entities to cache."""
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now().isoformat()
            parent = parent_id or ""
            # Clear old entries for this type/parent
            conn.execute(
                "DELETE FROM cache WHERE entity_type = ? AND parent_id = ?",
                (entity_type, parent),
            )
            for entity in entities:
                data = json.dumps(self._entity_to_dict(entity))
                conn.execute(
                    """
                    INSERT OR REPLACE INTO cache
                    (entity_type, entity_id, parent_id, data, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (entity_type, entity.id, parent, data, now),
                )
            conn.commit()

    def _load_entities(
        self,
        entity_type: str,
        from_dict_fn: Any,
        parent_id: str | None = None,
    ) -> list[Any]:
        """Load entities from cache."""
        with sqlite3.connect(self.db_path) as conn:
            parent = parent_id or ""
            cursor = conn.execute(
                """
                SELECT data, updated_at FROM cache
                WHERE entity_type = ? AND parent_id = ?
                """,
                (entity_type, parent),
            )
            entities = []
            for row in cursor.fetchall():
                data_str, updated_at = row
                if self._is_stale(updated_at):
                    continue
                try:
                    data = json.loads(data_str)
                    entity = from_dict_fn(data)
                    if entity:
                        entities.append(entity)
                except (json.JSONDecodeError, KeyError):
                    continue
            return entities

    def _entity_to_dict(self, entity: Any) -> dict[str, Any]:
        """Convert an entity to a dictionary for storage."""
        if hasattr(entity, "__dict__"):
            result = {}
            for key, value in entity.__dict__.items():
                if key.startswith("_"):
                    continue
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                elif isinstance(value, list):
                    result[key] = [self._entity_to_dict(v) for v in value]
                elif hasattr(value, "__dict__"):
                    result[key] = self._entity_to_dict(value)
                else:
                    result[key] = value
            return result
        return entity

    # Team methods
    def save_teams(self, teams: list[Team]) -> None:
        """Save teams to cache."""
        self._save_entities("teams", teams)

    def get_teams(self) -> list[Team]:
        """Get teams from cache."""
        return self._load_entities("teams", Team.from_dict)

    # Project methods
    def save_projects(self, projects: list[Project]) -> None:
        """Save projects to cache."""
        self._save_entities("projects", projects)

    def get_projects(self) -> list[Project]:
        """Get projects from cache."""
        return self._load_entities("projects", Project.from_dict)

    # User methods
    def save_users(self, users: list[User]) -> None:
        """Save users to cache."""
        self._save_entities("users", users)

    def get_users(self) -> list[User]:
        """Get users from cache."""
        return self._load_entities("users", User.from_dict)

    # Label methods
    def save_labels(self, labels: list[IssueLabel]) -> None:
        """Save labels to cache."""
        self._save_entities("labels", labels)

    def get_labels(self) -> list[IssueLabel]:
        """Get labels from cache."""
        return self._load_entities("labels", IssueLabel.from_dict)

    # Cycle methods
    def save_cycles(self, cycles: list[Cycle], team_id: str) -> None:
        """Save cycles to cache for a team."""
        self._save_entities("cycles", cycles, parent_id=team_id)

    def get_cycles(self, team_id: str) -> list[Cycle]:
        """Get cycles from cache for a team."""
        return self._load_entities("cycles", Cycle.from_dict, parent_id=team_id)

    # Workflow state methods
    def save_workflow_states(self, states: list[WorkflowState], team_id: str) -> None:
        """Save workflow states to cache for a team."""
        self._save_entities("workflow_states", states, parent_id=team_id)

    def get_workflow_states(self, team_id: str) -> list[WorkflowState]:
        """Get workflow states from cache for a team."""
        return self._load_entities("workflow_states", WorkflowState.from_dict, parent_id=team_id)

    # Issue methods
    def save_issues(self, issues: list[Issue]) -> None:
        """Save issues to cache."""
        self._save_entities("issues", issues)

    def get_issues(self) -> list[Issue]:
        """Get issues from cache."""
        return self._load_entities("issues", Issue.from_dict)

    def delete_issue(self, issue_id: str) -> None:
        """Delete an issue from cache."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM cache WHERE entity_type = ? AND entity_id = ?",
                ("issues", issue_id),
            )
            conn.commit()

    def clear(self) -> None:
        """Clear all cached data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cache")
            conn.commit()

    def add_recent_issue(self, issue_id: str, identifier: str, title: str, limit: int = 5) -> None:
        """Add or update an issue in recent history."""
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now().isoformat()
            conn.execute(
                """
                INSERT OR REPLACE INTO recent_issues
                (issue_id, identifier, title, accessed_at)
                VALUES (?, ?, ?, ?)
                """,
                (issue_id, identifier, title, now),
            )
            conn.execute(
                """
                DELETE FROM recent_issues
                WHERE issue_id NOT IN (
                    SELECT issue_id FROM recent_issues
                    ORDER BY accessed_at DESC
                    LIMIT ?
                )
                """,
                (limit,),
            )
            conn.commit()

    def get_recent_issues(self, limit: int = 5) -> list[tuple[str, str, str]]:
        """Get recently viewed issues."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT issue_id, identifier, title FROM recent_issues
                ORDER BY accessed_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            return cursor.fetchall()

    def clear_recent_issues(self) -> None:
        """Clear all recent issues history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM recent_issues")
            conn.commit()
