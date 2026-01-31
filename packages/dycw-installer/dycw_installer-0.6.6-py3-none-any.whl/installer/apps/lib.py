from __future__ import annotations

import re
import shutil
from pathlib import Path
from shlex import join
from typing import TYPE_CHECKING, assert_never

import utilities.subprocess
from utilities.constants import HOME
from utilities.core import (
    WhichError,
    extract_group,
    log_info,
    normalize_multi_line_str,
    normalize_str,
    one,
    which,
)
from utilities.subprocess import (
    APT_UPDATE,
    BASH_LS,
    apt_install,
    apt_install_cmd,
    apt_remove,
    apt_update,
    chmod,
    cp,
    curl,
    curl_cmd,
    install,
    maybe_sudo_cmd,
    run,
    symlink,
    tee,
    yield_ssh_temp_dir,
)

from installer.apps.constants import (
    GITHUB_TOKEN,
    PATH_BINARIES,
    PERMISSIONS_BINARY,
    PERMISSIONS_CONFIG,
    SHELL,
    SYSTEM_NAME,
)
from installer.apps.download import (
    yield_asset,
    yield_bz2_asset,
    yield_gzip_asset,
    yield_lzma_asset,
)
from installer.configs.constants import FILE_SYSTEM_ROOT
from installer.configs.lib import setup_shell_config
from installer.utilities import split_ssh, ssh_uv_install

if TYPE_CHECKING:
    from utilities.core import PermissionsLike
    from utilities.shellingham import Shell
    from utilities.types import (
        LoggerLike,
        MaybeSequenceStr,
        PathLike,
        Retry,
        SecretLike,
    )


def setup_apt_package(
    package: str,
    /,
    *,
    ssh: str | None = None,
    logger: LoggerLike | None = None,
    sudo: bool = False,
    retry: Retry | None = None,
) -> None:
    """Setup an 'apt' package."""
    match ssh, SYSTEM_NAME:
        case None, "Darwin":
            msg = f"Unsupported system: {SYSTEM_NAME!r}"
            raise ValueError(msg)
        case None, "Linux":
            try:
                _ = which(package)
                log_info(logger, "'apt' package %r is already set up", package)
            except WhichError:
                log_info(logger, "Setting up 'apt' package %r...", package)
                run(*maybe_sudo_cmd(*APT_UPDATE, sudo=sudo))
                run(*maybe_sudo_cmd(*apt_install_cmd(package), sudo=sudo))
        case str(), _:
            user, hostname = split_ssh(ssh)
            log_info(logger, "Setting up 'apt' package %r on %r...", package, hostname)
            cmds: list[list[str]] = [
                maybe_sudo_cmd(*APT_UPDATE, sudo=sudo),
                maybe_sudo_cmd(*apt_install_cmd(package), sudo=sudo),
            ]
            utilities.subprocess.ssh(
                user,
                hostname,
                *BASH_LS,
                input=normalize_str("\n".join(map(join, cmds))),
                retry=retry,
                logger=logger,
            )
        case never:
            assert_never(never)


##


