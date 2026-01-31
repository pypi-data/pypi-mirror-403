from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    from importlib.resources import files
except ImportError:  # pragma: no cover - Python <3.9
    files = None  # type: ignore[assignment]


def bundled_distromate_path() -> str | None:
    if files is None:
        return None

    try:
        base = files("pyinstaller_plus")
    except Exception:
        return None

    exe = base / "bin" / "distromate.exe"
    try:
        if exe.is_file():
            return str(Path(exe))
    except Exception:
        return None
    return None


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    exe_path = bundled_distromate_path()
    if not exe_path:
        print("[pyinstaller-plus] bundled distromate.exe not found.")
        return 127

    return subprocess.call([exe_path, *args])


if __name__ == "__main__":
    raise SystemExit(main())
