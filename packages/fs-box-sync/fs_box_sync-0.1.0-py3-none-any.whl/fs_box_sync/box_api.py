"""Pure Box API wrapper with token management."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import inspect
import json
import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

import aiofiles
import httpx
from platformdirs import user_config_dir

from .exceptions import (
    BoxAuthenticationError,
    BoxConflictError,
    BoxCredentialsError,
    BoxError,
    BoxNotFoundError,
    BoxPermissionError,
    BoxTokenProviderError,
)
from .types import BoxConfig, StoredCredentials, UploadPart

logger = logging.getLogger("fs_box_sync")

T = TypeVar("T")

# File size threshold for chunked upload (20MB)
FILE_SIZE_THRESHOLD = 20 * 1024 * 1024


class BoxAPI:
    """
    Pure Box API wrapper.

    Handles authentication and raw API calls.
    No Box Drive integration or sync logic.
    """

    def __init__(self, config: BoxConfig | None = None):
        self._expired_at = 0
        self._refresh_token = ""
        self._access_token = ""
        self._token_refresh_lock = asyncio.Lock()
        self._storage_load_task: asyncio.Task[bool] | None = None
        self._is_retrying = False
        self._token_provider: Callable[[str], Any] | None = None
        self._client_id = ""
        self._client_secret = ""
        self._redirect_uri = "https://oauth.pstmn.io/v1/callback"
        self._storage_path = self._get_default_storage_path()
        self.domain = "app.box.com"
        self._allow_insecure = False
        self.locale = "en-US"
        self._max_retries = 3
        self._retry_delay = 1000

        if config:
            self.apply_config(config)

    def apply_config(self, config: BoxConfig) -> None:
        """Apply configuration."""
        if config.access_token:
            self._access_token = config.access_token
            # Set a far future expiry for manual access tokens
            self._expired_at = self._now_ms() + 365 * 24 * 60 * 60 * 1000

        if config.token_provider:
            self._token_provider = config.token_provider

        if config.refresh_token:
            self._refresh_token = config.refresh_token

        if config.client_id:
            self._client_id = config.client_id

        if config.client_secret:
            self._client_secret = config.client_secret

        if config.redirect_uri:
            self._redirect_uri = config.redirect_uri

        if config.domain:
            self.domain = config.domain

        self._allow_insecure = config.allow_insecure

        if config.locale:
            self.locale = config.locale

        self._max_retries = config.max_retries
        self._retry_delay = config.retry_delay

    def _now_ms(self) -> int:
        """Get current time in milliseconds."""
        import time

        return int(time.time() * 1000)

    def _get_storage_directory(self) -> Path:
        """Get the storage directory based on platform."""
        return Path(user_config_dir("fs-box-sync"))

    def _get_default_storage_path(self) -> Path:
        """Get storage path for tokens."""
        return self._get_storage_directory() / "tokens.json"

    def _get_http_client(self) -> httpx.AsyncClient:
        """Get configured HTTP client."""
        return httpx.AsyncClient(verify=not self._allow_insecure, timeout=30.0)

    async def _save_to_storage(self) -> None:
        """Save credentials to storage."""
        if not self._refresh_token:
            return

        try:
            credentials = StoredCredentials(
                refresh_token=self._refresh_token,
                access_token=self._access_token,
                expires_at=self._expired_at,
                client_id=self._client_id,
            )

            self._storage_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(self._storage_path, "w") as f:
                await f.write(
                    json.dumps(
                        {
                            "refreshToken": credentials.refresh_token,
                            "accessToken": credentials.access_token,
                            "expiresAt": credentials.expires_at,
                            "clientId": credentials.client_id,
                        },
                        indent=2,
                    )
                )
        except Exception as e:
            logger.error(f"Failed to save credentials to storage: {e}")

    async def _load_from_storage(self) -> bool:
        """Load credentials from storage."""
        try:
            async with aiofiles.open(self._storage_path) as f:
                data = json.loads(await f.read())

            self._refresh_token = data["refreshToken"]
            self._access_token = data["accessToken"]
            self._expired_at = data["expiresAt"]
            self._client_id = data["clientId"]

            return True
        except Exception:
            return False

    def _ensure_credentials(self) -> None:
        """Ensure we have required credentials."""
        if not self._client_id and os.environ.get("BOX_CLIENT_ID"):
            self._client_id = os.environ["BOX_CLIENT_ID"]

        if not self._client_secret and os.environ.get("BOX_CLIENT_SECRET"):
            self._client_secret = os.environ["BOX_CLIENT_SECRET"]

        if not self._client_id or not self._client_secret:
            missing: list[str] = []
            if not self._client_id:
                missing.append("client_id")
            if not self._client_secret:
                missing.append("client_secret")

            raise BoxCredentialsError(
                f"Missing required credentials: {', '.join(missing)}.\n"
                "Provide via:\n"
                "1. BoxAPI(BoxConfig(client_id='...', client_secret='...'))\n"
                "2. Environment variables: BOX_CLIENT_ID, BOX_CLIENT_SECRET"
            )

    async def _check_token(self) -> None:
        """Check and refresh token if needed."""
        # If using access token only mode, skip credential check
        if self._access_token and not self._refresh_token and not self._token_provider:
            return

        self._ensure_credentials()

        # Try to load from storage on first call
        if self._storage_load_task is None:
            self._storage_load_task = asyncio.create_task(self._load_from_storage())

        if self._storage_load_task and not self._storage_load_task.done():
            await self._storage_load_task

        async with self._token_refresh_lock:
            if not self._refresh_token or self._now_ms() >= self._expired_at:
                if not self._refresh_token:
                    await self._forge_refresh_token()
                else:
                    await self._refresh_access_token()
                await self._save_to_storage()

    async def _forge_refresh_token(self) -> None:
        """Forge new refresh token via OAuth."""
        if not self._token_provider:
            raise BoxTokenProviderError(
                "No token provider configured. Please provide one via:\n"
                "1. BoxAPI(BoxConfig(token_provider=async_func))\n"
                "2. Provide refresh_token directly: BoxAPI(BoxConfig(refresh_token='...'))"
            )

        callback = (
            "https://account.box.com/api/oauth2/authorize?"
            f"client_id={self._client_id}"
            "&response_type=code"
        )

        # Call token provider (may be sync or async)
        if inspect.iscoroutinefunction(self._token_provider):
            code = await self._token_provider(callback)
        else:
            code = self._token_provider(callback)

        url = "https://api.box.com/oauth2/token"
        data = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "code": code,
            "redirect_uri": self._redirect_uri,
            "grant_type": "authorization_code",
        }

        async with self._get_http_client() as client:
            response = await client.post(
                url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                result = response.json()
                self._access_token = result["access_token"]
                self._expired_at = self._now_ms() + result["expires_in"] * 1000
                self._refresh_token = result["refresh_token"]
            else:
                logger.error(f"Failed to forge refresh token: {response.status_code}")
                raise BoxAuthenticationError("Failed to forge refresh token")

    async def _refresh_access_token(self) -> None:
        """Refresh access token."""
        url = "https://api.box.com/oauth2/token"
        data = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }

        async with self._get_http_client() as client:
            try:
                response = await client.post(
                    url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code == 200:
                    result = response.json()
                    self._access_token = result["access_token"]
                    self._expired_at = self._now_ms() + result["expires_in"] * 1000
                    self._refresh_token = result["refresh_token"]
                elif response.status_code in (400, 401):
                    logger.warning("Refresh token is invalid, falling back to provider")
                    self._refresh_token = ""
                    await self._forge_refresh_token()
                else:
                    logger.error(
                        f"Failed to refresh access token: {response.status_code}"
                    )
                    raise BoxAuthenticationError("Failed to refresh access token")
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (400, 401):
                    logger.warning(
                        "Refresh token is invalid (caught error), falling back to provider"
                    )
                    self._refresh_token = ""
                    await self._forge_refresh_token()
                else:
                    raise

    async def _invalidate_and_refresh(self) -> None:
        """Invalidate current tokens and refresh them."""
        logger.info("Token invalidated by 401 response, refreshing...")

        self._access_token = ""
        self._expired_at = 0

        if self._refresh_token:
            try:
                await self._refresh_access_token()
                return
            except Exception:
                logger.warning("Failed to refresh with refresh token, will try provider")

        if self._token_provider:
            await self._forge_refresh_token()
        else:
            raise BoxAuthenticationError(
                "Authentication failed and no token provider configured. "
                "Cannot recover from 401 error."
            )

    def _is_network_error(self, error: Exception) -> bool:
        """Check if an error is a transient network error."""
        message = str(error).lower()
        return any(
            keyword in message
            for keyword in [
                "socket hang up",
                "connection reset",
                "timed out",
                "connection refused",
                "name or service not known",
                "network",
            ]
        )

    async def _with_retry(self, operation: Callable[[], Any]) -> Any:
        """Wrapper for API requests with automatic retry."""
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                return await operation()
            except httpx.HTTPStatusError as e:
                last_error = e

                # Handle 401 errors (token refresh)
                if e.response.status_code == 401 and not self._is_retrying:
                    self._is_retrying = True
                    try:
                        logger.warning(
                            "Received 401, attempting to refresh token and retry..."
                        )
                        await self._invalidate_and_refresh()
                        return await operation()
                    finally:
                        self._is_retrying = False

                # Non-retryable HTTP error
                break

            except Exception as e:
                last_error = e

                # Handle network errors with exponential backoff
                if self._is_network_error(e) and attempt < self._max_retries:
                    delay = self._retry_delay * (2**attempt) / 1000
                    logger.warning(
                        f"Network error (attempt {attempt + 1}/{self._max_retries + 1}), "
                        f"retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    continue

                break

        raise self._enhance_error(last_error)

    def _enhance_error(self, error: Exception | None) -> Exception:
        """Enhance error messages to be more user-friendly."""
        if error is None:
            return BoxError("Unknown error")

        if isinstance(error, httpx.HTTPStatusError):
            status = error.response.status_code
            try:
                data = error.response.json()
                message = data.get("message", "")
            except Exception:
                message = ""

            if status == 401:
                return BoxAuthenticationError(
                    "Authentication failed. Please check your credentials."
                )
            elif status == 404:
                return BoxNotFoundError(
                    f"Resource not found: {message or 'The requested item does not exist'}"
                )
            elif status == 409:
                return BoxConflictError(
                    f"Conflict: {message or 'An item with this name already exists'}"
                )
            elif status == 403:
                return BoxPermissionError(
                    f"Permission denied: {message or 'You do not have access to this resource'}"
                )
            elif status >= 500:
                return BoxError(
                    f"Box server error ({status}): {message or 'Please try again later'}",
                    status_code=status,
                )

        return error if isinstance(error, BoxError) else BoxError(str(error))

    # ========== WEBHOOK OPERATIONS ==========

    async def get_all_webhooks(self) -> dict[str, Any]:
        """Get all webhooks."""
        await self._check_token()

        async def operation() -> dict[str, Any]:
            async with self._get_http_client() as client:
                response = await client.get(
                    "https://api.box.com/2.0/webhooks",
                    headers={"Authorization": f"Bearer {self._access_token}"},
                )
                response.raise_for_status()
                return response.json()

        return await self._with_retry(operation)

    async def create_webhook(self, folder_id: str, address: str) -> dict[str, Any]:
        """Create a webhook for a folder."""
        await self._check_token()

        async def operation() -> dict[str, Any]:
            payload = {
                "target": {"id": folder_id, "type": "folder"},
                "address": address,
                "triggers": ["FILE.UPLOADED"],
            }
            async with self._get_http_client() as client:
                response = await client.post(
                    "https://api.box.com/2.0/webhooks",
                    headers={"Authorization": f"Bearer {self._access_token}"},
                    json=payload,
                )
                response.raise_for_status()
                return response.json()

        return await self._with_retry(operation)

    async def delete_webhook(self, webhook_id: str) -> dict[str, Any]:
        """Delete a webhook."""
        await self._check_token()

        async def operation() -> dict[str, Any]:
            async with self._get_http_client() as client:
                response = await client.delete(
                    f"https://api.box.com/2.0/webhooks/{webhook_id}",
                    headers={"Authorization": f"Bearer {self._access_token}"},
                )
                response.raise_for_status()
                return response.json() if response.content else {}

        return await self._with_retry(operation)

    # ========== FILE OPERATIONS ==========

    async def get_file_info(self, file_id: str) -> dict[str, Any]:
        """Get file metadata."""
        await self._check_token()

        async def operation() -> dict[str, Any]:
            async with self._get_http_client() as client:
                response = await client.get(
                    f"https://api.box.com/2.0/files/{file_id}",
                    headers={"Authorization": f"Bearer {self._access_token}"},
                )
                response.raise_for_status()
                return response.json()

        return await self._with_retry(operation)

    async def get_file_content(self, file_id: str) -> str | None:
        """Get file content as string."""
        await self._check_token()

        async def operation() -> str | None:
            async with self._get_http_client() as client:
                response = await client.get(
                    f"https://api.box.com/2.0/files/{file_id}/content",
                    headers={"Authorization": f"Bearer {self._access_token}"},
                    follow_redirects=True,
                )
                response.raise_for_status()
                return response.text

        return await self._with_retry(operation)

    async def download_file(self, file_id: str, dest_path: str) -> None:
        """Download file to local path."""
        await self._check_token()

        async def operation() -> None:
            async with self._get_http_client() as client, client.stream(
                "GET",
                f"https://api.box.com/2.0/files/{file_id}/content",
                headers={"Authorization": f"Bearer {self._access_token}"},
                follow_redirects=True,
            ) as response:
                response.raise_for_status()
                async with aiofiles.open(dest_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        await f.write(chunk)

        await self._with_retry(operation)

    async def delete_file(self, file_id: str) -> dict[str, Any]:
        """Delete a file."""
        await self._check_token()

        async def operation() -> dict[str, Any]:
            async with self._get_http_client() as client:
                response = await client.delete(
                    f"https://api.box.com/2.0/files/{file_id}",
                    headers={"Authorization": f"Bearer {self._access_token}"},
                )
                response.raise_for_status()
                return response.json() if response.content else {}

        return await self._with_retry(operation)

    async def move_file(self, file_id: str, to_folder_id: str) -> dict[str, Any]:
        """Move file to another folder."""
        await self._check_token()

        async def operation() -> dict[str, Any]:
            async with self._get_http_client() as client:
                response = await client.put(
                    f"https://api.box.com/2.0/files/{file_id}",
                    headers={"Authorization": f"Bearer {self._access_token}"},
                    json={"parent": {"id": to_folder_id}},
                )
                response.raise_for_status()
                return response.json()

        return await self._with_retry(operation)

    async def upload_file(self, folder_id: str, file_path: str) -> str:
        """Upload a file to Box."""
        await self._check_token()

        file_size = os.path.getsize(file_path)

        if file_size > FILE_SIZE_THRESHOLD:
            return await self._chunked_upload(folder_id, file_path, file_size)
        else:
            return await self._normal_upload(folder_id, file_path)

    async def _normal_upload(self, folder_id: str, file_path: str) -> str:
        """Normal upload for files under 20MB."""

        async def operation() -> str:
            name = os.path.basename(file_path)
            attributes = json.dumps({"name": name, "parent": {"id": folder_id}})

            async with aiofiles.open(file_path, "rb") as f:
                file_content = await f.read()

            files: list[tuple[str, tuple[str | None, str | bytes]]] = [
                ("attributes", (None, attributes)),
                ("file", (name, file_content)),
            ]

            async with self._get_http_client() as client:
                response = await client.post(
                    "https://upload.box.com/api/2.0/files/content",
                    headers={"Authorization": f"Bearer {self._access_token}"},
                    files=files,
                )
                response.raise_for_status()
                result: dict[str, Any] = response.json()
                return str(result["entries"][0]["id"])

        return await self._with_retry(operation)

    async def _chunked_upload(
        self, folder_id: str, file_path: str, file_size: int
    ) -> str:
        """Chunked upload for files over 20MB."""
        session_id, upload_url, part_size = await self._create_upload_session(
            folder_id, file_path, file_size
        )

        parts, file_digest = await self._upload_chunks(
            upload_url, part_size, file_path, file_size
        )

        return await self._commit_session(session_id, parts, file_digest)

    async def _create_upload_session(
        self, folder_id: str, file_path: str, file_size: int
    ) -> tuple[str, str, int]:
        """Create an upload session for chunked upload."""

        async def operation() -> tuple[str, str, int]:
            name = os.path.basename(file_path)
            payload = {
                "folder_id": folder_id,
                "file_name": name,
                "file_size": file_size,
            }

            async with self._get_http_client() as client:
                response = await client.post(
                    "https://upload.box.com/api/2.0/files/upload_sessions",
                    headers={"Authorization": f"Bearer {self._access_token}"},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return (
                    data["id"],
                    data["session_endpoints"]["upload_part"],
                    data["part_size"],
                )

        return await self._with_retry(operation)

    async def _upload_chunks(
        self, upload_url: str, part_size: int, file_path: str, file_size: int
    ) -> tuple[list[UploadPart], str]:
        """Upload file in chunks."""
        parts: list[UploadPart] = []
        offset = 0
        file_hash = hashlib.sha1()

        async with aiofiles.open(file_path, "rb") as f:
            while offset < file_size:
                end = min(offset + part_size, file_size)
                chunk_size = end - offset

                await f.seek(offset)
                chunk = await f.read(chunk_size)

                file_hash.update(chunk)
                chunk_digest = base64.b64encode(hashlib.sha1(chunk).digest()).decode()

                headers = {
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(chunk_size),
                    "Digest": f"sha={chunk_digest}",
                    "Content-Range": f"bytes {offset}-{end - 1}/{file_size}",
                }

                async with self._get_http_client() as client:
                    response = await client.put(
                        upload_url,
                        headers=headers,
                        content=chunk,
                    )
                    response.raise_for_status()
                    part_data = response.json()["part"]
                    parts.append(
                        UploadPart(
                            offset=part_data["offset"],
                            part_id=part_data["part_id"],
                            sha1=part_data["sha1"],
                            size=part_data["size"],
                        )
                    )

                offset = end

        file_digest = base64.b64encode(file_hash.digest()).decode()
        return parts, file_digest

    async def _commit_session(
        self, session_id: str, parts: list[UploadPart], file_digest: str
    ) -> str:
        """Commit the upload session."""

        async def operation() -> str:
            payload = {
                "parts": [
                    {
                        "offset": p.offset,
                        "part_id": p.part_id,
                        "sha1": p.sha1,
                        "size": p.size,
                    }
                    for p in parts
                ]
            }

            async with self._get_http_client() as client:
                response = await client.post(
                    f"https://upload.box.com/api/2.0/files/upload_sessions/{session_id}/commit",
                    headers={
                        "Authorization": f"Bearer {self._access_token}",
                        "Digest": f"sha={file_digest}",
                    },
                    json=payload,
                )
                response.raise_for_status()
                return response.json()["entries"][0]["id"]

        return await self._with_retry(operation)

    # ========== FOLDER OPERATIONS ==========

    async def get_folder_info(self, folder_id: str) -> dict[str, Any]:
        """Get folder metadata."""
        await self._check_token()

        async def operation() -> dict[str, Any]:
            async with self._get_http_client() as client:
                response = await client.get(
                    f"https://api.box.com/2.0/folders/{folder_id}",
                    headers={"Authorization": f"Bearer {self._access_token}"},
                )
                response.raise_for_status()
                return response.json()

        return await self._with_retry(operation)

    async def list_folder_items(self, folder_id: str) -> dict[str, Any]:
        """List items in a folder."""
        await self._check_token()

        async def operation() -> dict[str, Any]:
            async with self._get_http_client() as client:
                response = await client.get(
                    f"https://api.box.com/2.0/folders/{folder_id}/items",
                    headers={"Authorization": f"Bearer {self._access_token}"},
                    params={"direction": "DESC"},
                )
                response.raise_for_status()
                return response.json()

        return await self._with_retry(operation)

    async def create_folder(
        self, parent_folder_id: str, name: str
    ) -> dict[str, Any]:
        """Create a new folder."""
        await self._check_token()

        async def operation() -> dict[str, Any]:
            async with self._get_http_client() as client:
                response = await client.post(
                    "https://api.box.com/2.0/folders",
                    headers={"Authorization": f"Bearer {self._access_token}"},
                    json={"name": name, "parent": {"id": parent_folder_id}},
                )
                response.raise_for_status()
                return response.json()

        return await self._with_retry(operation)

    async def search_in_folder(
        self, folder_id: str, query: str, type_: str | None = None
    ) -> list[dict[str, Any]]:
        """Search for items in a folder."""
        await self._check_token()

        async def operation() -> list[dict[str, Any]]:
            params: dict[str, str | int] = {
                "query": query,
                "content_types": "name",
                "ancestor_folder_ids": folder_id,
                "limit": 100,
            }

            if type_:
                params["type"] = type_

            async with self._get_http_client() as client:
                response = await client.get(
                    "https://api.box.com/2.0/search",
                    headers={"Authorization": f"Bearer {self._access_token}"},
                    params=params,
                )
                response.raise_for_status()
                return response.json()["entries"]

        return await self._with_retry(operation)

    # ========== SHARED LINKS ==========

    async def get_shared_link_file_id(self, link_id: str) -> str:
        """Get file ID from shared link."""
        await self._check_token()

        async def operation() -> str:
            async with self._get_http_client() as client:
                response = await client.get(
                    "https://api.box.com/2.0/shared_items",
                    headers={
                        "Authorization": f"Bearer {self._access_token}",
                        "BoxApi": f"shared_link=https://app.box.com/s/{link_id}",
                    },
                )
                response.raise_for_status()
                return response.json()["id"]

        return await self._with_retry(operation)

    async def download_from_shared_link(self, link_id: str, dest_path: str) -> None:
        """Download file from shared link."""
        await self._check_token()

        async def operation() -> None:
            file_id = await self.get_shared_link_file_id(link_id)

            async with self._get_http_client() as client, client.stream(
                "GET",
                f"https://api.box.com/2.0/files/{file_id}/content",
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "BoxApi": f"shared_link=https://app.box.com/s/{link_id}",
                },
                follow_redirects=True,
            ) as response:
                response.raise_for_status()
                async with aiofiles.open(dest_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        await f.write(chunk)

        await self._with_retry(operation)
