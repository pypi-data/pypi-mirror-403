"""
Command batching and transaction support.

Provides the `CommandBuffer` for collecting commands and the
context manager interface for batch operations.
"""

from __future__ import annotations
from contextlib import contextmanager
from threading import local
from typing import TYPE_CHECKING, Any, Generator, Optional

from .commands import AnyCommand
from .typing import CommandsResponse

if TYPE_CHECKING:
    from .client import Client


class CommandBuffer:
    """
    Buffer for collecting commands before sending to server.

    Supports two modes:
    1. Immediate mode (default): Commands are sent immediately
    2. Batch mode: Commands are buffered until flush() is called

    Usage:
        # Immediate mode (each command sent separately)
        buffer.add(AddTextBox(...))

        # Batch mode (all commands sent in one request)
        with buffer.batch():
            buffer.add(AddTextBox(...))
            buffer.add(SetText(...))
        # Commands are flushed here
    """

    def __init__(self, client: Client, deck_id: str):
        """
        Initialize the command buffer.

        Args:
            client: HTTP client for sending commands
            deck_id: ID of the deck to operate on
        """
        self._client = client
        self._deck_id = deck_id
        self._commands: list[AnyCommand] = []
        self._batch_depth = 0
        self._last_response: Optional[CommandsResponse] = None

    @property
    def is_batching(self) -> bool:
        """Return True if currently in batch mode."""
        return self._batch_depth > 0

    @property
    def pending_count(self) -> int:
        """Return the number of pending commands."""
        return len(self._commands)

    @property
    def last_response(self) -> Optional[CommandsResponse]:
        """Return the last response from the server."""
        return self._last_response

    def add(self, command: AnyCommand) -> Optional[CommandsResponse]:
        """
        Add a command to the buffer.

        In immediate mode, the command is sent right away.
        In batch mode, the command is buffered until flush().

        Args:
            command: Command to add

        Returns:
            Response if in immediate mode, None if batching
        """
        self._commands.append(command)

        if not self.is_batching:
            return self.flush()
        return None

    def flush(self) -> Optional[CommandsResponse]:
        """
        Send all buffered commands to the server.

        Returns:
            Server response, or None if no commands to send
        """
        if not self._commands:
            return None

        commands = self._commands
        self._commands = []

        self._last_response = self._client.post_commands(
            self._deck_id,
            commands,
            return_snapshot=True,
        )
        return self._last_response

    def clear(self) -> None:
        """Clear all pending commands without sending."""
        self._commands = []

    @contextmanager
    def batch(self) -> Generator[CommandBuffer, None, None]:
        """
        Context manager for batch operations.

        Commands added within this context are buffered and sent
        as a single request when the context exits.

        Example:
            with buffer.batch():
                buffer.add(AddTextBox(...))
                buffer.add(SetText(...))
            # Both commands sent here in one request

        Yields:
            self for chaining
        """
        self._batch_depth += 1
        try:
            yield self
        finally:
            self._batch_depth -= 1
            if self._batch_depth == 0:
                self.flush()


# Thread-local storage for the active batch context
_context = local()


def get_active_buffer() -> Optional[CommandBuffer]:
    """Get the currently active command buffer (if in a batch context)."""
    return getattr(_context, "buffer", None)


def set_active_buffer(buffer: Optional[CommandBuffer]) -> None:
    """Set the active command buffer for the current thread."""
    _context.buffer = buffer


@contextmanager
def batch_context(buffer: CommandBuffer) -> Generator[CommandBuffer, None, None]:
    """
    Context manager that sets the active buffer for the thread.

    This allows proxy objects to automatically use the correct buffer
    without needing explicit references.
    """
    previous = get_active_buffer()
    set_active_buffer(buffer)
    try:
        with buffer.batch():
            yield buffer
    finally:
        set_active_buffer(previous)
