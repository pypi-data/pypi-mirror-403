from typing import Any, Dict, Optional


class FabricError(Exception):
    """Base exception for FabRest SDK errors."""


class ValidationError(ValueError, FabricError):
    """Invalid input or parameters."""


class AuthenticationError(FabricError):
    """Authentication or token errors."""


class HttpError(FabricError):
    """HTTP error response wrapper."""

    def __init__(
        self,
        status_code: int,
        message: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}


class ThrottledError(HttpError):
    """HTTP 429 throttling error."""


class LongRunningOperationError(HttpError):
    """Long-running operation failure."""
