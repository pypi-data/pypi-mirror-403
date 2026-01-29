"""
Blueprint Model

Provides the Blueprint class for strategy blueprints with entry/exit triggers.
"""

from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from ..enums import OrderStrategy, TradeDirection, TrendType
from .trigger import Trigger


class Blueprint(BaseModel):
    """策略藍圖"""

    id: Optional[UUID] = Field(None, description="藍圖 ID（由資料庫自動填充）")
    name: str = Field(..., description="藍圖名稱")
    direction: TradeDirection = Field(..., description="方向")
    trend_type: TrendType = Field(..., description="趨勢類型")
    entry_first: bool = Field(..., description="是否優先進場")
    note: str = Field(default="", description="備註")

    entry_triggers: List[Trigger] = Field(..., description="進場觸發器列表")
    exit_triggers: List[Trigger] = Field(..., description="出場觸發器列表")

    @field_validator("direction", mode="before")
    @classmethod
    def convert_direction(cls, v: Any) -> TradeDirection:
        """自動轉換字串為 TradeDirection enum（case-insensitive）"""
        if isinstance(v, str):
            try:
                # Handle case-insensitive input (e.g., "LONG" → "Long")
                return TradeDirection(v.capitalize())
            except ValueError:
                valid_values = [e.value for e in TradeDirection]
                raise ValueError(
                    f"Invalid direction: '{v}'. Valid values: {', '.join(valid_values)}"
                )
        return v

    @field_validator("trend_type", mode="before")
    @classmethod
    def convert_trend_type(cls, v: Any) -> TrendType:
        """自動轉換字串為 TrendType enum（case-insensitive）"""
        if isinstance(v, str):
            try:
                # Handle case-insensitive input (e.g., "TREND" → "Trend")
                return TrendType(v.capitalize())
            except ValueError:
                valid_values = [e.value for e in TrendType]
                raise ValueError(
                    f"Invalid trend_type: '{v}'. Valid values: {', '.join(valid_values)}"
                )
        return v

    @model_validator(mode="after")
    def validate_entry_trigger_types(self) -> "Blueprint":
        """確保 entry triggers 只有 Favorable 或 Adverse 其中一種

        Entry triggers 設計上只允許使用 FavorableDelayEntry 或 AdverseDelayEntry
        其中一種，不能同時混用。這是因為 hypothetical entry price 的計算需要
        在兩種策略中選擇一種作為 fallback。
        """
        entry_strategies = [t.order_strategy for t in self.entry_triggers]

        has_favorable = OrderStrategy.FAVORABLE_DELAY_ENTRY in entry_strategies
        has_adverse = OrderStrategy.ADVERSE_DELAY_ENTRY in entry_strategies

        if has_favorable and has_adverse:
            raise ValueError(
                "Entry triggers cannot have both FavorableDelayEntry and AdverseDelayEntry. "
                "Please use only one type of delay entry strategy."
            )
        return self
