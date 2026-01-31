"""Tests for init_bundled_cli module.

Tests the bundled template initialization, including the wheel install scenario
where importlib.resources returns Traversable objects that need as_file() extraction.
"""
from pathlib import Path
from unittest.mock import MagicMock, patch
from contextlib import contextmanager
import tempfile
import os
import sys

import pytest


@contextmanager
def mock_as_file_returning(path):
    """Context manager that simulates as_file() returning a path."""
    yield path


class TestInitBundledCli:
    """Tests for init_bundled_cli.main()."""

    def test_main_copies_template_files(self, tmp_path, monkeypatch):
        """Should copy template files to destination."""
        # Create a mock template directory structure
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        (template_dir / ".paircoder").mkdir()
        (template_dir / ".paircoder" / "context").mkdir()
        (template_dir / ".paircoder" / "context" / "state.md").write_text("# State")
        (template_dir / ".claude").mkdir()
        (template_dir / ".claude" / "skills").mkdir()
        (template_dir / "CLAUDE.md").write_text("# Claude")

        # Create output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        monkeypatch.chdir(output_dir)

        # Mock the chain: res_files("bpsai_pair") / "data" / "cookiecutter-paircoder"
        mock_cookiecutter_dir = MagicMock()
        mock_cookiecutter_dir.iterdir.return_value = [template_dir]
        mock_cookiecutter_dir.is_dir.return_value = True

        mock_data_dir = MagicMock()
        mock_data_dir.__truediv__ = MagicMock(return_value=mock_cookiecutter_dir)

        mock_pkg = MagicMock()
        mock_pkg.__truediv__ = MagicMock(return_value=mock_data_dir)

        # Force reimport to pick up mocks
        if 'bpsai_pair.init_bundled_cli' in sys.modules:
            del sys.modules['bpsai_pair.init_bundled_cli']

        with patch('bpsai_pair.init_bundled_cli.res_files', return_value=mock_pkg), \
             patch('bpsai_pair.init_bundled_cli.as_file', side_effect=lambda t: mock_as_file_returning(template_dir)):
            from bpsai_pair import init_bundled_cli
            result = init_bundled_cli.main()

        assert result == 0
        assert (output_dir / ".paircoder" / "context" / "state.md").exists()
        assert (output_dir / ".claude" / "skills").exists()
        assert (output_dir / "CLAUDE.md").exists()

    def test_main_returns_error_when_template_not_found(self, tmp_path, monkeypatch):
        """Should return error code when packaged template not found."""
        monkeypatch.chdir(tmp_path)

        # Mock returns empty list (no template found)
        mock_cookiecutter_dir = MagicMock()
        mock_cookiecutter_dir.iterdir.return_value = []

        mock_data_dir = MagicMock()
        mock_data_dir.__truediv__ = MagicMock(return_value=mock_cookiecutter_dir)

        mock_pkg = MagicMock()
        mock_pkg.__truediv__ = MagicMock(return_value=mock_data_dir)

        if 'bpsai_pair.init_bundled_cli' in sys.modules:
            del sys.modules['bpsai_pair.init_bundled_cli']

        with patch('bpsai_pair.init_bundled_cli.res_files', return_value=mock_pkg):
            from bpsai_pair import init_bundled_cli
            result = init_bundled_cli.main()

        assert result == 1

    def test_main_copies_all_files_no_skip(self, tmp_path, monkeypatch):
        """Should copy all files (SKIP_FILES is empty as of v2.10.0).

        As of v2.10.0, config.yaml is no longer in the cookiecutter template.
        Config is generated dynamically by presets/wizard/Config.save().
        Therefore SKIP_FILES is empty and all template files are copied.
        """
        # Create template with various files
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        (template_dir / ".paircoder").mkdir()
        (template_dir / ".paircoder" / "context").mkdir()
        (template_dir / ".paircoder" / "context" / "state.md").write_text("# State")
        (template_dir / "other.txt").write_text("content")

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        monkeypatch.chdir(output_dir)

        mock_cookiecutter_dir = MagicMock()
        mock_cookiecutter_dir.iterdir.return_value = [template_dir]

        mock_data_dir = MagicMock()
        mock_data_dir.__truediv__ = MagicMock(return_value=mock_cookiecutter_dir)

        mock_pkg = MagicMock()
        mock_pkg.__truediv__ = MagicMock(return_value=mock_data_dir)

        if 'bpsai_pair.init_bundled_cli' in sys.modules:
            del sys.modules['bpsai_pair.init_bundled_cli']

        with patch('bpsai_pair.init_bundled_cli.res_files', return_value=mock_pkg), \
             patch('bpsai_pair.init_bundled_cli.as_file', side_effect=lambda t: mock_as_file_returning(template_dir)):
            from bpsai_pair import init_bundled_cli
            result = init_bundled_cli.main()

        assert result == 0
        # All files should be copied (no skip list)
        assert (output_dir / ".paircoder" / "context" / "state.md").exists()
        assert (output_dir / "other.txt").exists()

    def test_main_does_not_overwrite_existing_files(self, tmp_path, monkeypatch):
        """Should not overwrite existing files (non-destructive copy)."""
        # Create template
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        (template_dir / "existing.txt").write_text("template content")
        (template_dir / "new.txt").write_text("new content")

        # Create output with existing file
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "existing.txt").write_text("user content")
        monkeypatch.chdir(output_dir)

        mock_cookiecutter_dir = MagicMock()
        mock_cookiecutter_dir.iterdir.return_value = [template_dir]

        mock_data_dir = MagicMock()
        mock_data_dir.__truediv__ = MagicMock(return_value=mock_cookiecutter_dir)

        mock_pkg = MagicMock()
        mock_pkg.__truediv__ = MagicMock(return_value=mock_data_dir)

        if 'bpsai_pair.init_bundled_cli' in sys.modules:
            del sys.modules['bpsai_pair.init_bundled_cli']

        with patch('bpsai_pair.init_bundled_cli.res_files', return_value=mock_pkg), \
             patch('bpsai_pair.init_bundled_cli.as_file', side_effect=lambda t: mock_as_file_returning(template_dir)):
            from bpsai_pair import init_bundled_cli
            result = init_bundled_cli.main()

        assert result == 0
        # Existing file should keep its content
        assert (output_dir / "existing.txt").read_text() == "user content"
        # New file should be created
        assert (output_dir / "new.txt").read_text() == "new content"


