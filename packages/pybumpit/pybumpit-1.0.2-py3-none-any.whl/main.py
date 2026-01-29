"""pybumpit: npm version-like tool for Python projects."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Literal

import tomlkit
from python_clack import intro, is_cancel, log, outro, select

PYPROJECT_FILE = "pyproject.toml"

BumpType = Literal["major", "minor", "patch"]


def read_pyproject() -> tomlkit.TOMLDocument:
    """Read and parse pyproject.toml."""
    path = Path(PYPROJECT_FILE)
    if not path.exists():
        log.error(f"{PYPROJECT_FILE} not found")
        sys.exit(1)
    return tomlkit.parse(path.read_text())


def write_pyproject(doc: tomlkit.TOMLDocument) -> None:
    """Write pyproject.toml preserving formatting."""
    Path(PYPROJECT_FILE).write_text(tomlkit.dumps(doc))


def get_version(doc: tomlkit.TOMLDocument) -> str:
    """Extract version from pyproject.toml."""
    try:
        version = doc["project"]["version"]  # type: ignore[index]
        if not isinstance(version, str):
            log.error("Version must be a string")
            sys.exit(1)
        return version
    except KeyError:
        log.error("No version found in [project] section")
        sys.exit(1)


def set_version(doc: tomlkit.TOMLDocument, version: str) -> None:
    """Set version in pyproject.toml document."""
    doc["project"]["version"] = version  # type: ignore[index]


def bump_version(current: str, bump_type: BumpType) -> str:
    """Calculate new version based on bump type."""
    parts = current.split(".")
    if len(parts) != 3:
        log.error(f"Invalid version format: {current} (expected X.Y.Z)")
        sys.exit(1)

    try:
        major, minor, patch = map(int, parts)
    except ValueError:
        log.error(f"Invalid version format: {current} (expected numeric X.Y.Z)")
        sys.exit(1)

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def is_git_repo() -> bool:
    """Check if current directory is a git repository."""
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def is_working_tree_clean() -> bool:
    """Check if git working tree is clean (no uncommitted changes)."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    return len(result.stdout.strip()) == 0


def git_commit_and_tag(version: str) -> None:
    """Create git commit and tag for the version."""
    tag = f"v{version}"

    # Stage pyproject.toml
    subprocess.run(["git", "add", PYPROJECT_FILE], check=True)

    # Create commit
    subprocess.run(["git", "commit", "-m", tag], check=True)

    # Create tag
    subprocess.run(["git", "tag", "-a", tag, "-m", tag], check=True)


def prompt_bump_type(current_version: str) -> BumpType | None:
    """Show interactive prompt to select bump type."""
    intro("pybumpit")

    result = select(
        "Select version type",
        options=[
            {
                "value": "patch",
                "label": "Patch",
                "hint": f"{current_version} → {bump_version(current_version, 'patch')}",
            },
            {
                "value": "minor",
                "label": "Minor",
                "hint": f"{current_version} → {bump_version(current_version, 'minor')}",
            },
            {
                "value": "major",
                "label": "Major",
                "hint": f"{current_version} → {bump_version(current_version, 'major')}",
            },
        ],
    )

    if is_cancel(result):
        outro("Cancelled")
        return None

    return result  # type: ignore[return-value]


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Bump version in pyproject.toml (like npm version)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pybumpit           Interactive mode
  pybumpit patch     Bump patch version (0.1.0 -> 0.1.1)
  pybumpit minor     Bump minor version (0.1.0 -> 0.2.0)
  pybumpit major     Bump major version (0.1.0 -> 1.0.0)
  pybumpit patch -f  Bump even with uncommitted changes
""",
    )
    parser.add_argument(
        "bump_type",
        nargs="?",
        choices=["major", "minor", "patch"],
        help="Version bump type (interactive if omitted)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Allow bump with uncommitted changes",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Read current version
    doc = read_pyproject()
    current_version = get_version(doc)

    # Get bump type (from args or interactive prompt)
    bump_type: BumpType | None = args.bump_type
    if bump_type is None:
        bump_type = prompt_bump_type(current_version)
        if bump_type is None:
            sys.exit(1)

    # Check git status
    in_git = is_git_repo()
    if in_git and not args.force:
        if not is_working_tree_clean():
            log.error("Working tree has uncommitted changes. Use --force to override.")
            sys.exit(1)

    # Calculate new version
    new_version = bump_version(current_version, bump_type)

    # Update pyproject.toml
    set_version(doc, new_version)
    write_pyproject(doc)

    # Git commit and tag if in a git repo
    if in_git:
        git_commit_and_tag(new_version)

    # Output new version (like npm version)
    print(f"v{new_version}")


if __name__ == "__main__":
    main()
