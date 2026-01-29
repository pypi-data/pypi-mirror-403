"""Extended tests for configuration."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from linear_term.config import (
    THEMES,
    CacheConfig,
    Config,
    DefaultsConfig,
    LayoutConfig,
    ThemeColors,
    _parse_config,
    get_config_path,
    load_config,
    save_config,
)


class TestThemeColorsToTextual:
    def test_to_textual_theme(self):
        colors = ThemeColors()
        theme = colors.to_textual_theme("test-theme")
        assert theme.name == "test-theme"
        assert theme.primary == colors.accent
        assert theme.background == colors.background
        assert theme.foreground == colors.foreground

    def test_to_textual_theme_custom_colors(self):
        colors = ThemeColors(
            background="#000000",
            foreground="#ffffff",
            accent="#ff0000",
            success="#00ff00",
            warning="#ffff00",
            error="#ff0000",
        )
        theme = colors.to_textual_theme("custom")
        assert theme.background == "#000000"
        assert theme.foreground == "#ffffff"


class TestLayoutConfig:
    def test_defaults(self):
        config = LayoutConfig()
        assert config.sidebar_width == 28
        assert config.detail_panel_width == 40
        assert config.show_detail_panel is True
        assert config.show_sidebar is True

    def test_custom_values(self):
        config = LayoutConfig(
            sidebar_width=40,
            detail_panel_width=60,
            show_detail_panel=False,
            show_sidebar=False,
        )
        assert config.sidebar_width == 40
        assert config.show_detail_panel is False


class TestDefaultsConfig:
    def test_defaults(self):
        config = DefaultsConfig()
        assert config.view == "my-issues"
        assert config.sort_by == "priority"
        assert config.sort_order == "asc"
        assert config.filters == []

    def test_custom_values(self):
        config = DefaultsConfig(
            view="triage",
            sort_by="created",
            sort_order="desc",
            filters=["not-done", "assignee-me"],
        )
        assert config.view == "triage"
        assert "not-done" in config.filters


class TestCacheConfig:
    def test_defaults(self):
        config = CacheConfig()
        assert config.directory is None
        assert config.ttl_minutes == 30

    def test_custom_values(self):
        config = CacheConfig(directory="/custom/path", ttl_minutes=120)
        assert config.directory == "/custom/path"
        assert config.ttl_minutes == 120


class TestConfigGetCacheDirectory:
    def test_custom_directory(self):
        config = Config(cache=CacheConfig(directory="/custom/cache"))
        assert config.get_cache_directory() == Path("/custom/cache")

    def test_default_directory(self):
        config = Config()
        path = config.get_cache_directory()
        assert "linear-term" in str(path)


class TestConfigGetEditor:
    def test_configured_editor(self):
        config = Config(editor_command="nano")
        assert config.get_editor() == "nano"

    def test_env_editor(self):
        config = Config()
        with patch.dict(os.environ, {"EDITOR": "emacs"}):
            assert config.get_editor() == "emacs"

    def test_default_editor(self):
        config = Config()
        with patch.dict(os.environ, {}, clear=True):
            if "EDITOR" in os.environ:
                del os.environ["EDITOR"]
            assert config.get_editor() == "vim"


class TestConfigColumns:
    def test_default_columns(self):
        config = Config()
        assert "identifier" in config.columns
        assert "title" in config.columns
        assert "status" in config.columns
        assert "priority" in config.columns
        assert "assignee" in config.columns

    def test_custom_columns(self):
        config = Config(columns=["identifier", "title"])
        assert len(config.columns) == 2


class TestAllThemes:
    def test_all_themes_exist(self):
        expected_themes = [
            "material-dark",
            "gruvbox-dark",
            "linear",
            "dracula",
            "nord",
            "solarized-dark",
            "catppuccin-mocha",
            "one-dark",
            "tokyo-night",
        ]
        for theme_name in expected_themes:
            assert theme_name in THEMES

    def test_all_themes_have_colors(self):
        for _, colors in THEMES.items():
            assert colors.background is not None
            assert colors.foreground is not None
            assert colors.accent is not None
            assert colors.priority_urgent is not None
            assert colors.status_done is not None


class TestParseConfig:
    def test_parse_empty_dict(self):
        config = _parse_config({})
        assert config.api_key is None
        assert config.theme == "material-dark"

    def test_parse_api_key(self):
        config = _parse_config({"api_key": "lin_api_xxx"})
        assert config.api_key == "lin_api_xxx"

    def test_parse_workspace(self):
        config = _parse_config({"workspace": {"id": "ws-123"}})
        assert config.workspace_id == "ws-123"

    def test_parse_appearance(self):
        config = _parse_config({"appearance": {"theme": "dracula"}})
        assert config.theme == "dracula"

    def test_parse_layout(self):
        config = _parse_config(
            {
                "layout": {
                    "sidebar_width": 35,
                    "detail_panel_width": 50,
                    "show_detail_panel": False,
                    "show_sidebar": False,
                }
            }
        )
        assert config.layout.sidebar_width == 35
        assert config.layout.detail_panel_width == 50
        assert config.layout.show_detail_panel is False
        assert config.layout.show_sidebar is False

    def test_parse_defaults(self):
        config = _parse_config(
            {
                "defaults": {
                    "view": "triage",
                    "sort_by": "created",
                    "sort_order": "desc",
                    "filters": ["not-done"],
                }
            }
        )
        assert config.defaults.view == "triage"
        assert config.defaults.sort_by == "created"
        assert config.defaults.sort_order == "desc"
        assert config.defaults.filters == ["not-done"]

    def test_parse_columns(self):
        config = _parse_config({"columns": ["id", "title", "status"]})
        assert config.columns == ["id", "title", "status"]

    def test_parse_editor(self):
        config = _parse_config({"editor": {"command": "code"}})
        assert config.editor_command == "code"

    def test_parse_cache(self):
        config = _parse_config(
            {
                "cache": {
                    "directory": "/tmp/cache",
                    "ttl_minutes": 60,
                }
            }
        )
        assert config.cache.directory == "/tmp/cache"
        assert config.cache.ttl_minutes == 60

    def test_parse_keybindings(self):
        config = _parse_config(
            {
                "keybindings": {
                    "refresh": "ctrl+shift+r",
                }
            }
        )
        assert "refresh" in config.keybindings


class TestLoadConfig:
    def test_load_config_no_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("linear_term.config.get_config_path") as mock_path:
                mock_path.return_value = Path(tmpdir) / "config.yaml"
                with patch.dict(os.environ, {}, clear=True):
                    os.environ.pop("LINEAR_API_KEY", None)
                    config = load_config()
                    assert config.api_key is None

    def test_load_config_with_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("api_key: test_key\n")
            with patch("linear_term.config.get_config_path") as mock_path:
                mock_path.return_value = config_path
                config = load_config()
                assert config.api_key == "test_key"

    def test_load_config_env_var_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("api_key: $LINEAR_API_KEY\n")
            with patch("linear_term.config.get_config_path") as mock_path:
                mock_path.return_value = config_path
                with patch.dict(os.environ, {"LINEAR_API_KEY": "env_key"}):
                    config = load_config()
                    assert config.api_key == "env_key"

    def test_load_config_none_api_key_uses_env(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("theme: dracula\n")
            with patch("linear_term.config.get_config_path") as mock_path:
                mock_path.return_value = config_path
                with patch.dict(os.environ, {"LINEAR_API_KEY": "env_api_key"}):
                    config = load_config()
                    assert config.api_key == "env_api_key"


class TestSaveConfig:
    def test_save_config_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "linear-term" / "config.yaml"
            with patch("linear_term.config.get_config_path") as mock_path:
                mock_path.return_value = config_path
                config = Config(api_key="test_key", theme="dracula")
                save_config(config)
                assert config_path.exists()

    def test_save_config_contents(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            with patch("linear_term.config.get_config_path") as mock_path:
                mock_path.return_value = config_path
                config = Config(
                    api_key="test_key",
                    theme="dracula",
                    workspace_id="ws-123",
                    editor_command="vim",
                )
                save_config(config)

                content = config_path.read_text()
                assert "test_key" in content
                assert "dracula" in content
                assert "ws-123" in content
                assert "vim" in content

    def test_save_config_with_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            with patch("linear_term.config.get_config_path") as mock_path:
                mock_path.return_value = config_path
                config = Config(
                    defaults=DefaultsConfig(
                        view="triage",
                        filters=["not-done", "assignee-me"],
                    )
                )
                save_config(config)

                content = config_path.read_text()
                assert "triage" in content
                assert "not-done" in content

    def test_save_config_with_cache_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            with patch("linear_term.config.get_config_path") as mock_path:
                mock_path.return_value = config_path
                config = Config(cache=CacheConfig(directory="/custom/cache", ttl_minutes=120))
                save_config(config)

                content = config_path.read_text()
                assert "/custom/cache" in content
                assert "120" in content

    def test_save_config_with_keybindings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            with patch("linear_term.config.get_config_path") as mock_path:
                mock_path.return_value = config_path
                config = Config(keybindings={"refresh": "ctrl+r"})
                save_config(config)

                content = config_path.read_text()
                assert "keybindings" in content
                assert "ctrl+r" in content

    def test_save_config_no_api_key_placeholder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            with patch("linear_term.config.get_config_path") as mock_path:
                mock_path.return_value = config_path
                config = Config(api_key=None)
                save_config(config)

                content = config_path.read_text()
                assert "$LINEAR_API_KEY" in content


class TestGetConfigPath:
    def test_returns_path(self):
        path = get_config_path()
        assert isinstance(path, Path)
        assert "linear-term" in str(path)
        assert path.name == "config.yaml"
