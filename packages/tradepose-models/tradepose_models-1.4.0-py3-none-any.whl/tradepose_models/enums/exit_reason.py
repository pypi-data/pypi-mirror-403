"""Exit reason for closed positions."""

from enum import Enum


class ExitReason(str, Enum):
    """Exit reason for closed positions."""

    STOP_LOSS = "SL"
    TAKE_PROFIT = "TP"
    MANUAL = "MANUAL"
    SIGNAL = "SIGNAL"  # Trade signal triggered exit
    UNKNOWN = "UNKNOWN"
