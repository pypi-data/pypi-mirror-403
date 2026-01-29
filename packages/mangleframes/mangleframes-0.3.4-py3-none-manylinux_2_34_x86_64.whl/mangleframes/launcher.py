"""Find the MangleFrames viewer binary."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path


def find_viewer_binary() -> Path | None:
    """Find the mangleframes-viewer binary.

    Searches in order:
    1. Package bin directory (installed with package)
    2. Virtual environment bin directory
    3. System PATH
    4. Cargo target directory (for development)
    """
    pkg_dir = Path(__file__).parent
    pkg_binary = pkg_dir / "bin" / "mangleframes-viewer"
    if pkg_binary.exists():
        return pkg_binary

    venv_binary = Path(sys.executable).parent / "mangleframes-viewer"
    if venv_binary.exists():
        return venv_binary

    path_binary = shutil.which("mangleframes-viewer")
    if path_binary:
        return Path(path_binary)

    # Development: check cargo target directory
    repo_root = pkg_dir.parent.parent
    dev_binary = repo_root / "target" / "release" / "mangleframes-viewer"
    if dev_binary.exists():
        return dev_binary

    dev_binary_debug = repo_root / "target" / "debug" / "mangleframes-viewer"
    if dev_binary_debug.exists():
        return dev_binary_debug

    return None
