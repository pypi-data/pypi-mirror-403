"""Risk calculation methods for portfolio position sizing."""

from enum import Enum


class RiskMethod(str, Enum):
    """Risk calculation method for expected loss percentage.

    Determines how expected_loss_pct is calculated from historical trade data.
    Used by EngagementContextRepository.get_batch() when building EngagementContext.

    The expected_loss_pct is used in position sizing formula:
        point_loss = entry_price * expected_loss_pct
        loss_per_lot = point_loss * trading_point_value
        target_quantity = risk_capital / loss_per_lot

    All methods calculate from the same blueprint's historical trades
    (gateway.trades WHERE blueprint_id = ? AND status = closed).
    """

    MAE_MEDIAN_2X = "MAE_MEDIAN_2X"
    """Default method. median(mae / entry_price) * 2 from last 100 trades.

    Formula: expected_loss_pct = median(mae / entry_price) * 2.0
    Sample: Last 100 closed trades of the same blueprint

    Rationale:
    - Median is robust against outliers
    - 2x multiplier provides safety buffer for unexpected volatility
    - Simple and stable, recommended for most strategies

    Example:
        If median(mae/entry) = 0.015 (1.5%), expected_loss_pct = 0.03 (3%)
    """

    MAE_PERCENTILE_90 = "MAE_PERCENTILE_90"
    """Conservative method. 90th percentile of mae / entry_price from last 100 trades.

    Formula: expected_loss_pct = percentile_90(mae / entry_price)
    Sample: Last 100 closed trades of the same blueprint

    Rationale:
    - Uses tail risk (covers 90% of historical scenarios)
    - More conservative than median, smaller position sizes
    - Recommended for risk-averse portfolios

    Example:
        If p90(mae/entry) = 0.025 (2.5%), expected_loss_pct = 0.025 (2.5%)
    """


# Default method for new portfolios
DEFAULT_RISK_METHOD = RiskMethod.MAE_MEDIAN_2X
