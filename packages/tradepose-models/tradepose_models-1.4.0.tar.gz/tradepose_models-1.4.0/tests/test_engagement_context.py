"""Tests for EngagementContext model and ActionType enum."""

from decimal import Decimal
from uuid import uuid4

import pytest
from tradepose_models.enums import (
    ActionType,
    EngagementPhase,
    OrderSide,
    OrderStatus,
    OrderStrategy,
    TradeDirection,
)
from tradepose_models.trading import (
    EngagementContext,
    ExitReason,
)


class TestActionType:
    """Tests for ActionType enum."""

    def test_action_type_values(self):
        """Test ActionType enum has all expected values."""
        # Entry actions
        assert ActionType.MARKET_ENTRY == "MARKET_ENTRY"
        assert ActionType.LIMIT_ENTRY == "LIMIT_ENTRY"
        # Position actions
        assert ActionType.CLOSE_POSITION == "CLOSE_POSITION"
        assert ActionType.MODIFY_POSITION == "MODIFY_POSITION"
        # Order actions
        assert ActionType.MODIFY_ORDER == "MODIFY_ORDER"
        assert ActionType.CANCEL_ORDER == "CANCEL_ORDER"
        # No action
        assert ActionType.NONE == "NONE"

    def test_action_type_is_string_enum(self):
        """Test ActionType is a string enum for JSON serialization."""
        assert isinstance(ActionType.MARKET_ENTRY.value, str)
        assert ActionType.MARKET_ENTRY.value == "MARKET_ENTRY"


