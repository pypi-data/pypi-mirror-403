"""
Order strategy enumeration
"""

from enum import Enum


class OrderStrategy(str, Enum):
    """
    Order strategy enum (aligned with Rust OrderStrategy enum)

    Used to specify the execution strategy for entry/exit triggers.

    Rust mapping:
    - Rust: OrderStrategy::ImmediateEntry      → Python: OrderStrategy.IMMEDIATE_ENTRY      (u32: 0)
    - Rust: OrderStrategy::FavorableDelayEntry → Python: OrderStrategy.FAVORABLE_DELAY_ENTRY (u32: 1)
    - Rust: OrderStrategy::AdverseDelayEntry   → Python: OrderStrategy.ADVERSE_DELAY_ENTRY   (u32: 2)
    - Rust: OrderStrategy::ImmediateExit       → Python: OrderStrategy.IMMEDIATE_EXIT        (u32: 3)
    - Rust: OrderStrategy::StopLoss            → Python: OrderStrategy.STOP_LOSS             (u32: 4)
    - Rust: OrderStrategy::TakeProfit          → Python: OrderStrategy.TAKE_PROFIT           (u32: 5)
    - Rust: OrderStrategy::TrailingStop        → Python: OrderStrategy.TRAILING_STOP         (u32: 6)
    - Rust: OrderStrategy::Breakeven           → Python: OrderStrategy.BREAKEVEN             (u32: 7)
    - Rust: OrderStrategy::TimeoutExit         → Python: OrderStrategy.TIMEOUT_EXIT          (u32: 8)

    Entry Strategies:
        IMMEDIATE_ENTRY: Immediate entry on signal (required for Base Blueprint)
        FAVORABLE_DELAY_ENTRY: Wait for favorable price (pullback/retracement)
        ADVERSE_DELAY_ENTRY: Wait for breakout/aggressive entry

    Exit Strategies:
        IMMEDIATE_EXIT: Immediate exit on signal (required for Base Blueprint)
        STOP_LOSS: Fixed stop loss
        TAKE_PROFIT: Fixed take profit
        TRAILING_STOP: Dynamic trailing stop
        BREAKEVEN: Move stop to breakeven after profit
        TIMEOUT_EXIT: Exit after time limit
    """

    IMMEDIATE_ENTRY = "ImmediateEntry"
    FAVORABLE_DELAY_ENTRY = "FavorableDelayEntry"
    ADVERSE_DELAY_ENTRY = "AdverseDelayEntry"
    IMMEDIATE_EXIT = "ImmediateExit"
    STOP_LOSS = "StopLoss"
    TAKE_PROFIT = "TakeProfit"
    TRAILING_STOP = "TrailingStop"
    BREAKEVEN = "Breakeven"
    TIMEOUT_EXIT = "TimeoutExit"

    def to_int(self) -> int:
        """Convert to Rust-compatible integer value."""
        return _STRATEGY_TO_INT[self]

    @classmethod
    def from_int(cls, value: int) -> "OrderStrategy":
        """Create from Rust integer value.

        Args:
            value: Integer value (0-8)

        Returns:
            Corresponding OrderStrategy enum

        Raises:
            ValueError: If value is not a valid OrderStrategy integer
        """
        if value not in _INT_TO_STRATEGY:
            raise ValueError(f"Invalid OrderStrategy integer: {value}")
        return _INT_TO_STRATEGY[value]

    @classmethod
    def from_int_or_default(cls, value: int | None, default: "OrderStrategy") -> "OrderStrategy":
        """Create from Rust integer value with fallback default.

        Args:
            value: Integer value (0-8) or None
            default: Default value if value is None or invalid

        Returns:
            Corresponding OrderStrategy enum or default
        """
        if value is None:
            return default
        return _INT_TO_STRATEGY.get(value, default)


# Mapping tables (defined after class to reference enum members)
_STRATEGY_TO_INT: dict["OrderStrategy", int] = {
    OrderStrategy.IMMEDIATE_ENTRY: 0,
    OrderStrategy.FAVORABLE_DELAY_ENTRY: 1,
    OrderStrategy.ADVERSE_DELAY_ENTRY: 2,
    OrderStrategy.IMMEDIATE_EXIT: 3,
    OrderStrategy.STOP_LOSS: 4,
    OrderStrategy.TAKE_PROFIT: 5,
    OrderStrategy.TRAILING_STOP: 6,
    OrderStrategy.BREAKEVEN: 7,
    OrderStrategy.TIMEOUT_EXIT: 8,
}

_INT_TO_STRATEGY: dict[int, "OrderStrategy"] = {v: k for k, v in _STRATEGY_TO_INT.items()}
