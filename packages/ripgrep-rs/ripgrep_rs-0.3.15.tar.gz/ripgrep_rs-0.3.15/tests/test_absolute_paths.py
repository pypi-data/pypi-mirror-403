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

    def test_glob_with_absolute_like_upathtools(self):
        """Test that matches exactly what upathtools does in _glob.

        This mirrors the upathtools async_local_fs._glob implementation:
        - Uses resolved base path
        - Uses glob pattern
        - Passes absolute=True
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "file1.txt").write_text("content1")
            (tmppath / "file2.txt").write_text("content2")
            subdir = tmppath / "subdir"
            subdir.mkdir()
            (subdir / "file3.txt").write_text("content3")

            # This is exactly what upathtools does
            abs_base = str(Path(tmpdir).resolve())
            glob_pattern = "**/*.txt"

            result = files(
                patterns=["*"],
                paths=[abs_base],
                globs=[glob_pattern],
                hidden=False,
                no_ignore=False,
                max_depth=None,
                absolute=True,
            )

            assert len(result) == 3, f"Expected 3 files, got {len(result)}: {result}"

            for path in result:
                assert Path(path).is_absolute(), f"Path is not absolute: {path}"
                assert ".." not in path, f"Path contains '..': {path}"

            # Verify we can compute relative paths from base
            for path in result:
                rel = os.path.relpath(path, abs_base)
                # rel should be like "file1.txt" or "subdir/file3.txt", not "../../..."
                assert not rel.startswith(".."), f"Relative path escapes base: {rel}"

    def test_upathtools_read_folder_scenario(self):
        """Exact reproduction of the failing upathtools test_read_folder scenario.

        upathtools test creates:
        - file1.txt
        - file2.txt
        - subdir/file3.txt
        - subdir/file4.py

        Then calls read_folder with pattern="**/*.txt" which should find 3 .txt files.
        The bug was that paths came back as ../../../../../../private/var/... on macOS.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)

            # Create test files exactly as upathtools does
            (test_dir / "file1.txt").write_text("content1")
            (test_dir / "file2.txt").write_text("content2")
            subdir = test_dir / "subdir"
            subdir.mkdir()
            (subdir / "file3.txt").write_text("content3")
            (subdir / "file4.py").write_text("print('hello')")

            # Call ripgrep exactly as upathtools _glob does
            abs_base = str(test_dir.resolve())

            result = files(
                patterns=["*"],
                paths=[abs_base],
                globs=["**/*.txt"],
                hidden=False,
                no_ignore=False,
                max_depth=None,
                absolute=True,
            )

            # Should find 3 .txt files
            assert len(result) == 3, f"Expected 3 files, got {len(result)}: {result}"

            # All paths must be absolute without .. components
            for file_path in result:
                assert Path(file_path).is_absolute(), f"Not absolute: {file_path}"
                assert ".." not in file_path, f"Contains '..': {file_path}"

            # Compute relative paths as upathtools does
            rel_paths = set()
            for file_path in result:
                rel_path = os.path.relpath(str(file_path), str(abs_base))
                rel_paths.add(rel_path)
                # This is the key assertion - rel_path should NOT start with ..
                assert not rel_path.startswith(".."), (
                    f"Relative path escapes base: {rel_path} (from {file_path})"
                )

            # Check expected files are found
            expected = {"file1.txt", "file2.txt", os.path.join("subdir", "file3.txt")}
            assert rel_paths == expected, f"Expected {expected}, got {rel_paths}"

    def test_unresolved_input_path(self):
        """Test with non-resolved input path (like upathtools fixture provides).

        On Windows, tempfile.TemporaryDirectory may return short 8.3 paths like
        C:/Users/RUNNER~1/... but files are at C:/Users/runneradmin/...

        On macOS, /var is a symlink to /private/var.

        The key is: when absolute=True, the returned paths should be usable
        with os.path.relpath() against the ORIGINAL input path.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use Path(tmpdir) but NOT .resolve() - this is what upathtools does
            test_dir = Path(tmpdir)
            (test_dir / "file1.txt").write_text("content1")

            # upathtools passes: str(Path(base).resolve())
            # But the base_path used for relpath is the ORIGINAL test_dir
            abs_base = str(test_dir.resolve())

            result = files(
                patterns=["*"],
                paths=[abs_base],
                absolute=True,
            )

            assert len(result) == 1
            path = result[0]
            assert Path(path).is_absolute(), f"Path is not absolute: {path}"
            assert ".." not in path, f"Path contains '..': {path}"

            # Key test: relative path from the RESOLVED base should work
            rel = os.path.relpath(path, abs_base)
            assert not rel.startswith(".."), (
                f"Relative path escapes base: {rel} (path={path}, base={abs_base})"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestFilesWithInfo:
    """Tests for files_with_info function."""

    def test_files_with_info_basic(self):
        """Basic test: files_with_info returns dict with FileInfo objects."""
        from ripgrep_rs import FileInfo, files_with_info

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            test_file = tmppath / "file1.txt"
            test_file.write_text("content1")

            result = files_with_info(
                patterns=["*"],
                paths=[str(tmppath)],
                absolute=True,
            )

            assert len(result) == 1
            path, info = next(iter(result.items()))

            # Check path is absolute
            assert Path(path).is_absolute()
            assert ".." not in path

            # Check FileInfo attributes
            assert isinstance(info, FileInfo)
            assert info.name == path
            assert info.size == len("content1")
            assert info.type == "file"
            assert info.mtime > 0
            assert info.islink is False

    def test_files_with_info_multiple_files(self):
        """Test files_with_info with multiple files."""
        from ripgrep_rs import files_with_info

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "file1.txt").write_text("a")
            (tmppath / "file2.txt").write_text("bb")
            (tmppath / "file3.txt").write_text("ccc")

            result = files_with_info(
                patterns=["*"],
                paths=[str(tmppath)],
                globs=["*.txt"],
                absolute=True,
            )

            assert len(result) == 3

            # Check sizes match content
            sizes = {info.size for info in result.values()}
            assert sizes == {1, 2, 3}

    def test_files_with_info_matches_fsspec_format(self):
        """Test that FileInfo has all fields expected by fsspec."""
        from ripgrep_rs import files_with_info

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "test.txt").write_text("test content")

            result = files_with_info(
                patterns=["*"],
                paths=[str(tmppath)],
                absolute=True,
            )

            info = next(iter(result.values()))

            # All fsspec fields should be present
            assert hasattr(info, "name")
            assert hasattr(info, "size")
            assert hasattr(info, "type")
            assert hasattr(info, "created")
            assert hasattr(info, "islink")
            assert hasattr(info, "mode")
            assert hasattr(info, "uid")
            assert hasattr(info, "gid")
            assert hasattr(info, "mtime")
            assert hasattr(info, "ino")
            assert hasattr(info, "nlink")

    def test_files_with_info_with_glob(self):
        """Test files_with_info with glob patterns."""
        from ripgrep_rs import files_with_info

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "file.py").write_text("python")
            (tmppath / "file.txt").write_text("text")
            (tmppath / "file.rs").write_text("rust")

            result = files_with_info(
                patterns=["*"],
                paths=[str(tmppath)],
                globs=["*.py"],
                absolute=True,
            )

            assert len(result) == 1
            path = next(iter(result.keys()))
            assert path.endswith(".py")
