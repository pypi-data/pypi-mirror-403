#!/usr/bin/env python3
"""
Release tag creation utility for xt-workbench.

This script guides developers through creating properly formatted git tags for releases.
Supports automatic semver bumping (major/minor/patch) and custom version input with safeguards.

Release types:
  - staging: Creates v<VERSION>-rc tag for staging environment (from develop or production-support branches)
  - prod: Creates v<VERSION> tag by promoting a tested -rc tag

Branch rules:
  - Staging: Must be on develop or production-support branch (allow main with warning)
  - Production: Can be on any branch (checks git, not working tree)

Changelog management:
  - Automatically updates [Unreleased] section to new version before tagging
  - Commits changelog changes before tag creation
  - Supports --force to skip changelog check

Usage:
  python scripts/release.py

Or via poe (in backend directory):
  poe release-tag

Environment:
  Requires git, Python 3.12+, working git repository with tags
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

AUTO_CONFIRM = False


class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.CYAN}ℹ {text}{Colors.RESET}")


def run_command(cmd: str, cwd: Optional[str] = None) -> Tuple[int, str]:
    """Run a shell command and return exit code and output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        return result.returncode, result.stdout.strip()
    except Exception as e:
        print_error(f"Failed to run command: {cmd}\nError: {e}")
        sys.exit(1)


def get_repo_root() -> str:
    """Get the root directory of the git repository."""
    returncode, output = run_command("git rev-parse --show-toplevel")
    if returncode != 0:
        print_error("Not in a git repository")
        sys.exit(1)
    return output


def get_current_branch() -> str:
    """Get the current git branch name."""
    returncode, output = run_command("git rev-parse --abbrev-ref HEAD")
    if returncode != 0:
        print_error("Failed to get current branch")
        sys.exit(1)
    return output


def get_current_version() -> Optional[str]:
    """Detect current version from git tags."""
    print_info("Detecting current version from git tags...")

    # Use semver sort across all tags (not only reachable from HEAD). This avoids
    # `git describe` picking an older reachable tag when a newer tag exists on
    # another branch (e.g., latest tag v1.6.0-rc but current branch only sees
    # v1.5.12-rc).
    returncode, output = run_command("git tag -l 'v*' --sort=-version:refname")
    if returncode == 0 and output:
        for tag in output.split("\n"):
            match = re.match(r"v?(\d+\.\d+\.\d+)(-rc)?", tag)
            if match:
                version = match.group(1)
                print_success(f"Current version: {version} (from tag: {tag})")
                return version

    print_warning("Could not detect version automatically, defaulting to 0.0.0")
    return "0.0.0"


def parse_version(version_str: str) -> Optional[Tuple[int, int, int]]:
    """Parse semantic version string into (major, minor, patch) tuple."""
    match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", version_str)
    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3))
    return None


def format_version(major: int, minor: int, patch: int) -> str:
    """Format version tuple into semantic version string."""
    return f"{major}.{minor}.{patch}"


def bump_version(version: str, bump_type: str) -> str:
    """Bump version based on type (major, minor, patch)."""
    parsed = parse_version(version)
    if not parsed:
        print_error(f"Invalid version format: {version}")
        sys.exit(1)

    major, minor, patch = parsed

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        print_error(f"Invalid bump type: {bump_type}")
        sys.exit(1)

    return format_version(major, minor, patch)


def confirm_action(prompt: str, default: bool = True) -> bool:
    """Get user confirmation with default; auto-confirm when requested."""
    if AUTO_CONFIRM:
        return True

    default_str = "[Y/n]" if default else "[y/N]"
    response = input(f"{Colors.BOLD}{prompt} {default_str}: {Colors.RESET}").strip().lower()

    if response in ("y", "yes"):
        return True
    if response in ("n", "no"):
        return False
    return default


def choose_option(prompt: str, options: list, preselection: Optional[str] = None) -> str:
    """Let user choose from a list of options, honoring a preselection for non-interactive use."""
    if preselection:
        if preselection in options:
            return preselection
        print_error(f"Invalid selection '{preselection}'. Valid options: {', '.join(options)}")
        sys.exit(1)

    print(f"\n{Colors.BOLD}{prompt}{Colors.RESET}")
    for i, option in enumerate(options, 1):
        print(f"  {Colors.CYAN}{i}{Colors.RESET}. {option}")

    while True:
        choice = input(f"\n{Colors.BOLD}Select option [1-{len(options)}]: {Colors.RESET}").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print_error(f"Invalid selection. Please enter 1-{len(options)}")


