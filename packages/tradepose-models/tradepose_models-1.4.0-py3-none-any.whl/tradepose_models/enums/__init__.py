"""
Enumerations for TradePose platform

All enums are aligned with Rust backend types for JSON serialization.
"""

from .account_source import AccountSource
from .action_type import ActionType
from .broker_type import BrokerType
from .currency import Currency
from .engagement_phase import EngagementPhase
from .execution_mode import ExecutionMode
from .exit_reason import ExitReason
from .export_type import ExportType
from .fill_type import FillType
from .freq import Freq
from .indicator_type import IndicatorType
from .operation_type import OperationType
from .order_side import OrderSide
from .order_status import OrderStatus
from .order_strategy import OrderStrategy
from .order_type import OrderType
from .orderbook_event_type import OrderbookEventType
from .persist_mode import PersistMode
from .reject_reason import RejectReason
from .risk_method import DEFAULT_RISK_METHOD, RiskMethod
from .stream import RedisStream
from .task_status import TaskStatus
from .time_in_force import TimeInForce
from .trade_direction import TradeDirection
from .trend_type import TrendType
from .weekday import Weekday
from .write_origin import WriteOrigin

# Backwards compatibility alias (deprecated, use BrokerType instead)
Platform = BrokerType

__all__ = [
    "AccountSource",
    "ActionType",
    "BrokerType",
    "Currency",
    "EngagementPhase",
    "ExecutionMode",
    "ExitReason",
    "ExportType",
    "FillType",
    "Freq",
    "IndicatorType",
    "OperationType",
    "OrderSide",
    "OrderStatus",
    "OrderStrategy",
    "OrderType",
    "OrderbookEventType",
    "PersistMode",
    "Platform",  # Deprecated alias for BrokerType
    "RejectReason",
    "RiskMethod",
    "DEFAULT_RISK_METHOD",
    "RedisStream",
    "TaskStatus",
    "TimeInForce",
    "TradeDirection",
    "TrendType",
    "Weekday",
    "WriteOrigin",
]
