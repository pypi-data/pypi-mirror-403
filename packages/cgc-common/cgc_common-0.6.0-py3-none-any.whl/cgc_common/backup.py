"""Git repository backup utilities.

Provides non-destructive backup functionality using git clone --mirror.
Backups preserve the complete repository history and can be restored.

Usage:
    from cgc_common import create_git_mirror_backup, list_backups

    # Create a backup
    success, message, backup_path = create_git_mirror_backup(
        repo_path=Path("/path/to/repo"),
        archive_root=Path("/path/to/backups"),
    )

    # List existing backups
    backups = list_backups(
        archive_root=Path("/path/to/backups"),
        project_name="my-project",
    )

Backup Structure:
    archive_root/
    ├── project-a/
    │   ├── 2025-01-07_14-30-00.git/
    │   └── 2025-01-07_16-45-22.git/
    └── project-b/
        └── 2025-01-06_10-00-00.git/
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Timestamp format for backup directories
BACKUP_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"


@dataclass
class BackupInfo:
    """Information about a backup."""

    path: Path
    project_name: str
    timestamp: datetime
    size_bytes: int

    @property
    def size_human(self) -> str:
        """Human-readable size."""
        size = self.size_bytes
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def timestamp_str(self) -> str:
        """Formatted timestamp string."""
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")


def _get_dir_size(path: Path) -> int:
    """Calculate total size of directory in bytes."""
    total = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
    except (OSError, PermissionError):
        pass
    return total


def _is_git_repo(path: Path) -> bool:
    """Check if path is a git repository."""
    git_dir = path / ".git"
    return git_dir.exists() and git_dir.is_dir()


def create_git_mirror_backup(
    repo_path: Path | str,
    archive_root: Path | str,
    project_name: str | None = None,
) -> tuple[bool, str, Path | None]:
    """
    Create a git mirror backup of a repository.

    Uses `git clone --mirror` to create a complete backup including
    all branches, tags, and history. The original repository is
    preserved (non-destructive).

    Args:
        repo_path: Path to the git repository to backup
        archive_root: Base directory for backups
        project_name: Optional project name (defaults to repo folder name)

    Returns:
        Tuple of (success, message, backup_path)
        - success: True if backup was created
        - message: Status message (success or error details)
        - backup_path: Path to backup directory, or None on failure

    Example:
        success, msg, path = create_git_mirror_backup(
            Path("~/projects/my-app"),
            Path("~/backups"),
        )
        if success:
            print(f"Backup created at: {path}")
    """
    repo_path = Path(repo_path).expanduser().resolve()
    archive_root = Path(archive_root).expanduser().resolve()

    # Validate source
    if not repo_path.exists():
        return False, f"Repository does not exist: {repo_path}", None

    if not _is_git_repo(repo_path):
        return False, f"Not a git repository: {repo_path}", None

    # Determine project name
    name = project_name or repo_path.name

    # Create timestamped backup directory
    timestamp = datetime.now().strftime(BACKUP_TIMESTAMP_FORMAT)
    backup_dir = archive_root / name
    backup_path = backup_dir / f"{timestamp}.git"

    # Check if backup already exists (same second - unlikely but possible)
    if backup_path.exists():
        return False, f"Backup already exists: {backup_path}", None

    try:
        # Create parent directories
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Run git clone --mirror
        result = subprocess.run(
            ["git", "clone", "--mirror", str(repo_path), str(backup_path)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
        )

        if result.returncode != 0:
            # Clean up failed backup
            if backup_path.exists():
                shutil.rmtree(backup_path)
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            return False, f"git clone --mirror failed: {error_msg}", None

        # Calculate size
        size = _get_dir_size(backup_path)
        size_str = BackupInfo(
            path=backup_path,
            project_name=name,
            timestamp=datetime.now(),
            size_bytes=size,
        ).size_human

        logger.info(f"Backup created: {backup_path} ({size_str})")
        return True, f"Backup created: {backup_path.name} ({size_str})", backup_path

    except subprocess.TimeoutExpired:
        if backup_path.exists():
            shutil.rmtree(backup_path)
        return False, "Backup timed out after 5 minutes", None

    except PermissionError as e:
        return False, f"Permission denied: {e}", None

    except Exception as e:
        logger.exception(f"Backup failed: {e}")
        if backup_path.exists():
            shutil.rmtree(backup_path)
        return False, f"Backup failed: {e}", None


def list_backups(
    archive_root: Path | str,
    project_name: str | None = None,
) -> list[BackupInfo]:
    """
    List existing backups.

    Args:
        archive_root: Base directory for backups
        project_name: Filter by project name (None = all projects)

    Returns:
        List of BackupInfo objects, sorted by timestamp (newest first)

    Example:
        backups = list_backups(Path("~/backups"), "my-app")
        for b in backups:
            print(f"{b.timestamp_str}: {b.size_human}")
    """
    archive_root = Path(archive_root).expanduser().resolve()
    backups: list[BackupInfo] = []

    if not archive_root.exists():
        return backups

    # Get project directories to scan
    if project_name:
        project_dirs = [archive_root / project_name]
    else:
        project_dirs = [d for d in archive_root.iterdir() if d.is_dir()]

    for project_dir in project_dirs:
        if not project_dir.exists():
            continue

        proj_name = project_dir.name

        # Find all .git backup directories
        for backup_dir in project_dir.iterdir():
            if not backup_dir.is_dir():
                continue
            if not backup_dir.name.endswith(".git"):
                continue

            # Parse timestamp from directory name
            timestamp_str = backup_dir.name[:-4]  # Remove .git suffix
            try:
                timestamp = datetime.strptime(timestamp_str, BACKUP_TIMESTAMP_FORMAT)
            except ValueError:
                # Invalid timestamp format, skip
                continue

            backups.append(
                BackupInfo(
                    path=backup_dir,
                    project_name=proj_name,
                    timestamp=timestamp,
                    size_bytes=_get_dir_size(backup_dir),
                )
            )

    # Sort by timestamp, newest first
    backups.sort(key=lambda b: b.timestamp, reverse=True)
    return backups


def get_latest_backup(
    archive_root: Path | str,
    project_name: str,
) -> BackupInfo | None:
    """
    Get the most recent backup for a project.

    Args:
        archive_root: Base directory for backups
        project_name: Project name

    Returns:
        BackupInfo for latest backup, or None if no backups exist
    """
    backups = list_backups(archive_root, project_name)
    return backups[0] if backups else None


def delete_old_backups(
    archive_root: Path | str,
    project_name: str,
    keep_count: int = 5,
) -> tuple[int, list[str]]:
    """
    Delete old backups, keeping only the most recent ones.

    Args:
        archive_root: Base directory for backups
        project_name: Project name
        keep_count: Number of recent backups to keep (default: 5)

    Returns:
        Tuple of (deleted_count, deleted_paths)

    Example:
        count, paths = delete_old_backups(Path("~/backups"), "my-app", keep_count=3)
        print(f"Deleted {count} old backups")
    """
    if keep_count < 1:
        raise ValueError("keep_count must be at least 1")

    backups = list_backups(archive_root, project_name)
    to_delete = backups[keep_count:]  # Already sorted newest first

    deleted_paths: list[str] = []
    for backup in to_delete:
        try:
            shutil.rmtree(backup.path)
            deleted_paths.append(str(backup.path))
            logger.info(f"Deleted old backup: {backup.path}")
        except Exception as e:
            logger.warning(f"Failed to delete backup {backup.path}: {e}")

    return len(deleted_paths), deleted_paths


def restore_from_backup(
    backup_path: Path | str,
    target_path: Path | str,
) -> tuple[bool, str]:
    """
    Restore a repository from a mirror backup.

    Uses `git clone` to restore from the mirror backup.

    Args:
        backup_path: Path to the .git mirror backup
        target_path: Destination path for restored repository

    Returns:
        Tuple of (success, message)

    Example:
        success, msg = restore_from_backup(
            Path("~/backups/my-app/2025-01-07_14-30-00.git"),
            Path("~/restored/my-app"),
        )
    """
    backup_path = Path(backup_path).expanduser().resolve()
    target_path = Path(target_path).expanduser().resolve()

    if not backup_path.exists():
        return False, f"Backup does not exist: {backup_path}"

    if target_path.exists():
        return False, f"Target already exists: {target_path}"

    try:
        # Create parent directory
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Clone from mirror
        result = subprocess.run(
            ["git", "clone", str(backup_path), str(target_path)],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            if target_path.exists():
                shutil.rmtree(target_path)
            error_msg = result.stderr.strip() or "Unknown error"
            return False, f"Restore failed: {error_msg}"

        logger.info(f"Restored from backup: {backup_path} -> {target_path}")
        return True, f"Restored to: {target_path}"

    except subprocess.TimeoutExpired:
        if target_path.exists():
            shutil.rmtree(target_path)
        return False, "Restore timed out"

    except Exception as e:
        logger.exception(f"Restore failed: {e}")
        if target_path.exists():
            shutil.rmtree(target_path)
        return False, f"Restore failed: {e}"
