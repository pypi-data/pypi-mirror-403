"""Tests for configuration."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

from linear_term.config import (
    THEMES,
    Config,
    SavedFilter,
    ThemeColors,
    _parse_config,
    save_config,
)


class TestThemeColors:
    def test_default_values(self):
        colors = ThemeColors()
        assert colors.background == "#1e1e1e"
        assert colors.foreground == "#eeffff"
        assert colors.accent == "#82aaff"


class TestConfig:
    def test_default_values(self):
        config = Config()
        assert config.api_key is None
        assert config.theme == "material-dark"
        assert config.layout.sidebar_width == 28

    def test_get_theme_colors(self):
        config = Config(theme="material-dark")
        colors = config.get_theme_colors()
        assert colors.background == "#1e1e1e"

    def test_get_theme_colors_fallback(self):
        config = Config(theme="nonexistent")
        colors = config.get_theme_colors()
        assert colors.background == "#1e1e1e"

    def test_get_editor(self):
        config = Config(editor_command="nano")
        assert config.get_editor() == "nano"

    def test_get_editor_from_env(self):
        config = Config()
        original = os.environ.get("EDITOR")
        try:
            os.environ["EDITOR"] = "emacs"
            assert config.get_editor() == "emacs"
        finally:
            if original:
                os.environ["EDITOR"] = original
            elif "EDITOR" in os.environ:
                del os.environ["EDITOR"]


class TestTHEMES:
    def test_material_dark_exists(self):
        assert "material-dark" in THEMES

    def test_gruvbox_dark_exists(self):
        assert "gruvbox-dark" in THEMES

    def test_linear_exists(self):
        assert "linear" in THEMES


class TestSavedFilter:
    def test_create_saved_filter(self):
        sf = SavedFilter(name="My Filter", filter_state={"text": "bug"})
        assert sf.name == "My Filter"
        assert sf.filter_state == {"text": "bug"}

    def test_add_saved_filter(self):
        config = Config()
        sf = config.add_saved_filter("Test Filter", {"priority": "high"})
        assert sf.name == "Test Filter"
        assert len(config.saved_filters) == 1
        assert config.saved_filters[0].name == "Test Filter"

    def test_add_saved_filter_replaces_duplicate(self):
        config = Config()
        config.add_saved_filter("Test Filter", {"priority": "high"})
        config.add_saved_filter("Test Filter", {"priority": "urgent"})
        assert len(config.saved_filters) == 1
        assert config.saved_filters[0].filter_state == {"priority": "urgent"}

    def test_delete_saved_filter(self):
        config = Config()
        config.add_saved_filter("Filter 1", {"text": "a"})
        config.add_saved_filter("Filter 2", {"text": "b"})
        assert len(config.saved_filters) == 2

        result = config.delete_saved_filter("Filter 1")
        assert result is True
        assert len(config.saved_filters) == 1
        assert config.saved_filters[0].name == "Filter 2"

    def test_delete_nonexistent_filter(self):
        config = Config()
        config.add_saved_filter("Filter 1", {"text": "a"})
        result = config.delete_saved_filter("Nonexistent")
        assert result is False
        assert len(config.saved_filters) == 1

    def test_get_saved_filter(self):
        config = Config()
        config.add_saved_filter("My Filter", {"status": "in_progress"})
        sf = config.get_saved_filter("My Filter")
        assert sf is not None
        assert sf.name == "My Filter"
        assert sf.filter_state == {"status": "in_progress"}

    def test_get_nonexistent_filter(self):
        config = Config()
        sf = config.get_saved_filter("Nonexistent")
        assert sf is None


class TestSavedFilterPersistence:
    def test_parse_config_with_saved_filters(self):
        data = {
            "saved_filters": [
                {"name": "Filter 1", "filter_state": {"text": "bug", "priority": "high"}},
                {"name": "Filter 2", "filter_state": {"assignee": "me"}},
            ]
        }
        config = _parse_config(data)
        assert len(config.saved_filters) == 2
        assert config.saved_filters[0].name == "Filter 1"
        assert config.saved_filters[0].filter_state == {"text": "bug", "priority": "high"}
        assert config.saved_filters[1].name == "Filter 2"

    def test_parse_config_without_saved_filters(self):
        data = {"theme": "gruvbox-dark"}
        config = _parse_config(data)
        assert config.saved_filters == []

    def test_save_config_with_saved_filters(self):
        config = Config()
        config.add_saved_filter("Test Filter", {"priority": "urgent", "text": "critical"})

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            with patch("linear_term.config.get_config_path", return_value=config_path):
                save_config(config)

                with open(config_path) as f:
                    saved_data = yaml.safe_load(f)

                assert "saved_filters" in saved_data
                assert len(saved_data["saved_filters"]) == 1
                assert saved_data["saved_filters"][0]["name"] == "Test Filter"
                assert saved_data["saved_filters"][0]["filter_state"] == {
                    "priority": "urgent",
                    "text": "critical",
                }

    def test_save_config_without_saved_filters(self):
        config = Config()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            with patch("linear_term.config.get_config_path", return_value=config_path):
                save_config(config)

                with open(config_path) as f:
                    saved_data = yaml.safe_load(f)

                assert "saved_filters" not in saved_data