class TestEngagementContext:
    """Tests for EngagementContext model."""

    @pytest.fixture
    def base_context(self):
        """Create a base context for testing with all fields."""
        return EngagementContext(
            # ============================================================
            # 1. IDENTITY & RELATIONS
            # ============================================================
            engagement_id=uuid4(),
            config_id=uuid4(),
            trade_id=uuid4(),
            user_id=uuid4(),
            account_id=uuid4(),
            portfolio_id=uuid4(),
            # ============================================================
            # 2. STRATEGY METADATA
            # ============================================================
            strategy_name="Test Strategy",
            blueprint_name="Test Blueprint",
            # ============================================================
            # 3. INSTRUMENT SPECIFICATIONS
            # ============================================================
            symbol="EUR-USD",
            trading_symbol="EURUSD",
            trading_point_value=Decimal("100000"),
            price_precision=5,
            quantity_precision=2,
            # ============================================================
            # 4. PORTFOLIO & CAPITAL
            # ============================================================
            capital=Decimal("10000"),
            capital_currency="USD",
            capital_override=None,
            num_allocations=1,
            # ============================================================
            # 5. TRADE STATE
            # ============================================================
            direction=TradeDirection.LONG,
            trade_status=True,  # Open
            entry_price=Decimal("1.1000"),
            exit_price=None,
            mae=Decimal("50"),
            order_strategy=None,  # Default: IMMEDIATE_ENTRY
            entry_volatility=None,
            # ============================================================
            # 6. ENGAGEMENT LIFECYCLE
            # ============================================================
            phase=EngagementPhase.PENDING,
            target_quantity=Decimal("0.1"),
            # ============================================================
            # 7. BROKER STATE
            # ============================================================
            entry_broker_order_id=None,
            entry_status=None,
            entry_filled_qty=Decimal("0"),
            entry_avg_price=None,
            sl_broker_order_id=None,
            current_sl=None,
            tp_broker_order_id=None,
            current_tp=None,
            broker_position_id=None,
            current_entry_order_price=None,
            # ============================================================
            # 8. RISK CONTROL
            # ============================================================
            expected_loss_pct=None,
            historical_trade_count=0,
            risk_padding_pct=None,
        )

    def test_side_property_long(self, base_context):
        """Test side property for long direction."""
        assert base_context.side == OrderSide.BUY
        assert base_context.exit_side == OrderSide.SELL

    def test_side_property_short(self, base_context):
        """Test side property for short direction."""
        base_context.direction = TradeDirection.SHORT
        assert base_context.side == OrderSide.SELL
        assert base_context.exit_side == OrderSide.BUY

    def test_is_terminal_false(self, base_context):
        """Test is_terminal for non-terminal phase."""
        assert base_context.is_terminal is False

    def test_is_terminal_true(self, base_context):
        """Test is_terminal for terminal phases."""
        for phase in [
            EngagementPhase.CLOSED,
            EngagementPhase.FAILED,
            EngagementPhase.CANCELLED,
            EngagementPhase.EXPIRED,
        ]:
            base_context.phase = phase
            assert base_context.is_terminal is True

    def test_needs_entry_pending_open(self, base_context):
        """Test needs_entry for PENDING + trade open."""
        base_context.phase = EngagementPhase.PENDING
        base_context.trade_status = True
        assert base_context.needs_entry is True

    def test_needs_entry_pending_closed(self, base_context):
        """Test needs_entry for PENDING + trade closed."""
        base_context.phase = EngagementPhase.PENDING
        base_context.trade_status = False
        assert base_context.needs_entry is False

    def test_needs_exit_holding_closed(self, base_context):
        """Test needs_exit for HOLDING + trade closed."""
        base_context.phase = EngagementPhase.HOLDING
        base_context.trade_status = False
        assert base_context.needs_exit is True

    def test_needs_exit_holding_open(self, base_context):
        """Test needs_exit for HOLDING + trade open."""
        base_context.phase = EngagementPhase.HOLDING
        base_context.trade_status = True
        assert base_context.needs_exit is False

    def test_is_expired_pending_closed(self, base_context):
        """Test is_expired for PENDING + trade closed."""
        base_context.phase = EngagementPhase.PENDING
        base_context.trade_status = False
        assert base_context.is_expired is True

    # ==================== needs_modify tests ====================

    def test_needs_modify_holding_with_sl_change(self, base_context):
        """Test needs_modify when SL differs significantly from effective."""
        base_context.phase = EngagementPhase.HOLDING
        base_context.trade_status = True
        base_context.current_sl = Decimal("1.0900")
        base_context.adverse_exit_hypo_price = Decimal(
            "1.0950"
        )  # ~0.46% difference, > 0.1% tolerance
        assert base_context.needs_modify is True

    def test_needs_modify_holding_with_tp_change(self, base_context):
        """Test needs_modify when TP differs significantly from effective."""
        base_context.phase = EngagementPhase.HOLDING
        base_context.trade_status = True
        base_context.current_tp = Decimal("1.1100")
        base_context.favorable_exit_hypo_price = Decimal(
            "1.1200"
        )  # ~0.9% difference, > 0.1% tolerance
        assert base_context.needs_modify is True

    def test_needs_modify_holding_no_change(self, base_context):
        """Test needs_modify when SL/TP match effective exactly."""
        base_context.phase = EngagementPhase.HOLDING
        base_context.trade_status = True
        base_context.current_sl = Decimal("1.0900")
        base_context.adverse_exit_hypo_price = Decimal("1.0900")  # Same
        base_context.current_tp = Decimal("1.1100")
        base_context.favorable_exit_hypo_price = Decimal("1.1100")  # Same
        assert base_context.needs_modify is False

    def test_needs_modify_within_tolerance_returns_false(self, base_context):
        """Test needs_modify returns False when prices are within 0.1% tolerance.

        This handles spread adjustment: executor adjusts SL/TP by spread before
        sending to broker, so orderbook records adjusted prices while effective
        prices are theoretical (without spread).
        """
        base_context.phase = EngagementPhase.HOLDING
        base_context.trade_status = True
        # adverse_exit_hypo_price = 25245.38 (theoretical)
        # current_sl = 25245.37566 (adjusted, ~0.00002% diff, well within 0.1%)
        base_context.adverse_exit_hypo_price = Decimal("25245.38")
        base_context.current_sl = Decimal("25245.37566")
        base_context.favorable_exit_hypo_price = Decimal("25457.42")
        base_context.current_tp = Decimal("25457.41585")
        assert base_context.needs_modify is False

    def test_needs_modify_spread_adjustment_scenario(self, base_context):
        """Test needs_modify handles typical spread adjustment scenario.

        Production scenario:
        - hypo_price (effective) = 25245.38
        - adjusted_price (current) = 25245.38 - spread = 25245.37566
        - Difference is within tolerance, should NOT trigger re-modify
        """
        base_context.phase = EngagementPhase.HOLDING
        base_context.trade_status = True
        # Simulating US100.cash with ~5 point spread
        base_context.adverse_exit_hypo_price = Decimal("25004.22")
        base_context.current_sl = Decimal("25004.17")  # adjusted by spread
        base_context.favorable_exit_hypo_price = Decimal("25185.19")
        base_context.current_tp = Decimal("25185.24")  # adjusted by spread
        assert base_context.needs_modify is False

    def test_needs_modify_no_effective_values(self, base_context):
        """Test needs_modify when no effective values."""
        base_context.phase = EngagementPhase.HOLDING
        base_context.trade_status = True
        base_context.adverse_exit_hypo_price = None
        base_context.favorable_exit_hypo_price = None
        assert base_context.needs_modify is False

    def test_needs_modify_effective_but_no_current(self, base_context):
        """Test needs_modify returns True when effective exists but current is None."""
        base_context.phase = EngagementPhase.HOLDING
        base_context.trade_status = True
        base_context.adverse_exit_hypo_price = Decimal("1.0900")
        base_context.current_sl = None  # Not yet set
        assert base_context.needs_modify is True

    def test_needs_modify_not_holding(self, base_context):
        """Test needs_modify returns False when not in HOLDING phase."""
        base_context.phase = EngagementPhase.PENDING
        base_context.trade_status = True
        base_context.adverse_exit_hypo_price = Decimal("1.0950")
        assert base_context.needs_modify is False

    def test_needs_modify_trade_closed(self, base_context):
        """Test needs_modify returns False when trade is closed."""
        base_context.phase = EngagementPhase.HOLDING
        base_context.trade_status = False  # Closed
        base_context.adverse_exit_hypo_price = Decimal("1.0950")
        assert base_context.needs_modify is False

    # ==================== _is_price_within_tolerance tests ====================

    def test_is_price_within_tolerance_suggested_none(self, base_context):
        """Test _is_price_within_tolerance returns True when suggested is None."""
        result = base_context._is_price_within_tolerance(None, Decimal("1.0900"))
        assert result is True

    def test_is_price_within_tolerance_current_none(self, base_context):
        """Test _is_price_within_tolerance returns False when current is None."""
        result = base_context._is_price_within_tolerance(Decimal("1.0900"), None)
        assert result is False

    def test_is_price_within_tolerance_exact_match(self, base_context):
        """Test _is_price_within_tolerance returns True for exact match."""
        result = base_context._is_price_within_tolerance(Decimal("1.0900"), Decimal("1.0900"))
        assert result is True

    def test_is_price_within_tolerance_within_range(self, base_context):
        """Test _is_price_within_tolerance returns True when within 0.1% tolerance."""
        suggested = Decimal("25245.38")
        # 0.1% of 25245.38 = 25.24538
        # Difference = 0.00434, well within tolerance
        current = Decimal("25245.37566")
        result = base_context._is_price_within_tolerance(suggested, current)
        assert result is True

    def test_is_price_within_tolerance_outside_range(self, base_context):
        """Test _is_price_within_tolerance returns False when outside 0.1% tolerance."""
        suggested = Decimal("1.0900")
        # 0.1% of 1.0900 = 0.00109
        # Difference = 0.05 = 4.6%, way outside tolerance
        current = Decimal("1.0950")
        result = base_context._is_price_within_tolerance(suggested, current)
        assert result is False

    def test_is_price_within_tolerance_boundary(self, base_context):
        """Test _is_price_within_tolerance at exact boundary."""
        suggested = Decimal("10000")
        # 0.1% of 10000 = 10
        # Exactly at boundary should be within tolerance (<=)
        current = Decimal("10010")
        result = base_context._is_price_within_tolerance(suggested, current)
        assert result is True

        # Just outside boundary
        current = Decimal("10010.01")
        result = base_context._is_price_within_tolerance(suggested, current)
        assert result is False

    # ==================== determine_action tests ====================

    def test_determine_action_terminal_returns_none(self, base_context):
        """Test that terminal phases return NONE."""
        for phase in [
            EngagementPhase.CLOSED,
            EngagementPhase.FAILED,
            EngagementPhase.CANCELLED,
            EngagementPhase.EXPIRED,
        ]:
            base_context.phase = phase
            assert base_context.determine_action() == ActionType.NONE

    def test_determine_action_pending_open_immediate_returns_market_entry(self, base_context):
        """Test PENDING + trade open + IMMEDIATE_ENTRY returns MARKET_ENTRY."""
        base_context.phase = EngagementPhase.PENDING
        base_context.trade_status = True
        base_context.entry_reason = 0  # IMMEDIATE_ENTRY
        assert base_context.determine_action() == ActionType.MARKET_ENTRY

    def test_determine_action_pending_open_favorable_returns_limit_entry(self, base_context):
        """Test PENDING + trade open + FAVORABLE_DELAY_ENTRY returns LIMIT_ENTRY."""
        base_context.phase = EngagementPhase.PENDING
        base_context.trade_status = True
        base_context.entry_reason = 1  # FAVORABLE_DELAY_ENTRY
        assert base_context.determine_action() == ActionType.LIMIT_ENTRY

    def test_determine_action_pending_open_adverse_returns_limit_entry(self, base_context):
        """Test PENDING + trade open + ADVERSE_DELAY_ENTRY returns LIMIT_ENTRY."""
        base_context.phase = EngagementPhase.PENDING
        base_context.trade_status = True
        base_context.entry_reason = 2  # ADVERSE_DELAY_ENTRY
        assert base_context.determine_action() == ActionType.LIMIT_ENTRY

    def test_determine_action_pending_closed_returns_none(self, base_context):
        """Test PENDING + trade closed returns NONE (should mark EXPIRED)."""
        base_context.phase = EngagementPhase.PENDING
        base_context.trade_status = False
        assert base_context.determine_action() == ActionType.NONE

    def test_determine_action_holding_closed_returns_close_position(self, base_context):
        """Test HOLDING + trade closed returns CLOSE_POSITION."""
        base_context.phase = EngagementPhase.HOLDING
        base_context.trade_status = False
        base_context.entry_filled_qty = Decimal("0.1")
        base_context.broker_position_id = "12345"
        assert base_context.determine_action() == ActionType.CLOSE_POSITION

    def test_determine_action_holding_open_no_modify_returns_none(self, base_context):
        """Test HOLDING + trade open + no SL/TP change returns NONE."""
        base_context.phase = EngagementPhase.HOLDING
        base_context.trade_status = True
        base_context.adverse_exit_hypo_price = None
        base_context.favorable_exit_hypo_price = None
        assert base_context.determine_action() == ActionType.NONE

    def test_determine_action_holding_open_with_modify_returns_modify_position(self, base_context):
        """Test HOLDING + trade open + SL/TP change returns MODIFY_POSITION."""
        base_context.phase = EngagementPhase.HOLDING
        base_context.trade_status = True
        base_context.current_sl = Decimal("1.0900")
        base_context.adverse_exit_hypo_price = Decimal("1.0950")  # Different
        assert base_context.determine_action() == ActionType.MODIFY_POSITION

    def test_determine_action_entering_returns_none(self, base_context):
        """Test ENTERING phase returns NONE (waiting for broker)."""
        base_context.phase = EngagementPhase.ENTERING
        base_context.trade_status = True
        assert base_context.determine_action() == ActionType.NONE

    def test_determine_action_exiting_returns_none(self, base_context):
        """Test EXITING phase returns NONE (waiting for broker)."""
        base_context.phase = EngagementPhase.EXITING
        base_context.trade_status = False
        assert base_context.determine_action() == ActionType.NONE

    def test_entry_action_short_direction(self, base_context):
        """Test entry action for short direction."""
        base_context.direction = TradeDirection.SHORT
        base_context.phase = EngagementPhase.PENDING
        base_context.trade_status = True
        assert base_context.determine_action() == ActionType.MARKET_ENTRY
        assert base_context.side == OrderSide.SELL

    def test_exit_action_short_direction(self, base_context):
        """Test exit action for short direction."""
        base_context.direction = TradeDirection.SHORT
        base_context.phase = EngagementPhase.HOLDING
        base_context.trade_status = False
        base_context.entry_filled_qty = Decimal("0.1")
        base_context.broker_position_id = "12345"
        assert base_context.determine_action() == ActionType.CLOSE_POSITION
        assert base_context.exit_side == OrderSide.BUY

    # ==================== is_limit_entry tests ====================

    def test_is_limit_entry_immediate(self, base_context):
        """Test is_limit_entry is False for IMMEDIATE_ENTRY."""
        base_context.entry_reason = 0  # IMMEDIATE_ENTRY
        assert base_context.is_limit_entry is False

    def test_is_limit_entry_favorable(self, base_context):
        """Test is_limit_entry is True for FAVORABLE_DELAY_ENTRY."""
        base_context.entry_reason = 1  # FAVORABLE_DELAY_ENTRY
        assert base_context.is_limit_entry is True

    def test_is_limit_entry_adverse(self, base_context):
        """Test is_limit_entry is True for ADVERSE_DELAY_ENTRY."""
        base_context.entry_reason = 2  # ADVERSE_DELAY_ENTRY
        assert base_context.is_limit_entry is True

    # ==================== has_pending_entry_order tests ====================

    def test_has_pending_entry_order_true(self, base_context):
        """Test has_pending_entry_order for ENTERING with NEW order."""
        base_context.phase = EngagementPhase.ENTERING
        base_context.entry_broker_order_id = "123456"
        base_context.entry_status = OrderStatus.NEW
        assert base_context.has_pending_entry_order is True

    def test_has_pending_entry_order_partial_fill(self, base_context):
        """Test has_pending_entry_order for ENTERING with PARTIALLY_FILLED order."""
        base_context.phase = EngagementPhase.ENTERING
        base_context.entry_broker_order_id = "123456"
        base_context.entry_status = OrderStatus.PARTIALLY_FILLED
        assert base_context.has_pending_entry_order is True

    def test_has_pending_entry_order_no_order_id(self, base_context):
        """Test has_pending_entry_order is False when no order ID."""
        base_context.phase = EngagementPhase.ENTERING
        base_context.entry_broker_order_id = None
        base_context.entry_status = OrderStatus.NEW
        assert base_context.has_pending_entry_order is False

    def test_has_pending_entry_order_filled(self, base_context):
        """Test has_pending_entry_order is False when order is FILLED."""
        base_context.phase = EngagementPhase.ENTERING
        base_context.entry_broker_order_id = "123456"
        base_context.entry_status = OrderStatus.FILLED
        assert base_context.has_pending_entry_order is False

    def test_has_pending_entry_order_wrong_phase(self, base_context):
        """Test has_pending_entry_order is False when not in ENTERING phase."""
        base_context.phase = EngagementPhase.PENDING
        base_context.entry_broker_order_id = "123456"
        base_context.entry_status = OrderStatus.NEW
        assert base_context.has_pending_entry_order is False

    # ==================== needs_cancel_entry tests ====================

    def test_needs_cancel_entry_true(self, base_context):
        """Test needs_cancel_entry for ENTERING + trade closed."""
        base_context.phase = EngagementPhase.ENTERING
        base_context.entry_broker_order_id = "123456"
        base_context.entry_status = OrderStatus.NEW
        base_context.trade_status = False  # Trade closed
        assert base_context.needs_cancel_entry is True

    def test_needs_cancel_entry_trade_open(self, base_context):
        """Test needs_cancel_entry is False when trade still open."""
        base_context.phase = EngagementPhase.ENTERING
        base_context.entry_broker_order_id = "123456"
        base_context.entry_status = OrderStatus.NEW
        base_context.trade_status = True  # Trade open
        assert base_context.needs_cancel_entry is False

    def test_needs_cancel_entry_no_pending_order(self, base_context):
        """Test needs_cancel_entry is False when no pending order."""
        base_context.phase = EngagementPhase.ENTERING
        base_context.entry_broker_order_id = None
        base_context.trade_status = False
        assert base_context.needs_cancel_entry is False

    # ==================== needs_modify_entry tests ====================

    def test_needs_modify_entry_true(self, base_context):
        """Test needs_modify_entry when entry price changed."""
        base_context.phase = EngagementPhase.ENTERING
        base_context.entry_broker_order_id = "123456"
        base_context.entry_status = OrderStatus.NEW
        base_context.trade_status = True
        base_context.current_entry_order_price = Decimal("1.0950")
        # Set entry_reason and hypo_price to get suggested_entry_price
        # FAVORABLE_DELAY_ENTRY (1) uses favorable_entry_hypo_price
        base_context.entry_reason = 1
        base_context.favorable_entry_hypo_price = Decimal("1.0960")  # Different
        assert base_context.needs_modify_entry is True

    def test_needs_modify_entry_same_price(self, base_context):
        """Test needs_modify_entry is False when prices match."""
        base_context.phase = EngagementPhase.ENTERING
        base_context.entry_broker_order_id = "123456"
        base_context.entry_status = OrderStatus.NEW
        base_context.trade_status = True
        base_context.current_entry_order_price = Decimal("1.0950")
        # Set entry_reason and hypo_price to get suggested_entry_price
        base_context.entry_reason = 1  # FAVORABLE_DELAY_ENTRY
        base_context.favorable_entry_hypo_price = Decimal("1.0950")  # Same
        assert base_context.needs_modify_entry is False

    def test_needs_modify_entry_no_suggested_price(self, base_context):
        """Test needs_modify_entry is False when no suggested price."""
        base_context.phase = EngagementPhase.ENTERING
        base_context.entry_broker_order_id = "123456"
        base_context.entry_status = OrderStatus.NEW
        base_context.trade_status = True
        base_context.current_entry_order_price = Decimal("1.0950")
        # IMMEDIATE_ENTRY (0) returns None for suggested_entry_price
        base_context.entry_reason = 0
        assert base_context.needs_modify_entry is False

    def test_needs_modify_entry_trade_closed(self, base_context):
        """Test needs_modify_entry is False when trade closed."""
        base_context.phase = EngagementPhase.ENTERING
        base_context.entry_broker_order_id = "123456"
        base_context.entry_status = OrderStatus.NEW
        base_context.trade_status = False  # Closed
        base_context.current_entry_order_price = Decimal("1.0950")
        base_context.entry_reason = 1  # FAVORABLE_DELAY_ENTRY
        base_context.favorable_entry_hypo_price = Decimal("1.0960")
        assert base_context.needs_modify_entry is False

    # ==================== determine_action CANCEL_ORDER/MODIFY_ORDER tests ====================

    def test_determine_action_entering_trade_closed_returns_cancel_order(self, base_context):
        """Test ENTERING + trade closed returns CANCEL_ORDER."""
        base_context.phase = EngagementPhase.ENTERING
        base_context.entry_broker_order_id = "123456"
        base_context.entry_status = OrderStatus.NEW
        base_context.trade_status = False
        assert base_context.determine_action() == ActionType.CANCEL_ORDER

    def test_determine_action_entering_price_changed_returns_modify_order(self, base_context):
        """Test ENTERING + entry price changed returns MODIFY_ORDER."""
        base_context.phase = EngagementPhase.ENTERING
        base_context.entry_broker_order_id = "123456"
        base_context.entry_status = OrderStatus.NEW
        base_context.trade_status = True
        base_context.current_entry_order_price = Decimal("1.0950")
        # Set entry_reason and hypo_price to get suggested_entry_price
        base_context.entry_reason = 1  # FAVORABLE_DELAY_ENTRY
        base_context.favorable_entry_hypo_price = Decimal("1.0960")  # Different
        assert base_context.determine_action() == ActionType.MODIFY_ORDER

    def test_determine_action_entering_no_change_returns_none(self, base_context):
        """Test ENTERING with no changes returns NONE."""
        base_context.phase = EngagementPhase.ENTERING
        base_context.entry_broker_order_id = "123456"
        base_context.entry_status = OrderStatus.NEW
        base_context.trade_status = True
        base_context.current_entry_order_price = Decimal("1.0950")
        # Set entry_reason and hypo_price to get suggested_entry_price
        base_context.entry_reason = 1  # FAVORABLE_DELAY_ENTRY
        base_context.favorable_entry_hypo_price = Decimal("1.0950")  # Same
        assert base_context.determine_action() == ActionType.NONE


