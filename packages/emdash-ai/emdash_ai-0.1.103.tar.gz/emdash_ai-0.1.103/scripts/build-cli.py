#!/usr/bin/env python3
"""Build script for creating standalone emdash CLI binary using PyInstaller."""

import subprocess
import sys
import platform
from pathlib import Path

# Get the project root
PROJECT_ROOT = Path(__file__).parent.parent
CLI_DIR = PROJECT_ROOT / "packages" / "cli" / "emdash_cli"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"

def get_platform_suffix():
    """Get platform-specific suffix for the binary."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        if machine == "arm64":
            return "macos-arm64"
        return "macos-x64"
    elif system == "linux":
        return f"linux-{machine}"
    elif system == "windows":
        return "win-x64"
    return f"{system}-{machine}"

def build():
    """Build the emdash CLI binary."""
    print(f"Building emdash CLI for {platform.system()} {platform.machine()}...")

    # Entry point
    entry_point = CLI_DIR / "main.py"

    if not entry_point.exists():
        print(f"Error: Entry point not found: {entry_point}")
        sys.exit(1)

    # Output name
    suffix = get_platform_suffix()
    output_name = f"emdash-{suffix}"

    # PyInstaller command - use pyinstaller directly from PATH
    cmd = [
        "pyinstaller",
        "--onedir",  # Directory with executable (faster startup than --onefile)
        "--name", output_name,
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR / "pyinstaller"),
        "--specpath", str(BUILD_DIR),
        # Hidden imports that PyInstaller might miss
        "--hidden-import", "emdash_core",
        "--hidden-import", "emdash_cli",
        "--hidden-import", "emdash_cli.main",
        "--hidden-import", "emdash_core.graph",
        "--hidden-import", "emdash_core.graph.connection",
        "--hidden-import", "emdash_core.ingestion",
        "--hidden-import", "emdash_core.analytics",
        "--hidden-import", "emdash_core.agent",
        "--hidden-import", "emdash_core.embeddings",
        "--hidden-import", "emdash_core.api",
        "--hidden-import", "kuzu",
        "--hidden-import", "numpy",
        "--hidden-import", "networkx",
        "--hidden-import", "community",
        "--hidden-import", "astroid",
        "--hidden-import", "gitpython",
        "--hidden-import", "openai",
        "--hidden-import", "httpx",
        "--hidden-import", "pydantic",
        "--hidden-import", "click",
        "--hidden-import", "rich",
        "--hidden-import", "loguru",
        # Collect all data files from emdash packages
        "--collect-all", "emdash_core",
        "--collect-all", "emdash_cli",
        "--collect-all", "kuzu",
        # Clean build
        "--clean",
        "--noconfirm",
        # Entry point
        str(entry_point),
    ]

    print(f"Running: {' '.join(cmd[:10])}...")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode != 0:
        print("Build failed!")
        sys.exit(1)

    # --onedir creates: dist/<name>/<name> (executable inside directory)
    output_dir = DIST_DIR / output_name
    executable_name = output_name + (".exe" if platform.system() == "Windows" else "")
    executable_path = output_dir / executable_name

    if output_dir.exists():
        # Calculate total size of the directory
        total_size = sum(f.stat().st_size for f in output_dir.rglob("*") if f.is_file())
        size_mb = total_size / (1024 * 1024)
        print(f"\nBuild successful!")
        print(f"Output directory: {output_dir}")
        print(f"Executable: {executable_path}")
        print(f"Total size: {size_mb:.1f} MB")
        print(f"\nTo run from anywhere:")
        print(f"  {executable_path}")
        print(f"\nTo install globally (symlink to /usr/local/bin):")
        print(f"  sudo ln -sf {executable_path} /usr/local/bin/emdash-standalone")
    else:
        print(f"Warning: Expected output not found at {output_dir}")

if __name__ == "__main__":
    build()
