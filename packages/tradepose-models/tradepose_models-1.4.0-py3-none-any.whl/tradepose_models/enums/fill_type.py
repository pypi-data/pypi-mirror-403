"""Fill type for order execution."""

from enum import Enum


class FillType(str, Enum):
    """Fill type for order execution."""

    FULL = "FULL"
    PARTIAL = "PARTIAL"
