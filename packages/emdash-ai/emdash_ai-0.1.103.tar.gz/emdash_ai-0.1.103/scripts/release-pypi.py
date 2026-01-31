#!/usr/bin/env python3
"""Release script for emdash-ai Python packages to PyPI using uv.

This script:
1. Bumps the patch version in all pyproject.toml files
2. Temporarily switches to PyPI dependencies (from workspace)
3. Builds and publishes packages in order: core -> cli -> main
4. Restores local development paths

Usage:
    python3 scripts/release-pypi.py [--major | --minor | --patch] [--dry-run]

Options:
    --major     Bump major version (1.0.0 -> 2.0.0)
    --minor     Bump minor version (0.1.0 -> 0.2.0)
    --patch     Bump patch version (0.1.4 -> 0.1.5) [default]
    --dry-run   Show what would be done without making changes
"""

import sys

# Check Python version (use old-style formatting in case of Python 2)
if sys.version_info < (3, 8):
    print("Error: This script requires Python 3.8 or higher.")
    print("You are running Python %d.%d" % (sys.version_info.major, sys.version_info.minor))
    print("\nRun with: python3 scripts/release-pypi.py")
    sys.exit(1)

import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path

# Repository root
REPO_ROOT = Path(__file__).parent.parent

# Files to update (only pyproject.toml - __init__.py files use importlib.metadata)
VERSION_FILES = [
    REPO_ROOT / "pyproject.toml",
    REPO_ROOT / "packages/core/pyproject.toml",
    REPO_ROOT / "packages/cli/pyproject.toml",
]

# Package directories in publish order
PACKAGES = [
    ("emdash-core", REPO_ROOT / "packages/core"),
    ("emdash-cli", REPO_ROOT / "packages/cli"),
    ("emdash-ai", REPO_ROOT),
]


def get_current_version() -> str:
    """Get current version from root pyproject.toml."""
    pyproject = REPO_ROOT / "pyproject.toml"
    content = pyproject.read_text()
    match = re.search(r'version = "(\d+\.\d+\.\d+)"', content)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    return match.group(1)


def bump_version(version: str, bump_type: str) -> str:
    """Bump version string."""
    major, minor, patch = map(int, version.split("."))

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def update_version_in_file(file_path: Path, old_version: str, new_version: str, dry_run: bool) -> None:
    """Update version in a file."""
    content = file_path.read_text()

    # Replace version string
    new_content = content.replace(f'version = "{old_version}"', f'version = "{new_version}"')
    new_content = new_content.replace(f'__version__ = "{old_version}"', f'__version__ = "{new_version}"')

    if content != new_content:
        print(f"  Updating {file_path.relative_to(REPO_ROOT)}: {old_version} -> {new_version}")
        if not dry_run:
            file_path.write_text(new_content)


def switch_to_pypi_deps(new_version: str, dry_run: bool) -> dict[Path, str]:
    """Switch from workspace to PyPI dependencies. Returns original content for restore."""
    originals = {}

    # Main pyproject.toml - remove workspace sources for release
    main_pyproject = REPO_ROOT / "pyproject.toml"
    originals[main_pyproject] = main_pyproject.read_text()

    content = originals[main_pyproject]
    # Remove the [tool.uv.sources] section for PyPI release
    content = re.sub(
        r'\[tool\.uv\.sources\]\nemdash-core = \{ workspace = true \}\nemdash-cli = \{ workspace = true \}\n*',
        '',
        content
    )

    print(f"  Switching {main_pyproject.relative_to(REPO_ROOT)} to PyPI deps")
    if not dry_run:
        main_pyproject.write_text(content)

    # CLI pyproject.toml - remove workspace source
    cli_pyproject = REPO_ROOT / "packages/cli/pyproject.toml"
    originals[cli_pyproject] = cli_pyproject.read_text()

    content = originals[cli_pyproject]
    content = re.sub(
        r'\[tool\.uv\.sources\]\nemdash-core = \{ workspace = true \}\n*',
        '',
        content
    )

    print(f"  Switching {cli_pyproject.relative_to(REPO_ROOT)} to PyPI deps")
    if not dry_run:
        cli_pyproject.write_text(content)

    return originals


