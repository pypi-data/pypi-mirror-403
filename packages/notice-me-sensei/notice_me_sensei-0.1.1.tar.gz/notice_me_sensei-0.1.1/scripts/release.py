#!/usr/bin/env python3
"""Release helper script for sensei.

Bumps version in pyproject.toml, creates a release branch, and opens a PR.
When the PR is merged, GitHub Actions publishes to PyPI.

Usage:
    python scripts/release.py patch   # 0.1.0 -> 0.1.1
    python scripts/release.py minor   # 0.1.0 -> 0.2.0
    python scripts/release.py major   # 0.1.0 -> 1.0.0
    python scripts/release.py 0.2.0   # Explicit version
"""

import re
import subprocess
import sys
from pathlib import Path


def get_current_version(pyproject: Path) -> str:
    """Extract current version from pyproject.toml."""
    content = pyproject.read_text()
    match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    return match.group(1)


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse semver string into tuple."""
    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid semver: {version}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def bump_version(current: str, bump_type: str) -> str:
    """Calculate new version based on bump type."""
    major, minor, patch = parse_version(current)

    if bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "major":
        return f"{major + 1}.0.0"
    else:
        # Assume explicit version
        parse_version(bump_type)  # Validate format
        return bump_type


def update_pyproject(pyproject: Path, new_version: str) -> None:
    """Update version in pyproject.toml."""
    content = pyproject.read_text()
    updated = re.sub(
        r'^version = "[^"]+"',
        f'version = "{new_version}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    pyproject.write_text(updated)


def run(
    cmd: list[str], check: bool = True, capture: bool = False
) -> subprocess.CompletedProcess:
    """Run a shell command."""
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=capture, text=True)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/release.py <patch|minor|major|X.Y.Z>")
        return 1

    bump_type = sys.argv[1]

    # Find pyproject.toml
    repo_root = Path(__file__).parent.parent
    pyproject = repo_root / "pyproject.toml"

    if not pyproject.exists():
        print(f"Error: {pyproject} not found")
        return 1

    # Check we're on main
    result = run(["git", "branch", "--show-current"], capture=True)
    if result.stdout.strip() != "main":
        print("Error: Must be on main branch to create a release")
        return 1

    # Check for clean working directory
    result = run(["git", "status", "--porcelain"], capture=True)
    if result.stdout.strip():
        print("Error: Working directory not clean. Commit or stash changes first.")
        return 1

    # Make sure we're up to date
    run(["git", "pull", "--ff-only"])

    # Get current version and calculate new
    current = get_current_version(pyproject)
    try:
        new_version = bump_version(current, bump_type)
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    print(f"Bumping version: {current} -> {new_version}")

    # Create release branch
    branch = f"release/{new_version}"
    run(["git", "checkout", "-b", branch])

    # Update pyproject.toml
    update_pyproject(pyproject, new_version)
    print(f"Updated {pyproject}")

    # Commit and push
    run(["git", "add", "pyproject.toml"])
    run(["git", "commit", "-m", f"Bump version to {new_version}"])
    run(["git", "push", "-u", "origin", branch])

    # Create PR
    run([
        "gh", "pr", "create",
        "--title", f"Release {new_version}",
        "--body", f"Bump version to {new_version}\n\nWhen merged, this will automatically publish to PyPI and create a GitHub release.",
    ])

    print()
    print(f"Created PR for release {new_version}")
    print("When you merge the PR, it will automatically:")
    print("  1. Run all CI checks")
    print("  2. Publish to PyPI")
    print("  3. Create a git tag")
    print("  4. Create a GitHub Release")

    # Switch back to main
    run(["git", "checkout", "main"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
