"""Test absolute path handling across platforms.

These tests verify that the `absolute=True` parameter returns proper absolute paths
without any `..` components, which is critical for macOS and Windows where ripgrep
may return relative paths with parent directory references.
"""

import os
import tempfile
from pathlib import Path

import pytest

from ripgrep_rs import files


class TestAbsolutePaths:
    """Tests for absolute path handling."""

    def test_absolute_paths_basic(self):
        """Basic test: absolute=True should return absolute paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "file1.txt").write_text("content1")

            result = files(
                patterns=["*"],
                paths=[str(tmppath)],
                absolute=True,
            )

            assert len(result) == 1
            path = result[0]
            assert Path(path).is_absolute(), f"Path is not absolute: {path}"
            assert ".." not in path, f"Path contains '..': {path}"

    def test_absolute_paths_multiple_files(self):
        """Test with multiple files including subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "file1.txt").write_text("content1")
            (tmppath / "file2.txt").write_text("content2")
            subdir = tmppath / "subdir"
            subdir.mkdir()
            (subdir / "file3.txt").write_text("content3")

            result = files(
                patterns=["*"],
                paths=[str(tmppath)],
                absolute=True,
            )

            assert len(result) == 3, f"Expected 3 files, got {len(result)}: {result}"

            for path in result:
                assert Path(path).is_absolute(), f"Path is not absolute: {path}"
                assert ".." not in path, f"Path contains '..': {path}"

            # Verify filenames
            filenames = {Path(p).name for p in result}
            assert filenames == {"file1.txt", "file2.txt", "file3.txt"}

    def test_absolute_paths_with_resolved_input(self):
        """Test that resolved input paths work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir).resolve()  # Explicitly resolve
            (tmppath / "test.txt").write_text("hello")

            result = files(
                patterns=["*"],
                paths=[str(tmppath)],
                absolute=True,
            )

            assert len(result) == 1
            path = result[0]
            assert Path(path).is_absolute(), f"Path is not absolute: {path}"
            assert ".." not in path, f"Path contains '..': {path}"

    def test_absolute_paths_different_cwd(self):
        """Test that absolute paths work when cwd differs from search path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "test.txt").write_text("hello")

            original_cwd = os.getcwd()
            try:
                # Change to a different directory
                os.chdir(tempfile.gettempdir())

                result = files(
                    patterns=["*"],
                    paths=[str(tmppath)],
                    absolute=True,
                )

                assert len(result) == 1
                path = result[0]
                assert Path(path).is_absolute(), f"Path is not absolute: {path}"
                assert ".." not in path, f"Path contains '..': {path}"
            finally:
                os.chdir(original_cwd)

    def test_absolute_false_returns_paths(self):
        """Test that absolute=False returns paths (format varies by platform)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "test.txt").write_text("hello")

            result = files(
                patterns=["*"],
                paths=[str(tmppath)],
                absolute=False,
            )

            assert len(result) == 1

    def test_absolute_paths_deeply_nested(self):
        """Test with deeply nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            deep = tmppath / "a" / "b" / "c" / "d" / "e"
            deep.mkdir(parents=True)
            (deep / "deep.txt").write_text("deep content")

            result = files(
                patterns=["*"],
                paths=[str(tmppath)],
                absolute=True,
            )

            assert len(result) == 1
            path = result[0]
            assert Path(path).is_absolute(), f"Path is not absolute: {path}"
            assert ".." not in path, f"Path contains '..': {path}"
            assert "deep.txt" in path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
