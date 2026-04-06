"""Tests for config load/save and MRU path management."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def _make_ui(config_dir, output_dir):
    """Create InteractiveUI with custom config path and suppressed output."""
    from src.interactive_ui import InteractiveUI

    with patch.object(InteractiveUI, '__init__', lambda self, *a, **kw: None):
        ui = InteractiveUI.__new__(InteractiveUI)
        ui.config_path = config_dir / "conversation-extractor-config.json"
        ui.output_dir = output_dir
        ui.sessions = []
        ui.terminal_width = 80
        return ui


class TestConfigLoadSave:
    def test_load_config_no_file(self, tmp_path):
        ui = _make_ui(tmp_path, tmp_path / "out")
        config = ui._load_config()
        assert config == {"recent_custom_paths": []}

    def test_save_and_load_config(self, tmp_path):
        ui = _make_ui(tmp_path, tmp_path / "out")
        ui._save_config({"recent_custom_paths": ["/foo", "/bar"]})
        config = ui._load_config()
        assert config["recent_custom_paths"] == ["/foo", "/bar"]

    def test_load_config_corrupt_json(self, tmp_path):
        config_path = tmp_path / "conversation-extractor-config.json"
        config_path.write_text("not json!!!")
        ui = _make_ui(tmp_path, tmp_path / "out")
        config = ui._load_config()
        assert config == {"recent_custom_paths": []}


class TestUpdateRecentPaths:
    def test_add_new_path(self, tmp_path):
        ui = _make_ui(tmp_path, tmp_path / "out")
        ui._save_config({"recent_custom_paths": []})
        ui._update_recent_paths(Path("/new/path"))
        config = ui._load_config()
        assert config["recent_custom_paths"] == ["/new/path"]

    def test_mru_order(self, tmp_path):
        ui = _make_ui(tmp_path, tmp_path / "out")
        ui._save_config({"recent_custom_paths": ["/old"]})
        ui._update_recent_paths(Path("/new"))
        config = ui._load_config()
        assert config["recent_custom_paths"] == ["/new", "/old"]

    def test_max_three(self, tmp_path):
        ui = _make_ui(tmp_path, tmp_path / "out")
        ui._save_config({"recent_custom_paths": ["/a", "/b", "/c"]})
        ui._update_recent_paths(Path("/d"))
        config = ui._load_config()
        assert config["recent_custom_paths"] == ["/d", "/a", "/b"]

    def test_duplicate_moves_to_front(self, tmp_path):
        ui = _make_ui(tmp_path, tmp_path / "out")
        ui._save_config({"recent_custom_paths": ["/a", "/b", "/c"]})
        ui._update_recent_paths(Path("/b"))
        config = ui._load_config()
        assert config["recent_custom_paths"] == ["/b", "/a", "/c"]


class TestFolderSelectionWithRecentPaths:
    def test_recent_paths_shown_in_menu(self, tmp_path, capsys):
        """Recent custom paths should appear after default suggestions."""
        ui = _make_ui(tmp_path, tmp_path / "out")
        ui._save_config({"recent_custom_paths": ["/my/custom/path"]})

        # Simulate selecting '5' (first recent path)
        with patch("builtins.input", return_value="5"):
            with patch.object(type(ui), 'clear_screen', lambda self: None):
                with patch.object(type(ui), 'print_banner', lambda self: None):
                    result = ui.get_folder_selection()

        assert result == Path("/my/custom/path")
