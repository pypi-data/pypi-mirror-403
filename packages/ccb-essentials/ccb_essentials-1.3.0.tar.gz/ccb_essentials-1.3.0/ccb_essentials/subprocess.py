"""Helpers for subprocess."""

import logging
import subprocess
from pathlib import Path

from ccb_essentials.constant import UTF8


log = logging.getLogger(__name__)


def subprocess_command(  # type: ignore[no-untyped-def]
    cmd: str,
    report_process_error: bool = True,
    report_std_error: bool = True,
    raise_std_error: bool = False,
    strip_output: bool = False,
    **kwargs,
) -> str | None:
    """Run a command through subprocess."""
    try:
        res = subprocess.run(cmd, shell=True, check=True, capture_output=True, **kwargs)
        if raise_std_error:
            err = res.stderr.decode(UTF8)
            if err:
                raise subprocess.CalledProcessError(1, cmd, res.stdout, res.stderr)
        if report_std_error:
            err = res.stderr.decode(UTF8)
            if err:
                log.warning(err)
        decoded: str = res.stdout.decode(UTF8)
        if strip_output:
            return decoded.strip()
        return decoded
    except subprocess.CalledProcessError as e:
        if report_process_error:
            log.error(e)
            log.error(e.stderr.decode(UTF8))
        return None


def shell_escape(path: str | Path) -> str:
    """Escape a path for use the shell via subprocess_command(cmd)."""
    return '"' + str(path).replace('"', '\\"').replace('$', '\\$').replace('`', '\\`') + '"'
