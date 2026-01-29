"""
EngagementConfig Model

Static engagement configuration representing a user's trading setup.
Links user → account → binding → portfolio → strategy → blueprint.

One config per unique (user, account, binding, portfolio, strategy, blueprint) combination.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EngagementConfig(BaseModel):
    """Static engagement configuration.

    Represents the binding between a user's trading setup and a strategy/blueprint.
    Created via sync_engagement_configs() SQL function.

    Unique constraint: (user_id, account_id, binding_id, portfolio_id, strategy_id, blueprint_id)
    """

    id: UUID = Field(..., description="Config UUID (primary key)")
    user_id: UUID = Field(..., description="User UUID")
    account_id: UUID = Field(..., description="Trading account UUID")
    binding_id: UUID = Field(..., description="Account-Portfolio binding UUID")
    portfolio_id: UUID = Field(..., description="Portfolio UUID")
    strategy_id: UUID = Field(..., description="Strategy UUID")
    blueprint_id: UUID = Field(..., description="Blueprint UUID")

    # Optional references
    portfolio_allocation_id: Optional[UUID] = Field(
        None, description="Portfolio allocation UUID (SET NULL on delete)"
    )

    # Trading instrument mapping
    trading_instrument_id: Optional[int] = Field(None, description="Mapped trading instrument ID")
    symbol: Optional[str] = Field(None, description="Trading symbol for the mapped instrument")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class EngagementConfigSyncResult(BaseModel):
    """Result from sync_engagement_configs() SQL function."""

    config_id: UUID = Field(..., description="Config UUID")
    account_id: UUID = Field(..., description="Account UUID")
    binding_id: UUID = Field(..., description="Binding UUID")
    portfolio_id: UUID = Field(..., description="Portfolio UUID")
    strategy_id: UUID = Field(..., description="Strategy UUID")
    blueprint_id: UUID = Field(..., description="Blueprint UUID")
    is_new: bool = Field(..., description="True if config was newly created")
