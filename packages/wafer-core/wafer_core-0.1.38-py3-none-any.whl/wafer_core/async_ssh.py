"""Async SSH client for remote GPU execution.

Uses asyncssh with trio-asyncio bridge for compatibility with trio.
"""

import logging
import os
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

import asyncssh
import trio
import trio_asyncio

logger = logging.getLogger(__name__)


def _truncate(s: str, max_len: int = 500) -> str:
    """Truncate string for logging, preserving start and end."""
    if len(s) <= max_len:
        return s
    half = (max_len - 5) // 2
    return f"{s[:half]}[...]{s[-half:]}"


def _trio_wrap(coro_func):
    """Wrap asyncio coroutine for trio-asyncio."""
    return trio_asyncio.aio_as_trio(coro_func)


class AsyncSSHError(Exception):
    """Base exception for async SSH operations."""

    pass


class ConnectionError(AsyncSSHError):
    """SSH connection failed."""

    pass


class TransferError(AsyncSSHError):
    """File transfer failed."""

    pass


@dataclass(frozen=True)
class ExecResult:
    """Result of command execution."""

    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float = 0.0  # Execution time in milliseconds
    command: str = ""  # The command that was executed (for debugging)


@dataclass(frozen=True)
class CopyResult:
    """Result of file transfer operation.

    Includes debug_info for wide event logging - captures command details
    and raw output for debugging upload failures.
    """

    success: bool
    files_copied: int
    total_bytes: int
    duration_seconds: float
    error_message: str | None = None
    debug_info: dict | None = None  # rsync_cmd, stdout, stderr for debugging


