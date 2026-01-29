"""Order status enumeration."""

from enum import StrEnum


class OrderStatus(StrEnum):
    """Order status."""

    PENDING_NEW = "pending_new"
    NEW = "new"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"
