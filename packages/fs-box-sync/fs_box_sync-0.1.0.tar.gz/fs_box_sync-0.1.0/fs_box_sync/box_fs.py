"""High-level Box filesystem API with automatic Box Drive sync."""

from __future__ import annotations

import contextlib
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import aiofiles

from .box_api import BoxAPI
from .box_drive import BoxDrive
from .types import BoxConfig, FolderItem, SyncStatus, SyncStrategy
from .utils import format_date_folders, get_box_office_online_url


class BoxFS:
    """
    High-level Box filesystem API.

    Provides fs-like interface with automatic Box Drive sync.
    """

    def __init__(self, config: BoxConfig | None = None):
        self._api = BoxAPI(config)
        self._drive = BoxDrive(self._api, config)

    # ========== FILESYSTEM-LIKE OPERATIONS (ID-based) ==========

    async def read_dir(self, folder_id: str) -> list[str]:
        """
        Read directory contents from local Box Drive (waits for sync).

        Args:
            folder_id: Box folder ID

        Returns:
            List of filenames in the directory
        """
        sync_status = await self._drive.wait_for_sync(folder_id, "folder")
        if not sync_status.synced:
            raise OSError(f"Folder {folder_id} is not synced: {sync_status.error}")

        # Read from local filesystem
        local_path = sync_status.local_path
        assert local_path is not None
        return os.listdir(local_path)

    async def list_folder_items(self, folder_id: str) -> list[FolderItem]:
        """
        List directory contents with detailed info (from API).

        Args:
            folder_id: Box folder ID

        Returns:
            List of FolderItem objects with id, name, and type
        """
        items = await self._api.list_folder_items(folder_id)
        return [
            FolderItem(id=entry["id"], name=entry["name"], type=entry["type"])
            for entry in items["entries"]
        ]

    async def read_file(self, file_id: str) -> str:
        """
        Read file contents from local Box Drive (waits for sync).

        Args:
            file_id: Box file ID

        Returns:
            File contents as string
        """
        sync_status = await self._drive.wait_for_sync(file_id, "file")
        if not sync_status.synced:
            raise OSError(f"File {file_id} is not synced: {sync_status.error}")

        local_path = sync_status.local_path
        assert local_path is not None
        async with aiofiles.open(local_path, encoding="utf-8") as f:
            return await f.read()

    async def get_file_content(self, file_id: str) -> str:
        """
        Read file contents from Box Cloud (API).

        Args:
            file_id: Box file ID

        Returns:
            File contents as string
        """
        content = await self._api.get_file_content(file_id)
        return content or ""

    async def write_file(
        self, folder_id: str, filename: str, content: str
    ) -> str:
        """
        Write file contents by creating a temp file and uploading.

        Args:
            folder_id: Target folder ID in Box
            filename: Name for the new file
            content: File contents

        Returns:
            Uploaded file ID
        """
        # Create temp file
        temp_path = Path(tempfile.gettempdir()) / f"box-upload-{os.getpid()}-{filename}"

        async with aiofiles.open(temp_path, "w", encoding="utf-8") as f:
            await f.write(content)

        try:
            file_id = await self._api.upload_file(folder_id, str(temp_path))
            return file_id
        finally:
            # Clean up temp file
            with contextlib.suppress(OSError):
                temp_path.unlink()

    async def delete_file(self, file_id: str) -> None:
        """Delete a file by ID."""
        await self._api.delete_file(file_id)

    async def exists_and_synced(
        self, id_: str, type_: Literal["file", "folder"]
    ) -> bool:
        """Check if file/folder exists and is synced."""
        return await self._drive.is_synced(id_, type_)

    async def exists_by_name_and_synced(
        self,
        parent_folder_id: str,
        name: str,
        type_: Literal["file", "folder"],
    ) -> bool:
        """
        Check if a file/folder exists by name and is synced to Box Drive.

        Args:
            parent_folder_id: Parent folder ID to search in
            name: Name of the file/folder to find
            type_: Type of item

        Returns:
            True if found in cloud AND synced locally
        """
        id_ = await self.find_by_name(parent_folder_id, name)
        if not id_:
            return False
        return await self.exists_and_synced(id_, type_)

    async def get_local_path(
        self, id_: str, type_: Literal["file", "folder"]
    ) -> str:
        """Get local Box Drive path for a Box file/folder."""
        return await self._drive.get_local_path(id_, type_)

    async def get_local_path_synced(
        self,
        id_: str,
        type_: Literal["file", "folder"],
        strategy: SyncStrategy | None = None,
    ) -> str:
        """
        Get local Box Drive path and ensure it's synced.

        Args:
            id_: Box file/folder ID
            type_: Type of item
            strategy: Sync strategy (default: 'smart')

        Returns:
            Local filesystem path (guaranteed to exist)
        """
        sync_status = await self._drive.wait_for_sync(
            id_, type_, strategy or "smart"
        )
        if not sync_status.synced:
            raise OSError(f"Cannot get local path: {sync_status.error}")
        assert sync_status.local_path is not None
        return sync_status.local_path

    async def open_locally(
        self, id_: str, type_: Literal["file", "folder"]
    ) -> None:
        """Open file/folder locally in Box Drive."""
        sync_status = await self._drive.wait_for_sync(id_, type_)
        if not sync_status.synced:
            raise OSError(f"Cannot open: {sync_status.error}")

        assert sync_status.local_path is not None
        await self._drive.open_locally(sync_status.local_path)

    # ========== HIGHER-LEVEL OPERATIONS ==========

    async def find_by_name(
        self, folder_id: str, name: str
    ) -> str | None:
        """
        Find file/folder by name in a folder (partial match).

        Args:
            folder_id: Parent folder ID
            name: Name to search for (partial match)

        Returns:
            File/folder ID or None if not found
        """
        items = await self._api.list_folder_items(folder_id)
        for entry in items["entries"]:
            if name in entry["name"]:
                return entry["id"]
        return None

    async def search(
        self,
        folder_id: str,
        query: str,
        type_: Literal["file", "folder"] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for files/folders in a folder."""
        return await self._api.search_in_folder(folder_id, query, type_)

    async def create_folder_if_not_exists(
        self, parent_folder_id: str, name: str
    ) -> str:
        """
        Create folder if it doesn't exist.

        Args:
            parent_folder_id: Parent folder ID
            name: Folder name

        Returns:
            Folder ID (existing or newly created)
        """
        existing_id = await self.find_by_name(parent_folder_id, name)
        if existing_id:
            return existing_id

        folder = await self._api.create_folder(parent_folder_id, name)
        return folder["id"]

    async def upload_with_year_month_folders(
        self, folder_id: str, file_path: str
    ) -> str:
        """
        Upload file with automatic date-based folder structure.

        Creates year/month folders and uploads the file.
        Uses the global locale configured in BoxConfig.

        Args:
            folder_id: Base folder ID where date folders will be created
            file_path: Local file path to upload

        Returns:
            Uploaded file ID

        Example:
            # Configure locale first
            box.configure(BoxConfig(locale='ja-JP'))

            # Uploads to: folder_id/2024年/3月/file.pdf
            await box_fs.upload_with_year_month_folders('123', './file.pdf')
        """
        date = datetime.now()
        folders = format_date_folders(date, self._api.locale)

        # Create year folder
        year_folder_id = await self.create_folder_if_not_exists(
            folder_id, folders["year"]
        )

        # Create month folder
        month_folder_id = await self.create_folder_if_not_exists(
            year_folder_id, folders["month"]
        )

        # Upload file
        file_id = await self._api.upload_file(month_folder_id, file_path)

        # Delete local file after upload
        with contextlib.suppress(OSError):
            Path(file_path).unlink()

        return file_id

    def get_office_online_url(self, file_id: str) -> str:
        """
        Get Box Office Online editable URL for a file.

        Args:
            file_id: Box file ID

        Returns:
            Office Online URL
        """
        return get_box_office_online_url(file_id, self._api.domain)

    async def get_office_online_url_by_name(
        self, folder_id: str, file_name: str
    ) -> str:
        """
        Get Box Office Online URL by searching for file in folder.

        Args:
            folder_id: Folder to search in
            file_name: File name to search for

        Returns:
            Office Online URL or empty string if not found
        """
        file_id = await self.find_by_name(folder_id, file_name)
        if not file_id:
            return ""
        return self.get_office_online_url(file_id)

    async def upload_file(self, folder_id: str, file_path: str) -> str:
        """Upload file to Box."""
        return await self._api.upload_file(folder_id, file_path)

    async def upload_file_then_remove(
        self, folder_id: str, file_path: str
    ) -> str:
        """
        Upload file to Box and remove it locally.

        Args:
            folder_id: Target folder ID in Box
            file_path: Local file path to upload

        Returns:
            Uploaded file ID
        """
        file_id = await self._api.upload_file(folder_id, file_path)
        Path(file_path).unlink()
        return file_id

    async def download_file(self, file_id: str, dest_path: str) -> None:
        """Download file by ID."""
        await self._api.download_file(file_id, dest_path)

    async def move_file(
        self, file_id: str, to_folder_id: str
    ) -> dict[str, Any]:
        """Move file to another folder."""
        return await self._api.move_file(file_id, to_folder_id)

    async def get_file_info(self, file_id: str) -> dict[str, Any]:
        """Get file metadata."""
        return await self._api.get_file_info(file_id)

    async def get_folder_info(self, folder_id: str) -> dict[str, Any]:
        """Get folder metadata."""
        return await self._api.get_folder_info(folder_id)

    # ========== WEBHOOK OPERATIONS ==========

    async def get_all_webhooks(self) -> dict[str, Any]:
        """Get all webhooks."""
        return await self._api.get_all_webhooks()

    async def create_webhook(
        self, folder_id: str, address: str
    ) -> dict[str, Any]:
        """Create a webhook for a folder."""
        return await self._api.create_webhook(folder_id, address)

    async def delete_webhook(self, webhook_id: str) -> dict[str, Any]:
        """Delete a webhook."""
        return await self._api.delete_webhook(webhook_id)

    async def delete_all_webhooks(self) -> int:
        """
        Delete all webhooks.

        Returns:
            Number of webhooks deleted
        """
        webhooks = await self._api.get_all_webhooks()
        for webhook in webhooks["entries"]:
            await self._api.delete_webhook(webhook["id"])
        return len(webhooks["entries"])

    # ========== SHARED LINKS ==========

    async def download_from_shared_link(
        self, link_id: str, dest_path: str
    ) -> None:
        """Download file from shared link."""
        await self._api.download_from_shared_link(link_id, dest_path)

    # ========== BOX DRIVE OPERATIONS ==========

    async def is_box_drive_running(self) -> bool:
        """Check if Box Drive is running."""
        return await self._drive.is_box_drive_running()

    def is_box_drive_available(self) -> bool:
        """Check if Box Drive is available (path exists or can be detected)."""
        return self._drive.is_box_drive_available()

    async def wait_for_sync(
        self,
        id_: str,
        type_: Literal["file", "folder"],
        strategy: SyncStrategy | None = None,
    ) -> SyncStatus:
        """Wait for sync with custom strategy."""
        return await self._drive.wait_for_sync(id_, type_, strategy or "smart")

    def get_box_drive_root(self) -> str:
        """Get Box Drive root directory."""
        return self._drive.get_box_drive_root()
