"""Type definitions for fs-box-sync."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

# Type aliases
SyncStrategy = Literal["poll", "smart", "force"]


@dataclass
class BoxConfig:
    """Configuration for Box authentication and Box Drive integration."""

    # === Authentication ===
    # Access token for quick testing (expires in ~1 hour, no auto-refresh)
    access_token: str | None = None

    # Token provider function (e.g., Playwright automation)
    # Will be called when refresh token is needed initially
    token_provider: Callable[[str], Awaitable[str] | str] | None = None

    # Manual refresh token (if you already have one)
    refresh_token: str | None = None

    # Box API credentials
    client_id: str | None = None
    client_secret: str | None = None

    # Redirect URI for OAuth (default: https://oauth.pstmn.io/v1/callback)
    redirect_uri: str = "https://oauth.pstmn.io/v1/callback"

    # === Box Drive Configuration ===
    # Root directory of Box Drive
    # Windows: C:/Users/{username}/Box
    # Mac: ~/Library/CloudStorage/Box-Box
    # Linux: ~/Box (if using unofficial client)
    box_drive_root: str | None = None

    # === Box Domain Configuration ===
    # Box domain for Office Online URLs (e.g., 'foo.app.box.com', 'app.box.com')
    domain: str = "app.box.com"

    # === Sync Configuration ===
    # Default timeout for sync operations (ms)
    sync_timeout: int = 30000

    # Default poll interval for sync checks (ms)
    sync_interval: int = 1000

    # === Security Configuration ===
    # Allow insecure HTTPS connections (self-signed certificates)
    # WARNING: Only use in development/testing
    allow_insecure: bool = False

    # === Localization Configuration ===
    # Locale for date formatting (e.g., 'en-US', 'ja-JP', 'zh-CN')
    locale: str = "en-US"

    # === Retry Configuration ===
    # Maximum number of retries for network errors
    max_retries: int = 3

    # Initial delay between retries in ms
    retry_delay: int = 1000


@dataclass
class StoredCredentials:
    """Stored credentials in cross-platform storage."""

    refresh_token: str
    access_token: str
    expires_at: int  # Unix timestamp in milliseconds
    client_id: str
    # NOTE: client_secret is NOT stored (comes from env or config)


@dataclass
class SyncStatus:
    """Sync verification result."""

    synced: bool
    local_path: str | None = None
    error: str | None = None
    last_modified: datetime | None = None
    size: int | None = None


@dataclass
class UploadPart:
    """Chunked upload part metadata."""

    offset: int
    part_id: str
    sha1: str
    size: int


@dataclass
class FolderItem:
    """Item in a folder listing."""

    id: str
    name: str
    type: str
