"""Default configuration and constants for tarnished."""

from typing import Any

DEFAULT_DIR_NAME: str = ".tarnished"
DEFAULT_CONFIG_FILE: str = "config.json"
DEFAULT_STATE_FILE: str = "state.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "profiles": {}
}

DEFAULT_GITIGNORE: str = """# tarnished state file (local, not committed)
state.json
"""
