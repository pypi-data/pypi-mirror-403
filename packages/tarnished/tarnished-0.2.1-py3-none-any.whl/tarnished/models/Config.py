"""Configuration dataclass for tarnished profiles."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Profile:
    """A profile with glob patterns."""

    patterns: list[str] = field(default_factory=list)


@dataclass
class Config:
    """Configuration for tarnished profiles."""

    profiles: dict[str, Profile] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: Path) -> Config:
        """Load config from file, return empty config if not found."""
        if not path.exists():
            return cls()
        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create config from dictionary."""
        profiles: dict[str, Profile] = {}
        for name, profile_data in data.get("profiles", {}).items():
            profiles[name] = Profile(patterns=profile_data.get("patterns", []))
        return cls(profiles=profiles)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "profiles": {
                name: {"patterns": profile.patterns}
                for name, profile in self.profiles.items()
            }
        }

    def save(self, path: Path) -> None:
        """Save config to file with pretty printing."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
            f.write("\n")

    def get_profile(self, name: str) -> Profile | None:
        """Get a profile by name, or None if not found."""
        return self.profiles.get(name)

    def set_profile(self, name: str, profile: Profile) -> None:
        """Set or update a profile by name."""
        self.profiles[name] = profile
