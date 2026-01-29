"""
Orderbook Model

Provides the OrderbookEntry model for event sourcing of order lifecycle.
Each event in the order lifecycle is recorded as a separate entry.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ..enums import OrderbookEventType, OrderStrategy, WriteOrigin
from .orders import OrderSide, OrderStatus, OrderType


class OrderbookEntry(BaseModel):
    """Orderbook event entry (Event Sourcing).

    Records each event in the order lifecycle for audit and tracking.
    Each order state change creates a new entry (immutable log).

    Event Types:
    - ORDER_CREATED (0): Order submitted to broker
    - ORDER_MODIFIED (1): Order modified (price, quantity)
    - ORDER_CANCELLED (2): Order cancelled
    - PARTIAL_FILL (3): Order partially filled
    - FULLY_FILLED (4): Order fully filled
    - REJECTED (5): Order rejected by broker
    """

    id: UUID = Field(..., description="Entry UUID (primary key)")
    user_id: UUID = Field(..., description="User UUID")
    engagement_id: Optional[UUID] = Field(
        None, description="Engagement UUID (FK), None for external/unassociated orders"
    )

    event_type: OrderbookEventType = Field(..., description="Event type (SMALLINT: 0-5)")

    # Order details
    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="Order side (BUY/SELL)")
    order_type: OrderType = Field(
        ..., description="Order execution mechanism (market, limit, stop)"
    )
    order_strategy: Optional[OrderStrategy] = Field(
        None,
        description="Strategy purpose (WHY): ImmediateEntry, StopLoss, TakeProfit, etc.",
    )
    quantity: Decimal = Field(..., description="Order quantity")
    filled_quantity: Decimal = Field(
        default=Decimal("0"), description="Filled quantity (for partial fills)"
    )
    price: Optional[Decimal] = Field(None, description="Order price (for limit orders)")
    filled_price: Optional[Decimal] = Field(None, description="Average filled price")

    # Broker tracking
    broker_order_id: str | None = Field(
        None,
        description="Broker's order ID. None for open position sync (updated by deal sync).",
    )
    broker_position_id: str | None = Field(
        None,
        description="Broker's position ID for correlation (e.g., MT5 position ticket)",
    )
    status: OrderStatus = Field(..., description="Order status")

    # Record metadata
    write_origin: Optional[WriteOrigin] = Field(
        None,
        description="Record source: server_sync, callback, execute",
    )

    # Fee fields
    swap: Optional[Decimal] = Field(None, description="Overnight swap fee")
    commission: Optional[Decimal] = Field(None, description="Trading commission")
    tax: Optional[Decimal] = Field(None, description="Tax fee")

    # Timestamps
    created_at: datetime = Field(..., description="Event timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    broker_time: Optional[datetime] = Field(
        None,
        description="Broker server timestamp (UTC). Source: MT5 Position.time_msc, Deal.time_msc. "
        "NULL for events without server time (ORDER_CREATED, ORDER_MODIFIED, REJECTED).",
    )

    raw_data: dict = Field(default_factory=dict, description="Broker raw response (JSONB)")

    @property
    def is_filled(self) -> bool:
        """Check if order is fully filled."""
        return self.event_type == OrderbookEventType.FULLY_FILLED

    @property
    def is_partial(self) -> bool:
        """Check if order is partially filled."""
        return self.event_type == OrderbookEventType.PARTIAL_FILL

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity."""
        return self.quantity - self.filled_quantity

    @property
    def is_entry(self) -> bool:
        """Check if this is an entry order based on order_strategy."""
        if self.order_strategy is None:
            return False
        return self.order_strategy in {
            OrderStrategy.IMMEDIATE_ENTRY,
            OrderStrategy.FAVORABLE_DELAY_ENTRY,
            OrderStrategy.ADVERSE_DELAY_ENTRY,
        }

    @property
    def is_exit(self) -> bool:
        """Check if this is an exit order based on order_strategy."""
        if self.order_strategy is None:
            return False
        return self.order_strategy in {
            OrderStrategy.IMMEDIATE_EXIT,
            OrderStrategy.STOP_LOSS,
            OrderStrategy.TAKE_PROFIT,
            OrderStrategy.TRAILING_STOP,
            OrderStrategy.BREAKEVEN,
            OrderStrategy.TIMEOUT_EXIT,
        }
