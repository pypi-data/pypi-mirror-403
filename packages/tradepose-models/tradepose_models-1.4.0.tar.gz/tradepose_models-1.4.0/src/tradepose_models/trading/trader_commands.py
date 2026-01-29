"""Trader command models for Redis Stream communication.

Pydantic models for trader commands published to Redis Streams:
- SyncBrokerStatusCommand: Request broker status sync
- SyncEngagementsCommand: Sync engagements after Worker persists trades

Stream pattern: trader:commands:{user_id}:{node_seq}:{slot_idx}
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class BaseTraderCommand(BaseModel):
    """Base class for all trader commands."""

    timestamp: datetime = Field(
        ...,
        description="Command creation timestamp (UTC)",
    )


class SyncBrokerStatusCommand(BaseTraderCommand):
    """Command to request broker status synchronization."""

    command_type: Literal["sync_broker_status"] = Field(
        default="sync_broker_status",
        description="Command type identifier",
    )
    account_id: UUID = Field(
        ...,
        description="Trading account UUID to sync",
    )


class SyncEngagementsCommand(BaseTraderCommand):
    """Command to sync engagements after Worker persists trades.

    Published by EngagementSyncJob when new trades are persisted.
    Trader queries PostgreSQL for full engagement context using the IDs.
    """

    command_type: Literal["sync_engagements"] = Field(
        default="sync_engagements",
        description="Command type identifier",
    )
    account_id: UUID = Field(
        ...,
        description="Trading account UUID",
    )
    engagement_ids: list[UUID] = Field(
        ...,
        description="List of engagement UUIDs to sync (10-1000 items typical)",
        min_length=1,
    )
