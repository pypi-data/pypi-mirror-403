"""
Volatility Indicator Models

ATR and ATRQuantile indicators aligned with Rust backend.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ATRIndicator(BaseModel):
    """Average True Range (ATR) 指標

    對應 Rust: Indicator::ATR { period }

    Returns:
        單一數值欄位（不是 struct）

    Example:
        >>> atr = ATRIndicator(period=14)
        >>> atr = ATRIndicator(period=21)
    """

    type: Literal["ATR"] = "ATR"
    period: int = Field(gt=0, description="週期必須 > 0")


class ATRQuantileIndicator(BaseModel):
    """ATR Rolling Quantile 指標

    對應 Rust: Indicator::AtrQuantile { atr_column, window, quantile }

    計算 ATR 的滾動分位數，用於動態止損等場景。

    注意：這是依賴指標，必須先定義 ATR 指標。

    Args:
        atr_column: 引用的 ATR 列名（如 "ATR|14"）
        window: 滾動窗口大小
        quantile: 分位數值 (0, 1)，0.5 表示中位數

    Returns:
        單一數值欄位（不是 struct）

    Example:
        >>> atr_q = ATRQuantileIndicator(
        ...     atr_column="ATR|21",
        ...     window=40,
        ...     quantile=0.75  # 75th percentile
        ... )
    """

    type: Literal["AtrQuantile"] = "AtrQuantile"
    atr_column: str = Field(min_length=1, description="引用的 ATR 欄位名稱")
    window: int = Field(gt=0, description="滾動窗口大小必須 > 0")
    quantile: float = Field(gt=0, lt=1, description="分位數值 (0, 1)")
