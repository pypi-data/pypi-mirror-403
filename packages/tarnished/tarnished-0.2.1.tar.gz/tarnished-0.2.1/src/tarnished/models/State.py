"""State dataclass for tarnished checkpoints."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class Checkpoint:
    """A saved checkpoint for a profile."""

    checksum: str
    saved_at: datetime


@dataclass
class State:
    """State tracking for profile checkpoints."""

    checkpoints: dict[str, Checkpoint] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: Path) -> State:
        """Load state from file, return empty state if not found."""
        if not path.exists():
            return cls()
        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> State:
        """Create state from dictionary."""
        checkpoints: dict[str, Checkpoint] = {}
        for name, cp_data in data.items():
            checkpoints[name] = Checkpoint(
                checksum=cp_data["checksum"],
                saved_at=datetime.fromisoformat(cp_data["saved_at"]),
            )
        return cls(checkpoints=checkpoints)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            name: {
                "checksum": checkpoint.checksum,
                "saved_at": checkpoint.saved_at.isoformat(),
            }
            for name, checkpoint in self.checkpoints.items()
        }

    def save(self, path: Path) -> None:
        """Save state to file atomically (write to temp, then rename)."""
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write to a temporary file in the same directory
        # Using same directory ensures atomic rename on same filesystem
        fd, tmp_path = tempfile.mkstemp(
            dir=path.parent,
            prefix=".state_",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
                f.write("\n")
            # Atomic rename
            os.replace(tmp_path, path)
        except Exception:
            # Clean up temp file on failure
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def get_checkpoint(self, name: str) -> Checkpoint | None:
        """Get a checkpoint by profile name, or None if not found."""
        return self.checkpoints.get(name)

    def set_checkpoint(self, name: str, checksum: str) -> Checkpoint:
        """Set or update a checkpoint for a profile. Returns the created checkpoint."""
        checkpoint = Checkpoint(
            checksum=checksum,
            saved_at=datetime.now(UTC),
        )
        self.checkpoints[name] = checkpoint
        return checkpoint
