"""Export API request/response models."""

from uuid import UUID

from pydantic import BaseModel, Field

from tradepose_models.enums.export_type import ExportType
from tradepose_models.enums.persist_mode import PersistMode
from tradepose_models.strategy import StrategyConfig


class ExportRequest(BaseModel):
    """Worker-compatible export request model.

    This model matches the Gateway's requirements and generates events
    compatible with Worker's BacktestTaskEvent format.

    Required:
    - strategy_configs: Complete StrategyConfig objects (self-contained)
    - export_type: ExportType enum

    Optional (nested in backtest_request):
    - start_date, end_date, strategy_ids
    - strategy_name, blueprint_name (for enhanced-ohlcv)
    - base_instrument, base_freq, indicator_specs (for on-demand-ohlcv)
    - persist_mode: Where to store results (REDIS or PSQL)
    """

    # Required: Complete StrategyConfig objects (Pydantic models)
    strategy_configs: list[StrategyConfig] = Field(
        ..., description="List of complete StrategyConfig objects"
    )

    # Export type (using enum)
    export_type: ExportType = Field(
        ...,
        description="Export type: BACKTEST_RESULTS, LATEST_TRADES, ENHANCED_OHLCV, ON_DEMAND_OHLCV",
    )

    # Persistence mode (default: REDIS only)
    persist_mode: PersistMode = Field(
        default=PersistMode.REDIS,
        description="Where to persist results: REDIS (default) or PSQL (dual-write to PostgreSQL)",
    )

    # BacktestRequest fields (nested in worker event)
    start_date: str | None = Field(default=None, description="Start date ISO 8601 format")
    end_date: str | None = Field(default=None, description="End date ISO 8601 format")
    strategy_ids: list[str] | None = Field(
        default=None, description="Strategy IDs to execute (None = all)"
    )

    # For EnhancedOhlcv
    strategy_name: str | None = Field(
        default=None, description="Strategy name (for enhanced-ohlcv)"
    )
    blueprint_name: str | None = Field(
        default=None, description="Blueprint name (for enhanced-ohlcv)"
    )

    # For OnDemandOhlcv
    base_instrument: str | None = Field(
        default=None, description="Instrument ID for on-demand OHLCV"
    )
    base_freq: str | None = Field(default=None, description="Base frequency for on-demand OHLCV")
    indicator_specs: list[dict] | None = Field(
        default=None, description="Indicator specifications for on-demand OHLCV"
    )

    # For LatestTrades
    trade_count: int | None = Field(
        default=None,
        ge=1,
        description="Number of latest trades per (strategy, blueprint) to write (LatestTrades only, default: 2)",
    )


class ExportResponse(BaseModel):
    """Response model for export task creation."""

    task_id: UUID
    message: str
    operation_type: str
