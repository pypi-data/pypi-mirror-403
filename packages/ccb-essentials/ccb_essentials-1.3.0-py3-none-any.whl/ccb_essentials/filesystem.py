"""Filesystem helpers"""

import logging
import os
from collections.abc import Generator, Iterable
from contextlib import contextmanager
from pathlib import Path
from shutil import copy2
from tempfile import TemporaryDirectory

from ccb_essentials.subprocess import shell_escape, subprocess_command


log = logging.getLogger(__name__)


def real_path(path: str | Path, check_exists: bool = True, mkdir: bool = False) -> Path | None:
    """Clean `path` and verify that it exists."""
    path = str(path)
    real = Path(os.path.realpath(os.path.expanduser(path)))

    if not check_exists:
        return real

    if real.exists():
        return real

    if mkdir:
        log.debug("creating directory %s", str(real))
        real.mkdir(parents=True)
        return real

    return None


def assert_real_path(path: str | Path, mkdir: bool = False) -> Path:
    """Clean `path` and assert that it exists."""
    new_path = real_path(path, check_exists=True, mkdir=mkdir)
    if new_path is None:
        raise FileNotFoundError(f'path {path} does not exist')
    return new_path


def assert_real_file(path: str | Path) -> Path:
    """Clean `path` and assert that it is a file."""
    new_path = assert_real_path(path)
    if not new_path.is_file():
        raise OSError(f'path {path} is not a file')
    return new_path


def assert_real_dir(path: str | Path, mkdir: bool = False) -> Path:
    """Clean `path` and assert that it is a directory."""
    new_path = assert_real_path(path, mkdir)
    if not new_path.is_dir():
        raise NotADirectoryError(f'path {path} is not a directory')
    return new_path


@contextmanager
def temporary_path(name: str = "temp", touch: bool = False) -> Generator[Path]:
    """Create a Path to a temporary file with a known name. This differs from
    tempfile.TemporaryFile() which creates a file-like object and
    tempfile.NamedTemporaryFile() which produces a random file name."""
    if name == "":
        raise ValueError("can't create a temporary_path with no name")
    with TemporaryDirectory() as td:
        path = Path(td) / name
        if touch:
            path.touch()
        yield path


_SPACE = '    '
_BRANCH = '│   '
_TEE = '├── '
_LAST = '└── '


def tree(root: str | Path, prefix: str = '') -> Generator[str]:
    """Build a pretty-printable directory tree. Example usage:
    print(os.linesep.join(tree(path)))
    """
    if not isinstance(root, Path):
        root = assert_real_path(root)
    if not root.is_dir():
        yield root.name
    else:
        if prefix == '':
            yield root.name
        contents = sorted(root.iterdir())
        lc1 = len(contents) - 1
        for i, path in enumerate(contents):
            pointer = _TEE if i < lc1 else _LAST
            yield prefix + pointer + path.name
            if path.is_dir():
                extension = _BRANCH if i < lc1 else _SPACE
                yield from tree(path, prefix=prefix + extension)


def common_root(a: Path, b: Path) -> Path | None:
    """Find the deepest common directory."""
    if not a.is_absolute() or not b.is_absolute():
        return None
    if a.is_dir():
        a /= 'x'
    if b.is_dir():
        b /= 'x'
    a_parents = list(reversed(a.parents))
    b_parents = list(reversed(b.parents))
    root = Path()
    for n in range(min(len(a_parents), len(b_parents))):
        if a_parents[n] == b_parents[n]:
            root = a_parents[n]
        else:
            break
    return root


def common_ancestor(paths: Iterable[Path]) -> Path | None:
    """Return the deepest directory common to all `paths`."""
    common = None
    for path in [p if p.is_dir() else p.parent for p in paths]:
        if common is None:
            common = path
        elif common != path:
            common = common_root(common, path)
            if common is None:
                return None
    return common


def common_parent(paths: Iterable[Path]) -> Path | None:
    """Return the immediate parent directory, if all `paths` share a common parent."""
    common = None
    for path in paths:
        if common is None:
            common = path.parent
        elif common != path.parent:
            return None
    return common


