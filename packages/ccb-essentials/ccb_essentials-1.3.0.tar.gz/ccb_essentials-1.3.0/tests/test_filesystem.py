"""Unit tests"""

import os
from pathlib import Path
from random import random
from shutil import SameFileError
from tempfile import TemporaryDirectory

import pytest

from ccb_essentials.filesystem import (
    assert_real_dir,
    assert_real_file,
    assert_real_path,
    clone_file,
    real_path,
    temporary_path,
    tree,
)


def _expand(path: str) -> str:
    return os.path.realpath(os.path.expanduser(path))


class TestRealPath:
    """Unit tests for real_path()"""

    @staticmethod
    def test_absolute_path() -> None:
        """It should resolve an absolute path to the same path."""
        absolute_path = "/dev"  # This path should exist on all Posix systems.
        real = real_path(absolute_path, check_exists=True, mkdir=False)
        assert real is not None
        assert str(real) == absolute_path

    @staticmethod
    def test_path_type() -> None:
        """It should handle Path input the same as str."""
        absolute_path = Path("/dev")
        real = real_path(absolute_path, check_exists=True, mkdir=False)
        assert real is not None
        assert str(real) == str(absolute_path)

    @staticmethod
    def test_clean_slash() -> None:
        """It should clean up redundant directory separators."""
        absolute_path = "/dev"
        real = real_path("/" + absolute_path + "/", check_exists=True, mkdir=False)
        assert real is not None
        assert str(real) == absolute_path

    @staticmethod
    def test_nonexistent_path() -> None:
        """It should return None for a nonexistent path."""
        with TemporaryDirectory() as root:
            unknown_path = _expand(root) + "/unknown"
            real = real_path(unknown_path, check_exists=True, mkdir=False)
            assert real is None
            real = real_path(unknown_path, check_exists=False, mkdir=False)
            assert str(real) == unknown_path

    @staticmethod
    def test_file() -> None:
        """It should find a file on the filesystem if it exists."""
        with TemporaryDirectory() as root:
            new_path = _expand(root) + "/new"
            Path(new_path).touch()
            real = real_path(new_path, check_exists=True, mkdir=False)
            assert str(real) == new_path
            real = real_path(new_path, check_exists=False, mkdir=False)
            assert str(real) == new_path

    @staticmethod
    def test_directory() -> None:
        """It should find a directory on the filesystem if it exists."""
        with TemporaryDirectory() as root:
            new_path = _expand(root) + "/new"
            os.mkdir(new_path)
            real = real_path(new_path, check_exists=True, mkdir=False)
            assert str(real) == new_path
            real = real_path(new_path, check_exists=False, mkdir=False)
            assert str(real) == new_path

    @staticmethod
    def test_mkdir() -> None:
        """It should create a new directory if needed."""
        with TemporaryDirectory() as root:
            new_path = _expand(root) + "/new"
            real = real_path(new_path, check_exists=True, mkdir=False)
            assert real is None
            assert not Path(new_path).exists()
            real = real_path(new_path, check_exists=True, mkdir=True)
            assert str(real) == new_path
            assert Path(new_path).exists()

    @staticmethod
    def test_follow_symlink() -> None:
        """It should resolve a symlink to the destination path."""
        with TemporaryDirectory() as root:
            new_path = _expand(root) + "/new"
            Path(new_path).touch()
            link_path = _expand(root) + "/link"
            os.symlink(new_path, link_path)
            real = real_path(link_path, check_exists=True, mkdir=False)
            assert str(real) == new_path

    @staticmethod
    def test_expand_user() -> None:
        """It should expand a home directory to an absolute path."""
        user_dir = os.path.expanduser("~")
        new_file = "test_expand_user-" + str(int(random() * 1000000000))
        new_path = user_dir + "/" + new_file
        user_path = "~/" + new_file
        real = real_path(user_path, check_exists=False, mkdir=False)
        assert str(real) == new_path


class TestAssertRealPath:
    """Unit tests for assert_real_path()"""

    @staticmethod
    def test_assert_absolute_path() -> None:
        """It should resolve an absolute path to the same path."""
        absolute_path = "/dev"  # This path should exist on all Posix systems.
        real = assert_real_path(absolute_path, mkdir=False)
        assert str(real) == absolute_path

    @staticmethod
    def test_assert_nonexistent_path() -> None:
        """It should raise an exception for a nonexistent path."""
        with TemporaryDirectory() as root:
            unknown_path = _expand(root) + "/unknown"
            with pytest.raises(FileNotFoundError):
                assert_real_path(unknown_path, mkdir=False)

    @staticmethod
    def test_assert_mkdir() -> None:
        """It should create a new directory if needed."""
        with TemporaryDirectory() as root:
            new_path = _expand(root) + "/new"
            real = assert_real_path(new_path, mkdir=True)
            assert str(real) == new_path
            assert Path(new_path).exists()