class TestExitReasonSignal:
    """Test the SIGNAL exit reason."""

    def test_exit_reason_signal_exists(self):
        """Test that SIGNAL exit reason exists."""
        assert ExitReason.SIGNAL == "SIGNAL"


class TestCurrentEntryExitStrategy:
    """Tests for current_entry_strategy and current_exit_strategy computed properties."""

    @pytest.fixture
    def base_context(self):
        """Create a base context for testing."""
        return EngagementContext(
            engagement_id=uuid4(),
            config_id=uuid4(),
            trade_id=uuid4(),
            user_id=uuid4(),
            account_id=uuid4(),
            portfolio_id=uuid4(),
            strategy_name="Test Strategy",
            blueprint_name="Test Blueprint",
            symbol="EUR-USD",
            trading_symbol="EURUSD",
            trading_point_value=Decimal("100000"),
            price_precision=5,
            quantity_precision=2,
            capital=Decimal("10000"),
            capital_currency="USD",
            capital_override=None,
            num_allocations=1,
            direction=TradeDirection.LONG,
            trade_status=True,
            entry_price=Decimal("1.1000"),
            exit_price=None,
            mae=Decimal("50"),
            entry_reason=None,  # Use entry_reason instead of order_strategy
            entry_volatility=None,
            phase=EngagementPhase.PENDING,
            target_quantity=Decimal("0.1"),
            entry_broker_order_id=None,
            entry_status=None,
            entry_filled_qty=Decimal("0"),
            entry_avg_price=None,
            sl_broker_order_id=None,
            current_sl=None,
            tp_broker_order_id=None,
            current_tp=None,
            broker_position_id=None,
            current_entry_order_price=None,
            expected_loss_pct=None,
            historical_trade_count=0,
            risk_padding_pct=None,
        )

    # ==================== current_entry_strategy tests ====================

    def test_current_entry_strategy_no_entry_reason(self, base_context):
        """Test current_entry_strategy defaults to IMMEDIATE_ENTRY when entry_reason is None."""
        base_context.entry_reason = None
        assert base_context.current_entry_strategy == OrderStrategy.IMMEDIATE_ENTRY

    def test_current_entry_strategy_immediate_entry(self, base_context):
        """Test current_entry_strategy with entry_reason=0 (ImmediateEntry)."""
        base_context.entry_reason = 0
        assert base_context.current_entry_strategy == OrderStrategy.IMMEDIATE_ENTRY

    def test_current_entry_strategy_favorable_delay_entry(self, base_context):
        """Test current_entry_strategy with entry_reason=1 (FavorableDelayEntry)."""
        base_context.entry_reason = 1
        assert base_context.current_entry_strategy == OrderStrategy.FAVORABLE_DELAY_ENTRY

    def test_current_entry_strategy_adverse_delay_entry(self, base_context):
        """Test current_entry_strategy with entry_reason=2 (AdverseDelayEntry)."""
        base_context.entry_reason = 2
        assert base_context.current_entry_strategy == OrderStrategy.ADVERSE_DELAY_ENTRY

    def test_current_entry_strategy_entry_reason_takes_precedence(self, base_context):
        """Test entry_reason determines current_entry_strategy."""
        base_context.entry_reason = 1  # FavorableDelayEntry
        assert base_context.current_entry_strategy == OrderStrategy.FAVORABLE_DELAY_ENTRY

    def test_current_entry_strategy_unknown_value_defaults_to_immediate(self, base_context):
        """Test unknown entry_reason value defaults to IMMEDIATE_ENTRY."""
        base_context.entry_reason = 99  # Unknown value
        assert base_context.current_entry_strategy == OrderStrategy.IMMEDIATE_ENTRY

    # ==================== current_exit_strategy tests ====================

    def test_current_exit_strategy_no_exit_reason(self, base_context):
        """Test current_exit_strategy returns IMMEDIATE_EXIT when exit_reason is None."""
        base_context.exit_reason = None
        assert base_context.current_exit_strategy == OrderStrategy.IMMEDIATE_EXIT

    def test_current_exit_strategy_immediate_exit(self, base_context):
        """Test current_exit_strategy with exit_reason=3 (ImmediateExit)."""
        base_context.exit_reason = 3
        assert base_context.current_exit_strategy == OrderStrategy.IMMEDIATE_EXIT

    def test_current_exit_strategy_stop_loss(self, base_context):
        """Test current_exit_strategy with exit_reason=4 (StopLoss)."""
        base_context.exit_reason = 4
        assert base_context.current_exit_strategy == OrderStrategy.STOP_LOSS

    def test_current_exit_strategy_take_profit(self, base_context):
        """Test current_exit_strategy with exit_reason=5 (TakeProfit)."""
        base_context.exit_reason = 5
        assert base_context.current_exit_strategy == OrderStrategy.TAKE_PROFIT

    def test_current_exit_strategy_trailing_stop(self, base_context):
        """Test current_exit_strategy with exit_reason=6 (TrailingStop)."""
        base_context.exit_reason = 6
        assert base_context.current_exit_strategy == OrderStrategy.TRAILING_STOP

    def test_current_exit_strategy_breakeven(self, base_context):
        """Test current_exit_strategy with exit_reason=7 (Breakeven)."""
        base_context.exit_reason = 7
        assert base_context.current_exit_strategy == OrderStrategy.BREAKEVEN

    def test_current_exit_strategy_timeout_exit(self, base_context):
        """Test current_exit_strategy with exit_reason=8 (TimeoutExit)."""
        base_context.exit_reason = 8
        assert base_context.current_exit_strategy == OrderStrategy.TIMEOUT_EXIT

    def test_current_exit_strategy_unknown_value_defaults_to_immediate(self, base_context):
        """Test unknown exit_reason value defaults to IMMEDIATE_EXIT."""
        base_context.exit_reason = 99  # Unknown value
        assert base_context.current_exit_strategy == OrderStrategy.IMMEDIATE_EXIT

    # ==================== JSON serialization tests ====================

    def test_computed_fields_included_in_model_dump(self, base_context):
        """Test computed fields are included in model_dump output."""
        base_context.entry_reason = 1  # FavorableDelayEntry
        base_context.exit_reason = 4  # StopLoss
        data = base_context.model_dump()
        assert data["current_entry_strategy"] == OrderStrategy.FAVORABLE_DELAY_ENTRY
        assert data["current_exit_strategy"] == OrderStrategy.STOP_LOSS


