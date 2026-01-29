"""Singleton Box class with factory method pattern."""

from __future__ import annotations

from .box_api import BoxAPI
from .box_drive import BoxDrive
from .box_fs import BoxFS
from .types import BoxConfig


class Box(BoxFS):
    """
    Singleton Box class with factory method pattern.

    This is the main entry point for using fs-box-sync.
    Use the global `box` instance or call `get_box()` to get the singleton.
    """

    _instance: Box | None = None
    _initialized: bool = False

    def __new__(cls, config: BoxConfig | None = None) -> Box:
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, config: BoxConfig | None = None) -> None:
        if not Box._initialized:
            self._api = BoxAPI(config)
            self._drive = BoxDrive(self._api, config)
            Box._initialized = True

    def configure(self, config: BoxConfig) -> None:
        """
        Configure the singleton instance.

        Args:
            config: BoxConfig with authentication and settings

        Example:
            from fs_box_sync import box, BoxConfig

            box.configure(BoxConfig(
                client_id='your-client-id',
                client_secret='your-client-secret',
            ))
        """
        self._api.apply_config(config)
        self._drive = BoxDrive(self._api, config)


def get_box() -> Box:
    """
    Get the singleton Box instance.

    Returns:
        The global Box singleton instance
    """
    return Box()
