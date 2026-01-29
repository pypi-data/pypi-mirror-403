"""Trade persistence events for Redis Stream communication."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class TradesPersistedEvent(BaseModel):
    """Event published when trades are persisted to PostgreSQL.

    Published by Rust Worker after successful PostgreSQL write.
    Consumed by EngagementSyncConsumer for downstream processing.

    Redis Stream: trades:persisted
    """

    event_type: Literal["trades_persisted"] = Field(
        default="trades_persisted",
        description="Event type identifier",
    )
    user_id: UUID = Field(..., description="User UUID who owns the trades")
    task_id: UUID = Field(..., description="Task UUID that generated the trades")
    trades_count: int = Field(..., description="Number of trades persisted")
    strategy_names: list[str] = Field(
        default_factory=list,
        description="List of strategy names executed",
    )
    timestamp: datetime = Field(..., description="Event timestamp (ISO 8601)")