class TestEngagementContextValidators:
    """Test field validators for automatic type conversion from SQL rows."""

    @pytest.fixture
    def base_fields(self):
        """Base fields for creating EngagementContext with all fields."""
        return {
            # ============================================================
            # 1. IDENTITY & RELATIONS
            # ============================================================
            "engagement_id": uuid4(),
            "config_id": uuid4(),
            "trade_id": uuid4(),
            "user_id": uuid4(),
            "account_id": uuid4(),
            "portfolio_id": uuid4(),
            # ============================================================
            # 2. STRATEGY METADATA
            # ============================================================
            "strategy_name": "Test Strategy",
            "blueprint_name": "Test Blueprint",
            # ============================================================
            # 3. INSTRUMENT SPECIFICATIONS
            # ============================================================
            "symbol": "EURUSD",
            "trading_symbol": "EURUSD",
            "trading_point_value": Decimal("100000"),
            "price_precision": 5,
            "quantity_precision": 2,
            # ============================================================
            # 4. PORTFOLIO & CAPITAL
            # ============================================================
            "capital": Decimal("10000"),
            "capital_currency": "USD",
            "capital_override": None,
            "num_allocations": 1,
            # ============================================================
            # 5. TRADE STATE
            # ============================================================
            "trade_status": True,
            "entry_price": Decimal("1.1000"),
            "exit_price": None,
            "mae": Decimal("50"),
            "entry_volatility": None,
            # ============================================================
            # 6. ENGAGEMENT LIFECYCLE
            # ============================================================
            "phase": EngagementPhase.PENDING,
            "target_quantity": Decimal("0.1"),
            # ============================================================
            # 7. BROKER STATE
            # Note: entry_status excluded - tested explicitly by validators
            # ============================================================
            "entry_broker_order_id": None,
            # "entry_status" excluded - tests pass it explicitly
            "entry_filled_qty": Decimal("0"),
            "entry_avg_price": None,
            "sl_broker_order_id": None,
            "current_sl": None,
            "tp_broker_order_id": None,
            "current_tp": None,
            "broker_position_id": None,
            "current_entry_order_price": None,
            # ============================================================
            # 8. RISK CONTROL
            # ============================================================
            "expected_loss_pct": None,
            "historical_trade_count": 0,
            "risk_padding_pct": None,
        }

    def test_direction_validator_accepts_int_long(self, base_fields):
        """Test direction field accepts int 1 for LONG."""
        ctx = EngagementContext(direction=1, **base_fields)
        assert ctx.direction == TradeDirection.LONG

    def test_direction_validator_accepts_int_short(self, base_fields):
        """Test direction field accepts int -1 for SHORT."""
        ctx = EngagementContext(direction=-1, **base_fields)
        assert ctx.direction == TradeDirection.SHORT

    def test_direction_validator_accepts_enum(self, base_fields):
        """Test direction field accepts TradeDirection enum directly."""
        ctx = EngagementContext(direction=TradeDirection.LONG, **base_fields)
        assert ctx.direction == TradeDirection.LONG

    def test_entry_status_validator_accepts_string(self, base_fields):
        """Test entry_status field accepts string and converts to OrderStatus."""
        ctx = EngagementContext(
            direction=TradeDirection.LONG,
            entry_status="filled",
            **base_fields,
        )
        assert ctx.entry_status == OrderStatus.FILLED

    def test_entry_status_validator_accepts_string_new(self, base_fields):
        """Test entry_status field accepts 'new' string."""
        ctx = EngagementContext(
            direction=TradeDirection.LONG,
            entry_status="new",
            **base_fields,
        )
        assert ctx.entry_status == OrderStatus.NEW

    def test_entry_status_validator_accepts_none(self, base_fields):
        """Test entry_status field accepts None."""
        ctx = EngagementContext(
            direction=TradeDirection.LONG,
            entry_status=None,
            **base_fields,
        )
        assert ctx.entry_status is None

    def test_entry_status_validator_accepts_enum(self, base_fields):
        """Test entry_status field accepts OrderStatus enum directly."""
        ctx = EngagementContext(
            direction=TradeDirection.LONG,
            entry_status=OrderStatus.PARTIALLY_FILLED,
            **base_fields,
        )
        assert ctx.entry_status == OrderStatus.PARTIALLY_FILLED

    def test_entry_status_validator_invalid_string_returns_none(self, base_fields):
        """Test invalid entry_status string returns None."""
        ctx = EngagementContext(
            direction=TradeDirection.LONG,
            entry_status="invalid_status_xyz",
            **base_fields,
        )
        assert ctx.entry_status is None

    def test_entry_reason_validator_accepts_int(self, base_fields):
        """Test entry_reason field accepts int value."""
        ctx = EngagementContext(
            direction=TradeDirection.LONG,
            entry_reason=1,  # FavorableDelayEntry
            **base_fields,
        )
        assert ctx.entry_reason == 1
        assert ctx.current_entry_strategy == OrderStrategy.FAVORABLE_DELAY_ENTRY

    def test_entry_reason_validator_accepts_none(self, base_fields):
        """Test entry_reason field accepts None and defaults to IMMEDIATE_ENTRY."""
        ctx = EngagementContext(
            direction=TradeDirection.LONG,
            entry_reason=None,
            **base_fields,
        )
        assert ctx.entry_reason is None
        assert ctx.current_entry_strategy == OrderStrategy.IMMEDIATE_ENTRY

    def test_model_validate_from_dict_like_sql_row(self, base_fields):
        """Test model_validate works with dict simulating SQL row."""
        # Simulate what comes from SQL: direction as int, entry_status as string
        sql_row = {
            **base_fields,
            "direction": 1,  # int from SQL
            "entry_status": "filled",  # string from SQL
            "entry_filled_qty": "0.1",  # Decimal as string from SQL
        }
        ctx = EngagementContext.model_validate(sql_row)
        assert ctx.direction == TradeDirection.LONG
        assert ctx.entry_status == OrderStatus.FILLED
        assert ctx.entry_filled_qty == Decimal("0.1")


