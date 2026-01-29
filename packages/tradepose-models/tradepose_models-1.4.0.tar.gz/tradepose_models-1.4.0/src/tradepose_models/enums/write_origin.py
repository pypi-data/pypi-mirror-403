"""Write origin for orderbook entries."""

from enum import StrEnum


class WriteOrigin(StrEnum):
    """Tracks the source of orderbook record creation."""

    SERVER_SYNC = "server_sync"  # Queried from broker server
    CALLBACK = "callback"  # Received from broker callback
    EXECUTE = "execute"  # Execute order request/response
