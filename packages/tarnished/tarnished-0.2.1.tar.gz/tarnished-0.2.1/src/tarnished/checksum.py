"""Checksum computation logic for tarnished."""

import hashlib
from pathlib import Path

# Consistent checksum for empty file list
EMPTY_CHECKSUM = hashlib.md5(b"").hexdigest()


def expand_patterns(patterns: list[str], base_path: Path) -> list[Path]:
    """Expand glob patterns to a sorted list of files.

    Args:
        patterns: List of glob patterns to expand
        base_path: Base directory for glob expansion

    Returns:
        Sorted list of unique file paths matching the patterns.
        Symlinks are followed (resolved to their targets).
    """
    files: set[Path] = set()

    for pattern in patterns:
        for path in base_path.glob(pattern):
            # Only include files, not directories
            if path.is_file():
                # Follow symlinks by resolving the path
                resolved = path.resolve()
                files.add(resolved)

    # Sort for deterministic order
    return sorted(files)


def compute_checksum(patterns: list[str], base_path: Path) -> str:
    """Compute checksum from file metadata matching patterns.

    Uses file path (relative to base_path), size, and modification time
    to compute a deterministic checksum. This is faster than hashing
    file contents.

    Args:
        patterns: List of glob patterns to match files
        base_path: Base directory for pattern matching

    Returns:
        MD5 hex digest of combined file metadata, or EMPTY_CHECKSUM
        if no files match.
    """
    base_path = base_path.resolve()
    files = expand_patterns(patterns, base_path)

    if not files:
        return EMPTY_CHECKSUM

    # Build metadata string
    metadata_parts: list[str] = []

    for file_path in files:
        stat = file_path.stat()
        # Use relative path for portability, stat for change detection
        try:
            relative_path = file_path.relative_to(base_path)
        except ValueError:
            # File is outside base_path (e.g., resolved symlink)
            # Use absolute path as fallback
            relative_path = file_path

        # Include path, size, and mtime in metadata
        # Using repr() for mtime to preserve full precision
        metadata_parts.append(f"{relative_path} {stat.st_size} {stat.st_mtime!r}")

    # Hash the combined metadata
    combined = "\n".join(metadata_parts)
    return hashlib.md5(combined.encode()).hexdigest()
