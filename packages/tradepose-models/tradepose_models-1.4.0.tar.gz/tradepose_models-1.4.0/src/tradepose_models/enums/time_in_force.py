"""Time in force enumeration."""

from enum import StrEnum


class TimeInForce(StrEnum):
    """Time in force for orders."""

    GTC = "gtc"  # Good Till Cancel
    IOC = "ioc"  # Immediate or Cancel
    FOK = "fok"  # Fill or Kill