def is_version_lower_than_any_tag(version: str) -> bool:
    """Check if provided version is lower than any existing tag."""
    parsed = parse_version(version)
    if not parsed:
        return False

    returncode, output = run_command("git tag -l 'v*' --sort=-version:refname")
    if returncode != 0:
        return False

    tags = output.split("\n") if output else []
    for tag in tags:
        tag_parsed = parse_version(tag)
        if tag_parsed and tag_parsed > parsed:
            return True

    return False


def check_branch_validity(release_type: str, force: bool = False) -> bool:
    """Validate current branch for release type."""
    branch = get_current_branch()

    if release_type == "staging":
        allowed_branches = ["develop", "production-support", "main"]
        if branch not in allowed_branches:
            print_error(f"Staging releases can only be created from: {', '.join(allowed_branches)}")
            print_error(f"Current branch: {branch}")
            if not force:
                return False
            print_warning("--force flag used; proceeding anyway")

        if branch == "develop":
            print_warning(
                "You are on the 'develop' branch. Consider pushing these changes to 'main' via a PR before creating a staging release."
            )
            if not confirm_action("Continue with staging release?"):
                return False

    return True


def find_changelog_file(repo_root: str) -> Optional[Path]:
    """Find changelog file (supports CHANGELOG.md, changelog.md, HISTORY.md, etc.)."""
    changelog_patterns = [
        "changelog.md",
        "CHANGELOG.md",
        "CHANGELOG.MD",
        "HISTORY.md",
        "HISTORY.md",
        "changes.md",
        "CHANGES.md",
    ]

    repo_path = Path(repo_root)
    for pattern in changelog_patterns:
        candidate = repo_path / pattern
        if candidate.exists():
            return candidate

    return None


def update_changelog(changelog_path: Path, version: str, force: bool = False) -> bool:
    """Update changelog: replace [Unreleased] with new version heading."""
    print_info(f"Checking changelog: {changelog_path.name}")

    try:
        content = changelog_path.read_text(encoding="utf-8")
    except Exception as e:
        print_error(f"Failed to read changelog: {e}")
        if not force:
            print_warning("Use --force to skip changelog update")
            return False
        print_warning("Skipping changelog update (--force flag used)")
        return True

    # Check if [Unreleased] section exists
    unreleased_pattern = r"^## \[Unreleased\]\s*$"
    if not re.search(unreleased_pattern, content, flags=re.MULTILINE):
        print_warning("No [Unreleased] section found in changelog")
        if not confirm_action("Proceed without updating changelog?"):
            return False
        return True

    # Replace first [Unreleased] heading with new version heading, re-adding [Unreleased]
    updated_content = re.sub(
        unreleased_pattern,
        f"## [Unreleased]\n\n## {version}",
        content,
        count=1,
        flags=re.MULTILINE,
    )

    if updated_content == content:
        print_warning("Changelog appears unchanged after update attempt")
        if not confirm_action("Continue with release?"):
            return False
    else:
        try:
            changelog_path.write_text(updated_content, encoding="utf-8")
            print_success(f"Updated changelog with version {version}")
        except Exception as e:
            print_error(f"Failed to write changelog: {e}")
            if not force:
                return False
            print_warning("Could not write changelog (--force flag used)")

    return True


def commit_changelog(changelog_path: Path, version: str) -> bool:
    """Commit changelog changes."""
    returncode, _ = run_command("git status --porcelain")
    if returncode != 0:
        return False

    # Check if there are staged changes
    returncode, output = run_command("git diff --cached --name-only")
    if returncode != 0 or not output:
        # Nothing staged; add the changelog
        returncode, _ = run_command(f"git add {changelog_path}")
        if returncode != 0:
            print_error("Failed to stage changelog")
            return False

    # Commit
    commit_msg = f"chore: update changelog for {version}"
    returncode, output = run_command(f'git commit -m "{commit_msg}"')
    if returncode != 0:
        # Might already be committed or no changes
        print_warning(f"Changelog commit returned code {returncode}")
        # Not fatal; continue
    else:
        print_success(f"Committed changelog: {commit_msg}")

    return True


