"""CLI entry point for tarnished."""

import argparse
import json
import sys
from pathlib import Path

from tarnished.checksum import compute_checksum
from tarnished.defaults import (
    DEFAULT_CONFIG,
    DEFAULT_CONFIG_FILE,
    DEFAULT_DIR_NAME,
    DEFAULT_GITIGNORE,
    DEFAULT_STATE_FILE,
)
from tarnished.models import Config, Profile, State


def get_tarnished_paths() -> tuple[Path, Path, Path]:
    """Get paths for tarnished directory, config, and state files.

    Returns:
        Tuple of (tarnished_dir, config_path, state_path)
    """
    tarnished_dir = Path.cwd() / DEFAULT_DIR_NAME
    config_path = tarnished_dir / DEFAULT_CONFIG_FILE
    state_path = tarnished_dir / DEFAULT_STATE_FILE
    return tarnished_dir, config_path, state_path


def handle_init(args: argparse.Namespace) -> int:
    """Handle the init command - scaffold .tarnished/ directory."""
    tarnished_dir = Path.cwd() / DEFAULT_DIR_NAME
    config_path = tarnished_dir / DEFAULT_CONFIG_FILE
    gitignore_path = tarnished_dir / ".gitignore"

    if tarnished_dir.exists():
        print(f"{DEFAULT_DIR_NAME}/ already exists")
        return 0

    tarnished_dir.mkdir()
    config_path.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n")
    gitignore_path.write_text(DEFAULT_GITIGNORE)

    print(f"Initialized {DEFAULT_DIR_NAME}/ directory")
    return 0


def handle_save(args: argparse.Namespace) -> int:
    """Handle the save command - save checkpoint for profile.

    Behavior:
    - First time (profile doesn't exist): patterns are required, stored in config
    - Subsequent saves: patterns are optional (reuses stored patterns)
    - If patterns are provided, they update the profile's patterns
    - Computes checksum and saves to state
    """
    profile_name: str = args.profile
    patterns: list[str] = args.patterns or []

    tarnished_dir, config_path, state_path = get_tarnished_paths()

    # Load config and state
    config = Config.from_file(config_path)
    state = State.from_file(state_path)

    # Get existing profile (if any)
    existing_profile = config.get_profile(profile_name)

    # Determine patterns to use
    if patterns:
        # Patterns provided - use them (and update config)
        profile = Profile(patterns=patterns)
        config.set_profile(profile_name, profile)
        config.save(config_path)
    elif existing_profile is not None:
        # No patterns provided, but profile exists - reuse stored patterns
        profile = existing_profile
    else:
        # No patterns and profile doesn't exist - error
        print(
            f"Error: Profile '{profile_name}' does not exist. "
            "Patterns are required for new profiles."
        )
        return 1

    # Compute checksum
    base_path = Path.cwd()
    checksum = compute_checksum(profile.patterns, base_path)

    # Save checkpoint to state
    checkpoint = state.set_checkpoint(profile_name, checksum)
    state.save(state_path)

    saved_at_str = checkpoint.saved_at.strftime("%Y-%m-%d %H:%M")
    print(f"Saved checkpoint for '{profile_name}' at {saved_at_str}")
    return 0


def handle_check(args: argparse.Namespace) -> int:
    """Handle the check command - check if profile is tarnished.

    Exit codes:
    - 0: Clean (no changes)
    - 1: Tarnished (changes detected)
    - 2: Unknown profile (not in config or never saved)
    """
    profile_name: str = args.profile

    tarnished_dir, config_path, state_path = get_tarnished_paths()

    # Load config and state
    config = Config.from_file(config_path)
    state = State.from_file(state_path)

    # Get profile from config
    profile = config.get_profile(profile_name)
    if profile is None:
        print(f"{profile_name}: unknown profile")
        return 2

    # Get checkpoint from state
    checkpoint = state.get_checkpoint(profile_name)
    if checkpoint is None:
        # Profile exists in config but never saved - treat as unknown
        print(f"{profile_name}: unknown profile")
        return 2

    # Compute current checksum
    base_path = Path.cwd()
    current_checksum = compute_checksum(profile.patterns, base_path)

    # Compare checksums
    if current_checksum == checkpoint.checksum:
        print(f"{profile_name}: clean")
        return 0
    else:
        saved_at_str = checkpoint.saved_at.strftime("%Y-%m-%d %H:%M")
        print(f"{profile_name}: tarnished (files changed since {saved_at_str})")
        return 1


def handle_status(args: argparse.Namespace) -> int:
    """Handle the status command - show status of all profiles.

    Outputs JSON with format:
    {
        "profiles": {
            "name": {
                "status": "clean|tarnished|never_saved",
                "saved_at": "ISO datetime or null"
            }
        }
    }
    """
    tarnished_dir, config_path, state_path = get_tarnished_paths()

    # Load config and state
    config = Config.from_file(config_path)
    state = State.from_file(state_path)

    base_path = Path.cwd()
    result: dict[str, dict[str, str | None]] = {}

    for profile_name, profile in config.profiles.items():
        checkpoint = state.get_checkpoint(profile_name)

        if checkpoint is None:
            # Profile in config but never saved
            result[profile_name] = {
                "status": "never_saved",
                "saved_at": None,
            }
        else:
            # Compute current checksum and compare
            current_checksum = compute_checksum(profile.patterns, base_path)
            if current_checksum == checkpoint.checksum:
                status = "clean"
            else:
                status = "tarnished"

            result[profile_name] = {
                "status": status,
                "saved_at": checkpoint.saved_at.isoformat(),
            }

    output = {"profiles": result}
    print(json.dumps(output, indent=2))
    return 0


def main() -> int:
    """Main entry point for tarnished CLI."""
    parser = argparse.ArgumentParser(
        prog="tarnished",
        description="File state checkpoint tool - has your code tarnished?"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init command
    subparsers.add_parser("init", help="Initialize .tarnished/ directory")

    # save command
    save_parser = subparsers.add_parser("save", help="Save checkpoint for profile")
    save_parser.add_argument("profile", help="Profile name (e.g., lint:php)")
    save_parser.add_argument(
        "patterns",
        nargs="*",
        help="Glob patterns (optional if profile exists)"
    )

    # check command
    check_parser = subparsers.add_parser("check", help="Check if profile is tarnished")
    check_parser.add_argument("profile", help="Profile name to check")

    # status command
    subparsers.add_parser("status", help="Show status of all profiles (JSON)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    # Dispatch to handlers
    handlers = {
        "init": handle_init,
        "save": handle_save,
        "check": handle_check,
        "status": handle_status,
    }

    handler = handlers.get(args.command)
    if handler:
        return handler(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
