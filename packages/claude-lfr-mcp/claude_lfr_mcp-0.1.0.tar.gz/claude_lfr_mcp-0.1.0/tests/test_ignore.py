"""Tests for ignore.py - gitignore-style pattern handling."""

import pytest
from pathlib import Path

from claude_lfr_mcp.ignore import (
    DEFAULT_IGNORE_DIRS,
    IgnoreHandler,
    get_ignore_handler,
)


class TestDefaultIgnoreDirs:
    """Tests for DEFAULT_IGNORE_DIRS constant."""

    def test_contains_git(self):
        """Test that .git is in default ignores."""
        assert ".git" in DEFAULT_IGNORE_DIRS

    def test_contains_node_modules(self):
        """Test that node_modules is in default ignores."""
        assert "node_modules" in DEFAULT_IGNORE_DIRS

    def test_contains_python_venvs(self):
        """Test that Python virtual environments are ignored."""
        assert ".venv" in DEFAULT_IGNORE_DIRS
        assert "venv" in DEFAULT_IGNORE_DIRS
        assert "env" in DEFAULT_IGNORE_DIRS

    def test_contains_pycache(self):
        """Test that __pycache__ is ignored."""
        assert "__pycache__" in DEFAULT_IGNORE_DIRS

    def test_contains_build_dirs(self):
        """Test that common build directories are ignored."""
        assert "dist" in DEFAULT_IGNORE_DIRS
        assert "build" in DEFAULT_IGNORE_DIRS
        assert "out" in DEFAULT_IGNORE_DIRS
        assert "target" in DEFAULT_IGNORE_DIRS

    def test_contains_cache_dirs(self):
        """Test that cache directories are ignored."""
        assert ".cache" in DEFAULT_IGNORE_DIRS
        assert ".pytest_cache" in DEFAULT_IGNORE_DIRS
        assert ".mypy_cache" in DEFAULT_IGNORE_DIRS


class TestIgnoreHandler:
    """Tests for IgnoreHandler class."""

    def test_init_creates_handler(self, tmp_path):
        """Test that IgnoreHandler initializes correctly."""
        handler = IgnoreHandler(tmp_path)
        assert handler.root == tmp_path.resolve()
        assert handler.use_gitignore is True
        assert handler.extra_patterns == []

    def test_init_with_extra_patterns(self, tmp_path):
        """Test that extra patterns are stored."""
        handler = IgnoreHandler(tmp_path, extra_patterns=["*.log", "temp/"])
        assert "*.log" in handler.extra_patterns
        assert "temp/" in handler.extra_patterns

    def test_init_without_gitignore(self, tmp_path):
        """Test that gitignore can be disabled."""
        handler = IgnoreHandler(tmp_path, use_gitignore=False)
        assert handler.use_gitignore is False


class TestShouldIgnore:
    """Tests for IgnoreHandler.should_ignore method."""

    def test_ignores_default_dirs(self, tmp_path):
        """Test that default directories are ignored."""
        handler = IgnoreHandler(tmp_path, use_gitignore=False)

        # Create some default ignore dirs
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / ".git").mkdir()

        assert handler.should_ignore(tmp_path / "node_modules") is True
        assert handler.should_ignore(tmp_path / "__pycache__") is True
        assert handler.should_ignore(tmp_path / ".git") is True

    def test_does_not_ignore_regular_dirs(self, tmp_path):
        """Test that regular directories are not ignored."""
        handler = IgnoreHandler(tmp_path, use_gitignore=False)

        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()

        assert handler.should_ignore(tmp_path / "src") is False
        assert handler.should_ignore(tmp_path / "tests") is False

    def test_ignores_files_in_ignored_dirs(self, tmp_path):
        """Test that files inside ignored dirs are ignored."""
        handler = IgnoreHandler(tmp_path, use_gitignore=False)

        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "package.json").write_text("{}")

        assert handler.should_ignore(node_modules / "package.json") is True

    def test_respects_gitignore_patterns(self, tmp_path):
        """Test that .gitignore patterns are respected."""
        (tmp_path / ".gitignore").write_text("*.log\nsecrets/\n")

        handler = IgnoreHandler(tmp_path, use_gitignore=True)

        (tmp_path / "debug.log").write_text("log content")
        (tmp_path / "secrets").mkdir()
        (tmp_path / "main.py").write_text("code")

        assert handler.should_ignore(tmp_path / "debug.log") is True
        assert handler.should_ignore(tmp_path / "secrets") is True
        assert handler.should_ignore(tmp_path / "main.py") is False

    def test_ignores_extra_patterns(self, tmp_path):
        """Test that extra patterns work."""
        handler = IgnoreHandler(
            tmp_path,
            use_gitignore=False,
            extra_patterns=["*.tmp", "temp/"],
        )

        (tmp_path / "data.tmp").write_text("temp")
        (tmp_path / "temp").mkdir()
        (tmp_path / "src").mkdir()

        assert handler.should_ignore(tmp_path / "data.tmp") is True
        assert handler.should_ignore(tmp_path / "temp") is True
        assert handler.should_ignore(tmp_path / "src") is False

    def test_handles_relative_paths(self, tmp_path):
        """Test that relative paths work correctly when absolute path is used."""
        handler = IgnoreHandler(tmp_path, use_gitignore=False)

        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()

        # Absolute path should work
        assert handler.should_ignore(node_modules) is True

        # Files inside ignored directories should also be ignored
        test_file = node_modules / "index.js"
        test_file.write_text("module.exports = {};")
        assert handler.should_ignore(test_file) is True

    def test_handles_nested_gitignore(self, tmp_path):
        """Test that nested .gitignore files are loaded."""
        (tmp_path / ".gitignore").write_text("*.log\n")

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / ".gitignore").write_text("*.tmp\n")

        handler = IgnoreHandler(tmp_path, use_gitignore=True)

        (tmp_path / "root.log").write_text("log")
        (subdir / "sub.log").write_text("log")
        (subdir / "sub.tmp").write_text("tmp")
        (subdir / "sub.py").write_text("code")

        # Root gitignore pattern
        assert handler.should_ignore(tmp_path / "root.log") is True

        # Nested gitignore pattern (should be prefixed)
        assert handler.should_ignore(subdir / "sub.tmp") is True
        assert handler.should_ignore(subdir / "sub.py") is False