def create_tag(tag_name: str, push: bool = False) -> bool:
    """Create git tag and optionally push to remote."""
    # Check if tag already exists
    returncode, _ = run_command(f"git rev-parse {tag_name} 2>/dev/null")
    if returncode == 0:
        print_error(f"Tag '{tag_name}' already exists!")
        return False

    # Create tag
    returncode, output = run_command(f"git tag {tag_name}")
    if returncode != 0:
        print_error(f"Failed to create tag: {output}")
        return False

    print_success(f"Created tag: {tag_name}")

    if push:
        returncode, output = run_command(f"git push origin {tag_name}")
        if returncode != 0:
            print_error(f"Failed to push tag: {output}")
            print_warning("Tag created locally but not pushed. Delete it with: git tag -d " + tag_name)
            return False
        print_success(f"Pushed tag to remote: {tag_name}")

    return True


def handle_staging_release(
    force: bool = False, bump_preselect: Optional[str] = None, action_preselect: Optional[str] = None
) -> None:
    """Handle staging release (RC tag creation)."""
    print_header("Staging Release (RC tag)")

    # Check branch
    if not check_branch_validity("staging", force):
        print_warning("Staging release cancelled")
        return

    current_version = get_current_version()
    if not current_version:
        print_error("Could not determine current version")
        sys.exit(1)

    # Ask for version bump
    bump_type = choose_option("Select version bump type:", ["major", "minor", "patch"], preselection=bump_preselect)

    new_version = bump_version(current_version, bump_type)
    print_info(f"Version bump: {current_version} → {new_version}")

    if not confirm_action(
        f"\n{Colors.BOLD}Proceed with {Colors.CYAN}{bump_type}{Colors.RESET} bump to {Colors.GREEN}{new_version}{Colors.RESET}?"
    ):
        print_warning("Staging release cancelled")
        return

    # Update changelog
    repo_root = get_repo_root()
    changelog_path = find_changelog_file(repo_root)
    if changelog_path:
        if not update_changelog(changelog_path, new_version, force):
            print_warning("Staging release cancelled (changelog update failed)")
            return
        if not commit_changelog(changelog_path, new_version):
            print_warning("Failed to commit changelog, but continuing with tag creation")
    else:
        print_warning("No changelog file found; skipping changelog update")

    rc_tag = f"v{new_version}-rc"
    print_info(f"\nRC tag to create: {Colors.BOLD}{Colors.CYAN}{rc_tag}{Colors.RESET}")

    # Ask for push option
    action = choose_option(
        "What would you like to do?",
        ["Create tag locally only", "Create tag and push to remote", "Cancel"],
        preselection=action_preselect,
    )

    if action == "Cancel":
        print_warning("Staging release cancelled")
        return

    push = action == "Create tag and push to remote"

    if create_tag(rc_tag, push=push):
        print_success("\n✓ Staging release prepared!")
        print_info(f"RC tag: {Colors.BOLD}{rc_tag}{Colors.RESET}")
        if not push:
            print_info(f"Push with: {Colors.DIM}git push origin {rc_tag}{Colors.RESET}")
    else:
        print_error("Failed to create staging release")
        sys.exit(1)


