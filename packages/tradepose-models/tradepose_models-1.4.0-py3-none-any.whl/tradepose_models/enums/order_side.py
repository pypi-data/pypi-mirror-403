"""Order side enumeration."""

from enum import StrEnum


class OrderSide(StrEnum):
    """Order side (buy/sell)."""

    BUY = "buy"
    SELL = "sell"
