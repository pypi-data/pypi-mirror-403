"""
HTTP client for communicating with the PPTX Studio API.
"""

from __future__ import annotations
import os
import time
import uuid
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .errors import (
    AuthenticationError,
    ConnectionError,
    ConflictError,
    ExportError,
    RemoteError,
    RenderError,
    UploadError,
)
from .typing import (
    CommandsResponse,
    DeckSnapshot,
    ExportStatus,
    RenderStatus,
)
from .commands import AnyCommand


SDK_VERSION = "0.1.0"
SDK_CLIENT_TYPE = "python-sdk"

DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_POLL_INTERVAL = 0.5  # seconds
DEFAULT_MAX_POLL_ATTEMPTS = 30  # 30 * 0.5 = 15 seconds max wait


class Client:
    """
    HTTP client for the PPTX Studio API.

    Handles authentication, retries, and all API communication.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Initialize the client.

        Args:
            base_url: Base URL of the API (e.g., "https://api.pptx-studio.com").
                     If not provided, uses ATHENA_PPTX_BASE_URL environment variable.
            api_key: Optional API key for authentication.
                    If not provided, uses ATHENA_PPTX_API_KEY environment variable.
            timeout: Request timeout in seconds

        Raises:
            ValueError: If base_url is not provided and ATHENA_PPTX_BASE_URL is not set.
        """
        # Check environment variables if parameters not provided
        if base_url is None:
            base_url = os.environ.get("ATHENA_PPTX_BASE_URL")
            if base_url is None:
                raise ValueError(
                    "base_url must be provided or ATHENA_PPTX_BASE_URL environment variable must be set"
                )

        if api_key is None:
            api_key = os.environ.get("ATHENA_PPTX_API_KEY")

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry configuration."""
        session = requests.Session()

        # Configure retries for transient failures
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_headers(self) -> dict[str, str]:
        """Get request headers including auth if configured."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Client-Type": SDK_CLIENT_TYPE,
            "X-Client-Version": SDK_VERSION,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _handle_response(self, response: requests.Response) -> Any:
        """Handle API response, raising appropriate errors."""
        if response.status_code == 401:
            raise AuthenticationError("Invalid or expired API key")

        if response.status_code == 409:
            data = response.json() if response.text else {}
            raise ConflictError(
                data.get("message", "Conflict: resource was modified"),
                stale_ids=data.get("staleIds", []),
            )

        if not response.ok:
            try:
                data = response.json()
                raise RemoteError(
                    message=data.get("message", f"API error: {response.status_code}"),
                    status_code=response.status_code,
                    error_code=data.get("code"),
                    server_message=data.get("message"),
                )
            except ValueError:
                raise RemoteError(
                    message=f"API error: {response.status_code}",
                    status_code=response.status_code,
                )

        if response.status_code == 204 or not response.text:
            return None

        return response.json()

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> Any:
        """Make an HTTP request."""
        url = urljoin(self.base_url + "/", path.lstrip("/"))

        # Build headers - only include Content-Type when sending JSON body
        headers = self._get_headers()
        if json is None:
            # Remove Content-Type header when not sending a body
            headers.pop("Content-Type", None)

        try:
            response = self._session.request(
                method=method,
                url=url,
                json=json,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to {url}: {e}", url=url)
        except requests.Timeout as e:
            raise ConnectionError(f"Request timed out: {url}", url=url)

    def _download(self, url: str) -> bytes:
        """Download binary content from a URL."""
        try:
            response = self._session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to download from {url}: {e}", url=url)

    # -------------------------------------------------------------------------
    # Deck operations
    # -------------------------------------------------------------------------

    def get_deck(self, deck_id: str) -> dict[str, Any]:
        """Get deck metadata."""
        return self._request("GET", f"/decks/{deck_id}")

    def list_decks(self, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        """List all decks."""
        return self._request("GET", "/decks", params={"limit": limit, "offset": offset})

    def create_deck(self, name: Optional[str] = None) -> dict[str, Any]:
        """
        Create a new deck, returns upload URL and deck ID.

        Args:
            name: Optional name for the deck

        Returns:
            Dictionary with id, name, status, uploadUrl, createdAt
        """
        payload = {"name": name} if name else None
        return self._request("POST", "/decks", json=payload)

    def create_empty_deck(self, name: Optional[str] = None) -> dict[str, Any]:
        """
        Create a new empty deck that's immediately ready.

        Unlike create_deck(), this creates a deck without requiring an upload.
        The deck is immediately usable with no slides.

        Args:
            name: Optional name for the deck

        Returns:
            Dictionary with id, name, status, slideCount, createdAt
        """
        payload = {"name": name} if name else None
        return self._request("POST", "/decks/empty", json=payload)

    def delete_deck(self, deck_id: str) -> None:
        """Delete a deck."""
        self._request("DELETE", f"/decks/{deck_id}")

    def upload_file(
        self,
        file_path: str,
        name: Optional[str] = None,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        max_attempts: int = DEFAULT_MAX_POLL_ATTEMPTS,
    ) -> str:
        """
        Upload a PPTX file and wait for processing to complete.

        This is the main entry point for uploading files. It handles:
        1. Creating a new deck
        2. Uploading the file to the presigned URL
        3. Notifying the server that upload is complete
        4. Polling until ingest is finished

        Args:
            file_path: Path to the PPTX file to upload
            name: Optional name for the presentation (defaults to filename)
            poll_interval: Seconds between status polls
            max_attempts: Maximum number of poll attempts

        Returns:
            The deck ID of the uploaded presentation

        Raises:
            UploadError: If upload or processing fails
            FileNotFoundError: If the file doesn't exist
        """
        import os

        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Use filename as name if not provided
        if name is None:
            name = os.path.basename(file_path)
            # Remove extension
            if name.endswith('.pptx') or name.endswith('.potx'):
                name = name[:-5]

        # Step 1: Create deck to get presigned URL
        deck_info = self.create_deck(name)
        deck_id = deck_info["id"]
        upload_url = deck_info.get("uploadUrl")

        if not upload_url:
            raise UploadError("Server did not return upload URL", deck_id)

        # Step 2: Upload file to presigned URL
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()

            response = self._session.put(
                upload_url,
                data=file_data,
                headers={
                    "Content-Type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                },
                timeout=120,  # Longer timeout for uploads
            )
            response.raise_for_status()
        except Exception as e:
            raise UploadError(f"Failed to upload file: {e}", deck_id)

        # Step 3: Notify server that upload is complete
        try:
            self._request("POST", f"/decks/{deck_id}/upload-complete")
        except Exception as e:
            raise UploadError(f"Failed to notify upload complete: {e}", deck_id)

        # Step 4: Poll for processing to complete
        for _ in range(max_attempts):
            deck = self.get_deck(deck_id)
            status = deck.get("status")

            if status == "ready":
                return deck_id

            if status == "error":
                raise UploadError("Processing failed", deck_id)

            time.sleep(poll_interval)

        raise UploadError("Processing timed out", deck_id)

    def upload_file_async(
        self,
        file_path: str,
        name: Optional[str] = None,
    ) -> str:
        """
        Upload a PPTX file without waiting for processing.

        Use this when you want to start the upload and check status later.
        Call get_deck() to check when status becomes "ready".

        Args:
            file_path: Path to the PPTX file to upload
            name: Optional name for the presentation

        Returns:
            The deck ID (status will be "processing")

        Raises:
            UploadError: If upload fails
            FileNotFoundError: If the file doesn't exist
        """
        import os

        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Use filename as name if not provided
        if name is None:
            name = os.path.basename(file_path)
            if name.endswith('.pptx') or name.endswith('.potx'):
                name = name[:-5]

        # Step 1: Create deck to get presigned URL
        deck_info = self.create_deck(name)
        deck_id = deck_info["id"]
        upload_url = deck_info.get("uploadUrl")

        if not upload_url:
            raise UploadError("Server did not return upload URL", deck_id)

        # Step 2: Upload file to presigned URL
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()

            response = self._session.put(
                upload_url,
                data=file_data,
                headers={
                    "Content-Type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                },
                timeout=120,
            )
            response.raise_for_status()
        except Exception as e:
            raise UploadError(f"Failed to upload file: {e}", deck_id)

        # Step 3: Notify server that upload is complete
        try:
            self._request("POST", f"/decks/{deck_id}/upload-complete")
        except Exception as e:
            raise UploadError(f"Failed to notify upload complete: {e}", deck_id)

        return deck_id

    # -------------------------------------------------------------------------
    # Commands
    # -------------------------------------------------------------------------

    def post_commands(
        self,
        deck_id: str,
        commands: list[AnyCommand],
        return_snapshot: bool = True,
    ) -> CommandsResponse:
        """
        Send commands to apply to a deck.

        Args:
            deck_id: ID of the deck to modify
            commands: List of commands to apply
            return_snapshot: Whether to return updated snapshot

        Returns:
            Response with applied status, created IDs, and optional snapshot
        """
        # Validate all commands
        for cmd in commands:
            cmd.validate()

        payload = {
            "client": {"type": SDK_CLIENT_TYPE, "version": SDK_VERSION},
            "txn": {"id": str(uuid.uuid4()), "mode": "atomic"},
            "commands": [cmd.to_dict() for cmd in commands],
            "return": {"snapshot": return_snapshot},
        }

        return self._request("POST", f"/decks/{deck_id}/commands", json=payload)

    # -------------------------------------------------------------------------
    # Snapshot
    # -------------------------------------------------------------------------

    def get_snapshot(self, deck_id: str) -> DeckSnapshot:
        """Get the current state snapshot of a deck."""
        data = self._request("GET", f"/decks/{deck_id}/snapshot")
        return self._parse_snapshot(data)

    def _parse_snapshot(self, data: dict[str, Any]) -> DeckSnapshot:
        """Parse raw snapshot data into typed objects."""
        from .typing import DeckSnapshot, SlideSnapshot, ElementSnapshot, Transform

        slides = []
        for slide_data in data.get("slides", []):
            slides.append(
                SlideSnapshot(
                    id=slide_data["id"],
                    index=slide_data["index"],
                    element_ids=slide_data.get("elementIds", []),
                    background_color_hex=slide_data.get("backgroundColorHex"),
                    notes=slide_data.get("notes"),
                    layout_path=slide_data.get("layoutPath"),
                )
            )

        elements = {}
        for elem_id, elem_data in data.get("elements", {}).items():
            transform_data = elem_data.get("transform", {})
            elements[elem_id] = ElementSnapshot(
                id=elem_data["id"],
                type=elem_data["type"],
                slide_id=elem_data["slideId"],
                transform=Transform(
                    x=transform_data.get("x", 0),
                    y=transform_data.get("y", 0),
                    w=transform_data.get("w", 0),
                    h=transform_data.get("h", 0),
                    rot=transform_data.get("rot"),
                    flipH=transform_data.get("flipH"),
                    flipV=transform_data.get("flipV"),
                ),
                preview_text=elem_data.get("previewText"),
                properties=elem_data.get("properties"),
            )

        return DeckSnapshot(
            deck_id=data["deckId"],
            name=data.get("name", "Untitled"),
            slide_width_emu=data.get("slideWidthEmu", 9144000),
            slide_height_emu=data.get("slideHeightEmu", 6858000),
            slide_count=data.get("slideCount", len(slides)),
            slides=slides,
            elements=elements,
        )

    # -------------------------------------------------------------------------
    # Export
    # -------------------------------------------------------------------------

    def start_export(self, deck_id: str) -> str:
        """
        Start an export job.

        Returns:
            Job ID for polling status
        """
        result = self._request("POST", f"/decks/{deck_id}/export")
        return result["jobId"]

    def get_export_status(self, deck_id: str, job_id: str) -> ExportStatus:
        """Get the status of an export job."""
        return self._request("GET", f"/decks/{deck_id}/export/{job_id}")

    def export_and_download(
        self,
        deck_id: str,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        max_attempts: int = DEFAULT_MAX_POLL_ATTEMPTS,
    ) -> bytes:
        """
        Start export, poll for completion, and download the file.

        Args:
            deck_id: ID of the deck to export
            poll_interval: Seconds between status polls
            max_attempts: Maximum number of poll attempts

        Returns:
            PPTX file bytes
        """
        job_id = self.start_export(deck_id)

        for _ in range(max_attempts):
            status = self.get_export_status(deck_id, job_id)

            if status["status"] == "completed":
                download_url = status.get("downloadUrl")
                if not download_url:
                    raise ExportError("Export completed but no download URL", job_id)
                return self._download(download_url)

            if status["status"] in ("failed", "error"):
                raise ExportError(
                    status.get("error", "Export failed"), job_id
                )

            time.sleep(poll_interval)

        raise ExportError("Export timed out", job_id)

    # -------------------------------------------------------------------------
    # Render
    # -------------------------------------------------------------------------

    def start_render(self, deck_id: str, slide_index: int, scale: int = 2) -> str:
        """
        Start a render job for a slide.

        Args:
            deck_id: ID of the deck
            slide_index: Zero-based slide index (internally converted to 1-indexed for API)
            scale: Render scale factor (default 2x)

        Returns:
            Job ID for polling status
        """
        # API uses 1-indexed slide numbers in URLs
        slide_number = slide_index + 1
        result = self._request(
            "POST",
            f"/decks/{deck_id}/render/{slide_number}",
            params={"scale": scale},
        )
        return result["jobId"]

    def get_render_status(self, deck_id: str, job_id: str) -> RenderStatus:
        """Get the status of a render job."""
        return self._request("GET", f"/decks/{deck_id}/render/{job_id}/status")

    def render_slide(
        self,
        deck_id: str,
        slide_index: int,
        scale: int = 2,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        max_attempts: int = DEFAULT_MAX_POLL_ATTEMPTS,
    ) -> bytes:
        """
        Render a slide and download the PNG.

        Args:
            deck_id: ID of the deck
            slide_index: Zero-based slide index
            scale: Render scale factor
            poll_interval: Seconds between status polls
            max_attempts: Maximum number of poll attempts

        Returns:
            PNG image bytes
        """
        job_id = self.start_render(deck_id, slide_index, scale)

        for _ in range(max_attempts):
            status = self.get_render_status(deck_id, job_id)

            if status["status"] == "completed":
                image_url = status.get("imageUrl")
                if not image_url:
                    raise RenderError("Render completed but no image URL", job_id)
                return self._download(image_url)

            if status["status"] in ("failed", "error"):
                raise RenderError(
                    status.get("error", "Render failed"), job_id
                )

            time.sleep(poll_interval)

        raise RenderError("Render timed out", job_id)

    def render_slide_sync(
        self,
        deck_id: str,
        slide_index: int,
        scale: int = 2,
    ) -> bytes:
        """
        Synchronously render a slide (for development/testing).

        This endpoint may not be available in production.

        Args:
            deck_id: ID of the deck
            slide_index: Zero-based slide index (internally converted to 1-indexed for API)
            scale: Render scale factor

        Returns:
            PNG image bytes
        """
        # API uses 1-indexed slide numbers in URLs
        slide_number = slide_index + 1
        url = f"{self.base_url}/decks/{deck_id}/slides/{slide_number}/png"
        try:
            response = self._session.get(
                url,
                params={"scale": scale},
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            raise RenderError(f"Sync render failed: {e}")

    # -------------------------------------------------------------------------
    # Connection info
    # -------------------------------------------------------------------------

    def get_connection_info(self, deck_id: str) -> dict[str, str]:
        """
        Get yhub WebSocket connection info for real-time collaboration.

        Returns:
            Dictionary with wsUrl and authToken
        """
        return self._request("GET", f"/decks/{deck_id}/connection")