class TestWheelInstallScenario:
    """Tests specifically for wheel install behavior.

    When installed from PyPI (non-editable), importlib.resources returns
    Traversable objects that point inside the wheel. The as_file() context
    manager extracts these to a temp directory.
    """

    def test_as_file_is_used_for_traversable_extraction(self, tmp_path, monkeypatch):
        """Should use as_file() context manager to extract Traversable."""
        # Create template
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        (template_dir / "test.txt").write_text("content")

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        monkeypatch.chdir(output_dir)

        # Create a mock Traversable that is NOT a Path
        mock_traversable = MagicMock()
        mock_traversable.is_dir.return_value = True

        mock_cookiecutter_dir = MagicMock()
        mock_cookiecutter_dir.iterdir.return_value = [mock_traversable]

        mock_data_dir = MagicMock()
        mock_data_dir.__truediv__ = MagicMock(return_value=mock_cookiecutter_dir)

        mock_pkg = MagicMock()
        mock_pkg.__truediv__ = MagicMock(return_value=mock_data_dir)

        as_file_calls = []

        def track_as_file(traversable):
            as_file_calls.append(traversable)
            return mock_as_file_returning(template_dir)

        if 'bpsai_pair.init_bundled_cli' in sys.modules:
            del sys.modules['bpsai_pair.init_bundled_cli']

        with patch('bpsai_pair.init_bundled_cli.res_files', return_value=mock_pkg), \
             patch('bpsai_pair.init_bundled_cli.as_file', side_effect=track_as_file):
            from bpsai_pair import init_bundled_cli
            result = init_bundled_cli.main()

        assert result == 0
        # Verify as_file was called with the Traversable
        assert len(as_file_calls) == 1
        assert as_file_calls[0] is mock_traversable
        # Verify file was copied
        assert (output_dir / "test.txt").exists()

    def test_as_file_context_properly_managed(self, tmp_path, monkeypatch):
        """Should properly manage as_file context via ExitStack."""
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        (template_dir / "test.txt").write_text("content")

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        monkeypatch.chdir(output_dir)

        mock_traversable = MagicMock()
        mock_traversable.is_dir.return_value = True

        mock_cookiecutter_dir = MagicMock()
        mock_cookiecutter_dir.iterdir.return_value = [mock_traversable]

        mock_data_dir = MagicMock()
        mock_data_dir.__truediv__ = MagicMock(return_value=mock_cookiecutter_dir)

        mock_pkg = MagicMock()
        mock_pkg.__truediv__ = MagicMock(return_value=mock_data_dir)

        context_entered = []
        context_exited = []

        @contextmanager
        def tracking_context(traversable):
            context_entered.append(True)
            try:
                yield template_dir
            finally:
                context_exited.append(True)

        if 'bpsai_pair.init_bundled_cli' in sys.modules:
            del sys.modules['bpsai_pair.init_bundled_cli']

        with patch('bpsai_pair.init_bundled_cli.res_files', return_value=mock_pkg), \
             patch('bpsai_pair.init_bundled_cli.as_file', side_effect=tracking_context):
            from bpsai_pair import init_bundled_cli
            init_bundled_cli.main()

        # Verify context was properly entered and exited
        assert len(context_entered) == 1
        assert len(context_exited) == 1


class TestCopytreeNonDestructive:
    """Tests for copytree_non_destructive helper function."""

    def test_makes_scripts_executable(self, tmp_path):
        """Should make .sh scripts executable."""
        src = tmp_path / "src"
        src.mkdir()
        scripts_dir = src / "scripts"
        scripts_dir.mkdir()
        script = scripts_dir / "test.sh"
        script.write_text("#!/bin/bash\necho hello")

        dst = tmp_path / "dst"
        dst.mkdir()

        from bpsai_pair.init_bundled_cli import copytree_non_destructive
        copytree_non_destructive(src, dst)

        copied_script = dst / "scripts" / "test.sh"
        assert copied_script.exists()
        # Check executable bit is set
        import stat
        mode = copied_script.stat().st_mode
        assert mode & stat.S_IXUSR

    def test_creates_nested_directories(self, tmp_path):
        """Should create nested directory structure."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "a" / "b" / "c").mkdir(parents=True)
        (src / "a" / "b" / "c" / "deep.txt").write_text("deep")

        dst = tmp_path / "dst"
        dst.mkdir()

        from bpsai_pair.init_bundled_cli import copytree_non_destructive
        copytree_non_destructive(src, dst)

        assert (dst / "a" / "b" / "c" / "deep.txt").exists()
        assert (dst / "a" / "b" / "c" / "deep.txt").read_text() == "deep"
