"""Extended tests for the main application."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from linear_term.api.models import Issue, User, WorkflowState
from linear_term.app import FilterState, LinearTUI
from linear_term.config import Config, DefaultsConfig


class TestFilterState:
    def test_default_state(self):
        fs = FilterState()
        assert fs.exclude_done is False
        assert fs.in_progress_only is False
        assert fs.assignee_me is False
        assert fs.unassigned is False
        assert len(fs.priorities) == 0
        assert fs.due_overdue is False
        assert fs.due_today is False
        assert fs.due_this_week is False
        assert fs.due_this_month is False

    def test_is_active_false_by_default(self):
        fs = FilterState()
        assert fs.is_active() is False

    def test_is_active_with_exclude_done(self):
        fs = FilterState(exclude_done=True)
        assert fs.is_active() is True

    def test_is_active_with_in_progress_only(self):
        fs = FilterState(in_progress_only=True)
        assert fs.is_active() is True

    def test_is_active_with_assignee_me(self):
        fs = FilterState(assignee_me=True)
        assert fs.is_active() is True

    def test_is_active_with_unassigned(self):
        fs = FilterState(unassigned=True)
        assert fs.is_active() is True

    def test_is_active_with_priorities(self):
        fs = FilterState(priorities={1, 2})
        assert fs.is_active() is True

    def test_is_active_with_due_filters(self):
        fs = FilterState(due_overdue=True)
        assert fs.is_active() is True

        fs = FilterState(due_today=True)
        assert fs.is_active() is True

        fs = FilterState(due_this_week=True)
        assert fs.is_active() is True

        fs = FilterState(due_this_month=True)
        assert fs.is_active() is True

    def test_active_count_zero(self):
        fs = FilterState()
        assert fs.active_count() == 0

    def test_active_count_single(self):
        fs = FilterState(exclude_done=True)
        assert fs.active_count() == 1

    def test_active_count_multiple(self):
        fs = FilterState(
            exclude_done=True,
            in_progress_only=True,
            assignee_me=True,
        )
        assert fs.active_count() == 3

    def test_active_count_with_priorities(self):
        fs = FilterState(priorities={1, 2, 3})
        assert fs.active_count() == 3

    def test_active_count_all_active(self):
        fs = FilterState(
            exclude_done=True,
            in_progress_only=True,
            assignee_me=True,
            unassigned=True,
            priorities={1, 2},
            due_overdue=True,
            due_today=True,
            due_this_week=True,
            due_this_month=True,
        )
        assert fs.active_count() == 10


class TestLinearTUIInit:
    def test_init_with_config(self):
        config = Config(api_key="test_key")
        app = LinearTUI(config)
        assert app.config.api_key == "test_key"

    def test_init_without_config(self):
        with patch("linear_term.app.load_config") as mock_load:
            mock_load.return_value = Config()
            LinearTUI()
            mock_load.assert_called_once()

    def test_init_state(self):
        config = Config()
        app = LinearTUI(config)
        assert app._client is None
        assert app._cache is None
        assert app._viewer is None
        assert app._teams == []
        assert app._projects == []
        assert app._current_view == "my-issues"


class TestLinearTUICompose:
    @pytest.fixture
    def config(self):
        return Config(api_key="test_key")

    async def test_compose_creates_widgets(self, config):
        app = LinearTUI(config)
        async with app.run_test():
            assert app.query_one("#sidebar") is not None
            assert app.query_one("#issue-list") is not None
            assert app.query_one("#detail-panel") is not None
            assert app.query_one("#status-bar") is not None

    async def test_compose_creates_header_and_status_bar(self, config):
        from textual.widgets import Header

        from linear_term.widgets.status_bar import StatusBar

        app = LinearTUI(config)
        async with app.run_test():
            assert len(app.query(Header)) == 1
            assert len(app.query(StatusBar)) == 1


class TestLinearTUIActions:
    @pytest.fixture
    def config(self):
        return Config(api_key="test_key")

    async def test_action_toggle_sidebar(self, config):
        app = LinearTUI(config)
        async with app.run_test():
            sidebar = app.query_one("#sidebar")
            assert not sidebar.has_class("hidden")

            app.action_toggle_sidebar()
            assert sidebar.has_class("hidden")

            app.action_toggle_sidebar()
            assert not sidebar.has_class("hidden")

    async def test_action_toggle_detail(self, config):
        app = LinearTUI(config)
        async with app.run_test():
            detail = app.query_one("#detail-panel")
            assert not detail.has_class("hidden")

            app.action_toggle_detail()
            assert detail.has_class("hidden")

            app.action_toggle_detail()
            assert not detail.has_class("hidden")

    async def test_action_goto_my_issues(self, config):
        app = LinearTUI(config)
        async with app.run_test():
            app._current_view = "triage"
            app.action_goto_my_issues()
            assert app._current_view == "my-issues"

    async def test_action_goto_triage(self, config):
        app = LinearTUI(config)
        async with app.run_test():
            app._current_view = "my-issues"
            app.action_goto_triage()
            assert app._current_view == "triage"

    async def test_action_focus_panels(self, config):
        app = LinearTUI(config)
        async with app.run_test():
            app.action_focus_list()
            assert app._focused_panel == "list"

            app.action_focus_sidebar()
            assert app._focused_panel == "sidebar"

            app.action_focus_detail()
            assert app._focused_panel == "detail"

    async def test_action_focus_next_panel(self, config):
        app = LinearTUI(config)
        async with app.run_test():
            app._focused_panel = "list"
            app.action_focus_next_panel()
            assert app._focused_panel == "detail"

            app.action_focus_next_panel()
            assert app._focused_panel == "sidebar"

            app.action_focus_next_panel()
            assert app._focused_panel == "list"

    async def test_action_focus_prev_panel(self, config):
        app = LinearTUI(config)
        async with app.run_test():
            app._focused_panel = "list"
            app.action_focus_prev_panel()
            assert app._focused_panel == "sidebar"


class TestLinearTUIApplyClientFilters:
    @pytest.fixture
    def config(self):
        return Config(api_key="test_key")

    def test_no_filters(self, config):
        app = LinearTUI(config)
        issue = Issue(id="i1", identifier="T-1", title="Test")
        result = app._apply_client_filters([issue])
        assert len(result) == 1

    def test_exclude_done_filter(self, config):
        app = LinearTUI(config)
        app._filter_state.exclude_done = True

        completed_state = WorkflowState(id="s1", name="Done", color="#0f0", type="completed")
        todo_state = WorkflowState(id="s2", name="Todo", color="#888", type="unstarted")

        issues = [
            Issue(id="i1", identifier="T-1", title="Done issue", state=completed_state),
            Issue(id="i2", identifier="T-2", title="Todo issue", state=todo_state),
        ]
        result = app._apply_client_filters(issues)
        assert len(result) == 1
        assert result[0].identifier == "T-2"

    def test_in_progress_only_filter(self, config):
        app = LinearTUI(config)
        app._filter_state.in_progress_only = True

        started_state = WorkflowState(id="s1", name="In Progress", color="#0f0", type="started")
        todo_state = WorkflowState(id="s2", name="Todo", color="#888", type="unstarted")

        issues = [
            Issue(id="i1", identifier="T-1", title="In progress", state=started_state),
            Issue(id="i2", identifier="T-2", title="Todo", state=todo_state),
        ]
        result = app._apply_client_filters(issues)
        assert len(result) == 1
        assert result[0].identifier == "T-1"

    def test_unassigned_filter(self, config):
        app = LinearTUI(config)
        app._filter_state.unassigned = True

        assignee = User(id="u1", name="Alice")
        issues = [
            Issue(id="i1", identifier="T-1", title="Assigned", assignee=assignee),
            Issue(id="i2", identifier="T-2", title="Unassigned", assignee=None),
        ]
        result = app._apply_client_filters(issues)
        assert len(result) == 1
        assert result[0].identifier == "T-2"

    def test_priority_filter(self, config):
        app = LinearTUI(config)
        app._filter_state.priorities = {1, 2}

        issues = [
            Issue(id="i1", identifier="T-1", title="Urgent", priority=1),
            Issue(id="i2", identifier="T-2", title="High", priority=2),
            Issue(id="i3", identifier="T-3", title="Low", priority=4),
        ]
        result = app._apply_client_filters(issues)
        assert len(result) == 2

    def test_due_overdue_filter(self, config):
        app = LinearTUI(config)
        app._filter_state.due_overdue = True

        now = datetime.now()
        issues = [
            Issue(id="i1", identifier="T-1", title="Overdue", due_date=now - timedelta(days=1)),
            Issue(id="i2", identifier="T-2", title="Future", due_date=now + timedelta(days=1)),
            Issue(id="i3", identifier="T-3", title="No due", due_date=None),
        ]
        result = app._apply_client_filters(issues)
        assert len(result) == 1
        assert result[0].identifier == "T-1"

    def test_due_today_filter(self, config):
        app = LinearTUI(config)
        app._filter_state.due_today = True

        now = datetime.now()
        issues = [
            Issue(id="i1", identifier="T-1", title="Today", due_date=now),
            Issue(id="i2", identifier="T-2", title="Tomorrow", due_date=now + timedelta(days=1)),
        ]
        result = app._apply_client_filters(issues)
        assert len(result) == 1
        assert result[0].identifier == "T-1"

    def test_due_this_week_filter(self, config):
        app = LinearTUI(config)
        app._filter_state.due_this_week = True

        now = datetime.now()
        issues = [
            Issue(id="i1", identifier="T-1", title="This week", due_date=now + timedelta(days=3)),
            Issue(id="i2", identifier="T-2", title="Next month", due_date=now + timedelta(days=30)),
        ]
        result = app._apply_client_filters(issues)
        assert len(result) == 1
        assert result[0].identifier == "T-1"

    def test_due_this_month_filter(self, config):
        app = LinearTUI(config)
        app._filter_state.due_this_month = True

        now = datetime.now()
        issues = [
            Issue(id="i1", identifier="T-1", title="This month", due_date=now + timedelta(days=15)),
            Issue(id="i2", identifier="T-2", title="Far future", due_date=now + timedelta(days=60)),
        ]
        result = app._apply_client_filters(issues)
        assert len(result) == 1
        assert result[0].identifier == "T-1"

    def test_multiple_filters_combined(self, config):
        app = LinearTUI(config)
        app._filter_state.exclude_done = True
        app._filter_state.priorities = {1}

        completed_state = WorkflowState(id="s1", name="Done", color="#0f0", type="completed")
        todo_state = WorkflowState(id="s2", name="Todo", color="#888", type="unstarted")

        issues = [
            Issue(
                id="i1", identifier="T-1", title="Done urgent", priority=1, state=completed_state
            ),
            Issue(id="i2", identifier="T-2", title="Todo urgent", priority=1, state=todo_state),
            Issue(id="i3", identifier="T-3", title="Todo low", priority=4, state=todo_state),
        ]
        result = app._apply_client_filters(issues)
        assert len(result) == 1
        assert result[0].identifier == "T-2"


class TestLinearTUIApplyDefaultFilters:
    @pytest.fixture
    def config(self):
        return Config(
            api_key="test_key",
            defaults=DefaultsConfig(filters=["not-done", "assignee-me"]),
        )

    async def test_apply_default_filters(self, config):
        app = LinearTUI(config)
        async with app.run_test():
            app._apply_default_filters()
            assert app._filter_state.exclude_done is True
            assert app._filter_state.assignee_me is True

    async def test_apply_all_priority_filters(self):
        config = Config(
            api_key="test_key",
            defaults=DefaultsConfig(
                filters=["priority-urgent", "priority-high", "priority-medium", "priority-low"]
            ),
        )
        app = LinearTUI(config)
        async with app.run_test():
            app._apply_default_filters()
            assert 1 in app._filter_state.priorities
            assert 2 in app._filter_state.priorities
            assert 3 in app._filter_state.priorities
            assert 4 in app._filter_state.priorities

    async def test_apply_due_date_filters(self):
        config = Config(
            api_key="test_key",
            defaults=DefaultsConfig(
                filters=["due-overdue", "due-today", "due-this-week", "due-this-month"]
            ),
        )
        app = LinearTUI(config)
        async with app.run_test():
            app._apply_default_filters()
            assert app._filter_state.due_overdue is True
            assert app._filter_state.due_today is True
            assert app._filter_state.due_this_week is True
            assert app._filter_state.due_this_month is True


class TestLinearTUIResizeSidebar:
    @pytest.fixture
    def config(self):
        return Config(api_key="test_key")

    async def test_resize_sidebar_grow(self, config):
        app = LinearTUI(config)
        with patch("linear_term.app.save_config"):
            async with app.run_test():
                initial_width = app.config.layout.sidebar_width
                app._resize_sidebar(4)
                assert app.config.layout.sidebar_width == initial_width + 4

    async def test_resize_sidebar_shrink(self, config):
        app = LinearTUI(config)
        with patch("linear_term.app.save_config"):
            async with app.run_test():
                initial_width = app.config.layout.sidebar_width
                app._resize_sidebar(-4)
                assert app.config.layout.sidebar_width == initial_width - 4

    async def test_resize_sidebar_min_width(self, config):
        app = LinearTUI(config)
        with patch("linear_term.app.save_config"):
            async with app.run_test():
                app.config.layout.sidebar_width = 20
                app._resize_sidebar(-10)
                assert app.config.layout.sidebar_width >= 16

    async def test_resize_sidebar_max_width(self, config):
        app = LinearTUI(config)
        with patch("linear_term.app.save_config"):
            async with app.run_test():
                app.config.layout.sidebar_width = 56
                app._resize_sidebar(10)
                assert app.config.layout.sidebar_width <= 60
