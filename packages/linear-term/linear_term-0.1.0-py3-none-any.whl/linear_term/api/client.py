"""Linear GraphQL API client."""

from typing import Any

import httpx

from linear_term.api.models import (
    Comment,
    Cycle,
    Favorite,
    Issue,
    IssueHistory,
    IssueLabel,
    Project,
    Team,
    User,
    WorkflowState,
)

LINEAR_API_URL = "https://api.linear.app/graphql"


class LinearClientError(Exception):
    """Base exception for Linear client errors."""

    pass


class AuthenticationError(LinearClientError):
    """Authentication failed."""

    pass


class RateLimitError(LinearClientError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after {retry_after} seconds.")


class LinearClient:
    """Async client for Linear GraphQL API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "LinearClient":
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": self.api_key,
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def _execute(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GraphQL query."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = await self.client.post(LINEAR_API_URL, json=payload)

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(retry_after)

        if response.status_code == 400:
            error_detail = ""
            try:
                error_data = response.json()
                if "errors" in error_data:
                    error_msgs = [e.get("message", "Unknown") for e in error_data["errors"]]
                    query_name = "unknown"
                    if query:
                        query_name = query.strip().split("{")[0].strip().split()[-1]
                    error_detail = f" - GraphQL error in {query_name}: {'; '.join(error_msgs)}"
            except (ValueError, KeyError):
                pass
            raise LinearClientError(f"Bad Request (400){error_detail}")

        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            error_msg = data["errors"][0].get("message", "Unknown error")
            raise LinearClientError(f"GraphQL error: {error_msg}")

        return data.get("data", {})

    async def get_viewer(self) -> User | None:
        """Get the authenticated user."""
        query = """
        query Viewer {
            viewer {
                id
                name
                email
                displayName
                avatarUrl
                active
            }
        }
        """
        data = await self._execute(query)
        return User.from_dict(data.get("viewer"))

    async def get_teams(self) -> list[Team]:
        """Get all teams the user has access to."""
        query = """
        query Teams {
            teams {
                nodes {
                    id
                    name
                    key
                    description
                    color
                    icon
                }
            }
        }
        """
        data = await self._execute(query)
        teams = []
        for node in data.get("teams", {}).get("nodes", []):
            team = Team.from_dict(node)
            if team:
                teams.append(team)
        return teams

    async def get_workflow_states(self, team_id: str) -> list[WorkflowState]:
        """Get workflow states for a team."""
        query = """
        query WorkflowStates($teamId: ID!) {
            workflowStates(filter: { team: { id: { eq: $teamId } } }) {
                nodes {
                    id
                    name
                    color
                    type
                    position
                }
            }
        }
        """
        data = await self._execute(query, {"teamId": team_id})
        states = []
        for node in data.get("workflowStates", {}).get("nodes", []):
            state = WorkflowState.from_dict(node)
            if state:
                states.append(state)
        return sorted(states, key=lambda s: s.position)

    async def get_projects(
        self,
        team_id: str | None = None,
        include_archived: bool = False,
        first: int = 50,
        after: str | None = None,
    ) -> tuple[list[Project], str | None]:
        """Get projects, optionally filtered by team."""
        query = """
        query Projects($first: Int!, $after: String, $includeArchived: Boolean) {
            projects(first: $first, after: $after, includeArchived: $includeArchived) {
                nodes {
                    id
                    name
                    description
                    color
                    icon
                    state
                    progress
                    targetDate
                    startDate
                    lead {
                        id
                        name
                        email
                        displayName
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        variables: dict[str, Any] = {
            "first": first,
            "includeArchived": include_archived,
        }
        if after:
            variables["after"] = after

        data = await self._execute(query, variables)
        projects = []
        for node in data.get("projects", {}).get("nodes", []):
            project = Project.from_dict(node)
            if project:
                projects.append(project)

        page_info = data.get("projects", {}).get("pageInfo", {})
        next_cursor = page_info.get("endCursor") if page_info.get("hasNextPage") else None

        return projects, next_cursor

    async def get_cycles(
        self,
        team_id: str,
        first: int = 20,
        after: str | None = None,
    ) -> tuple[list[Cycle], str | None]:
        """Get cycles for a team."""
        query = """
        query Cycles($teamId: ID!, $first: Int!, $after: String) {
            cycles(
                filter: { team: { id: { eq: $teamId } } }
                first: $first
                after: $after
            ) {
                nodes {
                    id
                    name
                    number
                    startsAt
                    endsAt
                    progress
                    isActive
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        variables: dict[str, Any] = {
            "teamId": team_id,
            "first": first,
        }
        if after:
            variables["after"] = after

        data = await self._execute(query, variables)
        cycles = []
        for node in data.get("cycles", {}).get("nodes", []):
            cycle = Cycle.from_dict(node)
            if cycle:
                cycles.append(cycle)

        page_info = data.get("cycles", {}).get("pageInfo", {})
        next_cursor = page_info.get("endCursor") if page_info.get("hasNextPage") else None

        return cycles, next_cursor

    async def get_labels(self, team_id: str | None = None) -> list[IssueLabel]:
        """Get issue labels."""
        query = """
        query Labels($first: Int!) {
            issueLabels(first: $first) {
                nodes {
                    id
                    name
                    color
                    description
                }
            }
        }
        """
        data = await self._execute(query, {"first": 100})
        labels = []
        for node in data.get("issueLabels", {}).get("nodes", []):
            label = IssueLabel.from_dict(node)
            if label:
                labels.append(label)
        return labels

    async def get_users(self) -> list[User]:
        """Get all users in the organization."""
        query = """
        query Users {
            users {
                nodes {
                    id
                    name
                    email
                    displayName
                    avatarUrl
                    active
                }
            }
        }
        """
        data = await self._execute(query)
        users = []
        for node in data.get("users", {}).get("nodes", []):
            user = User.from_dict(node)
            if user:
                users.append(user)
        return users

    async def get_issues(
        self,
        team_id: str | None = None,
        project_id: str | None = None,
        cycle_id: str | None = None,
        assignee_id: str | None = None,
        state_id: str | None = None,
        state_type: str | None = None,
        priority: int | None = None,
        label_ids: list[str] | None = None,
        include_archived: bool = False,
        first: int = 50,
        after: str | None = None,
        order_by: str = "updatedAt",
    ) -> tuple[list[Issue], str | None]:
        """Get issues with optional filters."""
        query = """
        query Issues(
            $first: Int!
            $after: String
            $includeArchived: Boolean
            $filter: IssueFilter
            $orderBy: PaginationOrderBy
        ) {
            issues(
                first: $first
                after: $after
                includeArchived: $includeArchived
                filter: $filter
                orderBy: $orderBy
            ) {
                nodes {
                    id
                    identifier
                    title
                    description
                    priority
                    priorityLabel
                    estimate
                    dueDate
                    createdAt
                    updatedAt
                    completedAt
                    canceledAt
                    startedAt
                    url
                    branchName
                    state {
                        id
                        name
                        color
                        type
                        position
                    }
                    assignee {
                        id
                        name
                        email
                        displayName
                    }
                    creator {
                        id
                        name
                        email
                        displayName
                    }
                    team {
                        id
                        name
                        key
                    }
                    project {
                        id
                        name
                        color
                        icon
                    }
                    cycle {
                        id
                        name
                        number
                    }
                    parent {
                        id
                        identifier
                        title
                    }
                    labels {
                        nodes {
                            id
                            name
                            color
                        }
                    }
                    children {
                        nodes {
                            id
                            identifier
                            title
                            createdAt
                            state {
                                id
                                name
                                color
                                type
                            }
                            priority
                            priorityLabel
                            assignee {
                                id
                                name
                                displayName
                            }
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        filter_obj: dict[str, Any] = {}
        if team_id:
            filter_obj["team"] = {"id": {"eq": team_id}}
        if project_id:
            filter_obj["project"] = {"id": {"eq": project_id}}
        if cycle_id:
            filter_obj["cycle"] = {"id": {"eq": cycle_id}}
        if assignee_id:
            filter_obj["assignee"] = {"id": {"eq": assignee_id}}
        if state_id:
            filter_obj["state"] = {"id": {"eq": state_id}}
        if state_type:
            filter_obj["state"] = {"type": {"eq": state_type}}
        if priority is not None:
            filter_obj["priority"] = {"eq": priority}
        if label_ids:
            filter_obj["labels"] = {"id": {"in": label_ids}}

        variables: dict[str, Any] = {
            "first": first,
            "includeArchived": include_archived,
            "orderBy": order_by,
        }
        if after:
            variables["after"] = after
        if filter_obj:
            variables["filter"] = filter_obj

        data = await self._execute(query, variables)
        issues = []
        for node in data.get("issues", {}).get("nodes", []):
            issue = Issue.from_dict(node)
            if issue:
                issues.append(issue)

        page_info = data.get("issues", {}).get("pageInfo", {})
        next_cursor = page_info.get("endCursor") if page_info.get("hasNextPage") else None

        return issues, next_cursor

    async def get_issue(self, issue_id: str) -> Issue | None:
        """Get a single issue by ID with full details."""
        query = """
        query Issue($id: String!) {
            issue(id: $id) {
                id
                identifier
                title
                description
                priority
                priorityLabel
                estimate
                dueDate
                createdAt
                updatedAt
                completedAt
                canceledAt
                startedAt
                url
                branchName
                state {
                    id
                    name
                    color
                    type
                    position
                }
                assignee {
                    id
                    name
                    email
                    displayName
                }
                creator {
                    id
                    name
                    email
                    displayName
                }
                team {
                    id
                    name
                    key
                }
                project {
                    id
                    name
                    color
                    icon
                }
                cycle {
                    id
                    name
                    number
                }
                parent {
                    id
                    identifier
                    title
                }
                labels {
                    nodes {
                        id
                        name
                        color
                    }
                }
                children {
                    nodes {
                        id
                        identifier
                        title
                        createdAt
                        state {
                            id
                            name
                            color
                            type
                        }
                        priority
                        priorityLabel
                        assignee {
                            id
                            name
                            displayName
                        }
                    }
                }
                comments {
                    nodes {
                        id
                        body
                        createdAt
                        updatedAt
                        user {
                            id
                            name
                            email
                            displayName
                        }
                        parent {
                            id
                        }
                    }
                }
            }
        }
        """
        data = await self._execute(query, {"id": issue_id})
        return Issue.from_dict(data.get("issue"))

    async def create_issue(
        self,
        team_id: str,
        title: str,
        description: str | None = None,
        priority: int | None = None,
        state_id: str | None = None,
        assignee_id: str | None = None,
        project_id: str | None = None,
        cycle_id: str | None = None,
        parent_id: str | None = None,
        label_ids: list[str] | None = None,
        estimate: float | None = None,
        due_date: str | None = None,
    ) -> Issue | None:
        """Create a new issue."""
        query = """
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    description
                    priority
                    priorityLabel
                    estimate
                    dueDate
                    createdAt
                    updatedAt
                    url
                    state {
                        id
                        name
                        color
                        type
                    }
                    assignee {
                        id
                        name
                        email
                        displayName
                    }
                    team {
                        id
                        name
                        key
                    }
                    project {
                        id
                        name
                    }
                    cycle {
                        id
                        name
                        number
                    }
                    labels {
                        nodes {
                            id
                            name
                            color
                        }
                    }
                }
            }
        }
        """
        input_obj: dict[str, Any] = {
            "teamId": team_id,
            "title": title,
        }
        if description is not None:
            input_obj["description"] = description
        if priority is not None:
            input_obj["priority"] = priority
        if state_id:
            input_obj["stateId"] = state_id
        if assignee_id:
            input_obj["assigneeId"] = assignee_id
        if project_id:
            input_obj["projectId"] = project_id
        if cycle_id:
            input_obj["cycleId"] = cycle_id
        if parent_id:
            input_obj["parentId"] = parent_id
        if label_ids:
            input_obj["labelIds"] = label_ids
        if estimate is not None:
            input_obj["estimate"] = estimate
        if due_date:
            input_obj["dueDate"] = due_date

        data = await self._execute(query, {"input": input_obj})
        result = data.get("issueCreate", {})
        if result.get("success"):
            return Issue.from_dict(result.get("issue"))
        return None

    async def update_issue(
        self,
        issue_id: str,
        title: str | None = None,
        description: str | None = None,
        priority: int | None = None,
        state_id: str | None = None,
        assignee_id: str | None = None,
        project_id: str | None = None,
        cycle_id: str | None = None,
        parent_id: str | None = None,
        label_ids: list[str] | None = None,
        estimate: float | None = None,
        due_date: str | None = None,
    ) -> Issue | None:
        """Update an existing issue."""
        query = """
        mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
            issueUpdate(id: $id, input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    description
                    priority
                    priorityLabel
                    estimate
                    dueDate
                    createdAt
                    updatedAt
                    url
                    state {
                        id
                        name
                        color
                        type
                    }
                    assignee {
                        id
                        name
                        email
                        displayName
                    }
                    team {
                        id
                        name
                        key
                    }
                    project {
                        id
                        name
                    }
                    cycle {
                        id
                        name
                        number
                    }
                    labels {
                        nodes {
                            id
                            name
                            color
                        }
                    }
                }
            }
        }
        """
        input_obj: dict[str, Any] = {}
        if title is not None:
            input_obj["title"] = title
        if description is not None:
            input_obj["description"] = description
        if priority is not None:
            input_obj["priority"] = priority
        if state_id is not None:
            input_obj["stateId"] = state_id
        if assignee_id is not None:
            input_obj["assigneeId"] = assignee_id
        if project_id is not None:
            input_obj["projectId"] = project_id
        if cycle_id is not None:
            input_obj["cycleId"] = cycle_id
        if parent_id is not None:
            input_obj["parentId"] = parent_id
        if label_ids is not None:
            input_obj["labelIds"] = label_ids
        if estimate is not None:
            input_obj["estimate"] = estimate
        if due_date is not None:
            input_obj["dueDate"] = due_date

        if not input_obj:
            return None

        data = await self._execute(query, {"id": issue_id, "input": input_obj})
        result = data.get("issueUpdate", {})
        if result.get("success"):
            return Issue.from_dict(result.get("issue"))
        return None

    async def archive_issue(self, issue_id: str) -> bool:
        """Archive an issue."""
        query = """
        mutation ArchiveIssue($id: String!) {
            issueArchive(id: $id) {
                success
            }
        }
        """
        data = await self._execute(query, {"id": issue_id})
        return data.get("issueArchive", {}).get("success", False)

    async def delete_issue(self, issue_id: str) -> bool:
        """Delete an issue permanently."""
        query = """
        mutation DeleteIssue($id: String!) {
            issueDelete(id: $id) {
                success
            }
        }
        """
        data = await self._execute(query, {"id": issue_id})
        return data.get("issueDelete", {}).get("success", False)

    async def create_comment(
        self, issue_id: str, body: str, parent_id: str | None = None
    ) -> Comment | None:
        """Create a comment on an issue."""
        query = """
        mutation CreateComment($input: CommentCreateInput!) {
            commentCreate(input: $input) {
                success
                comment {
                    id
                    body
                    createdAt
                    updatedAt
                    user {
                        id
                        name
                        email
                        displayName
                    }
                    parent {
                        id
                    }
                }
            }
        }
        """
        input_obj: dict[str, Any] = {
            "issueId": issue_id,
            "body": body,
        }
        if parent_id:
            input_obj["parentId"] = parent_id

        data = await self._execute(query, {"input": input_obj})
        result = data.get("commentCreate", {})
        if result.get("success"):
            return Comment.from_dict(result.get("comment"))
        return None

    async def get_comments(self, issue_id: str) -> list[Comment]:
        """Get comments for an issue."""
        query = """
        query IssueComments($id: String!) {
            issue(id: $id) {
                comments {
                    nodes {
                        id
                        body
                        createdAt
                        updatedAt
                        user {
                            id
                            name
                            email
                            displayName
                        }
                        parent {
                            id
                        }
                    }
                }
            }
        }
        """
        data = await self._execute(query, {"id": issue_id})
        comments = []
        nodes = data.get("issue", {}).get("comments", {}).get("nodes", [])
        for node in nodes:
            comment = Comment.from_dict(node)
            if comment:
                comments.append(comment)
        return comments

    async def search_issues(
        self,
        query_text: str,
        first: int = 20,
    ) -> list[Issue]:
        """Search issues by text."""
        query = """
        query SearchIssues($term: String!, $first: Int!) {
            searchIssues(term: $term, first: $first) {
                nodes {
                    id
                    identifier
                    title
                    description
                    priority
                    priorityLabel
                    state {
                        id
                        name
                        color
                        type
                    }
                    assignee {
                        id
                        name
                        displayName
                    }
                    team {
                        id
                        name
                        key
                    }
                    project {
                        id
                        name
                    }
                }
            }
        }
        """
        data = await self._execute(query, {"term": query_text, "first": first})
        issues = []
        for node in data.get("searchIssues", {}).get("nodes", []):
            issue = Issue.from_dict(node)
            if issue:
                issues.append(issue)
        return issues

    async def get_issue_history(self, issue_id: str) -> list[IssueHistory]:
        """Get activity history for an issue."""
        query = """
        query IssueHistory($id: String!) {
            issue(id: $id) {
                history(first: 50) {
                    nodes {
                        id
                        createdAt
                        updatedAt
                        actor {
                            id
                            name
                            displayName
                        }
                        addedLabelIds
                        removedLabelIds
                        fromTitle
                        toTitle
                        fromPriority
                        toPriority
                        fromEstimate
                        toEstimate
                        fromDueDate
                        toDueDate
                        fromState {
                            id
                            name
                            type
                        }
                        toState {
                            id
                            name
                            type
                        }
                        fromAssignee {
                            id
                            name
                            displayName
                        }
                        toAssignee {
                            id
                            name
                            displayName
                        }
                        fromCycle {
                            id
                            name
                            number
                        }
                        toCycle {
                            id
                            name
                            number
                        }
                        fromProject {
                            id
                            name
                        }
                        toProject {
                            id
                            name
                        }
                        fromParent {
                            id
                            identifier
                            title
                        }
                        toParent {
                            id
                            identifier
                            title
                        }
                    }
                }
            }
        }
        """
        try:
            data = await self._execute(query, {"id": issue_id})
            history = []
            nodes = data.get("issue", {}).get("history", {}).get("nodes", [])
            for node in nodes:
                entry = IssueHistory.from_dict(node)
                if entry and entry.changes:
                    history.append(entry)
            return sorted(history, key=lambda h: h.created_at, reverse=True)
        except LinearClientError:
            return []

    async def get_favorites(self) -> list[Favorite]:
        """Get user's favorited issues."""
        query = """
        query Favorites {
            favorites {
                nodes {
                    id
                    type
                    issue {
                        id
                        identifier
                        title
                    }
                }
            }
        }
        """
        data = await self._execute(query)
        favorites = []
        for node in data.get("favorites", {}).get("nodes", []):
            favorite = Favorite.from_dict(node)
            if favorite:
                favorites.append(favorite)
        return favorites

    async def add_favorite(self, issue_id: str) -> str | None:
        """Add an issue to favorites. Returns the favorite ID."""
        query = """
        mutation FavoriteCreate($input: FavoriteCreateInput!) {
            favoriteCreate(input: $input) {
                favorite {
                    id
                }
                success
            }
        }
        """
        data = await self._execute(query, {"input": {"issueId": issue_id}})
        result = data.get("favoriteCreate", {})
        if result.get("success"):
            return result.get("favorite", {}).get("id")
        return None

    async def remove_favorite(self, favorite_id: str) -> bool:
        """Remove a favorite. Returns True if successful."""
        query = """
        mutation FavoriteDelete($id: String!) {
            favoriteDelete(id: $id) {
                success
            }
        }
        """
        data = await self._execute(query, {"id": favorite_id})
        return data.get("favoriteDelete", {}).get("success", False)

    async def close(self) -> None:
        """Close the client session."""
        if self._client:
            await self._client.aclose()
            self._client = None