def handle_prod_release(
    force: bool = False, action_preselect: Optional[str] = None, rc_tag_preselect: Optional[str] = None
) -> None:
    """Handle production release (promote RC tag to production)."""
    print_header("Production Release (promote RC tag)")

    # Get all RC tags
    returncode, output = run_command("git tag -l 'v*-rc' --sort=-version:refname")

    if returncode != 0 or not output:
        print_error("No RC tags found. Please create a staging release first.")
        sys.exit(1)

    available_rc_tags = output.strip().split("\n")

    if rc_tag_preselect:
        # Validate provided RC tag
        if rc_tag_preselect not in available_rc_tags:
            print_error(f"RC tag '{rc_tag_preselect}' not found.")
            print_info(f"Available RC tags: {', '.join(available_rc_tags[:5])}")
            sys.exit(1)
        rc_tag = rc_tag_preselect
    else:
        # Interactive selection
        rc_tag = choose_option(
            f"Select RC tag to promote (showing {min(10, len(available_rc_tags))} most recent):", available_rc_tags[:10]
        )

    print_info(f"RC tag to promote: {Colors.BOLD}{rc_tag}{Colors.RESET}")

    # Extract version from RC tag
    match = re.match(r"v?(\d+\.\d+\.\d+)-rc", rc_tag)
    if not match:
        print_error(f"Could not parse version from RC tag: {rc_tag}")
        sys.exit(1)

    version = match.group(1)
    prod_tag = f"v{version}"

    print_info(f"Production tag to create: {Colors.BOLD}{Colors.GREEN}{prod_tag}{Colors.RESET}")

    if not confirm_action(f"\nPromote {Colors.CYAN}{rc_tag}{Colors.RESET} to {Colors.GREEN}{prod_tag}{Colors.RESET}?"):
        print_warning("Production release cancelled")
        return

    # Update changelog if present (move version from Unreleased to dated section)
    repo_root = get_repo_root()
    changelog_path = find_changelog_file(repo_root)
    if changelog_path:
        if not update_changelog(changelog_path, version, force):
            print_warning("Production release cancelled (changelog update failed)")
            return
        if not commit_changelog(changelog_path, version):
            print_warning("Failed to commit changelog, but continuing with tag creation")

    # Ask for push option
    action = choose_option(
        "What would you like to do?",
        ["Create tag locally only", "Create tag and push to remote", "Cancel"],
        preselection=action_preselect,
    )

    if action == "Cancel":
        print_warning("Production release cancelled")
        return

    push = action == "Create tag and push to remote"

    if create_tag(prod_tag, push=push):
        print_success("\n✓ Production release prepared!")
        print_info(f"Production tag: {Colors.BOLD}{prod_tag}{Colors.RESET}")
        print_info("RC tag will be promoted by the release pipeline.")
        if not push:
            print_info(f"Push with: {Colors.DIM}git push origin {prod_tag}{Colors.RESET}")
    else:
        print_error("Failed to create production release")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Create release tags for xt-workbench",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/release.py           # Interactive menu
  python scripts/release.py --force   # Skip safety checks
        """,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip safety checks (branch validation, changelog checks)",
    )
    parser.add_argument(
        "--release-type",
        choices=["staging", "prod"],
        help="Run non-interactively for the given release type",
    )
    parser.add_argument(
        "--bump",
        choices=["major", "minor", "patch"],
        help="Version bump type for staging releases",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push the created tag to origin (non-interactive mode)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Assume yes for all confirmations (non-interactive)",
    )
    parser.add_argument(
        "--rc-tag",
        type=str,
        help="RC tag to promote for production releases (e.g., v1.5.13-rc)",
    )

    args = parser.parse_args()

    global AUTO_CONFIRM
    AUTO_CONFIRM = args.yes

    print_header("XT Workbench Release Manager")

    release_options = ["Staging (RC tag)", "Production (promote RC)", "Cancel"]
    release_preselect = None
    if args.release_type == "staging":
        release_preselect = "Staging (RC tag)"
    elif args.release_type == "prod":
        release_preselect = "Production (promote RC)"

    release_type = choose_option(
        "Select release type:",
        release_options,
        preselection=release_preselect,
    )

    if release_type == "Cancel":
        print_warning("Release cancelled")
        return

    push_action_preselect = "Create tag and push to remote" if args.push else "Create tag locally only"

    if release_type == "Staging (RC tag)":
        bump_preselect = args.bump
        if bump_preselect is None and args.release_type == "staging":
            print_error("--bump is required when --release-type staging is provided")
            sys.exit(1)
        handle_staging_release(force=args.force, bump_preselect=bump_preselect, action_preselect=push_action_preselect)
    elif release_type == "Production (promote RC)":
        if args.rc_tag is None and args.release_type == "prod":
            print_error("--rc-tag is required when --release-type prod is provided")
            sys.exit(1)
        handle_prod_release(force=args.force, action_preselect=push_action_preselect, rc_tag_preselect=args.rc_tag)


if __name__ == "__main__":
    main()
