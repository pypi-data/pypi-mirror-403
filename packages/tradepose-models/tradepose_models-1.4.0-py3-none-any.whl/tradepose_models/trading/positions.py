"""Position models."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from tradepose_models.enums import ExitReason, TradeDirection


class Position(BaseModel):
    """Unified open position model.

    Represents a currently open position on the broker.
    Used for broker sync state conversion.
    """

    # Core identifiers (required)
    broker_position_id: str = Field(..., description="Broker position identifier")
    symbol: str = Field(..., description="Unified symbol")
    direction: TradeDirection = Field(..., description="Position direction")

    # Position details (required)
    quantity: Decimal = Field(..., description="Position quantity")
    entry_price: Decimal = Field(..., description="Average entry price")
    current_price: Decimal = Field(..., description="Current market price")
    unrealized_pnl: Decimal = Field(..., description="Unrealized P&L")
    opened_at: datetime = Field(..., description="Position open time")

    # Risk management (optional)
    stop_loss: Decimal | None = Field(None, description="Stop loss price")
    take_profit: Decimal | None = Field(None, description="Take profit price")

    # Costs (optional, filled by adapter)
    swap: Decimal | None = Field(None, description="Overnight swap fee")
    commission: Decimal | None = Field(None, description="Trading commission")
    tax: Decimal | None = Field(None, description="Tax fee")
    realized_pnl: Decimal = Field(default=Decimal("0"), description="Realized P&L (partial closes)")

    # Broker-specific (optional)
    broker_symbol: str | None = Field(None, description="Broker-specific symbol")

    # Margin info (optional)
    margin_used: Decimal | None = Field(None, description="Margin used")
    leverage: Decimal | None = Field(None, description="Leverage")

    # MT5-specific (optional)
    magic: int | None = Field(None, description="MT5 magic number")
    comment: str | None = Field(None, description="MT5 comment")

    # Raw broker data
    raw_data: dict[str, Any] = Field(default_factory=dict, description="Broker-specific raw data")


class ClosedPosition(BaseModel):
    """Closed position with entry/exit details.

    Contains full lifecycle info for a closed position.
    Used for broker sync state conversion.
    """

    # Core identifiers (required)
    broker_position_id: str = Field(..., description="Broker position identifier")
    symbol: str = Field(..., description="Unified symbol")
    direction: TradeDirection = Field(..., description="Position direction")

    # Position details (required)
    quantity: Decimal = Field(..., description="Position quantity")
    entry_price: Decimal = Field(..., description="Entry price")
    exit_price: Decimal = Field(..., description="Exit price")
    exit_reason: ExitReason = Field(..., description="Exit reason (SL/TP/MANUAL/UNKNOWN)")
    realized_pnl: Decimal = Field(..., description="Realized profit/loss")
    exit_time: datetime = Field(..., description="Exit time")

    # Costs (optional, filled by adapter)
    swap: Decimal | None = Field(None, description="Overnight swap fee")
    commission: Decimal | None = Field(None, description="Trading commission")
    tax: Decimal | None = Field(None, description="Tax fee")

    # Timestamps (optional for entry)
    entry_time: datetime | None = Field(None, description="Entry time")

    # Broker-specific (optional)
    broker_symbol: str | None = Field(None, description="Broker-specific symbol")

    # Raw broker data
    raw_data: dict[str, Any] = Field(default_factory=dict, description="Broker-specific raw data")
