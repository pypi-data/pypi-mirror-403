"""Order info models for broker sync.

Models for representing order information from broker state synchronization.
These convert external broker order data to internal representation.

Design principle: Each order model represents an ATOMIC order - one entry, one SL,
or one TP. If a broker supports placing orders with bundled SL/TP (like MT5),
the adapter should parse the response into separate atomic order models.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from tradepose_models.enums import (
    FillType,
    OrderSide,
    OrderStatus,
    OrderStrategy,
    OrderType,
    RejectReason,
)


class PendingOrderInfo(BaseModel):
    """Pending order information for broker sync.

    Represents a single unfilled order on the broker.
    Each order is atomic - entry orders, SL orders, and TP orders
    are represented as separate instances.
    """

    broker_order_id: str = Field(..., description="Broker order identifier")
    broker_position_id: str | None = Field(None, description="Related broker position ID")
    engagement_id: UUID | None = Field(None, description="Related engagement UUID")
    symbol: str = Field(..., description="Symbol name")
    side: OrderSide = Field(..., description="Order side")
    order_type: OrderType = Field(..., description="Order execution mechanism")
    order_strategy: OrderStrategy | None = Field(None, description="Strategy purpose (WHY)")
    quantity: Decimal = Field(..., description="Order quantity")
    price: Decimal = Field(..., description="Order price")
    created_at: datetime = Field(..., description="Order creation time")
    status: OrderStatus = Field(..., description="Order status")
    raw_data: dict[str, Any] = Field(default_factory=dict, description="Broker-specific data")


class FilledOrderInfo(BaseModel):
    """Filled order information for broker sync.

    Contains execution details for a filled order.
    """

    broker_order_id: str = Field(..., description="Broker order identifier")
    broker_position_id: str = Field(..., description="Related broker position ID")
    engagement_id: UUID | None = Field(None, description="Related engagement UUID")
    symbol: str = Field(..., description="Symbol name")
    side: OrderSide = Field(..., description="Order side")
    order_type: OrderType = Field(..., description="Order execution mechanism")
    order_strategy: OrderStrategy | None = Field(None, description="Strategy purpose (WHY)")
    filled_price: Decimal = Field(..., description="Average fill price")
    filled_quantity: Decimal = Field(..., description="Filled quantity")
    fill_type: FillType = Field(..., description="Fill type (FULL/PARTIAL)")
    fill_time: datetime = Field(..., description="Fill time")
    swap: Decimal | None = Field(None, description="Overnight swap fee")
    commission: Decimal | None = Field(None, description="Trading commission")
    tax: Decimal | None = Field(None, description="Tax fee")
    raw_data: dict[str, Any] = Field(default_factory=dict, description="Broker-specific data")


class CancelledOrderInfo(BaseModel):
    """Cancelled order information for broker sync.

    Contains details about a cancelled pending order.
    """

    broker_order_id: str = Field(..., description="Broker order identifier")
    broker_position_id: str | None = Field(None, description="Related broker position ID")
    engagement_id: UUID | None = Field(None, description="Related engagement UUID")
    symbol: str = Field(..., description="Symbol name")
    side: OrderSide = Field(..., description="Order side")
    order_type: OrderType = Field(..., description="Order execution mechanism")
    order_strategy: OrderStrategy | None = Field(None, description="Strategy purpose (WHY)")
    quantity: Decimal = Field(..., description="Order quantity")
    price: Decimal | None = Field(None, description="Order price")
    cancelled_at: datetime = Field(..., description="Cancellation time")
    raw_data: dict[str, Any] = Field(default_factory=dict, description="Broker-specific data")


class RejectedOrderInfo(BaseModel):
    """Rejected order information for broker sync.

    Contains details about a rejected order.
    """

    broker_order_id: str | None = Field(None, description="Broker order identifier")
    broker_position_id: str | None = Field(None, description="Related broker position ID")
    engagement_id: UUID | None = Field(None, description="Related engagement UUID")
    symbol: str = Field(..., description="Symbol name")
    side: OrderSide = Field(..., description="Order side")
    order_type: OrderType = Field(..., description="Order execution mechanism")
    order_strategy: OrderStrategy | None = Field(None, description="Strategy purpose (WHY)")
    quantity: Decimal = Field(..., description="Order quantity")
    price: Decimal | None = Field(None, description="Order price")
    reject_reason: RejectReason = Field(..., description="Rejection reason")
    reject_message: str = Field(default="", description="Rejection message from broker")
    rejected_at: datetime = Field(..., description="Rejection time")
    raw_data: dict[str, Any] = Field(default_factory=dict, description="Broker-specific data")