class TestAssertRealFile:
    """Unit tests for assert_real_file()"""

    @staticmethod
    def test_absolute_file_path() -> None:
        """It should resolve an absolute path to the same path."""
        absolute_path = _expand("/bin/ls")  # This path should exist on all Posix systems, though it may be a symlink.
        real = assert_real_file(absolute_path)
        assert str(real) == absolute_path

    @staticmethod
    def test_nonexistent_file_path() -> None:
        """It should raise an exception for a nonexistent path."""
        with TemporaryDirectory() as root:
            unknown_path = _expand(root) + "/unknown"
            with pytest.raises(FileNotFoundError):
                assert_real_file(unknown_path)

    @staticmethod
    def test_dir() -> None:
        """It should raise an exception for a directory."""
        with TemporaryDirectory() as root, pytest.raises(OSError):
            assert_real_file(root)


class TestAssertRealDir:
    """Unit tests for assert_real_dir()"""

    @staticmethod
    def test_absolute_dir_path() -> None:
        """It should resolve an absolute path to the same path."""
        absolute_path = "/dev"  # This path should exist on all Posix systems.
        real = assert_real_dir(absolute_path, mkdir=False)
        assert str(real) == absolute_path

    @staticmethod
    def test_nonexistent_dir_path() -> None:
        """It should raise an exception for a nonexistent path."""
        with TemporaryDirectory() as root:
            unknown_path = _expand(root) + "/unknown"
            with pytest.raises(FileNotFoundError):
                assert_real_dir(unknown_path, mkdir=False)

    @staticmethod
    def test_file() -> None:
        """It should raise an exception for a file."""
        with TemporaryDirectory() as root:
            file_path = _expand(root) + "/file"
            Path(file_path).touch()
            with pytest.raises(NotADirectoryError):
                assert_real_dir(file_path, mkdir=False)

    @staticmethod
    def test_mkdir() -> None:
        """It should create a new directory if needed."""
        with TemporaryDirectory() as root:
            new_path = _expand(root) + "/new"
            real = assert_real_dir(new_path, mkdir=True)
            assert str(real) == new_path
            assert Path(new_path).exists()


class TestTemporaryPath:
    """Unit tests for temporary_path()"""

    @staticmethod
    def test_new_path() -> None:
        """It should create a new path on each invocation."""
        with temporary_path() as path:
            a = str(path)
        with temporary_path() as path:
            b = str(path)
        assert a != b

    @staticmethod
    def test_name() -> None:
        """It should set a custom file name."""
        name = "xyz"
        match_str = "/" + name
        with temporary_path(name=name) as path:
            path_str = str(path)
            assert path_str.find(match_str, len(path_str) - len(match_str)) != -1

    @staticmethod
    def test_touch() -> None:
        """It should touch the file."""
        with temporary_path() as path:
            assert not path.exists()
            assert not path.is_file()
        with temporary_path(touch=True) as path:
            assert path.exists()
            assert path.is_file()


class TestTree:
    """Unit tests for tree()"""

    @staticmethod
    def test_file() -> None:
        """It should list a bare file."""
        name = "xyz"
        expected = [name]
        with temporary_path(name=name) as file:
            file.touch()
            result = list(tree(file))
            assert result == expected

    @staticmethod
    def test_empty_directory() -> None:
        """It should list an empty directory."""
        name = "xyz"
        expected = [name]
        with temporary_path(name=name) as root:
            root.mkdir()
            result = list(tree(root))
            assert result == expected

    @staticmethod
    def test_directory_with_file() -> None:
        """It should list a directory with a file."""
        dir1 = "dir1"
        file1 = "file1"
        expected = [
            dir1,
            f"└── {file1}",
        ]
        with temporary_path(name=dir1) as root:
            root.mkdir()
            (root / file1).touch()
            result = list(tree(root))
            assert result == expected

    @staticmethod
    def test_deep_directory() -> None:
        """It should list subdirectories and files."""
        dir1 = "dir1"
        dir2 = "dir2"
        dir3 = "dir3"
        file1 = "file1"
        file2 = "file2"
        file3 = "file3"
        expected = [
            dir1,
            f"├── {dir2}",
            f"│   ├── {file2}",
            f"│   └── {file3}",
            f"├── {dir3}",
            f"└── {file1}",
        ]
        with temporary_path(name=dir1) as root:
            root.mkdir()
            (root / file1).touch()
            (root / dir2).mkdir()
            (root / dir2 / file2).touch()
            (root / dir2 / file3).touch()
            (root / dir3).mkdir()
            result = list(tree(root))
            assert result == expected


