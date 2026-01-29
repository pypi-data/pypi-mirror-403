"""
Momentum Indicator Models

RSI, CCI, and Stochastic indicators aligned with Rust backend.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class RSIIndicator(BaseModel):
    """Relative Strength Index (RSI) 指標

    對應 Rust: Indicator::RSI { period, column }

    Returns:
        單一數值欄位（0-100 範圍）
    """

    type: Literal["RSI"] = "RSI"
    period: int = Field(default=14, gt=0, description="週期必須 > 0")
    column: str = Field(default="close", pattern="^(open|high|low|close|volume)$")


class CCIIndicator(BaseModel):
    """Commodity Channel Index (CCI) 指標

    對應 Rust: Indicator::CCI { period }

    Returns:
        單一數值欄位
    """

    type: Literal["CCI"] = "CCI"
    period: int = Field(default=20, gt=0, description="週期必須 > 0")


class StochasticIndicator(BaseModel):
    """Stochastic Oscillator 指標

    對應 Rust: Indicator::Stochastic { k_period, d_period, fields }

    Returns:
        Struct { k: f64, d: f64 }
    """

    type: Literal["Stochastic"] = "Stochastic"
    k_period: int = Field(default=14, gt=0, description="%K 週期必須 > 0")
    d_period: int = Field(default=3, gt=0, description="%D 週期（平滑）必須 > 0")
    fields: Optional[List[str]] = Field(
        default=None, description="Select specific fields: ['k', 'd']"
    )
