#!/usr/bin/env python3
"""
Release script for @emdash/client npm package.

Builds, packs, and uploads the package to a public file host.

Usage:
    python scripts/release-node.py [patch|minor|major]
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


# Configuration
CLIENT_DIR = Path(__file__).parent.parent / "packages" / "client"
RELEASES_DIR = Path(__file__).parent.parent / "releases"
UPLOAD_URL = "https://catbox.moe/user/api.php"


def run(cmd: str, cwd: Path = None, capture: bool = True) -> str:
    """Run a shell command and return output."""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd or CLIENT_DIR,
        capture_output=capture,
        text=True
    )
    if result.returncode != 0:
        print(f"Error running: {cmd}")
        print(result.stderr)
        sys.exit(1)
    return result.stdout.strip() if capture else ""


def get_current_version() -> str:
    """Get current version from package.json."""
    package_json = CLIENT_DIR / "package.json"
    with open(package_json) as f:
        data = json.load(f)
    return data["version"]


def bump_version(current: str, bump_type: str) -> str:
    """Bump version number."""
    parts = current.split(".")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    return f"{major}.{minor}.{patch}"


def update_version(new_version: str):
    """Update version in package.json."""
    package_json = CLIENT_DIR / "package.json"
    with open(package_json) as f:
        data = json.load(f)

    data["version"] = new_version

    with open(package_json, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def build_package():
    """Build the TypeScript package."""
    print("  Building package...")
    run("npm install", capture=False)
    run("npm run build", capture=False)


def create_tarball(version: str) -> Path:
    """Create npm tarball."""
    print("  Creating tarball...")
    run("npm pack")
    tarball = CLIENT_DIR / f"emdash-client-{version}.tgz"
    return tarball


def upload_tarball(tarball: Path) -> str:
    """Upload tarball to catbox.moe and return URL."""
    print("  Uploading to catbox.moe...")

    result = subprocess.run(
        [
            "curl", "-s",
            "-X", "POST",
            "-F", "reqtype=fileupload",
            "-F", f"fileToUpload=@{tarball}",
            "https://catbox.moe/user/api.php"
        ],
        capture_output=True,
        text=True,
        cwd=tarball.parent
    )

    if result.returncode != 0:
        print(f"Upload failed: {result.stderr}")
        sys.exit(1)

    url = result.stdout.strip()
    if not url.startswith("https://"):
        print(f"Upload failed: {result.stdout}")
        sys.exit(1)

    return url


def save_to_releases(tarball: Path):
    """Copy tarball to releases directory."""
    RELEASES_DIR.mkdir(exist_ok=True)
    dest = RELEASES_DIR / tarball.name

    # Remove old versions
    for old in RELEASES_DIR.glob("emdash-client-*.tgz"):
        old.unlink()

    import shutil
    shutil.copy(tarball, dest)
    print(f"  Saved to {dest}")


def git_commit_and_push(version: str, url: str):
    """Commit version bump and push."""
    print("  Committing changes...")

    run(f"git add package.json", cwd=CLIENT_DIR)
    run(f"git add releases/", cwd=CLIENT_DIR.parent.parent)

    commit_msg = f"Release @emdash/client v{version}\\n\\nInstall: npm install {url}"
    run(f'git commit -m "Release @emdash/client v{version}"', cwd=CLIENT_DIR.parent.parent)
    run("git push", cwd=CLIENT_DIR.parent.parent)

    # Create git tag
    tag = f"client-v{version}"
    run(f'git tag -a {tag} -m "@emdash/client v{version}"', cwd=CLIENT_DIR.parent.parent)
    run(f"git push origin {tag}", cwd=CLIENT_DIR.parent.parent)


def main():
    # Parse arguments
    bump_type = "patch"
    if len(sys.argv) > 1:
        if sys.argv[1] in ["patch", "minor", "major"]:
            bump_type = sys.argv[1]
        else:
            print(f"Unknown bump type: {sys.argv[1]}")
            print("Usage: release-node.py [patch|minor|major]")
            sys.exit(1)

    # Get versions
    current_version = get_current_version()
    new_version = bump_version(current_version, bump_type)

    print(f"Releasing @emdash/client: {current_version} -> {new_version}")
    print(f"Bump type: {bump_type}")
    print()

    # Step 1: Update version
    print("Step 1: Updating version...")
    update_version(new_version)
    print(f"  Updated package.json to {new_version}")
    print()

    # Step 2: Build
    print("Step 2: Building package...")
    build_package()
    print("  Build successful")
    print()

    # Step 3: Create tarball
    print("Step 3: Creating tarball...")
    tarball = create_tarball(new_version)
    print(f"  Created {tarball.name}")
    print()

    # Step 4: Upload
    print("Step 4: Uploading tarball...")
    url = upload_tarball(tarball)
    print(f"  Uploaded to: {url}")
    print()

    # Step 5: Save to releases
    print("Step 5: Saving to releases/...")
    save_to_releases(tarball)
    print()

    # Step 6: Git commit and push
    print("Step 6: Git commit, tag, and push...")
    git_commit_and_push(new_version, url)
    print()

    # Cleanup
    tarball.unlink()

    # Done
    print("=" * 50)
    print(f"  @emdash/client v{new_version} released!")
    print("=" * 50)
    print()
    print("Install with:")
    print(f"  npm install {url}")
    print()


if __name__ == "__main__":
    main()
