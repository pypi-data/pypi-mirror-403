"""Sandbox for isolating file system side effects during agent testing."""

import os
import tempfile
from pathlib import Path
from typing import Any


class Sandbox:
    """
    A context manager that isolates file system operations.

    Creates a temporary directory and changes into it, so any files
    created by the agent are isolated from the user's actual project.

    Example:
        with Sandbox() as box:
            agent.run("Create a file called output.txt")
            content = box.get_file_content("output.txt")
            assert "expected" in content
    """

    def __init__(self, prefix: str = "agent_eval_"):
        """
        Initialize the sandbox.

        Args:
            prefix: Prefix for the temporary directory name.
        """
        self.prefix = prefix
        self._temp_dir: tempfile.TemporaryDirectory | None = None
        self._original_cwd: str | None = None
        self._sandbox_path: Path | None = None

    def __enter__(self) -> "Sandbox":
        """
        Enter the sandbox context.

        Creates a temporary directory and changes into it.
        """
        # Save the original working directory
        self._original_cwd = os.getcwd()

        # Create temporary directory
        self._temp_dir = tempfile.TemporaryDirectory(prefix=self.prefix)
        self._sandbox_path = Path(self._temp_dir.name)

        # Change into the sandbox directory
        os.chdir(self._sandbox_path)

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit the sandbox context.

        Restores the original working directory and cleans up the temp dir.
        Always restores the directory, even if an exception occurred.
        """
        try:
            # Always restore the original working directory
            if self._original_cwd is not None:
                os.chdir(self._original_cwd)
        finally:
            # Clean up the temporary directory
            if self._temp_dir is not None:
                try:
                    self._temp_dir.cleanup()
                except Exception:
                    # Ignore cleanup errors (e.g., if files are still open)
                    pass

    @property
    def path(self) -> Path:
        """Get the path to the sandbox directory."""
        if self._sandbox_path is None:
            raise RuntimeError("Sandbox is not active. Use within a 'with' statement.")
        return self._sandbox_path

    def file_exists(self, filename: str) -> bool:
        """
        Check if a file exists in the sandbox.

        Args:
            filename: Name or relative path of the file.

        Returns:
            True if the file exists, False otherwise.
        """
        if self._sandbox_path is None:
            raise RuntimeError("Sandbox is not active. Use within a 'with' statement.")
        return (self._sandbox_path / filename).exists()

    def get_file_content(self, filename: str, encoding: str = "utf-8") -> str:
        """
        Read the content of a file in the sandbox.

        Args:
            filename: Name or relative path of the file.
            encoding: Text encoding (default: utf-8).

        Returns:
            The file contents as a string.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            RuntimeError: If sandbox is not active.
        """
        if self._sandbox_path is None:
            raise RuntimeError("Sandbox is not active. Use within a 'with' statement.")

        file_path = self._sandbox_path / filename
        return file_path.read_text(encoding=encoding)

    def get_file_bytes(self, filename: str) -> bytes:
        """
        Read the content of a file as bytes.

        Args:
            filename: Name or relative path of the file.

        Returns:
            The file contents as bytes.
        """
        if self._sandbox_path is None:
            raise RuntimeError("Sandbox is not active. Use within a 'with' statement.")

        file_path = self._sandbox_path / filename
        return file_path.read_bytes()

    def get_file_size(self, filename: str) -> int:
        """
        Get the size of a file in bytes.

        Args:
            filename: Name or relative path of the file.

        Returns:
            File size in bytes, or -1 if file doesn't exist.
        """
        if self._sandbox_path is None:
            raise RuntimeError("Sandbox is not active. Use within a 'with' statement.")

        file_path = self._sandbox_path / filename
        if file_path.exists():
            return file_path.stat().st_size
        return -1

    def list_files(self, pattern: str = "*") -> list[str]:
        """
        List files in the sandbox matching a pattern.

        Args:
            pattern: Glob pattern (default: "*" for all files).

        Returns:
            List of filenames matching the pattern.
        """
        if self._sandbox_path is None:
            raise RuntimeError("Sandbox is not active. Use within a 'with' statement.")

        return [p.name for p in self._sandbox_path.glob(pattern) if p.is_file()]

    def list_all(self, pattern: str = "**/*") -> list[str]:
        """
        List all files and directories recursively.

        Args:
            pattern: Glob pattern (default: "**/*" for recursive).

        Returns:
            List of relative paths.
        """
        if self._sandbox_path is None:
            raise RuntimeError("Sandbox is not active. Use within a 'with' statement.")

        return [
            str(p.relative_to(self._sandbox_path))
            for p in self._sandbox_path.glob(pattern)
        ]
