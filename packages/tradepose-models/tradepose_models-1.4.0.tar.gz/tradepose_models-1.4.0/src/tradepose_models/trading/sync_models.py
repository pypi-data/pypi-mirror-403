"""Sync Broker Models.

Generic models for synchronizing broker state with local orderbook.
Broker-agnostic - specific implementations use raw_data for broker details.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from tradepose_models.enums import AccountSource, BrokerType

from .orders import (
    CancelledOrderInfo,
    FilledOrderInfo,
    PendingOrderInfo,
    RejectedOrderInfo,
)
from .positions import ClosedPosition, Position


class SyncStateResult(BaseModel):
    """Result of sync_state() operation.

    Contains current broker state and recent changes.
    All entries have engagement_id=None - the service layer uses
    broker_position_id to correlate with local orderbook entries.
    """

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(), description="Sync timestamp"
    )

    # Current state (snapshot)
    open_positions: list[Position] = Field(
        default_factory=list, description="Currently open positions"
    )
    pending_orders: list[PendingOrderInfo] = Field(
        default_factory=list, description="Pending orders"
    )

    # Changes detected (since `sync_from`)
    closed_positions: list[ClosedPosition] = Field(
        default_factory=list, description="Recently closed positions"
    )
    filled_orders: list[FilledOrderInfo] = Field(
        default_factory=list, description="Recently filled orders"
    )
    cancelled_orders: list[CancelledOrderInfo] = Field(
        default_factory=list, description="Recently cancelled orders"
    )
    rejected_orders: list[RejectedOrderInfo] = Field(
        default_factory=list, description="Recently rejected orders"
    )

    # Metadata
    user_id: UUID | str | None = Field(None, description="User ID")
    account_id: UUID | str | None = Field(None, description="Account ID")
    account_source: AccountSource | None = Field(
        None, description="Account source for broker timezone"
    )
    broker_type: BrokerType | None = Field(None, description="Broker type")
    sync_from: datetime | None = Field(None, description="Sync start time")
    sync_to: datetime | None = Field(None, description="Sync end time")

    @property
    def has_changes(self) -> bool:
        """Check if any changes were detected."""
        return bool(
            self.closed_positions
            or self.filled_orders
            or self.cancelled_orders
            or self.rejected_orders
        )

    @property
    def total_changes(self) -> int:
        """Count total number of changes."""
        return (
            len(self.closed_positions)
            + len(self.filled_orders)
            + len(self.cancelled_orders)
            + len(self.rejected_orders)
        )
