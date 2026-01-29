"""
Other Indicator Models

Bollinger Bands and RawOhlcv indicators aligned with Rust backend.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class BollingerBandsIndicator(BaseModel):
    """Bollinger Bands 指標

    對應 Rust: Indicator::BollingerBands { period, num_std, column, fields }

    Returns:
        Struct { upper: f64, middle: f64, lower: f64, bandwidth: f64 }
    """

    type: Literal["BollingerBands"] = "BollingerBands"
    period: int = Field(default=20, gt=0, description="週期必須 > 0")
    num_std: float = Field(default=2.0, gt=0, description="標準差倍數必須 > 0")
    column: str = Field(default="close", pattern="^(open|high|low|close|volume)$")
    fields: Optional[List[str]] = Field(
        default=None,
        description="Select specific fields: ['upper', 'middle', 'lower', 'bandwidth']",
    )


class RawOhlcvIndicator(BaseModel):
    """Raw OHLCV Column 指標

    對應 Rust: Indicator::RawOhlcv { column }

    直接引用 OHLCV 列，用於需要原始資料的場景。
    """

    type: Literal["RawOhlcv"] = "RawOhlcv"
    column: str = Field(pattern="^(open|high|low|close|volume)$")
