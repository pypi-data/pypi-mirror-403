"""Tests for indexer.py - chunking and file iteration logic (no heavy deps)."""

import pytest
from pathlib import Path

from claude_lfr_mcp.indexer import (
    CODE_EXTS,
    chunk_file,
    iter_code_files,
)
from claude_lfr_mcp.ignore import get_ignore_handler


class TestCodeExts:
    """Tests for CODE_EXTS constant."""

    def test_contains_python(self):
        """Test that Python extension is included."""
        assert ".py" in CODE_EXTS

    def test_contains_typescript(self):
        """Test that TypeScript extensions are included."""
        assert ".ts" in CODE_EXTS
        assert ".tsx" in CODE_EXTS

    def test_contains_javascript(self):
        """Test that JavaScript extensions are included."""
        assert ".js" in CODE_EXTS
        assert ".jsx" in CODE_EXTS

    def test_contains_systems_languages(self):
        """Test that systems languages are included."""
        assert ".rs" in CODE_EXTS  # Rust
        assert ".go" in CODE_EXTS  # Go
        assert ".c" in CODE_EXTS
        assert ".cpp" in CODE_EXTS
        assert ".h" in CODE_EXTS
        assert ".hpp" in CODE_EXTS

    def test_contains_enterprise_languages(self):
        """Test that enterprise languages are included."""
        assert ".java" in CODE_EXTS
        assert ".cs" in CODE_EXTS
        assert ".php" in CODE_EXTS


class TestChunkFile:
    """Tests for chunk_file function."""

    def test_chunks_small_file(self, tmp_path):
        """Test that a small file creates a single chunk."""
        repo_root = tmp_path
        test_file = tmp_path / "small.py"
        test_file.write_text("""def hello():
    print("Hello, world!")
""")

        chunks = chunk_file(test_file, repo_root)

        assert len(chunks) == 1
        rel_path, start, end, text = chunks[0]
        assert rel_path == "small.py"
        assert start == 1
        # File has 2 lines (def hello(): and print statement)
        assert end == 2
        assert "def hello():" in text

    def test_chunks_large_file(self, tmp_path, long_file_content):
        """Test that a large file creates multiple chunks."""
        repo_root = tmp_path
        test_file = tmp_path / "large.py"
        test_file.write_text(long_file_content)

        chunks = chunk_file(test_file, repo_root, max_lines=80)

        # 800 lines / 80 lines per chunk = 10 chunks
        assert len(chunks) == 10

        # Check first chunk
        rel_path, start, end, text = chunks[0]
        assert start == 1
        assert end == 80

        # Check second chunk
        rel_path, start, end, text = chunks[1]
        assert start == 81
        assert end == 160

    def test_custom_max_lines(self, tmp_path):
        """Test that max_lines parameter works."""
        repo_root = tmp_path
        test_file = tmp_path / "medium.py"
        content = "\n".join([f"line_{i}" for i in range(100)])
        test_file.write_text(content)

        # With max_lines=25, should create 4 chunks
        chunks = chunk_file(test_file, repo_root, max_lines=25)
        assert len(chunks) == 4

        # With max_lines=50, should create 2 chunks
        chunks = chunk_file(test_file, repo_root, max_lines=50)
        assert len(chunks) == 2

    def test_empty_file_returns_empty(self, tmp_path):
        """Test that empty file returns no chunks."""
        repo_root = tmp_path
        test_file = tmp_path / "empty.py"
        test_file.write_text("")

        chunks = chunk_file(test_file, repo_root)
        assert chunks == []

    def test_whitespace_only_file_returns_empty(self, tmp_path):
        """Test that whitespace-only file returns no chunks."""
        repo_root = tmp_path
        test_file = tmp_path / "whitespace.py"
        test_file.write_text("   \n\n   \n   ")

        chunks = chunk_file(test_file, repo_root)
        assert chunks == []

    def test_relative_path_in_subdirectory(self, tmp_path):
        """Test that relative paths are correct for subdirectories."""
        repo_root = tmp_path
        subdir = tmp_path / "src" / "lib"
        subdir.mkdir(parents=True)
        test_file = subdir / "module.py"
        test_file.write_text("def func(): pass")

        chunks = chunk_file(test_file, repo_root)

        assert len(chunks) == 1
        rel_path, _, _, _ = chunks[0]
        assert rel_path == "src/lib/module.py"

    def test_handles_binary_file_gracefully(self, tmp_path):
        """Test that binary files don't crash."""
        repo_root = tmp_path
        binary_file = tmp_path / "binary.py"
        binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe")

        # Should not raise, but content may be garbled
        chunks = chunk_file(binary_file, repo_root)
        # Either empty or contains something
        assert isinstance(chunks, list)

    def test_handles_nonexistent_file(self, tmp_path):
        """Test that nonexistent file returns empty list."""
        repo_root = tmp_path
        nonexistent = tmp_path / "does_not_exist.py"

        chunks = chunk_file(nonexistent, repo_root)
        assert chunks == []

    def test_handles_encoding_errors(self, tmp_path):
        """Test that files with encoding issues are handled."""
        repo_root = tmp_path
        bad_encoding = tmp_path / "bad_encoding.py"
        # Write invalid UTF-8 sequences
        bad_encoding.write_bytes(b"valid text\n\x80\x81\x82\nmore text")

        chunks = chunk_file(bad_encoding, repo_root)
        # Should not crash, errors="ignore" should handle it
        assert len(chunks) >= 1