class TestExpectedLossSLPrice:
    """Tests for expected_loss_sl_price computed property (Issue #651)."""

    @pytest.fixture
    def base_context(self):
        """Create a base context for testing."""
        return EngagementContext(
            engagement_id=uuid4(),
            config_id=uuid4(),
            trade_id=uuid4(),
            user_id=uuid4(),
            account_id=uuid4(),
            portfolio_id=uuid4(),
            strategy_name="Test Strategy",
            blueprint_name="Test Blueprint",
            symbol="EUR-USD",
            trading_symbol="EURUSD",
            trading_point_value=Decimal("100000"),
            price_precision=5,
            quantity_precision=2,
            capital=Decimal("10000"),
            capital_currency="USD",
            capital_override=None,
            num_allocations=1,
            direction=TradeDirection.LONG,
            trade_status=True,
            entry_price=Decimal("1.1000"),
            exit_price=None,
            mae=Decimal("50"),
            entry_volatility=None,
            phase=EngagementPhase.PENDING,
            target_quantity=Decimal("0.1"),
            entry_broker_order_id=None,
            entry_status=None,
            entry_filled_qty=Decimal("0"),
            entry_avg_price=None,
            sl_broker_order_id=None,
            current_sl=None,
            tp_broker_order_id=None,
            current_tp=None,
            broker_position_id=None,
            current_entry_order_price=None,
            expected_loss_pct=None,
            historical_trade_count=0,
            risk_padding_pct=None,
        )

    def test_expected_loss_sl_price_long(self, base_context):
        """Test SL calculation for LONG position.

        Formula: sl = entry_price * (1 - expected_loss_pct)
        """
        base_context.expected_loss_pct = Decimal("0.02")  # 2% loss
        base_context.entry_price = Decimal("1.1000")

        # sl = 1.1000 * (1 - 0.02) = 1.1000 * 0.98 = 1.0780
        result = base_context.expected_loss_sl_price
        assert result == Decimal("1.0780")  # Rounded to price_precision=5

    def test_expected_loss_sl_price_short(self, base_context):
        """Test SL calculation for SHORT position.

        Formula: sl = entry_price * (1 + expected_loss_pct)
        """
        base_context.direction = TradeDirection.SHORT
        base_context.expected_loss_pct = Decimal("0.02")  # 2% loss
        base_context.entry_price = Decimal("1.1000")

        # sl = 1.1000 * (1 + 0.02) = 1.1000 * 1.02 = 1.1220
        result = base_context.expected_loss_sl_price
        assert result == Decimal("1.122")  # Rounded to price_precision=5

    def test_expected_loss_sl_price_uses_suggested_entry_price_first(self, base_context):
        """Test SL uses suggested_entry_price (pending order) over entry_price.

        suggested_entry_price is computed from entry_reason and *_entry_hypo_price fields.
        """
        base_context.expected_loss_pct = Decimal("0.02")
        base_context.entry_price = Decimal("1.1000")
        # Set entry_reason=1 (FAVORABLE_DELAY_ENTRY) and favorable_entry_hypo_price
        # to get suggested_entry_price = 1.0950
        base_context.entry_reason = 1  # FAVORABLE_DELAY_ENTRY
        base_context.favorable_entry_hypo_price = Decimal("1.0950")

        # Verify suggested_entry_price is computed correctly
        assert base_context.suggested_entry_price == Decimal("1.0950")

        # sl = 1.0950 * (1 - 0.02) = 1.0731
        result = base_context.expected_loss_sl_price
        assert result == Decimal("1.0731")

    def test_expected_loss_sl_price_no_expected_loss_pct(self, base_context):
        """Test returns None when expected_loss_pct is None."""
        base_context.expected_loss_pct = None
        assert base_context.expected_loss_sl_price is None

    def test_expected_loss_sl_price_zero_expected_loss_pct(self, base_context):
        """Test returns None when expected_loss_pct is 0."""
        base_context.expected_loss_pct = Decimal("0")
        assert base_context.expected_loss_sl_price is None

    def test_expected_loss_sl_price_negative_expected_loss_pct(self, base_context):
        """Test returns None when expected_loss_pct is negative."""
        base_context.expected_loss_pct = Decimal("-0.01")
        assert base_context.expected_loss_sl_price is None

    def test_expected_loss_sl_price_no_entry_price(self, base_context):
        """Test returns None when no entry price is available.

        entry_price, base_entry_price, and suggested_entry_price all None.
        suggested_entry_price is computed from entry_reason + *_entry_hypo_price.
        """
        base_context.expected_loss_pct = Decimal("0.02")
        base_context.entry_price = None
        base_context.base_entry_price = None
        # Ensure suggested_entry_price is None by not setting entry hypo prices
        base_context.favorable_entry_hypo_price = None
        base_context.adverse_entry_hypo_price = None
        assert base_context.expected_loss_sl_price is None