def clone_file(source: Path | str, dest: Path | str) -> Path:
    """Python shell utilities don't support copy-on-write as of 3.13.
    In 3.14 it's supported for Linux only.
    https://docs.python.org/3/library/shutil.html#platform-dependent-efficient-copy-operations
    https://github.com/python/cpython/issues/81338
    Ask the operating system to copy using clonefile() if possible, otherwise fall back to shutil.copy2().
    Source and destination must both be files.
    Returns the destination Path.
    """
    # Expand the paths so that the equality checks and filesystem checks below work on the real files.
    source_expanded = real_path(source, check_exists=False)
    assert source_expanded is not None
    dest_expanded = real_path(dest, check_exists=False)
    assert dest_expanded is not None

    # Reuse the inputs if they are already expanded Path objects, in case they have a cached stat() result.
    source_real: Path = source if isinstance(source, Path) and source == source_expanded else source_expanded
    dest_real: Path = dest if isinstance(dest, Path) and dest == dest_expanded else dest_expanded

    dest_dir = dest_real.parent
    if (
        source_real != dest_real  # not the same file
        and (source_real.is_file() and dest_dir.is_dir())  # they exist; hopefully the destination is writeable
        and (dest_real.is_file() or not dest_real.exists())  # either overwrite the file or write a new file
        and source_real.stat().st_dev == dest_dir.stat().st_dev  # on the same device, required to copy-on-write
    ):
        cmd = f'cp -c {shell_escape(source_real)} {shell_escape(dest_real)}'
        log.debug(cmd)
        if subprocess_command(cmd, raise_std_error=True) is not None:
            return dest_real

    copy2(source_real, dest_real)
    return dest_real


if __name__ == '__main__':
    # todo unit tests
    for test1 in [
        ('/', '/', '/'),
        ('/', '/bin/echo', '/'),
        ('/bin/echo', '/', '/'),
        ('/usr/bin', '/usr/bin/yes', '/usr/bin'),
        ('/usr/bin/yes', '/usr/bin', '/usr/bin'),
        ('/usr/bin/yes', '/usr/bin/yes', '/usr/bin'),
        ('/usr/local/bin', '/usr/bin/yes', '/usr'),
        ('/usr/local/bin', '/usr/bin', '/usr'),
        ('/usr/bin', '/usr/local/bin', '/usr'),
    ]:
        assert common_root(assert_real_path(test1[0]), assert_real_path(test1[1])) == assert_real_path(test1[2]), test1
        assert common_ancestor((assert_real_path(test1[0]), assert_real_path(test1[1]))) == assert_real_path(test1[2]), test1  # noqa: E501 # fmt: skip

    test2: tuple[Path | None, list[str]]
    for test2 in [
        (None, []),
        (Path('/'), ['/']),
        (Path('/'), ['/', '/']),
        (Path('/bin'), ['/bin']),
        (Path('/bin'), ['/bin', '/bin']),
        (Path('/bin'), ['/bin/echo', '/bin/kill', '/bin/ls', '/bin/mv']),
        (Path('/usr'), ['/usr/lib/dyld', '/usr/sbin/cron', '/usr/bin/yes']),
        (Path('/'), ['/bin/echo', '/bin/kill', '/usr/bin/yes']),
        (Path('/'), ['/bin/echo', '/usr/bin/yes', '/bin/kill']),
        (Path('/'), ['/usr/bin/yes', '/bin/echo', '/bin/kill']),
    ]:
        assert common_ancestor(map(assert_real_path, test2[1])) == test2[0], test2

    test3: tuple[Path | None, list[str]]
    for test3 in [
        (None, []),
        (Path('/'), ['/']),
        (Path('/'), ['/', '/']),
        (Path('/'), ['/bin']),
        (Path('/'), ['/bin', '/bin']),
        (Path('/bin'), ['/bin/echo', '/bin/kill', '/bin/ls', '/bin/mv']),
        (None, ['/usr/lib/dyld', '/usr/sbin/cron', '/usr/bin/yes']),
        (None, ['/bin/echo', '/bin/kill', '/usr/bin/yes']),
        (None, ['/bin/echo', '/usr/bin/yes', '/bin/kill']),
        (None, ['/usr/bin/yes', '/bin/echo', '/bin/kill']),
    ]:
        assert common_parent(map(assert_real_path, test3[1])) == test3[0], test3
