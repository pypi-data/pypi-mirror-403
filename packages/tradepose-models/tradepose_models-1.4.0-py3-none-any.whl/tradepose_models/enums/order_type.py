"""Order type enumeration."""

from enum import StrEnum


class OrderType(StrEnum):
    """Order execution mechanism (HOW the order executes).

    Describes the execution mechanism, not the strategy purpose.
    Use OrderStrategy to describe WHY the order exists (entry, stop loss, etc.).

    Immediate Execution:
        MARKET: Market order - immediate fill at best available price
        LIMIT: Limit order - fill at specified price or better

    Server-side Conditional Trigger:
        STOP: Stop order - triggers market order when price reaches stop level
        STOP_LIMIT: Stop-limit order - triggers limit order when price reaches stop level

    Local Detection Trigger:
        LOCAL_STOP: Local detection triggers market order
        LOCAL_STOP_LIMIT: Local detection triggers limit order
    """

    # Immediate execution
    MARKET = "market"
    LIMIT = "limit"

    # Server-side conditional trigger
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

    # Local detection trigger
    LOCAL_STOP = "local_stop"
    LOCAL_STOP_LIMIT = "local_stop_limit"
