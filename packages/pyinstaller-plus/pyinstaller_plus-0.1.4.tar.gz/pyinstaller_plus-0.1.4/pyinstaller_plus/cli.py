from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Tuple

from .distromate import bundled_distromate_path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python <3.11
    tomllib = None  # type: ignore[assignment]

DEFAULT_INSTALL_URL = "https://api.distromate.net/install.ps1"


def _split_dm_args(
    argv: Iterable[str],
) -> Tuple[list[str], bool, str | None, bool, bool, str | None]:
    py_args: list[str] = []
    publish = False
    dm_version: str | None = None
    dm_install = False
    dm_no_install = False
    dm_install_url: str | None = None

    args = list(argv)
    i = 0
    while i < len(args):
        arg = args[i]

        if arg == "--":
            py_args.extend(args[i + 1 :])
            break

        if arg in {"--publish", "--dm-publish"}:
            publish = True
            i += 1
            continue

        if arg == "-p":
            next_arg = args[i + 1] if i + 1 < len(args) else None
            if next_arg and not next_arg.startswith("-"):
                py_args.extend([arg, next_arg])
                i += 2
            else:
                publish = True
                i += 1
            continue

        if arg.startswith("--dm-version="):
            dm_version = arg.split("=", 1)[1]
            i += 1
            continue

        if arg == "--dm-version":
            if i + 1 >= len(args):
                raise SystemExit("Missing value for --dm-version.")
            dm_version = args[i + 1]
            i += 2
            continue

        if arg == "--dm-install":
            dm_install = True
            i += 1
            continue

        if arg == "--no-dm-install":
            dm_no_install = True
            i += 1
            continue

        if arg.startswith("--dm-install-url="):
            dm_install_url = arg.split("=", 1)[1]
            i += 1
            continue

        if arg == "--dm-install-url":
            if i + 1 >= len(args):
                raise SystemExit("Missing value for --dm-install-url.")
            dm_install_url = args[i + 1]
            i += 2
            continue

        py_args.append(arg)
        i += 1

    return py_args, publish, dm_version, dm_install, dm_no_install, dm_install_url


def _read_pyproject_version(start_dir: Path) -> str | None:
    if tomllib is None:
        return None

    for current in [start_dir, *start_dir.parents]:
        pyproject = current / "pyproject.toml"
        if not pyproject.is_file():
            continue
        try:
            data = tomllib.loads(pyproject.read_bytes())
        except Exception:
            return None
        return data.get("project", {}).get("version")

    return None


def _run_command(cmd: list[str]) -> int:
    print(f"[pyinstaller-plus] $ {' '.join(cmd)}")
    try:
        completed = subprocess.run(cmd, check=False)
    except FileNotFoundError:
        print(f"[pyinstaller-plus] Command not found: {cmd[0]}")
        return 127
    return completed.returncode


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _install_distromate(url: str) -> bool:
    if os.name != "nt":
        print("[pyinstaller-plus] distromate install script is Windows-only.")
        return False
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        f"irm {url} | iex",
    ]
    return _run_command(cmd) == 0


def _find_distromate() -> str | None:
    path = shutil.which("distromate")
    if path:
        return path
    return bundled_distromate_path()


def _ensure_distromate(auto_install: bool, install_url: str) -> str | None:
    found = _find_distromate()
    if found:
        return found

    if not auto_install:
        print("[pyinstaller-plus] distromate CLI not found in PATH.")
        print(
            "[pyinstaller-plus] Install it with: "
            f"powershell -Command \"irm {install_url} | iex\""
        )
        return None

    print("[pyinstaller-plus] distromate CLI not found. Installing...")
    if not _install_distromate(install_url):
        return None

    found = _find_distromate()
    if not found:
        print("[pyinstaller-plus] distromate install finished, but CLI not found.")
        return None
    return found


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    py_args, publish, dm_version, dm_install, dm_no_install, dm_install_url = _split_dm_args(
        args
    )

    if not py_args:
        py_args = ["-h"]

    pyinstaller_cmd = [sys.executable, "-m", "PyInstaller", *py_args]
    rc = _run_command(pyinstaller_cmd)
    if rc != 0:
        return rc
    if len(py_args) == 1 and py_args[0] in {"-h", "--help", "--version"}:
        return 0

    auto_install = True
    if "PYINSTALLER_PLUS_AUTO_INSTALL" in os.environ:
        auto_install = _is_truthy(os.environ.get("PYINSTALLER_PLUS_AUTO_INSTALL"))
    if dm_install:
        auto_install = True
    if dm_no_install:
        auto_install = False
    install_url = (
        dm_install_url
        or os.environ.get("PYINSTALLER_PLUS_INSTALL_URL")
        or DEFAULT_INSTALL_URL
    )

    distromate_cmd = _ensure_distromate(auto_install, install_url)
    if not distromate_cmd:
        return 127

    if dm_version is None:
        dm_version = _read_pyproject_version(Path(os.getcwd()))
    if not dm_version:
        print(
            "[pyinstaller-plus] distromate version not specified. "
            "Use --dm-version <version> to continue."
        )
        return 2

    dm_cmd = [distromate_cmd, "publish" if publish else "package", "-v", dm_version]
    return _run_command(dm_cmd)


if __name__ == "__main__":
    raise SystemExit(main())
