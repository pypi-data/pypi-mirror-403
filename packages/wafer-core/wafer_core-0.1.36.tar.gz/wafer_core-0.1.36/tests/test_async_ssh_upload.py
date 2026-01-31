"""Regression tests for AsyncSSHClient file upload.

Tests the fix for trio.Path.rglob() API misuse that caused "Uploaded 0 files".
The bug was using `async for f in path.rglob("*")` instead of
`for f in await path.rglob("*")`.

These tests require a real SSH target to run. Skip if not available.

Run with: pytest tests/test_async_ssh_upload.py -v
"""

import os
import tempfile
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any

import pytest
import trio
import trio_asyncio

# Skip all tests if SSH target not configured
SSH_TARGET = os.environ.get("WAFER_TEST_SSH_TARGET", "chiraag@45.76.244.62:22")
SSH_KEY = os.environ.get("WAFER_TEST_SSH_KEY", "~/.ssh/id_ed25519")


def ssh_available() -> bool:
    """Check if SSH target is available."""
    key_path = Path(SSH_KEY).expanduser()
    return key_path.exists()


pytestmark = pytest.mark.skipif(
    not ssh_available(),
    reason=f"SSH key not found at {SSH_KEY}",
)


def run_with_trio_asyncio(async_fn: Callable[[], Coroutine[Any, Any, None]]) -> None:
    """Run an async function with trio_asyncio event loop."""

    async def wrapper() -> None:
        async with trio_asyncio.open_loop():
            await async_fn()

    trio.run(wrapper)


def test_upload_directory_finds_files():
    """Test that _upload_directory correctly finds all files.

    This is the regression test for the trio.Path.rglob() bug.
    Before the fix, this would return 0 files uploaded.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test files at root level
        (tmppath / "file1.py").write_text("# file 1\nprint('hello')\n")
        (tmppath / "file2.py").write_text("# file 2\nprint('world')\n")

        # Create __pycache__ (should be skipped)
        pycache = tmppath / "__pycache__"
        pycache.mkdir()
        (pycache / "file1.cpython-312.pyc").write_bytes(b"fake pyc")

        async def run_test() -> None:
            from wafer_core.async_ssh import AsyncSSHClient

            async with AsyncSSHClient(SSH_TARGET, SSH_KEY) as client:
                import time

                remote_dir = f"/tmp/wafer_test_upload_{int(time.time())}"

                try:
                    # Create remote directory
                    await client.exec(f"mkdir -p {remote_dir}")

                    # Upload the test directory
                    result = await client.upload_files(
                        str(tmppath),
                        remote_dir,
                        recursive=True,
                    )

                    # Verify upload succeeded
                    assert result.success, f"Upload failed: {result.error_message}"

                    # Verify files exist on remote (this is what really matters)
                    ls_result = await client.exec(f"find {remote_dir} -type f -name '*.py' | wc -l")
                    file_count = int(ls_result.stdout.strip())
                    assert file_count == 2, f"Expected 2 .py files on remote, found {file_count}"

                    # Verify __pycache__ was NOT uploaded
                    pycache_result = await client.exec(
                        f"find {remote_dir} -name '__pycache__' | wc -l"
                    )
                    pycache_count = int(pycache_result.stdout.strip())
                    assert pycache_count == 0, "__pycache__ should not be uploaded"

                finally:
                    # Cleanup
                    await client.exec(f"rm -rf {remote_dir}")

        run_with_trio_asyncio(run_test)


def test_upload_nested_directories():
    """Test uploading nested directories works without race conditions.

    This tests the fix for the parallel upload race condition where
    subdirectories weren't created before files were uploaded into them.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create nested directory structure
        (tmppath / "root.py").write_text("# root\n")

        subdir1 = tmppath / "subdir1"
        subdir1.mkdir()
        (subdir1 / "file1.py").write_text("# subdir1/file1\n")
        (subdir1 / "file2.py").write_text("# subdir1/file2\n")

        subdir2 = tmppath / "subdir2"
        subdir2.mkdir()
        (subdir2 / "file3.py").write_text("# subdir2/file3\n")

        # Deeply nested
        deep = tmppath / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "deep.py").write_text("# deep nested\n")

        async def run_test() -> None:
            from wafer_core.async_ssh import AsyncSSHClient

            async with AsyncSSHClient(SSH_TARGET, SSH_KEY) as client:
                import time

                remote_dir = f"/tmp/wafer_test_nested_{int(time.time())}"

                try:
                    await client.exec(f"mkdir -p {remote_dir}")

                    result = await client.upload_files(
                        str(tmppath),
                        remote_dir,
                        recursive=True,
                    )

                    # Should upload successfully
                    assert result.success, f"Upload failed: {result.error_message}"

                    # Verify directory structure on remote (this is what really matters)
                    ls_result = await client.exec(f"find {remote_dir} -type f -name '*.py'")
                    remote_files = [f for f in ls_result.stdout.strip().split("\n") if f]
                    assert len(remote_files) == 5, (
                        f"Expected 5 files on remote, found {len(remote_files)}"
                    )

                    # Verify deeply nested file exists
                    deep_check = await client.exec(
                        f"test -f {remote_dir}/a/b/c/deep.py && echo yes"
                    )
                    assert "yes" in deep_check.stdout, "Deeply nested file not uploaded"

                finally:
                    await client.exec(f"rm -rf {remote_dir}")

        run_with_trio_asyncio(run_test)


def test_upload_empty_directory():
    """Test uploading an empty directory succeeds (no files to transfer)."""
    with tempfile.TemporaryDirectory() as tmpdir:

        async def run_test() -> None:
            from wafer_core.async_ssh import AsyncSSHClient

            async with AsyncSSHClient(SSH_TARGET, SSH_KEY) as client:
                import time

                remote_dir = f"/tmp/wafer_test_empty_{int(time.time())}"

                try:
                    await client.exec(f"mkdir -p {remote_dir}")

                    result = await client.upload_files(
                        tmpdir,
                        remote_dir,
                        recursive=True,
                    )

                    # rsync should succeed even for empty directories
                    assert result.success

                    # Verify no files on remote (just the directory)
                    ls_result = await client.exec(f"find {remote_dir} -type f | wc -l")
                    file_count = int(ls_result.stdout.strip())
                    assert file_count == 0, f"Expected 0 files, found {file_count}"

                finally:
                    await client.exec(f"rm -rf {remote_dir}")

        run_with_trio_asyncio(run_test)


def test_upload_single_file():
    """Test uploading a single file (not directory)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("# test file\n")
        local_path = f.name

    try:

        async def run_test() -> None:
            from wafer_core.async_ssh import AsyncSSHClient

            async with AsyncSSHClient(SSH_TARGET, SSH_KEY) as client:
                import time

                remote_path = f"/tmp/wafer_test_single_{int(time.time())}.py"

                try:
                    result = await client.upload_files(
                        local_path,
                        remote_path,
                        recursive=False,
                    )

                    assert result.success
                    assert result.files_copied == 1

                    # Verify content
                    cat_result = await client.exec(f"cat {remote_path}")
                    assert "# test file" in cat_result.stdout

                finally:
                    await client.exec(f"rm -f {remote_path}")

        run_with_trio_asyncio(run_test)
    finally:
        os.unlink(local_path)