def setup_asset(
    asset_owner: str,
    asset_repo: str,
    path: PathLike,
    /,
    *,
    logger: LoggerLike | None = None,
    tag: str | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    match_system: bool = False,
    match_c_std_lib: bool = False,
    match_machine: bool = False,
    not_matches: MaybeSequenceStr | None = None,
    endswith: MaybeSequenceStr | None = None,
    not_endswith: MaybeSequenceStr | None = None,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    """Setup a GitHub asset."""
    log_info(logger, "Setting up GitHub asset...")
    with yield_asset(
        asset_owner,
        asset_repo,
        tag=tag,
        token=token,
        match_system=match_system,
        match_c_std_lib=match_c_std_lib,
        match_machine=match_machine,
        not_matches=not_matches,
        endswith=endswith,
        not_endswith=not_endswith,
    ) as src:
        cp(src, path, sudo=sudo, perms=perms, owner=owner, group=group)


##


def setup_age(
    *,
    logger: LoggerLike | None = None,
    ssh: str | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
    retry: Retry | None = None,
) -> None:
    """Set up 'age'."""
    match ssh:
        case None:
            try:
                _ = which("age")
                log_info(logger, "'age' is already set up")
            except WhichError:
                log_info(logger, "Setting up 'age'...")
                with yield_gzip_asset(
                    "FiloSottile",
                    "age",
                    token=token,
                    match_system=True,
                    match_machine=True,
                    not_endswith=["proof"],
                ) as temp:
                    srcs = {p for p in temp.iterdir() if p.name.startswith("age")}
                    for src in srcs:
                        dest = Path(path_binaries, src.name)
                        cp(src, dest, sudo=sudo, perms=perms, owner=owner, group=group)
        case str():
            ssh_uv_install(
                ssh,
                "age",
                logger=logger,
                token=token,
                path_binaries=path_binaries,
                sudo=sudo,
                perms=perms,
                owner=owner,
                group=group,
                retry=retry,
            )
        case never:
            assert_never(never)


##


def setup_bat(
    *,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    """Set up 'bat'."""
    try:
        _ = which("bat")
        log_info(logger, "'bat' is already set up")
    except WhichError:
        log_info(logger, "Setting up 'bat'...")
        with yield_gzip_asset(
            "sharkdp",
            "bat",
            token=token,
            match_system=True,
            match_c_std_lib=True,
            match_machine=True,
        ) as temp:
            src = temp / "bat"
            dest = Path(path_binaries, src.name)
            cp(src, dest, sudo=sudo, perms=perms, owner=owner, group=group)


##


def setup_bottom(
    *,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    """Set up 'bottom'."""
    try:
        _ = which("btm")
        log_info(logger, "'bottom' is already set up")
    except WhichError:
        log_info(logger, "Setting up 'bottom'...")
        with yield_gzip_asset(
            "ClementTsang",
            "bottom",
            token=token,
            match_system=True,
            match_c_std_lib=True,
            match_machine=True,
            not_matches=[r"\d+\.tar\.gz$"],
        ) as temp:
            src = temp / "btm"
            dest = Path(path_binaries, src.name)
            cp(src, dest, sudo=sudo, perms=perms, owner=owner, group=group)


##


def setup_curl(
    *,
    ssh: str | None = None,
    logger: LoggerLike | None = None,
    sudo: bool = False,
    retry: Retry | None = None,
) -> None:
    """Set up 'curl'."""
    setup_apt_package("curl", ssh=ssh, logger=logger, sudo=sudo, retry=retry)


##


def setup_delta(
    *,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    """Set up 'delta'."""
    try:
        _ = which("delta")
        log_info(logger, "'delta' is already set up")
    except WhichError:
        log_info(logger, "Setting up 'delta'...")
        with yield_gzip_asset(
            "dandavison",
            "delta",
            token=token,
            match_system=True,
            match_c_std_lib=True,
            match_machine=True,
        ) as temp:
            src = temp / "delta"
            dest = Path(path_binaries, src.name)
            cp(src, dest, sudo=sudo, perms=perms, owner=owner, group=group)


##


def setup_direnv(
    *,
    ssh: str | None = None,
    logger: LoggerLike | None = None,
    path_binaries: PathLike = PATH_BINARIES,
    token: SecretLike | None = GITHUB_TOKEN,
    sudo: bool = False,
    perms_binary: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
    etc: bool = False,
    shell: Shell | None = None,
    home: PathLike | None = None,
    perms_config: PermissionsLike = PERMISSIONS_CONFIG,
    root: PathLike | None = None,
    retry: Retry | None = None,
) -> None:
    """Set up 'direnv'."""
    match ssh:
        case None:
            try:
                _ = which("direnv")
                log_info(logger, "'direnv' is already set up")
            except WhichError:
                log_info(logger, "Setting up 'direnv'...")
                if ssh is None:
                    dest = Path(path_binaries, "direnv")
                    setup_asset(
                        "direnv",
                        "direnv",
                        dest,
                        token=token,
                        match_system=True,
                        match_machine=True,
                        sudo=sudo,
                        perms=perms_binary,
                        owner=owner,
                        group=group,
                    )
                    setup_shell_config(
                        'eval "$(direnv hook bash)"',
                        'eval "$(direnv hook fish)"',
                        "direnv hook fish | source",
                        etc="direnv" if etc else None,
                        shell=SHELL if shell is None else shell,
                        home=HOME if home is None else home,
                        perms=perms_config,
                        owner=owner,
                        group=group,
                        root=FILE_SYSTEM_ROOT if root is None else root,
                    )
        case str():
            ssh_uv_install(
                ssh,
                "direnv",
                logger=logger,
                path_binaries=path_binaries,
                token=token,
                sudo=sudo,
                perms_binary=perms_binary,
                owner=owner,
                group=group,
                etc=etc,
                shell=shell,
                home=home,
                perms_config=perms_config,
                root=root,
                retry=retry,
            )
        case never:
            assert_never(never)


##


def setup_docker(
    *,
    ssh: str | None = None,
    logger: LoggerLike | None = None,
    sudo: bool = False,
    user: str | None = None,
    retry: Retry | None = None,
) -> None:
    match ssh, SYSTEM_NAME:
        case None, "Darwin":
            msg = f"Unsupported system: {SYSTEM_NAME!r}"
            raise ValueError(msg)
        case None, "Linux":
            try:
                _ = which("docker")
                log_info(logger, "'docker' is already set up")
            except WhichError:
                log_info(logger, "Setting up 'docker'....")
                apt_remove(
                    "docker.io",
                    "docker-doc",
                    "docker-compose",
                    "podman-docker",
                    "containerd",
                    "runc",
                    sudo=sudo,
                )
                apt_update(sudo=sudo)
                apt_install("ca-certificates", "curl", sudo=sudo)
                docker_asc = Path("/etc/apt/keyrings/docker.asc")
                install(
                    docker_asc.parent, directory=True, mode="u=rwx,g=rx,o=rx", sudo=sudo
                )
                curl(
                    "https://download.docker.com/linux/debian/gpg",
                    output=docker_asc,
                    sudo=sudo,
                )
                chmod(docker_asc, "u=rw,g=r,o=r", sudo=sudo)
                release = Path("/etc/os-release").read_text()
                pattern = re.compile(r"^VERSION_CODENAME=(\w+)$")
                line = one(
                    line for line in release.splitlines() if pattern.search(line)
                )
                codename = extract_group(pattern, line)
                tee(
                    "/etc/apt/sources.list.d/docker.sources",
                    normalize_multi_line_str(f"""
                            Types: deb
                            URIs: https://download.docker.com/linux/debian
                            Suites: {codename}
                            Components: stable
                            Signed-By: /etc/apt/keyrings/docker.asc
                        """),
                    sudo=sudo,
                )
                apt_install(
                    "docker-ce",
                    "docker-ce-cli",
                    "containerd.io",
                    "docker-buildx-plugin",
                    "docker-compose-plugin",
                    update=True,
                    sudo=sudo,
                )
            if user is not None:
                run(*maybe_sudo_cmd("usermod", "-aG", "docker", user, sudo=sudo))
        case str(), _:
            ssh_uv_install(
                ssh, "docker", logger=logger, sudo=sudo, user=user, retry=retry
            )
        case never:
            assert_never(never)


##


def setup_dust(
    *,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    """Set up 'dust'."""
    try:
        _ = which("dust")
        log_info(logger, "'dust' is already set up")
    except WhichError:
        log_info(logger, "Setting up 'dust'....")
        match SYSTEM_NAME:
            case "Darwin":
                match_machine = False
            case "Linux":
                match_machine = True
            case never:
                assert_never(never)
        with yield_gzip_asset(
            "bootandy",
            "dust",
            token=token,
            match_system=True,
            match_c_std_lib=True,
            match_machine=match_machine,
        ) as temp:
            src = temp / "dust"
            dest = Path(path_binaries, src.name)
            cp(src, dest, sudo=sudo, perms=perms, owner=owner, group=group)


##


def setup_eza(
    *,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    """Set up 'eza'."""
    try:
        _ = which("eza")
        log_info(logger, "'eza' is already set up")
    except WhichError:
        log_info(logger, "Setting up 'eza'....")
        match SYSTEM_NAME:
            case "Darwin":
                asset_owner = "cargo-bins"
                asset_repo = "cargo-quickinstall"
                tag = "eza"
                match_c_std_lib = False
                not_endswith = ["sig"]
            case "Linux":
                asset_owner = "eza-community"
                asset_repo = "eza"
                tag = None
                match_c_std_lib = True
                not_endswith = ["zip"]
            case never:
                assert_never(never)
        with yield_gzip_asset(
            asset_owner,
            asset_repo,
            tag=tag,
            token=token,
            match_system=True,
            match_c_std_lib=match_c_std_lib,
            match_machine=True,
            not_endswith=not_endswith,
        ) as src:
            dest = Path(path_binaries, src.name)
            cp(src, dest, sudo=sudo, perms=perms, owner=owner, group=group)


##


def setup_fd(
    *,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    """Set up 'fd'."""
    try:
        _ = which("fd")
        log_info(logger, "'fd' is already set up")
    except WhichError:
        log_info(logger, "Setting up 'fd'....")
        with yield_gzip_asset(
            "sharkdp",
            "fd",
            token=token,
            match_system=True,
            match_c_std_lib=True,
            match_machine=True,
        ) as temp:
            src = temp / "fd"
            dest = Path(path_binaries, src.name)
            cp(src, dest, sudo=sudo, perms=perms, owner=owner, group=group)


##


def setup_fzf(
    *,
    ssh: str | None = None,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms_binary: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
    etc: bool = False,
    shell: Shell | None = None,
    home: PathLike | None = None,
    perms_config: PermissionsLike = PERMISSIONS_CONFIG,
    root: PathLike | None = None,
    retry: Retry | None = None,
) -> None:
    """Set up 'fzf'."""
    match ssh:
        case None:
            try:
                _ = which("fzf")
                log_info(logger, "'fzf' is already set up")
            except WhichError:
                log_info(logger, "Setting up 'fzf'...")
                with yield_gzip_asset(
                    "junegunn",
                    "fzf",
                    token=token,
                    match_system=True,
                    match_machine=True,
                ) as src:
                    dest = Path(path_binaries, src.name)
                    cp(
                        src,
                        dest,
                        sudo=sudo,
                        perms=perms_binary,
                        owner=owner,
                        group=group,
                    )
                setup_shell_config(
                    'eval "$(fzf --bash)"',
                    "source <(fzf --zsh)",
                    "fzf --fish | source",
                    etc="fzf" if etc else None,
                    shell=SHELL if shell is None else shell,
                    home=HOME if home is None else home,
                    perms=perms_config,
                    owner=owner,
                    group=group,
                    root=FILE_SYSTEM_ROOT if root is None else root,
                )
        case str():
            ssh_uv_install(
                ssh,
                "fzf",
                logger=logger,
                token=token,
                path_binaries=path_binaries,
                sudo=sudo,
                perms_binary=perms_binary,
                owner=owner,
                group=group,
                etc=etc,
                shell=shell,
                home=home,
                perms_config=perms_config,
                root=root,
                retry=retry,
            )
        case never:
            assert_never(never)


##


def setup_git(
    *,
    logger: LoggerLike | None = None,
    ssh: str | None = None,
    sudo: bool = False,
    retry: Retry | None = None,
) -> None:
    """Set up 'git'."""
    setup_apt_package("git", logger=logger, ssh=ssh, sudo=sudo, retry=retry)


##


def setup_jq(
    *,
    force: bool = False,
    logger: LoggerLike | None = None,
    path_binaries: PathLike = PATH_BINARIES,
    token: SecretLike | None = GITHUB_TOKEN,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    """Set up 'jq'."""
    if (shutil.which("jq") is None) or force:
        log_info(logger, "Setting up 'jq'...")
        dest = Path(path_binaries, "jq")
        setup_asset(
            "jqlang",
            "jq",
            dest,
            token=token,
            match_system=True,
            match_machine=True,
            not_endswith=["linux64"],
            sudo=sudo,
            perms=perms,
            owner=owner,
            group=group,
        )
    else:
        log_info(logger, "'jq' is already set up")


##


def setup_just(
    *,
    ssh: str | None = None,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
    retry: Retry | None = None,
) -> None:
    """Set up 'just'."""
    match ssh:
        case None:
            try:
                _ = which("just")
                log_info(logger, "'just' is already set up")
            except WhichError:
                log_info(logger, "Setting up 'just'...")
                if ssh is None:
                    with yield_gzip_asset(
                        "casey",
                        "just",
                        token=token,
                        match_system=True,
                        match_machine=True,
                    ) as temp:
                        src = temp / "just"
                        dest = Path(path_binaries, src.name)
                        cp(src, dest, sudo=sudo, perms=perms, owner=owner, group=group)
        case str():
            ssh_uv_install(
                ssh,
                "just",
                logger=logger,
                token=token,
                path_binaries=path_binaries,
                sudo=sudo,
                perms=perms,
                owner=owner,
                group=group,
                retry=retry,
            )
        case never:
            assert_never(never)


##


def setup_neovim(
    *,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    """Set up 'neovim'."""
    try:
        _ = which("nvim")
        log_info(logger, "'nvim' is already set up")
    except WhichError:
        log_info(logger, "Setting up 'neovim'...")
        with yield_gzip_asset(
            "neovim",
            "neovim",
            token=token,
            match_system=True,
            match_machine=True,
            not_endswith=["appimage", "zsync"],
        ) as temp:
            dest_dir = Path(path_binaries, "nvim-dir")
            cp(temp, dest_dir, sudo=sudo, perms=perms, owner=owner, group=group)
            dest_bin = Path(path_binaries, "nvim")
            symlink(dest_dir / "bin/nvim", dest_bin, sudo=sudo)


##


def setup_pve_fake_subscription(
    *,
    ssh: str | None = None,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    retry: Retry | None = None,
) -> None:
    """Set up 'pve-fake-subscription'."""
    match ssh, SYSTEM_NAME:
        case None, "Darwin":
            msg = f"Unsupported system: {SYSTEM_NAME!r}"
            raise ValueError(msg)
        case None, "Linux":
            log_info(logger, "Setting up 'pve-fake-subscription'...")
            with yield_asset(
                "Jamesits", "pve-fake-subscription", token=token, endswith="deb"
            ) as temp:
                run("dpkg", "-i", str(temp))
        case str(), _:
            ssh_uv_install(
                ssh, "pve-fake-subscription", logger=logger, token=token, retry=retry
            )
        case never:
            assert_never(never)


##


def setup_restic(
    *,
    logger: LoggerLike | None = None,
    ssh: str | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
    retry: Retry | None = None,
) -> None:
    """Set up 'restic'."""
    log_info(logger, "Setting up 'restic'...")
    if ssh is None:
        with yield_bz2_asset(
            "restic", "restic", token=token, match_system=True, match_machine=True
        ) as src:
            dest = Path(path_binaries, "restic")
            cp(src, dest, sudo=sudo, perms=perms, owner=owner, group=group)
        return
    ssh_uv_install(
        ssh,
        "restic",
        logger=logger,
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
        retry=retry,
    )


##


def setup_ripgrep(
    *,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    """Set up 'ripgrep'."""
    log_info(logger, "Setting up 'ripgrep'...")
    with yield_gzip_asset(
        "burntsushi",
        "ripgrep",
        token=token,
        match_system=True,
        match_machine=True,
        not_endswith=["sha256"],
    ) as temp:
        src = temp / "rg"
        dest = Path(path_binaries, src.name)
        cp(src, dest, sudo=sudo, perms=perms, owner=owner, group=group)


##


def setup_rsync(
    *,
    logger: LoggerLike | None = None,
    ssh: str | None = None,
    sudo: bool = False,
    retry: Retry | None = None,
) -> None:
    """Set up 'rsync'."""
    setup_apt_package("rsync", logger=logger, ssh=ssh, sudo=sudo, retry=retry)


##


def setup_ruff(
    *,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    """Set up 'ruff'."""
    log_info(logger, "Setting up 'ruff'...")
    with yield_gzip_asset(
        "astral-sh",
        "ruff",
        token=token,
        match_system=True,
        match_c_std_lib=True,
        match_machine=True,
        not_endswith=["sha256"],
    ) as temp:
        src = temp / "ruff"
        dest = Path(path_binaries, src.name)
        cp(src, dest, sudo=sudo, perms=perms, owner=owner, group=group)


##


def setup_sd(
    *,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    """Set up 'sd'."""
    log_info(logger, "Setting up 'sd'...")
    with yield_gzip_asset(
        "chmln",
        "sd",
        token=token,
        match_system=True,
        match_c_std_lib=True,
        match_machine=True,
    ) as temp:
        src = temp / "sd"
        dest = Path(path_binaries, src.name)
        cp(src, dest, sudo=sudo, perms=perms, owner=owner, group=group)


##


def setup_shellcheck(
    *,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    """Set up 'shellcheck'."""
    log_info(logger, "Setting up 'shellcheck'...")
    with yield_gzip_asset(
        "koalaman",
        "shellcheck",
        token=token,
        match_system=True,
        match_machine=True,
        not_endswith=["tar.xz"],
    ) as temp:
        src = temp / "shellcheck"
        dest = Path(path_binaries, src.name)
        cp(src, dest, sudo=sudo, perms=perms, owner=owner, group=group)


##


def setup_shfmt(
    *,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    """Set up 'shfmt'."""
    log_info(logger, "Setting up 'shfmt'...")
    dest = Path(path_binaries, "shfmt")
    setup_asset(
        "mvdan",
        "sh",
        dest,
        token=token,
        match_system=True,
        match_machine=True,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
    )


##


def setup_sops(
    *,
    logger: LoggerLike | None = None,
    ssh: str | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
    retry: Retry | None = None,
) -> None:
    """Set up 'sops'."""
    log_info(logger, "Setting up 'sops'...")
    if ssh is None:
        dest = Path(path_binaries, "sops")
        setup_asset(
            "getsops",
            "sops",
            dest,
            token=token,
            match_system=True,
            match_machine=True,
            not_endswith=["json"],
            sudo=sudo,
            perms=perms,
            owner=owner,
            group=group,
        )
        return
    ssh_uv_install(
        ssh,
        "sops",
        logger=logger,
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
        retry=retry,
    )


##


def setup_starship(
    *,
    logger: LoggerLike | None = None,
    ssh: str | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms_binary: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
    etc: bool = False,
    home: PathLike | None = None,
    shell: Shell | None = None,
    starship_toml: PathLike | None = None,
    perms_config: PermissionsLike = PERMISSIONS_BINARY,
    root: PathLike | None = None,
    retry: Retry | None = None,
) -> None:
    """Set up 'starship'."""
    log_info(logger, "Setting up 'starship'...")
    if ssh is None:
        with yield_gzip_asset(
            "starship",
            "starship",
            token=token,
            match_system=True,
            match_c_std_lib=True,
            match_machine=True,
            not_endswith=["sha256"],
        ) as src:
            dest = Path(path_binaries, src.name)
            cp(src, dest, sudo=sudo, perms=perms_binary, owner=owner, group=group)
        shell_use = SHELL if shell is None else shell
        export = ["export STARSHIP_CONFIG='/etc/starship.toml'"] if etc else []
        home_use = HOME if home is None else home
        root_use = FILE_SYSTEM_ROOT if root is None else root
        setup_shell_config(
            [*export, 'eval "$(starship init bash)"'],
            [*export, 'eval "$(starship init zsh)"'],
            [*export, "starship init fish | source"],
            etc="starship" if etc else None,
            shell=shell_use,
            home=home_use,
            perms=perms_config,
            owner=owner,
            group=group,
            root=root_use,
        )
        if starship_toml is not None:
            if etc:
                dest = Path(root_use, "etc/starship.toml")
            else:
                dest = Path(home_use, ".config/starship.toml")
            cp(
                starship_toml,
                dest,
                sudo=sudo,
                perms=perms_config,
                owner=owner,
                group=group,
            )
        return
    ssh_uv_install(
        ssh,
        "starship",
        logger=logger,
        token=token,
        path_binaries=path_binaries,
        sudo=sudo,
        perms_binary=perms_binary,
        owner=owner,
        group=group,
        etc=etc,
        home=home,
        shell=shell,
        starship_toml=starship_toml,
        perms_config=perms_config,
        root=root,
        retry=retry,
    )


##


def setup_taplo(
    *,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    """Set up 'taplo'."""
    log_info(logger, "Setting up 'taplo'...")
    with yield_gzip_asset(
        "tamasfe", "taplo", token=token, match_system=True, match_machine=True
    ) as src:
        dest = Path(path_binaries, "taplo")
        cp(src, dest, sudo=sudo, perms=perms, owner=owner, group=group)


##


def setup_uv(
    *,
    logger: LoggerLike | None = None,
    ssh: str | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
    retry: Retry | None = None,
) -> None:
    """Set up 'uv'."""
    log_info(logger, "Setting up 'uv'...")
    if ssh is None:
        with yield_gzip_asset(
            "astral-sh",
            "uv",
            token=token,
            match_system=True,
            match_c_std_lib=True,
            match_machine=True,
            not_endswith=["sha256"],
        ) as temp:
            src = temp / "uv"
            dest = Path(path_binaries, src.name)
            cp(src, dest, sudo=sudo, perms=perms, owner=owner, group=group)
    else:
        user, hostname = split_ssh(ssh)
        with yield_ssh_temp_dir(user, hostname, retry=retry, logger=logger) as temp:
            utilities.subprocess.ssh(
                user,
                hostname,
                *BASH_LS,
                input=setup_uv_cmd(temp, path_binaries=path_binaries, sudo=sudo),
                retry=retry,
                logger=logger,
            )


def setup_uv_cmd(
    temp_dir: PathLike,
    /,
    *,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
) -> str:
    """Command to setup 'uv'."""
    output = Path(temp_dir, "install.sh")
    cmds: list[list[str]] = [
        curl_cmd("https://astral.sh/uv/install.sh", output=output),
        maybe_sudo_cmd(
            "env",
            f"UV_INSTALL_DIR={path_binaries}",
            "UV_NO_MODIFY_PATH=1",
            "sh",
            str(output),
            sudo=sudo,
        ),
    ]
    return normalize_str("\n".join(map(join, cmds)))


##


def setup_watchexec(
    *,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    """Set up 'watchexec'."""
    log_info(logger, "Setting up 'watchexec'...")
    with yield_lzma_asset(
        "watchexec",
        "watchexec",
        token=token,
        match_system=True,
        match_c_std_lib=True,
        match_machine=True,
        not_endswith=["b3", "deb", "rpm", "sha256", "sha512"],
    ) as temp:
        src = temp / "watchexec"
        dest = Path(path_binaries, src.name)
        cp(src, dest, sudo=sudo, perms=perms, owner=owner, group=group)


##


def setup_yq(
    *,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
) -> None:
    """Set up 'yq'."""
    log_info(logger, "Setting up 'yq'...")
    dest = Path(path_binaries, "yq")
    setup_asset(
        "mikefarah",
        "yq",
        dest,
        token=token,
        match_system=True,
        match_machine=True,
        not_endswith=["tar.gz"],
        sudo=sudo,
        perms=perms,
        owner=owner,
        group=group,
    )


##


def setup_zoxide(
    *,
    ssh: str | None = None,
    force: bool = False,
    logger: LoggerLike | None = None,
    token: SecretLike | None = GITHUB_TOKEN,
    path_binaries: PathLike = PATH_BINARIES,
    sudo: bool = False,
    perms_binary: PermissionsLike = PERMISSIONS_BINARY,
    owner: str | int | None = None,
    group: str | int | None = None,
    etc: bool = False,
    shell: Shell | None = None,
    home: PathLike | None = None,
    perms_config: PermissionsLike = PERMISSIONS_CONFIG,
    root: PathLike | None = None,
    retry: Retry | None = None,
) -> None:
    """Set up 'zoxide'."""
    match ssh:
        case None:
            if (shutil.which("zoxide") is None) or force:
                log_info(logger, "Setting up 'zoxide'...")
                with yield_gzip_asset(
                    "ajeetdsouza",
                    "zoxide",
                    token=token,
                    match_system=True,
                    match_machine=True,
                ) as temp:
                    src = temp / "zoxide"
                    dest = Path(path_binaries, src.name)
                    cp(
                        src,
                        dest,
                        sudo=sudo,
                        perms=perms_binary,
                        owner=owner,
                        group=group,
                    )
                shell_use = SHELL if shell is None else shell
                setup_shell_config(
                    'eval "$(zoxide init --cmd j bash)"',
                    'eval "$(zoxide init --cmd j zsh)"',
                    "zoxide init --cmd j fish | source",
                    etc="zoxide" if etc else None,
                    shell=shell_use,
                    home=HOME if home is None else home,
                    perms=perms_config,
                    owner=owner,
                    group=group,
                    root=FILE_SYSTEM_ROOT if root is None else root,
                )
            else:
                log_info(logger, "'zoxide' is already set up")
        case str():
            ssh_uv_install(
                ssh,
                "zoxide",
                token=token,
                path_binaries=path_binaries,
                sudo=sudo,
                perms_binary=perms_binary,
                owner=owner,
                group=group,
                etc=etc,
                shell=shell,
                home=home,
                perms_config=perms_config,
                root=root,
                retry=retry,
                logger=logger,
            )
        case never:
            assert_never(never)


__all__ = [
    "setup_age",
    "setup_apt_package",
    "setup_asset",
    "setup_bat",
    "setup_bottom",
    "setup_curl",
    "setup_delta",
    "setup_direnv",
    "setup_docker",
    "setup_dust",
    "setup_eza",
    "setup_fd",
    "setup_fzf",
    "setup_git",
    "setup_jq",
    "setup_just",
    "setup_neovim",
    "setup_pve_fake_subscription",
    "setup_restic",
    "setup_ripgrep",
    "setup_rsync",
    "setup_ruff",
    "setup_sd",
    "setup_shellcheck",
    "setup_shfmt",
    "setup_sops",
    "setup_starship",
    "setup_taplo",
    "setup_uv",
    "setup_uv_cmd",
    "setup_yq",
    "setup_zoxide",
]
