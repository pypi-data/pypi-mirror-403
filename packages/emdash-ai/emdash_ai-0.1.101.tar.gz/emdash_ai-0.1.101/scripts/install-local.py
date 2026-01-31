#!/usr/bin/env python3
"""Install emdash packages globally in editable mode using uv.

This script installs the local development version of all emdash packages
globally, so changes to the source code are reflected immediately.

Usage:
    python3 scripts/install-local.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def find_uv():
    """Find uv executable."""
    uv = shutil.which("uv")
    if uv:
        return uv

    print("Error: uv is not installed.")
    print("Install with: curl -LsSf https://astral.sh/uv/install.sh | sh")
    sys.exit(1)


def main():
    print("Installing emdash packages globally (editable mode) using uv...\n")

    uv = find_uv()

    # Install the main package which includes core and cli as dependencies
    result = subprocess.run(
        [uv, "pip", "install", "-e", str(REPO_ROOT)],
        capture_output=False,
    )

    if result.returncode != 0:
        print("\nInstallation failed!")
        sys.exit(1)

    # Verify installation
    print("\n" + "=" * 50)
    print("Verifying installation...")
    print("=" * 50 + "\n")

    # Get uv version
    result = subprocess.run(
        [uv, "--version"],
        capture_output=True,
        text=True,
    )
    uv_output = result.stdout.strip()
    print(f"Using: {uv_output}\n")

    # Use uv pip show to verify versions
    for pkg in ["emdash-ai", "emdash-core", "emdash-cli"]:
        result = subprocess.run(
            [uv, "pip", "show", pkg],
            capture_output=True,
            text=True,
        )
        for line in result.stdout.split("\n"):
            if line.startswith("Version:"):
                version = line.split(":")[1].strip()
                print(f"{pkg}: {version}")
                break

    print("\nInstallation complete!")
    print("Run 'emdash --version' to verify.")


if __name__ == "__main__":
    main()
