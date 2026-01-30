"""Configuration for file output permissions."""

import fnmatch
from pathlib import Path

import yaml

_config_cache: dict | None = None


def _get_config_path() -> Path:
    """Get the path to the configuration file."""
    return Path.home() / ".config" / "mcp-svg-animator" / "config.yaml"


def load_config() -> dict:
    """Load configuration from file.

    Returns:
        Configuration dictionary with file_output.allowed list.
        Returns empty allowed list if config file doesn't exist.
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    config_path = _get_config_path()
    if not config_path.exists():
        _config_cache = {"file_output": {"allowed": []}}
        return _config_cache

    content = config_path.read_text()
    loaded = yaml.safe_load(content)
    if not isinstance(loaded, dict):
        loaded = {}

    # Ensure structure exists
    if "file_output" not in loaded:
        loaded["file_output"] = {"allowed": []}
    if "allowed" not in loaded["file_output"]:
        loaded["file_output"]["allowed"] = []

    _config_cache = loaded
    return _config_cache


def clear_config_cache() -> None:
    """Clear the cached configuration. Useful for testing."""
    global _config_cache
    _config_cache = None


def is_path_allowed(file_path: str, file_type: str) -> bool:
    """Check if writing to a path is allowed for a given file type.

    Args:
        file_path: The absolute path to check.
        file_type: The file type (svg, png, webm).

    Returns:
        True if writing is allowed, False otherwise.
    """
    config = load_config()
    allowed_paths = config["file_output"]["allowed"]

    if not allowed_paths:
        return False

    file_path_obj = Path(file_path).resolve()

    for entry in allowed_paths:
        allowed_pattern = entry["path"]
        allowed_types = entry.get("types", [])

        if file_type not in allowed_types:
            continue

        # Expand ~ to home directory
        expanded_pattern = str(Path(allowed_pattern).expanduser())

        if _path_matches_pattern(file_path_obj, expanded_pattern):
            return True

    return False


def _path_matches_pattern(file_path: Path, pattern: str) -> bool:
    """Check if a file path matches an allowed pattern.

    The pattern can be:
    - An exact directory path (file can be in dir or any subdirectory)
    - A glob pattern with * or **

    Args:
        file_path: The resolved file path to check.
        pattern: The pattern to match against.

    Returns:
        True if the path matches the pattern.
    """
    # Get the directory of the file
    file_dir = file_path.parent

    # Check if pattern contains glob characters
    if "*" in pattern:
        return _glob_match(file_dir, pattern)

    # Exact directory match - check if file is under this directory
    pattern_path = Path(pattern).resolve()
    try:
        file_dir.relative_to(pattern_path)
        return True
    except ValueError:
        return False


def _glob_match(file_dir: Path, pattern: str) -> bool:
    """Match a directory against a glob pattern.

    Supports:
    - * for single directory level
    - ** for any number of directory levels

    Args:
        file_dir: The directory containing the file.
        pattern: The glob pattern.

    Returns:
        True if the directory matches the pattern.
    """
    # Convert pattern to parts
    pattern_parts = Path(pattern).parts
    dir_parts = file_dir.parts

    return _match_parts(dir_parts, pattern_parts, 0, 0)


def _match_parts(
    dir_parts: tuple, pattern_parts: tuple, dir_idx: int, pattern_idx: int
) -> bool:
    """Recursively match directory parts against pattern parts.

    Args:
        dir_parts: The directory path parts.
        pattern_parts: The pattern parts.
        dir_idx: Current index in dir_parts.
        pattern_idx: Current index in pattern_parts.

    Returns:
        True if the parts match.
    """
    # If we've consumed all pattern parts, the directory must be at or past the pattern
    if pattern_idx >= len(pattern_parts):
        return True

    # If we've run out of directory parts but still have pattern parts
    if dir_idx >= len(dir_parts):
        # Only match if remaining pattern parts are all **
        return all(p == "**" for p in pattern_parts[pattern_idx:])

    pattern_part = pattern_parts[pattern_idx]
    dir_part = dir_parts[dir_idx]

    if pattern_part == "**":
        # ** can match zero or more directory levels
        # Try matching zero levels (skip **)
        if _match_parts(dir_parts, pattern_parts, dir_idx, pattern_idx + 1):
            return True
        # Try matching one level and continue with **
        if _match_parts(dir_parts, pattern_parts, dir_idx + 1, pattern_idx):
            return True
        return False

    elif "*" in pattern_part or "?" in pattern_part:
        # Single-level glob match using fnmatch
        if fnmatch.fnmatch(dir_part, pattern_part):
            return _match_parts(dir_parts, pattern_parts, dir_idx + 1, pattern_idx + 1)
        return False

    else:
        # Exact match required
        if dir_part == pattern_part:
            return _match_parts(dir_parts, pattern_parts, dir_idx + 1, pattern_idx + 1)
        return False
