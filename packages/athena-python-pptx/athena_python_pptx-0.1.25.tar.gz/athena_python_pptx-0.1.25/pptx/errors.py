"""
Exception types for the PPTX SDK.
"""

from __future__ import annotations
from typing import Any, Optional


class PptxSdkError(Exception):
    """Base exception for all SDK errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class UnsupportedFeatureError(PptxSdkError):
    """
    Raised when an unsupported python-pptx feature is accessed.

    athena-python-pptx maintains API compatibility with python-pptx but
    not all features are implemented yet. This exception clearly indicates
    what isn't available and may suggest alternatives.

    Examples:
        # When accessing charts (not yet supported)
        UnsupportedFeatureError(
            "shapes.add_chart",
            "Adding charts is not yet supported. Consider using add_picture() "
            "with a chart image instead."
        )
    """

    def __init__(self, feature: str, message: Optional[str] = None):
        if message:
            full_message = f"[{feature}] {message}"
        else:
            full_message = (
                f"Feature '{feature}' is not yet implemented in athena-python-pptx. "
                f"See https://github.com/pptx-studio/athena-python-pptx for supported features."
            )
        super().__init__(full_message, {"feature": feature})
        self.feature = feature

    def __str__(self) -> str:
        return self.message


class RemoteError(PptxSdkError):
    """
    Raised when the server rejects a command or returns an error.

    Includes the HTTP status code and error details from the server.
    """

    def __init__(
        self,
        message: str,
        status_code: int,
        error_code: Optional[str] = None,
        server_message: Optional[str] = None,
    ):
        super().__init__(
            message,
            {
                "status_code": status_code,
                "error_code": error_code,
                "server_message": server_message,
            },
        )
        self.status_code = status_code
        self.error_code = error_code
        self.server_message = server_message


class ConflictError(PptxSdkError):
    """
    Raised when a command references stale or invalid IDs.

    This can happen when:
    - A shape was deleted by another collaborator
    - A slide index is out of bounds
    - An element ID doesn't exist
    """

    def __init__(self, message: str, stale_ids: Optional[list[str]] = None):
        super().__init__(message, {"stale_ids": stale_ids})
        self.stale_ids = stale_ids or []


class ValidationError(PptxSdkError):
    """
    Raised when command validation fails.

    This is a client-side error that occurs before sending to the server.
    """

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, {"field": field})
        self.field = field


class ConnectionError(PptxSdkError):
    """
    Raised when unable to connect to the server.
    """

    def __init__(self, message: str, url: Optional[str] = None):
        super().__init__(message, {"url": url})
        self.url = url


class AuthenticationError(PptxSdkError):
    """
    Raised when authentication fails.
    """

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class ExportError(PptxSdkError):
    """
    Raised when export fails.
    """

    def __init__(self, message: str, job_id: Optional[str] = None):
        super().__init__(message, {"job_id": job_id})
        self.job_id = job_id


class RenderError(PptxSdkError):
    """
    Raised when rendering fails.
    """

    def __init__(self, message: str, job_id: Optional[str] = None):
        super().__init__(message, {"job_id": job_id})
        self.job_id = job_id


class UploadError(PptxSdkError):
    """
    Raised when file upload fails.
    """

    def __init__(self, message: str, deck_id: Optional[str] = None):
        super().__init__(message, {"deck_id": deck_id})
        self.deck_id = deck_id