class TestEffectiveSLProperty:
    """Tests for effective_sl computed property (Issue #651).

    Priority: adverse_exit_hypo_price > expected_loss_sl_price
    """

    @pytest.fixture
    def base_context(self):
        """Create a base context for testing."""
        return EngagementContext(
            engagement_id=uuid4(),
            config_id=uuid4(),
            trade_id=uuid4(),
            user_id=uuid4(),
            account_id=uuid4(),
            portfolio_id=uuid4(),
            strategy_name="Test Strategy",
            blueprint_name="Test Blueprint",
            symbol="EUR-USD",
            trading_symbol="EURUSD",
            trading_point_value=Decimal("100000"),
            price_precision=5,
            quantity_precision=2,
            capital=Decimal("10000"),
            capital_currency="USD",
            capital_override=None,
            num_allocations=1,
            direction=TradeDirection.LONG,
            trade_status=True,
            entry_price=Decimal("1.1000"),
            exit_price=None,
            mae=Decimal("50"),
            entry_volatility=None,
            phase=EngagementPhase.PENDING,
            target_quantity=Decimal("0.1"),
            entry_broker_order_id=None,
            entry_status=None,
            entry_filled_qty=Decimal("0"),
            entry_avg_price=None,
            sl_broker_order_id=None,
            current_sl=None,
            tp_broker_order_id=None,
            current_tp=None,
            broker_position_id=None,
            current_entry_order_price=None,
            expected_loss_pct=None,
            historical_trade_count=0,
            risk_padding_pct=None,
        )

    def test_effective_sl_uses_adverse_exit_hypo_price(self, base_context):
        """Test effective_sl returns adverse_exit_hypo_price when available."""
        base_context.adverse_exit_hypo_price = Decimal("1.0900")
        base_context.expected_loss_pct = Decimal("0.02")  # Would calculate to 1.0780

        # Should use adverse_exit_hypo_price, not expected_loss calculation
        assert base_context.effective_sl == Decimal("1.09")

    def test_effective_sl_fallback_to_expected_loss(self, base_context):
        """Test effective_sl falls back to expected_loss_sl_price."""
        base_context.adverse_exit_hypo_price = None
        base_context.expected_loss_pct = Decimal("0.02")
        base_context.entry_price = Decimal("1.1000")

        # Should calculate from expected_loss_pct: 1.1000 * 0.98 = 1.0780
        assert base_context.effective_sl == Decimal("1.0780")

    def test_effective_sl_none_when_no_data(self, base_context):
        """Test effective_sl returns None when no data available."""
        base_context.adverse_exit_hypo_price = None
        base_context.expected_loss_pct = None

        assert base_context.effective_sl is None

    def test_effective_tp_uses_favorable_exit_hypo_price(self, base_context):
        """Test effective_tp returns favorable_exit_hypo_price."""
        base_context.favorable_exit_hypo_price = Decimal("1.1200")

        assert base_context.effective_tp == Decimal("1.12")

    def test_effective_tp_none_when_no_data(self, base_context):
        """Test effective_tp returns None when no favorable_exit_hypo_price."""
        base_context.favorable_exit_hypo_price = None

        assert base_context.effective_tp is None