class TestCloneFile:
    """Unit tests for clone_file()"""

    @staticmethod
    def test_basic_clone_with_string_input() -> None:
        """It should clone a file from string path to string path."""
        with TemporaryDirectory() as root:
            source_path = _expand(root) + "/source.txt"
            dest_path = _expand(root) + "/dest.txt"
            source_content = "test content"
            Path(source_path).write_text(source_content)
            result = clone_file(source_path, dest_path)
            assert isinstance(result, Path)
            assert str(result) == dest_path
            assert result.read_text() == source_content

    @staticmethod
    def test_clone_with_path_objects() -> None:
        """It should handle Path objects as input."""
        with TemporaryDirectory() as root:
            source_path = Path(_expand(root)) / "source.txt"
            dest_path = Path(_expand(root)) / "dest.txt"
            source_content = "test content with Path objects"
            source_path.write_text(source_content)
            result = clone_file(source_path, dest_path)
            assert isinstance(result, Path)
            assert result == dest_path
            assert result.read_text() == source_content

    @staticmethod
    def test_overwrite_existing_file() -> None:
        """It should overwrite an existing destination file."""
        with TemporaryDirectory() as root:
            source_path = _expand(root) + "/source.txt"
            dest_path = _expand(root) + "/dest.txt"
            Path(source_path).write_text("new content")
            Path(dest_path).write_text("old content")
            result = clone_file(source_path, dest_path)
            assert str(result) == dest_path
            assert result.read_text() == "new content"

    @staticmethod
    def test_clone_with_binary_content() -> None:
        """It should preserve binary content during clone."""
        with TemporaryDirectory() as root:
            source_path = Path(_expand(root)) / "source.bin"
            dest_path = Path(_expand(root)) / "dest.bin"
            binary_content = b"\x00\x01\x02\x03\xff\xfe\xfd"
            source_path.write_bytes(binary_content)
            clone_file(source_path, dest_path)
            assert dest_path.read_bytes() == binary_content

    @staticmethod
    def test_clone_preserves_metadata() -> None:
        """It should preserve file metadata (via shutil.copy2)."""
        with TemporaryDirectory() as root:
            source_path = Path(_expand(root)) / "source.txt"
            dest_path = Path(_expand(root)) / "dest.txt"
            source_path.write_text("content")
            original_stat = source_path.stat()
            clone_file(source_path, dest_path)
            dest_stat = dest_path.stat()
            assert dest_path.is_file()
            assert dest_stat.st_mtime == original_stat.st_mtime

    @staticmethod
    def test_source_does_not_exist() -> None:
        """It should raise an error if source doesn't exist."""
        with TemporaryDirectory() as root:
            source_path = _expand(root) + "/nonexistent.txt"
            dest_path = _expand(root) + "/dest.txt"
            with pytest.raises(FileNotFoundError):
                clone_file(source_path, dest_path)

    @staticmethod
    def test_source_is_directory() -> None:
        """It should raise an error if source is a directory."""
        with TemporaryDirectory() as root:
            source_dir = _expand(root) + "/sourcedir"
            dest_path = _expand(root) + "/dest.txt"
            os.mkdir(source_dir)
            with pytest.raises(OSError):
                clone_file(source_dir, dest_path)

    @staticmethod
    def test_destination_directory_does_not_exist() -> None:
        """It should raise an error if destination directory doesn't exist."""
        with TemporaryDirectory() as root:
            source_path = _expand(root) + "/source.txt"
            dest_path = _expand(root) + "/parent/dest.txt"
            Path(source_path).touch()
            with pytest.raises(OSError):
                clone_file(source_path, dest_path)

    @staticmethod
    def test_clone_symlink_source() -> None:
        """It should follow symlinks in the source path."""
        with TemporaryDirectory() as root:
            real_source = _expand(root) + "/real_source.txt"
            link_source = _expand(root) + "/link_source.txt"
            dest_path = _expand(root) + "/dest.txt"
            Path(real_source).write_text("real content")
            os.symlink(real_source, link_source)
            clone_file(link_source, dest_path)
            assert Path(dest_path).is_file()
            assert Path(dest_path).read_text() == "real content"

    @staticmethod
    def test_same_source_and_dest() -> None:
        """It should raise SameFileError when source and dest are the same."""
        with TemporaryDirectory() as root:
            file_path = _expand(root) + "/file.txt"
            Path(file_path).write_text("content")
            with pytest.raises(SameFileError):
                clone_file(file_path, file_path)
