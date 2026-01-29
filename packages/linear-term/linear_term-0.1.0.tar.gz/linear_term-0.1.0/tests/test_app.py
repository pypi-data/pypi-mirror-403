"""Tests for the main application."""

import pytest

from linear_term.app import LinearTUI
from linear_term.config import Config


class TestLinearTUI:
    @pytest.fixture
    def config(self):
        return Config(
            api_key="test_api_key",
            theme="material-dark",
        )

    async def test_app_creation(self, config):
        """Test that the app can be created."""
        app = LinearTUI(config)
        assert app.config == config
        assert app._client is None
        assert app._cache is None

    async def test_app_compose(self, config):
        """Test that the app composes correctly."""
        app = LinearTUI(config)
        async with app.run_test():
            assert app.query_one("#sidebar") is not None
            assert app.query_one("#issue-list") is not None
            assert app.query_one("#detail-panel") is not None
            assert app.query_one("#status-bar") is not None

    async def test_toggle_sidebar(self, config):
        """Test sidebar toggle."""
        app = LinearTUI(config)
        async with app.run_test():
            sidebar = app.query_one("#sidebar")
            assert not sidebar.has_class("hidden")

            app.action_toggle_sidebar()
            assert sidebar.has_class("hidden")

            app.action_toggle_sidebar()
            assert not sidebar.has_class("hidden")

    async def test_toggle_detail(self, config):
        """Test detail panel toggle."""
        app = LinearTUI(config)
        async with app.run_test():
            detail = app.query_one("#detail-panel")
            assert not detail.has_class("hidden")

            app.action_toggle_detail()
            assert detail.has_class("hidden")

            app.action_toggle_detail()
            assert not detail.has_class("hidden")
