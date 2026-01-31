from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import utilities.subprocess
from utilities.constants import HOME, PWD
from utilities.core import log_info, write_text
from utilities.subprocess import cp

from installer.clone.constants import GIT_CLONE_HOST
from installer.configs.lib import setup_ssh_config

if TYPE_CHECKING:
    from collections.abc import Iterator

    from utilities.types import LoggerLike, PathLike


def git_clone(
    key: PathLike,
    owner: str,
    repo: str,
    /,
    *,
    logger: LoggerLike | None = None,
    home: PathLike = HOME,
    host: str = GIT_CLONE_HOST,
    port: int | None = None,
    dest: PathLike = PWD,
    branch: str | None = None,
) -> None:
    log_info(logger, "Cloning repository...")
    key = Path(key)
    setup_ssh_config(logger=logger, home=home)
    _setup_deploy_key(key, home=home, host=host, port=port)
    utilities.subprocess.git_clone(
        f"git@{key.stem}:{owner}/{repo}", dest, branch=branch
    )


def _setup_deploy_key(
    path: PathLike,
    /,
    *,
    home: PathLike = HOME,
    host: str = GIT_CLONE_HOST,
    port: int | None = None,
) -> None:
    path = Path(path)
    stem = path.stem
    path_config = _get_path_config(stem, home=home)
    text = "\n".join(_yield_config_lines(stem, home=home, host=host, port=port))
    write_text(path_config, text, overwrite=True)
    dest = _get_path_deploy_key(stem, home=home)
    cp(path, dest, perms="u=rw,g=,o=")


def _get_path_config(stem: str, /, *, home: PathLike = HOME) -> Path:
    return Path(home, f".ssh/config.d/{stem}.conf")


def _yield_config_lines(
    stem: str,
    /,
    *,
    home: PathLike = HOME,
    host: str = GIT_CLONE_HOST,
    port: int | None = None,
) -> Iterator[str]:
    path_key = _get_path_deploy_key(stem, home=home)
    yield f"Host {stem}"
    indent = 4 * " "
    yield f"{indent}User git"
    yield f"{indent}HostName {host}"
    if port is not None:
        yield (f"{indent}Port {port}")
    yield f"{indent}IdentityFile {path_key}"
    yield f"{indent}IdentitiesOnly yes"


def _get_path_deploy_key(stem: str, /, *, home: PathLike = HOME) -> Path:
    return Path(home, ".ssh/deploy-keys", stem)


__all__ = ["git_clone"]