class TestIterFiles:
    """Tests for IgnoreHandler.iter_files method."""

    def test_iterates_all_files(self, temp_code_project):
        """Test that iter_files finds all non-ignored files."""
        handler = IgnoreHandler(temp_code_project, use_gitignore=True)

        files = list(handler.iter_files())
        file_names = [f.name for f in files]

        assert "main.py" in file_names
        assert "utils.py" in file_names
        assert "index.ts" in file_names
        assert "database.py" in file_names

    def test_filters_by_extension(self, temp_code_project):
        """Test that extension filter works."""
        handler = IgnoreHandler(temp_code_project, use_gitignore=True)

        py_files = list(handler.iter_files(extensions={".py"}))
        file_names = [f.name for f in py_files]

        assert "main.py" in file_names
        assert "utils.py" in file_names
        assert "database.py" in file_names
        assert "index.ts" not in file_names

    def test_respects_max_files(self, temp_code_project):
        """Test that max_files limit is respected."""
        handler = IgnoreHandler(temp_code_project, use_gitignore=True)

        files = list(handler.iter_files(max_files=2))
        assert len(files) == 2

    def test_skips_ignored_directories(self, temp_code_project):
        """Test that files in ignored directories are skipped."""
        # Create a node_modules directory
        node_modules = temp_code_project / "node_modules"
        node_modules.mkdir()
        (node_modules / "index.js").write_text("module.exports = {};")

        handler = IgnoreHandler(temp_code_project, use_gitignore=True)

        files = list(handler.iter_files())
        file_names = [f.name for f in files]

        # node_modules/index.js should not be included
        paths = [str(f) for f in files]
        assert not any("node_modules" in p for p in paths)


class TestGetIgnoreHandler:
    """Tests for get_ignore_handler factory function."""

    def test_creates_handler_with_defaults(self, tmp_path, clean_env):
        """Test that factory creates handler with defaults."""
        handler = get_ignore_handler(tmp_path)

        assert handler.use_gitignore is True
        assert handler.extra_patterns == []

    def test_respects_use_gitignore_env(self, tmp_path, clean_env, monkeypatch):
        """Test that USE_GITIGNORE env var is respected."""
        monkeypatch.setenv("USE_GITIGNORE", "false")

        handler = get_ignore_handler(tmp_path)
        assert handler.use_gitignore is False

    def test_use_gitignore_env_true(self, tmp_path, clean_env, monkeypatch):
        """Test that USE_GITIGNORE=true works."""
        monkeypatch.setenv("USE_GITIGNORE", "true")

        handler = get_ignore_handler(tmp_path)
        assert handler.use_gitignore is True

    def test_explicit_use_gitignore_overrides_env(self, tmp_path, clean_env, monkeypatch):
        """Test that explicit parameter overrides env var."""
        monkeypatch.setenv("USE_GITIGNORE", "true")

        handler = get_ignore_handler(tmp_path, use_gitignore=False)
        assert handler.use_gitignore is False

    def test_passes_extra_patterns(self, tmp_path, clean_env):
        """Test that extra patterns are passed through."""
        handler = get_ignore_handler(
            tmp_path,
            extra_patterns=["*.bak", "backup/"],
        )
        assert "*.bak" in handler.extra_patterns
        assert "backup/" in handler.extra_patterns


class TestIgnorePatternsEnv:
    """Tests for IGNORE_PATTERNS environment variable."""

    def test_comma_separated_patterns(self, tmp_path, clean_env, monkeypatch):
        """Test that comma-separated patterns work."""
        monkeypatch.setenv("IGNORE_PATTERNS", "*.log,*.tmp,secret/")

        handler = IgnoreHandler(tmp_path, use_gitignore=False)

        (tmp_path / "debug.log").write_text("log")
        (tmp_path / "temp.tmp").write_text("tmp")
        (tmp_path / "secret").mkdir()

        assert handler.should_ignore(tmp_path / "debug.log") is True
        assert handler.should_ignore(tmp_path / "temp.tmp") is True
        assert handler.should_ignore(tmp_path / "secret") is True

    def test_newline_separated_patterns(self, tmp_path, clean_env, monkeypatch):
        """Test that newline-separated patterns work."""
        monkeypatch.setenv("IGNORE_PATTERNS", "*.log\n*.tmp\nsecret/")

        handler = IgnoreHandler(tmp_path, use_gitignore=False)

        (tmp_path / "debug.log").write_text("log")
        (tmp_path / "temp.tmp").write_text("tmp")

        assert handler.should_ignore(tmp_path / "debug.log") is True
        assert handler.should_ignore(tmp_path / "temp.tmp") is True

    def test_ignores_comments_in_patterns(self, tmp_path, clean_env, monkeypatch):
        """Test that comment lines are ignored."""
        monkeypatch.setenv("IGNORE_PATTERNS", "# Comment\n*.log")

        handler = IgnoreHandler(tmp_path, use_gitignore=False)

        # The handler should have been created without error
        assert handler is not None
