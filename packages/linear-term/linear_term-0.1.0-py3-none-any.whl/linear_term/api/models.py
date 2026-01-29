"""Data models for Linear API entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class User:
    """Linear user model."""

    id: str
    name: str
    email: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    active: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "User | None":
        if not data:
            return None
        return cls(
            id=data["id"],
            name=data.get("name", "Unknown"),
            email=data.get("email"),
            display_name=data.get("displayName") or data.get("display_name"),
            avatar_url=data.get("avatarUrl") or data.get("avatar_url"),
            active=data.get("active", True),
        )


@dataclass
class WorkflowState:
    """Linear workflow state model."""

    id: str
    name: str
    color: str
    type: str
    position: float = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "WorkflowState | None":
        if not data:
            return None
        return cls(
            id=data["id"],
            name=data.get("name", "Unknown"),
            color=data.get("color", "#888888"),
            type=data.get("type", "unstarted"),
            position=data.get("position", 0),
        )


@dataclass
class IssueLabel:
    """Linear issue label model."""

    id: str
    name: str
    color: str
    description: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "IssueLabel | None":
        if not data:
            return None
        return cls(
            id=data["id"],
            name=data.get("name", "Unknown"),
            color=data.get("color", "#888888"),
            description=data.get("description"),
        )


@dataclass
class Team:
    """Linear team model."""

    id: str
    name: str
    key: str
    description: str | None = None
    color: str | None = None
    icon: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Team | None":
        if not data:
            return None
        return cls(
            id=data["id"],
            name=data.get("name", "Unknown"),
            key=data.get("key", "???"),
            description=data.get("description"),
            color=data.get("color"),
            icon=data.get("icon"),
        )


@dataclass
class Project:
    """Linear project model."""

    id: str
    name: str
    description: str | None = None
    color: str | None = None
    icon: str | None = None
    state: str = "planned"
    progress: float = 0
    target_date: datetime | None = None
    start_date: datetime | None = None
    lead: User | None = None
    issue_count: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Project | None":
        if not data:
            return None
        return cls(
            id=data["id"],
            name=data.get("name", "Unknown"),
            description=data.get("description"),
            color=data.get("color"),
            icon=data.get("icon"),
            state=data.get("state", "planned"),
            progress=data.get("progress", 0),
            target_date=_parse_datetime(data.get("targetDate") or data.get("target_date")),
            start_date=_parse_datetime(data.get("startDate") or data.get("start_date")),
            lead=User.from_dict(data.get("lead")),
            issue_count=data.get("issue_count", 0),
        )


@dataclass
class Cycle:
    """Linear cycle model."""

    id: str
    name: str | None
    number: int
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    progress: float = 0
    completed_issue_count: int = 0
    total_issue_count: int = 0
    is_active: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Cycle | None":
        if not data:
            return None
        return cls(
            id=data["id"],
            name=data.get("name"),
            number=data.get("number", 0),
            starts_at=_parse_datetime(data.get("startsAt") or data.get("starts_at")),
            ends_at=_parse_datetime(data.get("endsAt") or data.get("ends_at")),
            progress=data.get("progress", 0),
            completed_issue_count=data.get("completed_issue_count", 0),
            total_issue_count=data.get("total_issue_count", 0),
            is_active=data.get("isActive") or data.get("is_active", False),
        )

    @property
    def display_name(self) -> str:
        """Get display name for the cycle."""
        if self.name:
            return self.name
        return f"Cycle {self.number}"


@dataclass
class Comment:
    """Linear comment model."""

    id: str
    body: str
    created_at: datetime
    updated_at: datetime | None = None
    user: User | None = None
    parent_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Comment | None":
        if not data:
            return None
        parent_data = data.get("parent")
        if isinstance(parent_data, dict):
            parent_id = parent_data.get("id")
        else:
            parent_id = data.get("parent_id")
        return cls(
            id=data["id"],
            body=data.get("body", ""),
            created_at=_parse_datetime(data.get("createdAt") or data.get("created_at"))
            or datetime.now(),
            updated_at=_parse_datetime(data.get("updatedAt") or data.get("updated_at")),
            user=User.from_dict(data.get("user")),
            parent_id=parent_id,
        )


@dataclass
class IssueHistory:
    """Linear issue history/activity model."""

    id: str
    created_at: datetime
    actor: User | None = None
    from_priority: int | None = None
    to_priority: int | None = None
    changes: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "IssueHistory | None":
        if not data:
            return None

        changes = {}

        if data.get("fromTitle") or data.get("toTitle"):
            changes["title"] = {
                "from": data.get("fromTitle"),
                "to": data.get("toTitle"),
            }
        if data.get("fromPriority") is not None or data.get("toPriority") is not None:
            changes["priority"] = {
                "from": data.get("fromPriority"),
                "to": data.get("toPriority"),
            }
        if data.get("fromEstimate") is not None or data.get("toEstimate") is not None:
            changes["estimate"] = {
                "from": data.get("fromEstimate"),
                "to": data.get("toEstimate"),
            }
        if data.get("fromDueDate") or data.get("toDueDate"):
            changes["dueDate"] = {
                "from": data.get("fromDueDate"),
                "to": data.get("toDueDate"),
            }
        added_label_ids = data.get("addedLabelIds") or []
        removed_label_ids = data.get("removedLabelIds") or []
        # Also handle addedLabels/removedLabels with nodes structure
        added_labels_nodes = data.get("addedLabels", {}).get("nodes") or []
        removed_labels_nodes = data.get("removedLabels", {}).get("nodes") or []
        added_label_names = [n.get("name") for n in added_labels_nodes if n.get("name")]
        removed_label_names = [n.get("name") for n in removed_labels_nodes if n.get("name")]
        if added_label_ids or removed_label_ids or added_label_names or removed_label_names:
            changes["labels"] = {
                "added_count": len(added_label_ids) or len(added_label_names),
                "removed_count": len(removed_label_ids) or len(removed_label_names),
                "added": added_label_names,
                "removed": removed_label_names,
            }
        if data.get("fromState") or data.get("toState"):
            from_state = data.get("fromState") or {}
            to_state = data.get("toState") or {}
            changes["state"] = {
                "from": from_state.get("name"),
                "to": to_state.get("name"),
            }
        if data.get("fromAssignee") or data.get("toAssignee"):
            from_assignee = data.get("fromAssignee") or {}
            to_assignee = data.get("toAssignee") or {}
            changes["assignee"] = {
                "from": from_assignee.get("displayName") or from_assignee.get("name"),
                "to": to_assignee.get("displayName") or to_assignee.get("name"),
            }
        if data.get("fromCycle") or data.get("toCycle"):
            from_cycle = data.get("fromCycle") or {}
            to_cycle = data.get("toCycle") or {}
            from_cycle_name = from_cycle.get("name")
            if not from_cycle_name and from_cycle.get("number"):
                from_cycle_name = f"Cycle {from_cycle.get('number')}"
            to_cycle_name = to_cycle.get("name")
            if not to_cycle_name and to_cycle.get("number"):
                to_cycle_name = f"Cycle {to_cycle.get('number')}"
            changes["cycle"] = {
                "from": from_cycle_name,
                "to": to_cycle_name,
            }
        if data.get("fromProject") or data.get("toProject"):
            from_project = data.get("fromProject") or {}
            to_project = data.get("toProject") or {}
            changes["project"] = {
                "from": from_project.get("name"),
                "to": to_project.get("name"),
            }
        if data.get("fromParent") or data.get("toParent"):
            from_parent = data.get("fromParent") or {}
            to_parent = data.get("toParent") or {}
            changes["parent"] = {
                "from": from_parent.get("identifier"),
                "to": to_parent.get("identifier"),
            }

        return cls(
            id=data["id"],
            created_at=_parse_datetime(data.get("createdAt")) or datetime.now(),
            actor=User.from_dict(data.get("actor")),
            from_priority=data.get("fromPriority"),
            to_priority=data.get("toPriority"),
            changes=changes if changes else None,
        )

    def describe(self) -> str:
        """Get a human-readable description of the change."""
        parts = []
        if self.changes:
            if "state" in self.changes:
                c = self.changes["state"]
                from_s = c["from"] or "None"
                to_s = c["to"] or "None"
                parts.append(f"Status: {from_s} → {to_s}")
            if "assignee" in self.changes:
                c = self.changes["assignee"]
                from_a = c["from"] or "Unassigned"
                to_a = c["to"] or "Unassigned"
                parts.append(f"Assignee: {from_a} → {to_a}")
            if "priority" in self.changes:
                c = self.changes["priority"]
                priorities = ["No Priority", "Urgent", "High", "Medium", "Low"]
                from_val = c["from"]
                to_val = c["to"]
                valid_from = from_val is not None and 0 <= from_val <= 4
                valid_to = to_val is not None and 0 <= to_val <= 4
                from_p = priorities[from_val] if valid_from else "None"
                to_p = priorities[to_val] if valid_to else "None"
                parts.append(f"Priority: {from_p} → {to_p}")
            if "title" in self.changes:
                parts.append("Title changed")
            if "estimate" in self.changes:
                c = self.changes["estimate"]
                parts.append(f"Estimate: {c['from'] or 'None'} → {c['to'] or 'None'}")
            if "dueDate" in self.changes:
                parts.append("Due date changed")
            if "cycle" in self.changes:
                c = self.changes["cycle"]
                from_c = c["from"] or "None"
                to_c = c["to"] or "None"
                parts.append(f"Cycle: {from_c} → {to_c}")
            if "project" in self.changes:
                c = self.changes["project"]
                from_p = c["from"] or "None"
                to_p = c["to"] or "None"
                parts.append(f"Project: {from_p} → {to_p}")
            if "parent" in self.changes:
                c = self.changes["parent"]
                from_p = c["from"] or "None"
                to_p = c["to"] or "None"
                parts.append(f"Parent: {from_p} → {to_p}")
            if "labels" in self.changes:
                c = self.changes["labels"]
                added_names = c.get("added") or []
                removed_names = c.get("removed") or []
                if added_names:
                    parts.append(f"Added labels: {', '.join(added_names)}")
                elif c.get("added_count"):
                    parts.append(f"Added {c['added_count']} label(s)")
                if removed_names:
                    parts.append(f"Removed labels: {', '.join(removed_names)}")
                elif c.get("removed_count"):
                    parts.append(f"Removed {c['removed_count']} label(s)")
        return " | ".join(parts) if parts else "Updated"


@dataclass
class Favorite:
    """Linear favorite model."""

    id: str
    issue_id: str
    issue_identifier: str
    issue_title: str

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Favorite | None":
        if not data:
            return None
        # Only handle issue favorites
        if data.get("type") != "issue":
            return None
        issue_data = data.get("issue")
        if not issue_data:
            return None
        return cls(
            id=data["id"],
            issue_id=issue_data["id"],
            issue_identifier=issue_data.get("identifier", "???"),
            issue_title=issue_data.get("title", "Untitled"),
        )


@dataclass
class Issue:
    """Linear issue model."""

    id: str
    identifier: str
    title: str
    description: str | None = None
    priority: int = 0
    priority_label: str = "No Priority"
    estimate: float | None = None
    due_date: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    canceled_at: datetime | None = None
    started_at: datetime | None = None
    state: WorkflowState | None = None
    assignee: User | None = None
    creator: User | None = None
    team: Team | None = None
    project: Project | None = None
    cycle: Cycle | None = None
    parent: "Issue | None" = None
    labels: list[IssueLabel] = field(default_factory=list)
    children: list["Issue"] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    url: str | None = None
    branch_name: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Issue | None":
        if not data:
            return None

        labels = []
        labels_data = data.get("labels")
        if labels_data:
            if isinstance(labels_data, dict) and labels_data.get("nodes"):
                labels_data = labels_data["nodes"]
            if isinstance(labels_data, list):
                labels = [IssueLabel.from_dict(lbl) for lbl in labels_data if lbl is not None]
                labels = [lbl for lbl in labels if lbl is not None]

        children = []
        children_data = data.get("children")
        if children_data:
            if isinstance(children_data, dict) and children_data.get("nodes"):
                children_data = children_data["nodes"]
            if isinstance(children_data, list):
                children = [Issue.from_dict(c) for c in children_data if c is not None]
                children = [c for c in children if c is not None]

        comments = []
        comments_data = data.get("comments")
        if comments_data:
            if isinstance(comments_data, dict) and comments_data.get("nodes"):
                comments_data = comments_data["nodes"]
            if isinstance(comments_data, list):
                comments = [Comment.from_dict(c) for c in comments_data if c is not None]
                comments = [c for c in comments if c is not None]

        parent = None
        if data.get("parent"):
            parent = Issue.from_dict(data["parent"])

        return cls(
            id=data["id"],
            identifier=data.get("identifier", "???"),
            title=data.get("title", "Untitled"),
            description=data.get("description"),
            priority=data.get("priority", 0),
            priority_label=data.get("priorityLabel") or data.get("priority_label", "No Priority"),
            estimate=data.get("estimate"),
            due_date=_parse_datetime(data.get("dueDate") or data.get("due_date")),
            created_at=_parse_datetime(data.get("createdAt") or data.get("created_at")),
            updated_at=_parse_datetime(data.get("updatedAt") or data.get("updated_at")),
            completed_at=_parse_datetime(data.get("completedAt") or data.get("completed_at")),
            canceled_at=_parse_datetime(data.get("canceledAt") or data.get("canceled_at")),
            started_at=_parse_datetime(data.get("startedAt") or data.get("started_at")),
            state=WorkflowState.from_dict(data.get("state")),
            assignee=User.from_dict(data.get("assignee")),
            creator=User.from_dict(data.get("creator")),
            team=Team.from_dict(data.get("team")),
            project=Project.from_dict(data.get("project")),
            cycle=Cycle.from_dict(data.get("cycle")),
            parent=parent,
            labels=labels,
            children=children,
            comments=comments,
            url=data.get("url"),
            branch_name=data.get("branchName") or data.get("branch_name"),
        )

    @property
    def status_icon(self) -> str:
        """Get ASCII status icon."""
        if not self.state:
            return "○"
        state_type = self.state.type.lower()
        if state_type == "triage":
            return "◇"
        elif state_type == "backlog":
            return "○"
        elif state_type == "unstarted":
            return "○"
        elif state_type == "started":
            return "●"
        elif state_type == "completed":
            return "✓"
        elif state_type == "canceled":
            return "⊗"
        return "○"

    @property
    def priority_icon(self) -> str:
        """Get priority indicator."""
        icons = {0: "---", 1: "!!!", 2: "!!", 3: "!", 4: "-"}
        return icons.get(self.priority, "---")


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse ISO datetime string."""
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
