"""
Moving Average Indicator Models

SMA, EMA, SMMA, WMA indicators aligned with Rust backend.
"""

from typing import Literal

from pydantic import BaseModel, Field


class SMAIndicator(BaseModel):
    """Simple Moving Average (SMA) 指標

    對應 Rust: Indicator::SMA { period, column }

    Args:
        period: 計算週期（必須 > 0）
        column: 計算欄位名稱（預設 "close"）

    Example:
        >>> sma = SMAIndicator(period=20)
        >>> sma = SMAIndicator(period=50, column="high")
    """

    type: Literal["SMA"] = "SMA"
    period: int = Field(gt=0, description="週期必須 > 0")
    column: str = Field(
        default="close", pattern="^(open|high|low|close|volume)$", description="OHLCV 欄位名稱"
    )


class EMAIndicator(BaseModel):
    """Exponential Moving Average (EMA) 指標

    對應 Rust: Indicator::EMA { period, column }
    """

    type: Literal["EMA"] = "EMA"
    period: int = Field(gt=0, description="週期必須 > 0")
    column: str = Field(default="close", pattern="^(open|high|low|close|volume)$")


class SMMAIndicator(BaseModel):
    """Smoothed Moving Average (SMMA) 指標

    對應 Rust: Indicator::SMMA { period, column }
    """

    type: Literal["SMMA"] = "SMMA"
    period: int = Field(gt=0, description="週期必須 > 0")
    column: str = Field(default="close", pattern="^(open|high|low|close|volume)$")


class WMAIndicator(BaseModel):
    """Weighted Moving Average (WMA) 指標

    對應 Rust: Indicator::WMA { period, column }
    """

    type: Literal["WMA"] = "WMA"
    period: int = Field(gt=0, description="週期必須 > 0")
    column: str = Field(default="close", pattern="^(open|high|low|close|volume)$")
