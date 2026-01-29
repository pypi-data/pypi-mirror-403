"""
fs-box-sync: Python SDK for Box API with seamless Box Drive integration.

This package provides a 3-layer architecture for interacting with Box:
- BoxAPI: Pure REST API wrapper with token management
- BoxDrive: Sync bridge for Box Drive local filesystem integration
- BoxFS: High-level filesystem-like API combining both layers

Quick Start:
    from fs_box_sync import box, BoxConfig

    # Configure with your credentials
    box.configure(BoxConfig(
        client_id='your-client-id',
        client_secret='your-client-secret',
    ))

    # Use the high-level API
    files = await box.list_folder_items('0')  # List root folder
    content = await box.get_file_content('file-id')
    file_id = await box.upload_file('folder-id', './local-file.pdf')
"""

from .box import Box, get_box
from .box_api import BoxAPI
from .box_drive import BoxDrive
from .box_fs import BoxFS
from .exceptions import (
    BoxAuthenticationError,
    BoxConflictError,
    BoxCredentialsError,
    BoxDriveNotAvailableError,
    BoxError,
    BoxNotFoundError,
    BoxPermissionError,
    BoxSyncTimeoutError,
    BoxTokenProviderError,
)
from .types import (
    BoxConfig,
    FolderItem,
    StoredCredentials,
    SyncStatus,
    SyncStrategy,
    UploadPart,
)
from .utils import (
    format_date_folders,
    get_box_office_online_url,
    get_file_extension,
    is_office_file,
    sanitize_filename,
)

# Singleton instance
box = get_box()

__all__ = [
    # Main singleton
    "box",
    # Classes
    "Box",
    "BoxFS",
    "BoxAPI",
    "BoxDrive",
    # Factory function
    "get_box",
    # Types
    "BoxConfig",
    "StoredCredentials",
    "SyncStatus",
    "SyncStrategy",
    "UploadPart",
    "FolderItem",
    # Exceptions
    "BoxError",
    "BoxAuthenticationError",
    "BoxNotFoundError",
    "BoxConflictError",
    "BoxPermissionError",
    "BoxDriveNotAvailableError",
    "BoxSyncTimeoutError",
    "BoxCredentialsError",
    "BoxTokenProviderError",
    # Utilities
    "format_date_folders",
    "get_box_office_online_url",
    "sanitize_filename",
    "get_file_extension",
    "is_office_file",
]

__version__ = "0.1.0"
