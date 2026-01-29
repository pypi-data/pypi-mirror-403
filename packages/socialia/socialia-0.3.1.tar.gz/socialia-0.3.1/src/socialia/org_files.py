#!/usr/bin/env python3
"""File management utilities for org mode drafts.

Handles automatic movement of files between directories:
- drafts/    -> Work in progress
- scheduled/ -> Ready, waiting for posting time
- posted/    -> Archive after posting
"""

import shutil
from pathlib import Path


def _find_target_dir(filepath: Path, target_name: str) -> Path | None:
    """Find sibling directory with given name.

    Looks for directories like:
    - Same parent level: drafts/ -> scheduled/ (siblings)
    - e.g., project/drafts/file.org -> project/scheduled/
    """
    parent = filepath.parent

    # Check sibling directory (same level as current dir)
    sibling = parent.parent / target_name
    if sibling.exists() and sibling.is_dir():
        return sibling

    # Check if parent IS the target (file already in target dir)
    if parent.name == target_name:
        return parent

    return None


def move_to_scheduled(filepath: Path) -> Path | None:
    """Move file from drafts/ to scheduled/ directory.

    Returns new path if moved, None if no scheduled/ directory found.
    """
    filepath = Path(filepath)
    scheduled_dir = _find_target_dir(filepath, "scheduled")
    if not scheduled_dir:
        return None

    # Don't move if already in scheduled
    if filepath.parent == scheduled_dir:
        return filepath

    new_path = scheduled_dir / filepath.name
    shutil.move(str(filepath), str(new_path))
    return new_path


def move_to_posted(filepath: Path) -> Path | None:
    """Move file from scheduled/ to posted/ directory.

    Returns new path if moved, None if no posted/ directory found.
    """
    filepath = Path(filepath)
    posted_dir = _find_target_dir(filepath, "posted")
    if not posted_dir:
        return None

    # Don't move if already in posted
    if filepath.parent == posted_dir:
        return filepath

    new_path = posted_dir / filepath.name
    shutil.move(str(filepath), str(new_path))
    return new_path


def get_file_stage(filepath: Path) -> str:
    """Get current stage of a file based on directory.

    Returns: 'drafts', 'scheduled', 'posted', or 'unknown'
    """
    filepath = Path(filepath)
    parent_name = filepath.parent.name

    if parent_name in ("drafts", "scheduled", "posted"):
        return parent_name
    return "unknown"


def ensure_project_dirs(base_path: Path) -> dict[str, Path]:
    """Ensure drafts/, scheduled/, posted/ directories exist.

    Args:
        base_path: Project base directory

    Returns:
        dict with 'drafts', 'scheduled', 'posted' paths
    """
    base_path = Path(base_path)
    dirs = {}

    for name in ("drafts", "scheduled", "posted"):
        dir_path = base_path / name
        dir_path.mkdir(parents=True, exist_ok=True)
        dirs[name] = dir_path

    return dirs
