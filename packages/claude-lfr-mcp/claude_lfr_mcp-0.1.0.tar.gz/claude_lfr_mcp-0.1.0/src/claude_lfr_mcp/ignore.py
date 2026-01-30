"""Gitignore-style pattern handling for code indexing."""

import os
from pathlib import Path
from typing import Iterator, List, Optional, Set

import pathspec

# Expanded default ignore directories
DEFAULT_IGNORE_DIRS: Set[str] = {
    # Version control
    ".git",
    # IDE/Editor configs
    ".devcontainer",
    # Dependencies
    "node_modules",
    ".venv",
    "venv",
    "env",
    "ENV",
    ".eggs",
    # Build outputs
    "dist",
    "build",
    "out",
    "target",
    # Python caches
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    # JavaScript caches
    ".next",
    ".nuxt",
    ".svelte-kit",
    # General caches
    ".cache",
    ".coverage",
}


class IgnoreHandler:
    """Handles gitignore-style pattern matching for file exclusion."""

    def __init__(
        self,
        root: Path,
        use_gitignore: bool = True,
        extra_patterns: Optional[List[str]] = None,
    ):
        """Initialize the ignore handler.

        Args:
            root: Root directory for the project.
            use_gitignore: Whether to parse .gitignore files.
            extra_patterns: Additional patterns to ignore (gitignore syntax).
        """
        self.root = root.resolve()
        self.use_gitignore = use_gitignore
        self.extra_patterns = extra_patterns or []

        # Build the combined pattern spec
        self._spec = self._build_spec()

    def _build_spec(self) -> pathspec.GitIgnoreSpec:
        """Build the combined pathspec from all pattern sources."""
        patterns: List[str] = []

        # 1. Default ignore directories (always applied)
        for dir_name in DEFAULT_IGNORE_DIRS:
            patterns.append(f"{dir_name}/")

        # 2. IGNORE_PATTERNS environment variable
        env_patterns = os.getenv("IGNORE_PATTERNS", "")
        if env_patterns:
            # Support both comma and newline separation
            for line in env_patterns.replace(",", "\n").split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)

        # 3. Extra patterns from CLI or MCP
        for pattern in self.extra_patterns:
            pattern = pattern.strip()
            if pattern and not pattern.startswith("#"):
                patterns.append(pattern)

        # 4. Load .gitignore files if enabled
        if self.use_gitignore:
            patterns.extend(self._load_gitignore_files())

        return pathspec.GitIgnoreSpec.from_lines(patterns)

    def _load_gitignore_files(self) -> List[str]:
        """Load all .gitignore files recursively from the root."""
        patterns: List[str] = []

        # Walk through directory to find all .gitignore files
        for gitignore_path in self.root.rglob(".gitignore"):
            try:
                rel_dir = gitignore_path.parent.relative_to(self.root)
                prefix = str(rel_dir) + "/" if rel_dir != Path(".") else ""

                with gitignore_path.open("r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Prefix patterns with the relative directory
                            if prefix and not line.startswith("/"):
                                patterns.append(f"{prefix}{line}")
                            elif prefix and line.startswith("/"):
                                # Rooted patterns become relative to the gitignore location
                                patterns.append(f"{prefix}{line[1:]}")
                            else:
                                patterns.append(line)
            except OSError:
                continue

        return patterns

    def should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored.

        Args:
            path: Path to check (can be absolute or relative to root).

        Returns:
            True if the path should be ignored.
        """
        # Ensure we have a relative path for matching
        try:
            if path.is_absolute():
                rel_path = path.relative_to(self.root)
            else:
                rel_path = path
        except ValueError:
            # Path is outside root
            return True

        # Convert to posix-style path for matching
        path_str = rel_path.as_posix()

        # For directories, append a slash for proper matching
        if path.is_dir():
            path_str = path_str.rstrip("/") + "/"

        return self._spec.match_file(path_str)

    def iter_files(
        self,
        extensions: Optional[Set[str]] = None,
        max_files: int = 0,
    ) -> Iterator[Path]:
        """Iterate over non-ignored files in the root directory.

        Args:
            extensions: Set of file extensions to include (with dot, e.g., {'.py'}).
            max_files: Maximum number of files to yield (0 = no limit).

        Yields:
            Paths to non-ignored files.
        """
        count = 0
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue

            if self.should_ignore(path):
                continue

            if extensions and path.suffix.lower() not in extensions:
                continue

            yield path
            count += 1
            if max_files and count >= max_files:
                break


def get_ignore_handler(
    root: Path,
    use_gitignore: Optional[bool] = None,
    extra_patterns: Optional[List[str]] = None,
) -> IgnoreHandler:
    """Create an IgnoreHandler with environment variable defaults.

    Args:
        root: Root directory for the project.
        use_gitignore: Whether to parse .gitignore files.
                       If None, uses USE_GITIGNORE env var (default: true).
        extra_patterns: Additional patterns to ignore.

    Returns:
        Configured IgnoreHandler instance.
    """
    if use_gitignore is None:
        env_val = os.getenv("USE_GITIGNORE", "true").lower()
        use_gitignore = env_val not in ("false", "0", "no")

    return IgnoreHandler(
        root=root,
        use_gitignore=use_gitignore,
        extra_patterns=extra_patterns,
    )
