"""Artifact-related functions for capture tool."""

import logging
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path

import trio

from wafer_core.tools.capture_tool.dtypes import (
    ArtifactDiff,
    DirectorySnapshot,
    FileInfo,
)

logger = logging.getLogger(__name__)


def _matches_denylist(path: Path, denylist: list[str]) -> bool:
    """Check if path matches any denylist pattern."""
    path_str = str(path)
    for pattern in denylist:
        if fnmatch(path_str, pattern):
            return True
        if "**/" in pattern:
            simple_pattern = pattern.replace("**/", "")
            if fnmatch(path_str, simple_pattern) or fnmatch(path.name, simple_pattern):
                return True
            for parent in path.parents:
                if fnmatch(str(parent), pattern) or fnmatch(parent.name, simple_pattern):
                    return True
    return False


async def snapshot_directory(
    root: Path | str, denylist: list[str] | None = None
) -> DirectorySnapshot:
    """Create a snapshot of directory state."""
    logger.debug(f"Creating directory snapshot: {root}")
    root = Path(root)
    denylist = denylist or []

    files: dict[Path, FileInfo] = {}

    def _scan() -> dict[Path, FileInfo]:
        """Scan directory tree (runs in thread)."""
        result: dict[Path, FileInfo] = {}
        for item in root.rglob("*"):
            if not item.is_file():
                continue

            try:
                rel_path = item.relative_to(root)
            except ValueError:
                continue

            if _matches_denylist(rel_path, denylist):
                logger.debug(f"Skipping denylisted file: {rel_path}")
                continue

            try:
                stat = item.stat()
                file_info = FileInfo(
                    path=rel_path,
                    size=stat.st_size,
                    mtime=stat.st_mtime,
                    checksum=None,
                )
                result[rel_path] = file_info
            except OSError as e:
                logger.warning(f"Failed to stat file {rel_path}: {e}")
                continue

        return result

    files = await trio.to_thread.run_sync(_scan)

    logger.info(f"Snapshot complete: {len(files)} files")

    return DirectorySnapshot(
        files=files, timestamp=datetime.now(timezone.utc), root=root
    )


def diff_snapshots(before: DirectorySnapshot, after: DirectorySnapshot) -> ArtifactDiff:
    """Compute difference between two directory snapshots."""
    logger.debug("Computing snapshot diff")

    before_paths = set(before.files.keys())
    after_paths = set(after.files.keys())

    new_files = sorted(after_paths - before_paths)
    deleted_files = sorted(before_paths - after_paths)

    modified_files: list[Path] = []
    for path in sorted(before_paths & after_paths):
        before_info = before.files[path]
        after_info = after.files[path]

        if before_info.size != after_info.size or before_info.mtime != after_info.mtime:
            modified_files.append(path)

    logger.info(
        f"Diff: {len(new_files)} new, {len(modified_files)} modified, {len(deleted_files)} deleted"
    )

    return ArtifactDiff(
        new_files=new_files, modified_files=modified_files, deleted_files=deleted_files
    )


async def collect_file_contents(
    root: Path, paths: list[Path], compute_checksums: bool = True
) -> dict[Path, str]:
    """Collect contents of multiple files."""
    logger.debug(f"Collecting {len(paths)} files")

    async def read_file(path: Path) -> tuple[Path, str]:
        """Read a single file."""
        full_path = root / path

        def _read() -> str:
            with open(full_path, encoding="utf-8", errors="replace") as f:
                return f.read()

        content = await trio.to_thread.run_sync(_read)
        return path, content

    results: dict[Path, str] = {}
    async with trio.open_nursery() as nursery:
        result_list: list[tuple[Path, str]] = []

        async def _collect() -> None:
            for path in paths:
                try:
                    result = await read_file(path)
                    result_list.append(result)
                except Exception as e:
                    logger.warning(f"Failed to read {path}: {e}")

        nursery.start_soon(_collect)

    results = dict(result_list)
    logger.info(f"Collected {len(results)} files")
    return results