class TestIterCodeFiles:
    """Tests for iter_code_files function."""

    def test_finds_code_files(self, temp_code_project):
        """Test that code files are found."""
        files = list(iter_code_files(temp_code_project))

        file_names = [f.name for f in files]
        assert "main.py" in file_names
        assert "utils.py" in file_names
        assert "index.ts" in file_names
        assert "database.py" in file_names

    def test_respects_max_files(self, temp_code_project):
        """Test that max_files limit is respected."""
        files = list(iter_code_files(temp_code_project, max_files=2))
        assert len(files) == 2

    def test_skips_ignored_directories(self, temp_code_project):
        """Test that ignored directories are skipped."""
        # Create node_modules
        node_modules = temp_code_project / "node_modules"
        node_modules.mkdir()
        (node_modules / "lodash.js").write_text("module.exports = {};")

        files = list(iter_code_files(temp_code_project))

        paths = [str(f) for f in files]
        assert not any("node_modules" in p for p in paths)

    def test_only_returns_code_extensions(self, temp_code_project):
        """Test that only code file extensions are returned."""
        # Create non-code files
        (temp_code_project / "readme.md").write_text("# README")
        (temp_code_project / "data.json").write_text("{}")
        (temp_code_project / "style.css").write_text("body {}")

        files = list(iter_code_files(temp_code_project))

        file_names = [f.name for f in files]
        assert "readme.md" not in file_names
        assert "data.json" not in file_names
        assert "style.css" not in file_names

    def test_uses_custom_ignore_handler(self, temp_code_project):
        """Test that custom ignore handler is used."""
        # Create a handler that ignores lib/
        handler = get_ignore_handler(
            temp_code_project,
            extra_patterns=["lib/"],
        )

        files = list(iter_code_files(
            temp_code_project,
            ignore_handler=handler,
        ))

        paths = [str(f) for f in files]
        # lib/database.py should be excluded
        assert not any("lib" in p for p in paths)

    def test_respects_gitignore(self, temp_code_project):
        """Test that .gitignore patterns are respected."""
        # The fixture already has a .gitignore with __pycache__/
        pycache = temp_code_project / "__pycache__"
        pycache.mkdir()
        (pycache / "module.cpython-310.pyc").write_bytes(b"compiled")

        files = list(iter_code_files(temp_code_project))

        paths = [str(f) for f in files]
        assert not any("__pycache__" in p for p in paths)


class TestChunkLineNumbers:
    """Tests for correct line numbering in chunks."""

    def test_first_chunk_starts_at_one(self, tmp_path):
        """Test that first chunk starts at line 1."""
        repo_root = tmp_path
        test_file = tmp_path / "test.py"
        test_file.write_text("\n".join([f"line {i}" for i in range(50)]))

        chunks = chunk_file(test_file, repo_root)

        _, start, _, _ = chunks[0]
        assert start == 1

    def test_chunk_boundaries_are_correct(self, tmp_path):
        """Test that chunk boundaries don't overlap or have gaps."""
        repo_root = tmp_path
        test_file = tmp_path / "test.py"
        # 160 lines -> 2 chunks of 80
        test_file.write_text("\n".join([f"line {i}" for i in range(160)]))

        chunks = chunk_file(test_file, repo_root, max_lines=80)

        assert len(chunks) == 2

        # First chunk: 1-80
        _, start1, end1, _ = chunks[0]
        assert start1 == 1
        assert end1 == 80

        # Second chunk: 81-160
        _, start2, end2, _ = chunks[1]
        assert start2 == 81
        assert end2 == 160

    def test_last_chunk_end_matches_file_length(self, tmp_path):
        """Test that last chunk ends at correct line."""
        repo_root = tmp_path
        test_file = tmp_path / "test.py"
        # 100 lines -> chunk 1: 1-80, chunk 2: 81-100
        test_file.write_text("\n".join([f"line {i}" for i in range(100)]))

        chunks = chunk_file(test_file, repo_root, max_lines=80)

        assert len(chunks) == 2

        _, _, end, _ = chunks[-1]
        assert end == 100
