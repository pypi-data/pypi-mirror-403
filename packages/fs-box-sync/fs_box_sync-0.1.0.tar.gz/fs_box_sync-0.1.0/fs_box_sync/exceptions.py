"""Custom exception classes for fs-box-sync."""


class BoxError(Exception):
    """Base exception for Box API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class BoxAuthenticationError(BoxError):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class BoxNotFoundError(BoxError):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class BoxConflictError(BoxError):
    """Conflict (e.g., item already exists)."""

    def __init__(self, message: str = "Conflict"):
        super().__init__(message, status_code=409)


class BoxPermissionError(BoxError):
    """Permission denied."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status_code=403)


class BoxDriveNotAvailableError(BoxError):
    """Box Drive is not available."""

    def __init__(self, message: str = "Box Drive is not available"):
        super().__init__(message)


class BoxSyncTimeoutError(BoxError):
    """Sync timeout exceeded."""

    def __init__(self, message: str = "Sync timeout exceeded"):
        super().__init__(message)


class BoxCredentialsError(BoxError):
    """Missing or invalid credentials."""

    def __init__(self, message: str = "Missing or invalid credentials"):
        super().__init__(message)


class BoxTokenProviderError(BoxError):
    """Token provider not configured or failed."""

    def __init__(self, message: str = "Token provider not configured"):
        super().__init__(message)