class AsyncSSHClient:
    """Async SSH client for remote GPU execution.

    Uses asyncssh for true async I/O, bridged to trio via trio-asyncio.

    Example:
        async with AsyncSSHClient("user@host:22", "~/.ssh/id_ed25519") as client:
            result = await client.exec("nvidia-smi")
            print(result.stdout)

            async for line in client.exec_stream("python train.py"):
                print(line)
    """

    def __init__(
        self,
        ssh_target: str,
        ssh_key: str,
        timeout: int = 30,
    ) -> None:
        """Initialize async SSH client.

        Args:
            ssh_target: SSH target as "user@host:port" or "user@host"
            ssh_key: Path to SSH private key
            timeout: Connection timeout in seconds
        """
        # Parse SSH target
        if "@" not in ssh_target:
            raise ValueError(f"Invalid ssh_target format: {ssh_target}. Expected user@host:port")

        user_host, _, port_str = ssh_target.partition(":")
        user, _, host = user_host.partition("@")

        self.user = user
        self.host = host
        self.port = int(port_str) if port_str else 22
        self.ssh_key = os.path.expanduser(ssh_key)
        self.timeout = timeout

        self._conn: asyncssh.SSHClientConnection | None = None

    async def _establish_connection(self) -> asyncssh.SSHClientConnection:
        """Establish SSH connection with retry logic."""
        max_attempts = 3
        delay = 2
        backoff = 2

        start_time = time.perf_counter()

        for attempt in range(max_attempts):
            attempt_start = time.perf_counter()
            try:
                conn = await _trio_wrap(asyncssh.connect)(
                    host=self.host,
                    port=self.port,
                    username=self.user,
                    client_keys=[self.ssh_key],
                    connect_timeout=self.timeout,
                    keepalive_interval=30,
                    known_hosts=None,
                )
                total_duration_ms = (time.perf_counter() - start_time) * 1000

                # Wide event for successful connection
                logger.info(
                    "ssh_connect",
                    extra={
                        "event": "ssh_connect",
                        "host": self.host,
                        "port": self.port,
                        "user": self.user,
                        "success": True,
                        "attempts": attempt + 1,
                        "duration_ms": round(total_duration_ms, 2),
                    },
                )
                return conn

            except Exception as e:
                attempt_duration_ms = (time.perf_counter() - attempt_start) * 1000

                if attempt < max_attempts - 1:
                    wait_time = delay * (backoff**attempt)
                    logger.info(
                        "ssh_connect_retry",
                        extra={
                            "event": "ssh_connect_retry",
                            "host": self.host,
                            "port": self.port,
                            "user": self.user,
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "attempt_duration_ms": round(attempt_duration_ms, 2),
                            "retry_delay_s": wait_time,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                    )
                    await trio.sleep(wait_time)
                else:
                    total_duration_ms = (time.perf_counter() - start_time) * 1000
                    # Wide event for failed connection
                    logger.error(
                        "ssh_connect_failed",
                        extra={
                            "event": "ssh_connect_failed",
                            "host": self.host,
                            "port": self.port,
                            "user": self.user,
                            "success": False,
                            "attempts": max_attempts,
                            "duration_ms": round(total_duration_ms, 2),
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                    )
                    raise ConnectionError(
                        f"Failed to connect to {self.user}@{self.host}:{self.port} "
                        f"after {max_attempts} attempts: {e}"
                    ) from e

        raise ConnectionError(f"Failed to connect to {self.user}@{self.host}:{self.port}")

    async def _get_connection(self) -> asyncssh.SSHClientConnection:
        """Get or create SSH connection."""
        if self._conn is None:
            self._conn = await self._establish_connection()
            return self._conn

        # Check if connection is still alive
        if self._conn._transport.is_closing():
            logger.debug("SSH connection inactive, reconnecting...")
            self._conn = await self._establish_connection()

        return self._conn

    async def exec(
        self,
        command: str,
        working_dir: str | None = None,
    ) -> ExecResult:
        """Execute command on remote.

        Args:
            command: Command to execute
            working_dir: Optional working directory

        Returns:
            ExecResult with stdout, stderr, exit_code, duration_ms, command
        """
        conn = await self._get_connection()

        full_command = command
        if working_dir:
            full_command = f"cd {working_dir} && {command}"

        start_time = time.perf_counter()
        result = await _trio_wrap(conn.run)(full_command, check=False)
        duration_ms = (time.perf_counter() - start_time) * 1000

        stdout = result.stdout or ""
        stderr = result.stderr or ""
        exit_code = result.exit_status or 0

        # Wide event for SSH command execution
        logger.info(
            "ssh_exec",
            extra={
                "event": "ssh_exec",
                "host": self.host,
                "port": self.port,
                "user": self.user,
                "command": _truncate(full_command, 200),
                "working_dir": working_dir,
                "exit_code": exit_code,
                "duration_ms": round(duration_ms, 2),
                "stdout_len": len(stdout),
                "stderr_len": len(stderr),
                "stdout_preview": _truncate(stdout, 200) if stdout else None,
                "stderr_preview": _truncate(stderr, 200) if stderr else None,
            },
        )

        return ExecResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            duration_ms=duration_ms,
            command=full_command,
        )

    async def exec_stream(
        self,
        command: str,
        working_dir: str | None = None,
    ) -> AsyncIterator[str]:
        """Execute command and stream output line-by-line.

        Args:
            command: Command to execute
            working_dir: Optional working directory

        Yields:
            Lines of output as they're produced
        """
        conn = await self._get_connection()

        full_command = command
        if working_dir:
            full_command = f"cd {working_dir} && {command}"

        # Wide event for stream start
        logger.info(
            "ssh_exec_stream_start",
            extra={
                "event": "ssh_exec_stream_start",
                "host": self.host,
                "port": self.port,
                "user": self.user,
                "command": _truncate(full_command, 200),
                "working_dir": working_dir,
            },
        )

        start_time = time.perf_counter()
        lines_yielded = 0

        # Use PTY to combine stdout/stderr
        process = await _trio_wrap(conn.create_process)(full_command, term_type="ansi")
        try:
            while True:
                try:
                    line = await _trio_wrap(process.stdout.readline)()
                    if not line:
                        break
                    lines_yielded += 1
                    yield line.rstrip("\r\n")
                except EOFError:
                    break
        finally:
            process.close()
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Wide event for stream completion
            logger.info(
                "ssh_exec_stream_end",
                extra={
                    "event": "ssh_exec_stream_end",
                    "host": self.host,
                    "port": self.port,
                    "user": self.user,
                    "command": _truncate(full_command, 200),
                    "duration_ms": round(duration_ms, 2),
                    "lines_yielded": lines_yielded,
                },
            )

    async def expand_path(self, path: str) -> str:
        """Expand ~ and env vars in path on remote."""
        result = await self.exec(f"echo {path}")
        return result.stdout.strip()

    async def upload_files(
        self,
        local_path: str,
        remote_path: str,
        recursive: bool = False,
        exclude: list[str] | None = None,
        use_sftp: bool = False,
    ) -> CopyResult:
        """Upload files from local to remote.

        By default uses rsync for efficient delta transfers on directories.
        Set use_sftp=True to use SFTP through the existing asyncssh connection,
        which avoids spawning a new SSH subprocess (useful when rsync times out
        due to rate limiting or connection issues).

        Args:
            local_path: Local file or directory path
            remote_path: Remote destination path
            recursive: Upload directories recursively
            exclude: Patterns to exclude (default: __pycache__, *.pyc, .git, .venv, etc.)
            use_sftp: If True, use SFTP instead of rsync for directories.
                      SFTP is slower but uses the existing SSH connection.

        Returns:
            CopyResult with transfer statistics
        """
        import time

        start_time = time.time()

        local_path_obj = trio.Path(local_path)
        if not await local_path_obj.exists():
            raise TransferError(f"Local path not found: {local_path}")

        is_directory = await local_path_obj.is_dir()
        if is_directory and not recursive:
            raise TransferError(f"{local_path} is a directory. Use recursive=True")

        try:
            if is_directory:
                if use_sftp:
                    # Use SFTP through existing connection (no new SSH subprocess)
                    return await self._sftp_upload_directory(
                        local_path, remote_path, exclude, start_time
                    )
                else:
                    # Use rsync (faster for large dirs, but spawns new SSH)
                    return await self._rsync_upload(local_path, remote_path, exclude, start_time)
            else:
                # For single files, always use SFTP (simpler)
                return await self._sftp_upload_file(local_path, remote_path, start_time)

        except Exception as e:
            duration = time.time() - start_time
            return CopyResult(
                success=False,
                files_copied=0,
                total_bytes=0,
                duration_seconds=duration,
                error_message=str(e),
            )

    async def _rsync_upload(
        self,
        local_path: str,
        remote_path: str,
        exclude: list[str] | None,
        start_time: float,
    ) -> CopyResult:
        """Upload directory using rsync over SSH."""
        import time

        # Default exclusions - include .venv to avoid uploading local virtualenvs
        if exclude is None:
            exclude = [
                "__pycache__",
                "*.pyc",
                ".git",
                ".ruff_cache",
                ".pytest_cache",
                ".venv",
                "*.egg-info",
                "uv.lock",
            ]

        # Build rsync command with SSH ControlMaster for connection reuse
        # ControlMaster allows rsync to piggyback on existing SSH connections,
        # avoiding connection timeouts when the remote has rate limiting
        control_path = "/tmp/ssh-wafer-%r@%h:%p"
        ssh_opts = (
            f"ssh -i {self.ssh_key} -p {self.port} "
            f"-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
            f"-o ControlMaster=auto -o ControlPath={control_path} -o ControlPersist=60 "
            f"-o ConnectTimeout=30 -o ServerAliveInterval=15 -o ServerAliveCountMax=3"
        )
        rsync_args = [
            "rsync",
            "-avz",  # archive mode + verbose + compression
            "--delete",  # remove files on remote that don't exist locally
            "--timeout=120",  # rsync-level timeout
            "-e",
            ssh_opts,
        ]

        # Add exclusions
        for pattern in exclude:
            rsync_args.extend(["--exclude", pattern])

        # Add source (trailing slash = contents of directory)
        rsync_args.append(f"{local_path}/")
        # Add destination
        rsync_args.append(f"{self.user}@{self.host}:{remote_path}/")

        # Build debug info for wide event logging
        debug_info = {
            "rsync_cmd": " ".join(rsync_args),
            "local_path": local_path,
            "remote_path": remote_path,
            "remote_target": f"{self.user}@{self.host}:{self.port}",
            "exclude_patterns": exclude,
        }

        try:
            result = await trio.run_process(
                rsync_args,
                capture_stdout=True,
                capture_stderr=True,
                check=False,  # Don't raise on non-zero exit, we handle it below
            )

            duration = time.time() - start_time
            stdout = result.stdout.decode() if result.stdout else ""
            stderr = result.stderr.decode() if result.stderr else ""

            # Add raw output to debug info
            debug_info["stdout"] = stdout
            debug_info["stderr"] = stderr
            debug_info["returncode"] = result.returncode

            if result.returncode != 0:
                return CopyResult(
                    success=False,
                    files_copied=0,
                    total_bytes=0,
                    duration_seconds=duration,
                    error_message=f"rsync failed (exit {result.returncode}): {stderr}",
                    debug_info=debug_info,
                )

            # Parse rsync output to count files
            # Count non-empty lines that look like file transfers
            lines = [
                line
                for line in stdout.strip().split("\n")
                if line and not line.startswith((" ", "sent", "total", "receiving", "building"))
            ]
            files_copied = len(lines)

            return CopyResult(
                success=True,
                files_copied=files_copied,
                total_bytes=0,  # rsync doesn't easily report this
                duration_seconds=duration,
                debug_info=debug_info,
            )

        except FileNotFoundError as e:
            raise TransferError("rsync not found. Install rsync to use directory upload.") from e

    async def _sftp_upload_file(
        self,
        local_path: str,
        remote_path: str,
        start_time: float,
    ) -> CopyResult:
        """Upload single file using SFTP."""
        import time

        conn = await self._get_connection()
        sftp = await _trio_wrap(conn.start_sftp_client)()

        try:
            # Ensure remote directory exists
            remote_dir = os.path.dirname(remote_path)
            if remote_dir and remote_dir != ".":
                await self._create_remote_dir(sftp, remote_dir)

            file_stat = await trio.Path(local_path).stat()
            await _trio_wrap(sftp.put)(local_path, remote_path)

            duration = time.time() - start_time
            return CopyResult(
                success=True,
                files_copied=1,
                total_bytes=file_stat.st_size,
                duration_seconds=duration,
            )
        finally:
            sftp.exit()

    async def _sftp_upload_directory(
        self,
        local_path: str,
        remote_path: str,
        exclude: list[str] | None,
        start_time: float,
    ) -> CopyResult:
        """Upload directory recursively using SFTP through existing asyncssh connection.

        This avoids spawning a new SSH subprocess (like rsync does), which can fail
        when the remote has rate limiting or connection restrictions.
        """
        import fnmatch
        import time

        # Default exclusions
        if exclude is None:
            exclude = [
                "__pycache__",
                "*.pyc",
                ".git",
                ".ruff_cache",
                ".pytest_cache",
                ".venv",
                "*.egg-info",
                "uv.lock",
            ]

        conn = await self._get_connection()
        sftp = await _trio_wrap(conn.start_sftp_client)()

        files_copied = 0
        total_bytes = 0
        errors: list[str] = []

        def should_exclude(path: trio.Path | Path, patterns: list[str]) -> bool:
            """Check if path matches any exclusion pattern."""
            name = path.name
            for pattern in patterns:
                if fnmatch.fnmatch(name, pattern):
                    return True
                # Also check full relative path for patterns like "dir/file"
                if fnmatch.fnmatch(str(path), pattern):
                    return True
            return False

        try:
            # Ensure remote base directory exists
            await self._create_remote_dir(sftp, remote_path)

            local_base = trio.Path(local_path)

            # Walk directory tree and collect files to upload
            files_to_upload: list[tuple[trio.Path, str]] = []

            async def collect_files(local_dir: trio.Path, remote_dir: str) -> None:
                """Recursively collect files to upload."""
                entries = await local_dir.iterdir()
                for entry in entries:
                    if should_exclude(entry, exclude):
                        continue

                    rel_path = entry.relative_to(local_base)
                    remote_file_path = f"{remote_path}/{rel_path}"

                    if await entry.is_dir():
                        await collect_files(entry, remote_file_path)
                    else:
                        files_to_upload.append((entry, remote_file_path))

            await collect_files(local_base, remote_path)

            # Upload files with concurrency limit
            async def upload_one(local_file: trio.Path, remote_file: str) -> tuple[int, str | None]:
                """Upload a single file. Returns (bytes, error_or_none)."""
                try:
                    # Ensure parent directory exists
                    remote_dir = os.path.dirname(remote_file)
                    await self._create_remote_dir(sftp, remote_dir)

                    stat = await local_file.stat()
                    await _trio_wrap(sftp.put)(str(local_file), remote_file)
                    return stat.st_size, None
                except Exception as e:
                    return 0, f"{local_file}: {e}"

            # Use limited concurrency to avoid overwhelming the connection
            # asyncssh handles multiplexing, but too many concurrent ops can still cause issues
            semaphore = trio.Semaphore(10)

            async def upload_with_limit(
                local_file: trio.Path, remote_file: str
            ) -> tuple[int, str | None]:
                async with semaphore:
                    return await upload_one(local_file, remote_file)

            async with trio.open_nursery() as nursery:
                results: list[tuple[int, str | None]] = []

                async def upload_and_collect(local_file: trio.Path, remote_file: str) -> None:
                    result = await upload_with_limit(local_file, remote_file)
                    results.append(result)

                for local_file, remote_file in files_to_upload:
                    nursery.start_soon(upload_and_collect, local_file, remote_file)

            # Aggregate results
            for bytes_uploaded, error in results:
                if error:
                    errors.append(error)
                else:
                    files_copied += 1
                    total_bytes += bytes_uploaded

            duration = time.time() - start_time

            debug_info = {
                "method": "sftp",
                "local_path": local_path,
                "remote_path": remote_path,
                "remote_target": f"{self.user}@{self.host}:{self.port}",
                "exclude_patterns": exclude,
                "files_attempted": len(files_to_upload),
                "files_copied": files_copied,
                "errors": errors[:10] if errors else None,  # Limit error list
            }

            if errors:
                return CopyResult(
                    success=False,
                    files_copied=files_copied,
                    total_bytes=total_bytes,
                    duration_seconds=duration,
                    error_message=f"Failed to upload {len(errors)} files: {errors[0]}",
                    debug_info=debug_info,
                )

            return CopyResult(
                success=True,
                files_copied=files_copied,
                total_bytes=total_bytes,
                duration_seconds=duration,
                debug_info=debug_info,
            )

        finally:
            sftp.exit()

    async def _create_remote_dir(self, sftp, remote_dir: str) -> None:
        """Create remote directory recursively."""
        try:
            await _trio_wrap(sftp.stat)(remote_dir)
        except (FileNotFoundError, asyncssh.SFTPNoSuchFile):
            parent_dir = os.path.dirname(remote_dir)
            if parent_dir and parent_dir != remote_dir:
                await self._create_remote_dir(sftp, parent_dir)
            try:
                await _trio_wrap(sftp.mkdir)(remote_dir)
            except (OSError, asyncssh.SFTPError):
                pass  # Directory might have been created by another process

    async def download_files(
        self,
        remote_path: str,
        local_path: str,
        recursive: bool = False,
    ) -> CopyResult:
        """Download files from remote to local.

        Args:
            remote_path: Remote file or directory path
            local_path: Local destination path
            recursive: Download directories recursively

        Returns:
            CopyResult with transfer statistics
        """
        import time

        start_time = time.time()

        try:
            conn = await self._get_connection()

            # Check if remote path exists
            result = await self.exec(f"test -e {remote_path}")
            if result.exit_code != 0:
                raise TransferError(f"Remote path not found: {remote_path}")

            # Check if directory
            result = await self.exec(f"test -d {remote_path}")
            is_directory = result.exit_code == 0

            if is_directory and not recursive:
                raise TransferError(f"{remote_path} is a directory. Use recursive=True")

            sftp = await _trio_wrap(conn.start_sftp_client)()
            try:
                files_copied = 0
                total_bytes = 0

                if is_directory:
                    files_copied, total_bytes = await self._download_directory(
                        sftp, conn, remote_path, local_path
                    )
                else:
                    total_bytes = await self._download_file(sftp, remote_path, local_path)
                    files_copied = 1

                duration = time.time() - start_time

                return CopyResult(
                    success=True,
                    files_copied=files_copied,
                    total_bytes=total_bytes,
                    duration_seconds=duration,
                )
            finally:
                sftp.exit()

        except (ConnectionError, TransferError):
            raise
        except Exception as e:
            duration = time.time() - start_time
            return CopyResult(
                success=False,
                files_copied=0,
                total_bytes=0,
                duration_seconds=duration,
                error_message=str(e),
            )

    async def _download_file(self, sftp, remote_path: str, local_path: str) -> int:
        """Download single file and return bytes transferred."""
        local_dir = Path(local_path).parent
        local_dir.mkdir(parents=True, exist_ok=True)

        attrs = await _trio_wrap(sftp.stat)(remote_path)
        file_size = attrs.size

        await _trio_wrap(sftp.get)(remote_path, local_path)
        return file_size

    async def _download_directory(
        self, sftp, conn, remote_path: str, local_path: str
    ) -> tuple[int, int]:
        """Download directory recursively using parallel downloads."""
        result = await _trio_wrap(conn.run)(f"find {remote_path} -type f", check=True)
        file_list = [f.strip() for f in result.stdout.split("\n") if f.strip()]

        files_copied = 0
        total_bytes = 0

        async def download_one_file(remote_file: str) -> None:
            nonlocal files_copied, total_bytes

            rel_path = Path(remote_file).relative_to(remote_path)
            local_file = str(Path(local_path) / rel_path)

            try:
                file_bytes = await self._download_file(sftp, remote_file, local_file)
                files_copied += 1
                total_bytes += file_bytes
            except Exception as e:
                logger.warning(f"Failed to download {rel_path}: {e}")

        # Download files in parallel
        async with trio.open_nursery() as nursery:
            for remote_file in file_list:
                nursery.start_soon(download_one_file, remote_file)

        return files_copied, total_bytes

    async def close(self) -> None:
        """Close SSH connection."""
        if self._conn:
            self._conn.close()
            await _trio_wrap(self._conn.wait_closed)()
            self._conn = None

    async def __aenter__(self) -> "AsyncSSHClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