def restore_local_deps(originals: dict[Path, str], dry_run: bool) -> None:
    """Restore local development paths."""
    for file_path, content in originals.items():
        print(f"  Restoring {file_path.relative_to(REPO_ROOT)} to workspace paths")
        if not dry_run:
            file_path.write_text(content)

    # Regenerate uv.lock with workspace paths
    print(f"  Regenerating uv.lock...")
    if not dry_run:
        subprocess.run(
            ["uv", "lock"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )


def build_and_publish(package_name: str, package_dir: Path, dry_run: bool, token: str | None = None) -> bool:
    """Build and publish a package to PyPI using uv."""
    print(f"\n  Building {package_name}...")

    # Remove uv.lock to avoid workspace dependencies being used
    lock_file = package_dir / "uv.lock"
    if lock_file.exists():
        print(f"    Removing {lock_file.name} to use PyPI deps")
        if not dry_run:
            lock_file.unlink()

    # Clean workspace root dist folder to avoid uploading old wheels
    # uv build in a workspace puts files in the workspace root's dist/
    dist_dir = REPO_ROOT / "dist"
    if dist_dir.exists() and not dry_run:
        shutil.rmtree(dist_dir)

    if dry_run:
        print(f"    [dry-run] Would run: uv build --package {package_name}")
        print(f"    [dry-run] Would run: uv publish dist/*")
        return True

    # Build from workspace root with --package flag
    result = subprocess.run(
        ["uv", "build", "--package", package_name],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"    Build failed: {result.stderr}")
        return False
    print(f"    Build successful")

    # Publish from workspace root where dist/ is located
    print(f"  Publishing {package_name}...")

    # Build publish command with optional token
    dist_files = list(dist_dir.glob("*"))
    publish_cmd = ["uv", "publish"] + [str(f) for f in dist_files]
    if token:
        publish_cmd.extend(["--token", token])

    result = subprocess.run(
        publish_cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"    Publish failed: {result.stderr}")
        return False
    print(f"    Published successfully!")

    return True


def git_commit_and_tag(new_version: str, dry_run: bool) -> bool:
    """Commit version bump and create git tag."""
    print(f"\n  Committing version bump...")

    if dry_run:
        print(f"    [dry-run] Would run: git add -A")
        print(f"    [dry-run] Would run: git commit -m 'Release v{new_version} to PyPI'")
        print(f"    [dry-run] Would run: git tag -a v{new_version}")
        print(f"    [dry-run] Would run: git push && git push origin v{new_version}")
        return True

    # Stage all changes
    result = subprocess.run(["git", "add", "-A"], cwd=REPO_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    git add failed: {result.stderr}")
        return False

    # Commit
    commit_msg = f"Release v{new_version} to PyPI"
    result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=REPO_ROOT, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"    git commit failed: {result.stderr}")
        return False
    print(f"    Committed: {commit_msg}")

    # Create tag
    result = subprocess.run(
        ["git", "tag", "-a", f"v{new_version}", "-m", f"Release v{new_version}"],
        cwd=REPO_ROOT, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"    git tag failed: {result.stderr}")
        return False
    print(f"    Tagged: v{new_version}")

    # Push commit and tag
    result = subprocess.run(["git", "push"], cwd=REPO_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    git push failed: {result.stderr}")
        return False

    result = subprocess.run(
        ["git", "push", "origin", f"v{new_version}"],
        cwd=REPO_ROOT, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"    git push tag failed: {result.stderr}")
        return False
    print(f"    Pushed to GitHub")

    return True


def main():
    parser = argparse.ArgumentParser(description="Release emdash packages to PyPI")
    parser.add_argument("--major", action="store_true", help="Bump major version")
    parser.add_argument("--minor", action="store_true", help="Bump minor version")
    parser.add_argument("--patch", action="store_true", help="Bump patch version (default)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--no-git", action="store_true", help="Skip git commit/tag/push")
    parser.add_argument("--token", type=str, help="PyPI token (or set PYPI_TOKEN env var)")
    args = parser.parse_args()

    # Get PyPI token from argument or environment
    token = args.token or os.environ.get("PYPI_TOKEN")
    if not token and not args.dry_run:
        print("Error: PyPI token required. Provide via --token or PYPI_TOKEN env var.")
        sys.exit(1)

    # Check uv is installed
    if not shutil.which("uv"):
        print("Error: uv is not installed.")
        print("Install with: curl -LsSf https://astral.sh/uv/install.sh | sh")
        sys.exit(1)

    # Determine bump type
    if args.major:
        bump_type = "major"
    elif args.minor:
        bump_type = "minor"
    else:
        bump_type = "patch"

    dry_run = args.dry_run
    if dry_run:
        print("=== DRY RUN MODE ===\n")

    # Get current and new versions
    current_version = get_current_version()
    new_version = bump_version(current_version, bump_type)

    print(f"Releasing emdash-ai: {current_version} -> {new_version}")
    print(f"Bump type: {bump_type}")
    print()

    # Step 1: Update versions in all files
    print("Step 1: Updating version numbers...")
    for file_path in VERSION_FILES:
        if file_path.exists():
            update_version_in_file(file_path, current_version, new_version, dry_run)
    print()

    # Step 2: Switch to PyPI dependencies
    print("Step 2: Switching to PyPI dependencies...")
    originals = switch_to_pypi_deps(new_version, dry_run)
    print()

    # Step 3: Build and publish packages in order
    print("Step 3: Building and publishing packages...")
    success = True
    for package_name, package_dir in PACKAGES:
        if not build_and_publish(package_name, package_dir, dry_run, token):
            success = False
            print(f"\nFailed to publish {package_name}. Stopping.")
            break
    print()

    # Step 4: Restore local development paths
    print("Step 4: Restoring local development paths...")
    restore_local_deps(originals, dry_run)
    print()

    # Step 5: Git commit, tag, and push
    if success and not args.no_git:
        print("Step 5: Git commit, tag, and push...")
        if not git_commit_and_tag(new_version, dry_run):
            print("  Warning: Git operations failed, but PyPI publish succeeded")
    print()

    if success:
        print(f"=== Release {new_version} complete! ===")
        print(f"\nPackages published:")
        print(f"  - emdash-core {new_version}: https://pypi.org/project/emdash-core/")
        print(f"  - emdash-cli {new_version}: https://pypi.org/project/emdash-cli/")
        print(f"  - emdash-ai {new_version}: https://pypi.org/project/emdash-ai/")
        print(f"\nInstall with: uv pip install emdash-ai=={new_version}")
    else:
        print("=== Release failed ===")
        sys.exit(1)


if __name__ == "__main__":
    main()
