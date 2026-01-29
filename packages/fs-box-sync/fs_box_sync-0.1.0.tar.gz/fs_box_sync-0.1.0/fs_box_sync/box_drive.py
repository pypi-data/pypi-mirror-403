"""Box Drive sync bridge for local filesystem integration."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from .exceptions import BoxDriveNotAvailableError
from .types import BoxConfig, SyncStatus, SyncStrategy

if TYPE_CHECKING:
    from .box_api import BoxAPI

logger = logging.getLogger("fs_box_sync")


class BoxDrive:
    """
    Box Drive sync bridge.

    Handles path conversion and sync verification between Box Cloud and Box Drive.
    Box Drive path detection is lazy - it only occurs when an operation
    that requires local filesystem access is called.
    """

    def __init__(self, api: BoxAPI, config: BoxConfig | None = None):
        self._api = api
        self._box_drive_root: str | None = config.box_drive_root if config else None
        self._box_drive_root_detected = False
        self._sync_timeout = config.sync_timeout if config else 30000
        self._sync_interval = config.sync_interval if config else 1000

    def _get_box_drive_root_lazy(self) -> str:
        """
        Get Box Drive root with lazy detection.

        Only detects/validates when actually needed for local operations.
        """
        if not self._box_drive_root_detected:
            if not self._box_drive_root:
                self._box_drive_root = self._detect_box_drive_root()
            self._box_drive_root_detected = True
        return self._box_drive_root  # type: ignore

    def is_box_drive_available(self) -> bool:
        """
        Check if Box Drive is available without throwing.

        Returns:
            True if Box Drive path is configured or can be detected
        """
        if self._box_drive_root:
            return Path(self._box_drive_root).exists()
        try:
            self._get_box_drive_root_lazy()
            return True
        except BoxDriveNotAvailableError:
            return False

    def _detect_box_drive_root(self) -> str:
        """Auto-detect Box Drive root directory based on platform."""
        home_dir = Path.home()

        if sys.platform == "win32":
            # Windows: C:/Users/{username}/Box
            default_path = home_dir / "Box"
            if default_path.exists():
                return str(default_path)
            raise BoxDriveNotAvailableError(
                f"Box Drive root not found. Please provide box_drive_root in config.\n"
                f"Expected: {default_path}"
            )
        elif sys.platform == "darwin":
            # macOS: ~/Library/CloudStorage/Box-Box
            default_path = home_dir / "Library" / "CloudStorage" / "Box-Box"
            if default_path.exists():
                return str(default_path)
            raise BoxDriveNotAvailableError(
                f"Box Drive root not found. Please provide box_drive_root in config.\n"
                f"Expected: {default_path}"
            )
        else:
            # Linux: ~/Box (unofficial clients)
            default_path = home_dir / "Box"
            if default_path.exists():
                return str(default_path)
            raise BoxDriveNotAvailableError(
                f"Box Drive root not found. Please provide box_drive_root in config.\n"
                f"Expected: {default_path}"
            )

    async def is_box_drive_running(self) -> bool:
        """Check if Box Drive is running."""
        try:
            if sys.platform == "win32":
                result = await asyncio.to_thread(
                    subprocess.run,
                    ['tasklist', '/FI', 'IMAGENAME eq Box.exe'],
                    capture_output=True,
                    text=True,
                )
                return "Box.exe" in result.stdout
            elif sys.platform == "darwin":
                result = await asyncio.to_thread(
                    subprocess.run,
                    ["pgrep", "-f", "Box.app"],
                    capture_output=True,
                    text=True,
                )
                return len(result.stdout.strip()) > 0
            else:
                # Linux - just check if directory is accessible
                return (
                    self.is_box_drive_available()
                    and Path(self._get_box_drive_root_lazy()).exists()
                )
        except Exception:
            return False

    async def get_local_path(
        self, id_: str, type_: Literal["file", "folder"]
    ) -> str:
        """
        Convert Box file/folder ID to local Box Drive path.

        Args:
            id_: Box file or folder ID
            type_: Type of item ("file" or "folder")

        Returns:
            Local filesystem path

        Raises:
            BoxDriveNotAvailableError: If Box Drive is not available
        """
        box_drive_root = self._get_box_drive_root_lazy()

        if type_ == "file":
            file_info = await self._api.get_file_info(id_)
            # Remove "All Files" from path
            parent_path = file_info["path_collection"]["entries"][1:]
            path_parts = [entry["name"] for entry in parent_path] + [file_info["name"]]
        else:
            folder_info = await self._api.get_folder_info(id_)
            # Remove "All Files" from path
            parent_path = folder_info["path_collection"]["entries"][1:]
            path_parts = [entry["name"] for entry in parent_path] + [folder_info["name"]]

        return str(Path(box_drive_root, *path_parts))

    async def wait_for_sync(
        self,
        id_: str,
        type_: Literal["file", "folder"],
        strategy: SyncStrategy = "smart",
    ) -> SyncStatus:
        """
        Wait for file/folder to sync with various strategies.

        Args:
            id_: Box file or folder ID
            type_: Type of item
            strategy: Sync strategy ("poll", "smart", or "force")

        Returns:
            SyncStatus with sync result
        """
        local_path = await self.get_local_path(id_, type_)

        if strategy == "poll":
            return await self._poll_sync(local_path)
        elif strategy == "smart":
            return await self._smart_sync(id_, type_, local_path)
        elif strategy == "force":
            return await self._force_sync(id_, type_, local_path)
        else:
            return await self._smart_sync(id_, type_, local_path)

    async def _poll_sync(self, local_path: str) -> SyncStatus:
        """Poll strategy: Simple file existence check with timeout."""
        start_time = asyncio.get_event_loop().time() * 1000
        interval_sec = self._sync_interval / 1000

        while (asyncio.get_event_loop().time() * 1000 - start_time) < self._sync_timeout:
            try:
                path = Path(local_path)
                if path.exists():
                    stats = path.stat()
                    return SyncStatus(
                        synced=True,
                        local_path=local_path,
                        last_modified=datetime.fromtimestamp(stats.st_mtime),
                        size=stats.st_size,
                    )
            except OSError as e:
                if e.errno != 2:  # Not ENOENT
                    logger.warning(f"Error checking path {local_path}: {e}")

            await asyncio.sleep(interval_sec)

        return SyncStatus(
            synced=False,
            local_path=local_path,
            error=f"Timeout: File did not appear within {self._sync_timeout / 1000} seconds",
        )

    async def _smart_sync(
        self, id_: str, type_: Literal["file", "folder"], local_path: str
    ) -> SyncStatus:
        """Smart strategy: Verify file size and modification time match cloud."""
        start_time = asyncio.get_event_loop().time() * 1000
        interval_sec = self._sync_interval / 1000

        # Get cloud metadata
        cloud_size: int | None = None
        if type_ == "file":
            file_info = await self._api.get_file_info(id_)
            cloud_size = file_info.get("size")

        while (asyncio.get_event_loop().time() * 1000 - start_time) < self._sync_timeout:
            try:
                path = Path(local_path)
                if path.exists():
                    stats = path.stat()

                    # For files, verify size matches
                    if type_ == "file" and cloud_size is not None:
                        if stats.st_size == cloud_size:
                            return SyncStatus(
                                synced=True,
                                local_path=local_path,
                                last_modified=datetime.fromtimestamp(stats.st_mtime),
                                size=stats.st_size,
                            )
                        # File exists but wrong size - still syncing
                    else:
                        # For folders, just check existence
                        return SyncStatus(
                            synced=True,
                            local_path=local_path,
                            last_modified=datetime.fromtimestamp(stats.st_mtime),
                            size=stats.st_size,
                        )
            except OSError as e:
                if e.errno != 2:  # Not ENOENT
                    logger.warning(f"Error checking path {local_path}: {e}")

            await asyncio.sleep(interval_sec)

        return SyncStatus(
            synced=False,
            local_path=local_path,
            error=f"Timeout: File did not fully sync within {self._sync_timeout / 1000} seconds",
        )

    async def _force_sync(
        self, id_: str, type_: Literal["file", "folder"], local_path: str
    ) -> SyncStatus:
        """Force strategy: Try to trigger Box Drive sync."""
        # Check if Box Drive is running
        is_running = await self.is_box_drive_running()
        if not is_running:
            return SyncStatus(
                synced=False,
                local_path=local_path,
                error="Box Drive is not running",
            )

        # Try to access parent directory to trigger sync
        parent_dir = Path(local_path).parent
        with contextlib.suppress(OSError):
            list(parent_dir.iterdir())

        # Fall back to smart sync
        return await self._smart_sync(id_, type_, local_path)

    async def is_synced(self, id_: str, type_: Literal["file", "folder"]) -> bool:
        """Check if path exists locally and is synced."""
        try:
            status = await self.wait_for_sync(id_, type_, "poll")
            return status.synced
        except Exception:
            return False

    def get_box_drive_root(self) -> str:
        """
        Get Box Drive root directory.

        Raises:
            BoxDriveNotAvailableError: If Box Drive is not available
        """
        return self._get_box_drive_root_lazy()

    async def open_locally(self, local_path: str) -> None:
        """
        Open file/folder in Box Drive locally.

        Uses platform-specific open command.
        """
        try:
            if sys.platform == "win32":
                await asyncio.to_thread(os.startfile, local_path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                await asyncio.to_thread(
                    subprocess.run, ["open", local_path], check=True
                )
            else:
                await asyncio.to_thread(
                    subprocess.run, ["xdg-open", local_path], check=True
                )
        except Exception as e:
            raise OSError(f"Failed to open {local_path}: {e}") from e
