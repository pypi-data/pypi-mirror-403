"""
Engagement Model

Dynamic trade execution state linked to an EngagementConfig.
Tracks the lifecycle of a trade from signal to completion.

9-Phase lifecycle:
    PENDING(0) → ENTERING(1) → HOLDING(2) → EXITING(3) → CLOSED(4)
                     │                           │
                     ▼                           ▼
                 FAILED(5)                 EXIT_FAILED(7)

    CANCELLED(6) - Signal cancelled before execution
    EXPIRED(8)   - Trade closed before entry could be executed
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ..enums import EngagementPhase


class Engagement(BaseModel):
    """Dynamic trade execution state.

    Links to EngagementConfig for static configuration.
    One engagement per (config_id, trade_id) combination.

    Unique constraint: (config_id, trade_id)
    """

    id: UUID = Field(..., description="Engagement UUID (primary key)")
    config_id: UUID = Field(..., description="EngagementConfig UUID")
    trade_id: UUID = Field(..., description="Trade UUID")

    # Entry time from trade (for ordering)
    entry_time: datetime = Field(..., description="Trade entry time for ordering")

    # Position sizing
    target_quantity: Optional[Decimal] = Field(
        None, description="Calculated position size based on MAE formula"
    )

    # Phase system (8 states)
    phase: EngagementPhase = Field(
        default=EngagementPhase.PENDING,
        description="Engagement phase (0-7)",
    )

    # Fill tracking
    filled_entry_qty: Decimal = Field(
        default=Decimal("0"), description="Quantity filled for entry order"
    )
    filled_exit_qty: Decimal = Field(
        default=Decimal("0"), description="Quantity filled for exit order"
    )
    filled_entry_avg_price: Optional[Decimal] = Field(
        None, description="Average fill price for entry orders"
    )
    filled_exit_avg_price: Optional[Decimal] = Field(
        None, description="Average fill price for exit orders"
    )

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Phase helper properties
    @property
    def is_pending_phase(self) -> bool:
        """Check if engagement is in PENDING phase."""
        return self.phase == EngagementPhase.PENDING

    @property
    def is_entering_phase(self) -> bool:
        """Check if engagement is in ENTERING phase."""
        return self.phase == EngagementPhase.ENTERING

    @property
    def is_holding_phase(self) -> bool:
        """Check if engagement is in HOLDING phase (position open)."""
        return self.phase == EngagementPhase.HOLDING

    @property
    def is_exiting_phase(self) -> bool:
        """Check if engagement is in EXITING phase."""
        return self.phase == EngagementPhase.EXITING

    @property
    def is_closed_phase(self) -> bool:
        """Check if engagement is in CLOSED phase."""
        return self.phase == EngagementPhase.CLOSED

    @property
    def is_failed_phase(self) -> bool:
        """Check if engagement is in FAILED phase."""
        return self.phase == EngagementPhase.FAILED

    @property
    def is_cancelled_phase(self) -> bool:
        """Check if engagement is in CANCELLED phase."""
        return self.phase == EngagementPhase.CANCELLED

    @property
    def is_exit_failed_phase(self) -> bool:
        """Check if engagement is in EXIT_FAILED phase."""
        return self.phase == EngagementPhase.EXIT_FAILED

    @property
    def is_expired_phase(self) -> bool:
        """Check if engagement is in EXPIRED phase."""
        return self.phase == EngagementPhase.EXPIRED

    @property
    def is_terminal(self) -> bool:
        """Check if engagement is in a terminal state (no more transitions)."""
        return self.phase in (
            EngagementPhase.CLOSED,
            EngagementPhase.FAILED,
            EngagementPhase.CANCELLED,
            EngagementPhase.EXPIRED,
        )

    @property
    def needs_intervention(self) -> bool:
        """Check if engagement needs manual intervention."""
        return self.phase == EngagementPhase.EXIT_FAILED


class EngagementWithConfig(BaseModel):
    """Engagement with expanded config fields for API responses."""

    # Engagement fields
    id: UUID
    config_id: UUID
    trade_id: UUID
    entry_time: datetime
    target_quantity: Optional[Decimal] = None
    phase: EngagementPhase = EngagementPhase.PENDING
    filled_entry_qty: Decimal = Decimal("0")
    filled_exit_qty: Decimal = Decimal("0")
    filled_entry_avg_price: Optional[Decimal] = None
    filled_exit_avg_price: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    # Expanded config fields
    user_id: UUID
    account_id: UUID
    binding_id: UUID
    portfolio_id: UUID
    strategy_id: UUID
    blueprint_id: UUID
    portfolio_allocation_id: Optional[UUID] = None
    trading_instrument_id: Optional[int] = None
    symbol: Optional[str] = None
