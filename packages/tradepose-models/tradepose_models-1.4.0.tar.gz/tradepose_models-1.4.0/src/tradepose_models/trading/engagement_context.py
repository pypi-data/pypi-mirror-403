"""EngagementContext model for unified engagement state.

This model aggregates data from multiple database tables into a single context object
for BrokerExecutor decision making and order execution.

Data Sources:
    - gateway.engagements: phase, target_quantity
    - gateway.engagement_configs: symbol, trading_instrument_id, strategy_id, blueprint_id
    - gateway.trades: direction, entry_price, mae, order_strategy, volatility, hypo prices
    - gateway.orderbook: broker order IDs, status, SL/TP prices
    - gateway.portfolios: capital, currency
    - gateway.account_portfolio_bindings: capital_override
    - gateway.portfolio_allocations: count for num_allocations
    - gateway.strategies: name, base_instrument
    - gateway.blueprints: name
    - data.instruments: point_value, price_precision, quantity_precision, broker symbol

Used by BrokerExecutor.process_engagement() to determine and execute actions.
"""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, computed_field, field_validator

from tradepose_models.enums import (
    ActionType,
    EngagementPhase,
    OrderSide,
    OrderStatus,
    OrderStrategy,
    TradeDirection,
)


class EngagementContext(BaseModel):
    """Engagement complete context - built from single SQL query with JOINs.

    This model represents a snapshot of all relevant database state for a single
    engagement at query time. It contains:

    1. Identity & Relations: UUIDs linking to parent records
    2. Strategy Metadata: Names for logging/debugging
    3. Instrument Specifications: Symbol mapping and precision for order placement
    4. Portfolio & Capital: Position sizing inputs
    5. Trade State: Signal direction, prices, volatility from Rust Worker
    6. Engagement Lifecycle: Phase state machine
    7. Broker State: Order book entries aggregated by order_type
    8. Modify Signals: Rust Worker suggested price adjustments
    9. Risk Control: Padding and expected loss for validation

    Used by BrokerExecutor.process_engagement() which routes to:
    - execute_market_entry(ctx) for MARKET_ENTRY
    - execute_limit_entry(ctx) for LIMIT_ENTRY (LIMIT or STOP order)
    - execute_close_position(ctx) for CLOSE_POSITION
    - execute_modify_position(ctx) for MODIFY_POSITION
    - execute_modify_order(ctx) for MODIFY_ORDER
    - execute_cancel_order(ctx) for CANCEL_ORDER
    """

    # ============================================================
    # 1. IDENTITY & RELATIONS
    # ============================================================
    # Primary keys and foreign key references for record correlation
    # Source: gateway.engagements, gateway.engagement_configs
    # ============================================================

    engagement_id: UUID = Field(
        ...,
        description="Primary key. Source: gateway.engagements.id",
    )
    config_id: UUID = Field(
        ...,
        description="FK to engagement_configs. Source: gateway.engagements.config_id",
    )
    trade_id: UUID = Field(
        ...,
        description="FK to trades. Source: gateway.engagements.trade_id",
    )
    user_id: UUID = Field(
        ...,
        description="FK to users. Source: gateway.engagement_configs.user_id",
    )
    account_id: UUID = Field(
        ...,
        description="FK to trading_accounts. Source: gateway.engagement_configs.account_id",
    )
    portfolio_id: UUID = Field(
        ...,
        description="FK to portfolios. Source: gateway.engagement_configs.portfolio_id",
    )

    # ============================================================
    # 2. STRATEGY METADATA
    # ============================================================
    # Names for logging, debugging, and audit trails
    # Source: gateway.strategies, gateway.blueprints
    # ============================================================

    strategy_name: str = Field(
        ...,
        description="Strategy name for logging. Source: gateway.strategies.name",
    )
    blueprint_name: str = Field(
        ...,
        description="Blueprint name for logging. Source: gateway.blueprints.name",
    )

    # ============================================================
    # 3. INSTRUMENT SPECIFICATIONS
    # ============================================================
    # Symbol mapping and precision for order placement
    # Source: gateway.engagement_configs, data.instruments
    #
    # Note: `symbol` is the signal instrument (e.g., "NQ" from strategy)
    #       `trading_symbol` is the execution instrument (e.g., "MNQ" mapped for account)
    # ============================================================

    symbol: str = Field(
        ...,
        description="Signal instrument symbol. Source: gateway.engagement_configs.symbol",
    )
    trading_symbol: str | None = Field(
        None,
        description="Broker-specific execution symbol. "
        "Source: data.instruments.broker_symbol via trading_instrument_id. "
        "May differ from signal symbol (e.g., NQ -> MNQ mapping).",
    )
    trading_point_value: Decimal | None = Field(
        None,
        description="USD value per point movement for position sizing. "
        "Source: data.instruments.point_value. "
        "Examples: XAUUSD=100, US100.cash=1, MNQ=2, NQ=20, ES=50, MES=5.",
    )
    price_precision: int = Field(
        default=5,
        description="Number of decimal places for price. "
        "Source: data.instruments.price_precision. "
        "Used for order price rounding (e.g., 5 for EURUSD, 2 for JPY pairs).",
    )
    quantity_precision: int = Field(
        default=2,
        description="Number of decimal places for quantity. "
        "Source: data.instruments.quantity_precision. "
        "Used for lot size rounding (e.g., 2 for 0.01 lot increments).",
    )

    # ============================================================
    # 4. PORTFOLIO & CAPITAL
    # ============================================================
    # Position sizing inputs from portfolio configuration
    # Source: gateway.portfolios, gateway.account_portfolio_bindings,
    #         gateway.portfolio_allocations
    #
    # Position Sizing Formula:
    #   effective_capital = capital_override ?? capital
    #   risk_capital = effective_capital / num_allocations
    #   point_loss = entry_price * expected_loss_pct
    #   loss_per_lot = point_loss * trading_point_value
    #   target_quantity = risk_capital / loss_per_lot
    # ============================================================

    capital: Decimal = Field(
        ...,
        description="Portfolio base capital. Source: gateway.portfolios.capital",
    )
    capital_currency: str = Field(
        default="USD",
        description="Portfolio capital currency. Source: gateway.portfolios.currency",
    )
    capital_override: Decimal | None = Field(
        None,
        description="Account-level capital override. "
        "Source: gateway.account_portfolio_bindings.capital_override. "
        "If set, used instead of portfolio.capital for this account.",
    )
    num_allocations: int = Field(
        default=1,
        description="Number of strategy/blueprint allocations in portfolio. "
        "Source: COUNT(gateway.portfolio_allocations) WHERE portfolio_id = ?. "
        "Used for capital division: risk_capital = capital / num_allocations.",
    )

    # ============================================================
    # 5. TRADE STATE
    # ============================================================
    # Signal direction, prices, and volatility from Rust Worker
    # Source: gateway.trades (populated by Rust Worker processing)
    # ============================================================

    direction: TradeDirection = Field(
        ...,
        description="Trade direction (1=LONG, -1=SHORT). Source: gateway.trades.direction",
    )
    trade_status: bool = Field(
        ...,
        description="Trade open/closed status. Source: gateway.trades.status. "
        "True=open (signal active), False=closed (signal ended).",
    )
    is_adv_triggered: bool = Field(
        default=False,
        description="Whether the trade has been triggered (entry filled). "
        "Source: gateway.trades.is_adv_triggered. "
        "False=pending entry (use hypo prices), True=triggered (use entry_price).",
    )
    entry_price: Decimal | None = Field(
        None,
        description="Trade entry price from signal. Source: gateway.trades.entry_price. "
        "NULL for untriggered trades.",
    )
    base_entry_price: Decimal | None = Field(
        None,
        description="Base entry price before order strategy adjustment. "
        "Source: gateway.trades.base_entry_price. "
        "Used as fallback for position sizing when hypo prices unavailable.",
    )
    exit_price: Decimal | None = Field(
        None,
        description="Trade exit price if closed. Source: gateway.trades.exit_price",
    )
    mae: Decimal | None = Field(
        None,
        description="Maximum Adverse Excursion for this trade. "
        "Source: gateway.trades.mae. Used for SL calculation.",
    )

    # Volatility fields for risk-adjusted sizing
    entry_volatility: Decimal | None = Field(
        None,
        description="ATR/volatility at entry time. Source: gateway.trades.entry_volatility",
    )

    # Entry reason (dynamically updated by Rust Worker)
    entry_reason: int | None = Field(
        None,
        description="Entry reason from Rust Worker. "
        "Maps to OrderStrategy: 0=ImmediateEntry, 1=FavorableDelayEntry, 2=AdverseDelayEntry. "
        "Source: gateway.trades.entry_reason",
    )
    favorable_entry_hypo_price: Decimal | None = Field(
        None,
        description="Favorable entry hypothetical price. Source: gateway.trades.favorable_entry_hypo_price",
    )
    adverse_entry_hypo_price: Decimal | None = Field(
        None,
        description="Adverse entry hypothetical price. Source: gateway.trades.adverse_entry_hypo_price",
    )

    # Exit reason (dynamically updated by Rust Worker)
    exit_reason: int | None = Field(
        None,
        description="Exit reason from Rust Worker. "
        "Maps to OrderStrategy: 3=ImmediateExit, 4=StopLoss, 5=TakeProfit, 6=TrailingStop, 7=Breakeven, 8=TimeoutExit. "
        "Source: gateway.trades.exit_reason",
    )
    favorable_exit_hypo_price: Decimal | None = Field(
        None,
        description="Favorable exit hypothetical price. Source: gateway.trades.favorable_exit_hypo_price",
    )
    adverse_exit_hypo_price: Decimal | None = Field(
        None,
        description="Adverse exit hypothetical price. Source: gateway.trades.adverse_exit_hypo_price",
    )

    # ============================================================
    # 6. ENGAGEMENT LIFECYCLE
    # ============================================================
    # Phase state machine and target position
    # Source: gateway.engagements
    #
    # Phase Flow:
    #   PENDING -> ENTERING -> HOLDING -> EXITING -> CLOSED
    #                    \-> FAILED / CANCELLED / EXPIRED
    # ============================================================

    phase: EngagementPhase = Field(
        ...,
        description="Engagement phase (9-state). Source: gateway.engagements.phase",
    )
    target_quantity: Decimal | None = Field(
        None,
        description="Target position size (lots). Source: gateway.engagements.target_quantity. "
        "Calculated from position sizing formula using capital, MAE, point_value.",
    )

    # ============================================================
    # 7. BROKER STATE (Aggregated from Orderbook)
    # ============================================================
    # Current broker order/position state aggregated by order_strategy
    # Source: gateway.orderbook (aggregated via CTE by order_strategy)
    #
    # OrderType: Execution mechanism (HOW)
    #   - MARKET: Immediate market order
    #   - LIMIT: Limit order
    #   - STOP: Stop order (triggers market)
    #
    # OrderStrategy: Strategy purpose (WHY)
    #   - ImmediateEntry, FavorableDelayEntry, AdverseDelayEntry: Entry
    #   - StopLoss, TakeProfit, TrailingStop, etc.: Exit
    # ============================================================

    # Entry order state (order_strategy IN entry strategies)
    entry_broker_order_id: str | None = Field(
        None,
        description="Entry order broker ID. Source: orderbook.broker_order_id "
        "WHERE order_strategy IN (ImmediateEntry, FavorableDelayEntry, AdverseDelayEntry)",
    )
    entry_status: OrderStatus | None = Field(
        None,
        description="Entry order status. Source: orderbook.status",
    )
    exit_status: OrderStatus | None = Field(
        None,
        description="Exit order status. Source: orderbook.status "
        "WHERE order_strategy IN (ImmediateExit, StopLoss, TakeProfit, etc.)",
    )
    entry_filled_qty: Decimal = Field(
        default=Decimal("0"),
        description="Entry filled quantity. Source: orderbook.filled_quantity",
    )
    entry_avg_price: Decimal | None = Field(
        None,
        description="Entry average fill price. Source: orderbook.avg_price",
    )

    # SL order state (order_strategy=StopLoss)
    sl_broker_order_id: str | None = Field(
        None,
        description="Stop loss order broker ID. Source: orderbook.broker_order_id "
        "WHERE order_strategy IN (StopLoss, TrailingStop, Breakeven)",
    )
    current_sl: Decimal | None = Field(
        None,
        description="Current stop loss price. Source: orderbook.price WHERE order_strategy=StopLoss",
    )

    # TP order state (order_strategy=TakeProfit)
    tp_broker_order_id: str | None = Field(
        None,
        description="Take profit order broker ID. Source: orderbook.broker_order_id "
        "WHERE order_strategy=TakeProfit",
    )
    current_tp: Decimal | None = Field(
        None,
        description="Current take profit price. Source: orderbook.price WHERE order_strategy=TakeProfit",
    )

    # Position tracking (MT5: position ticket from deal)
    broker_position_id: str | None = Field(
        None,
        description="Broker position ID for correlation. Source: orderbook.broker_position_id. "
        "MT5: position ticket from DEAL response.",
    )

    # Current pending order price (for ENTERING phase modification)
    current_entry_order_price: Decimal | None = Field(
        None,
        description="Current pending entry order price. Source: orderbook.price "
        "WHERE status=NEW AND is_entry=True. Used for needs_modify_entry check.",
    )

    # ============================================================
    # 8. RISK CONTROL & POSITION SIZING RESULT
    # ============================================================
    # Risk validation parameters and calculation results
    #
    # expected_loss_pct: Calculated by EngagementContextRepository using
    #   historical MAE statistics. Default method:
    #   median(mae / entry_price) * 2 from last 100 trades of same blueprint
    #
    # risk_padding_pct: Custom padding % for entry validation (e.g., 0.02 = 2%)
    #   Converted to price: padding_price = entry_price * risk_padding_pct
    # ============================================================

    expected_loss_pct: Decimal | None = Field(
        None,
        description="Expected loss percentage for position sizing. "
        "Calculated from historical MAE statistics (e.g., median(mae/entry) * 2). "
        "Used in: target_quantity = risk_capital / (entry_price * expected_loss_pct * point_value).",
    )
    historical_trade_count: int = Field(
        default=0,
        description="Number of historical trades used for MAE statistics. "
        "Indicates sample size reliability (e.g., 100 trades).",
    )
    risk_padding_pct: Decimal | None = Field(
        None,
        description="Custom padding percentage for entry risk validation (0.02 = 2%). "
        "Source: gateway.portfolios.risk_padding_pct or derived from risk config. "
        "If None, adapter uses default (2x spread as percentage of entry price).",
    )

    # ============================================================
    # FIELD VALIDATORS
    # ============================================================
    # Automatic conversion for SQL row data types

    @field_validator("direction", mode="before")
    @classmethod
    def convert_direction(cls, v: int | TradeDirection) -> TradeDirection:
        """Convert int to TradeDirection (1=LONG, -1=SHORT)."""
        if isinstance(v, TradeDirection):
            return v
        return TradeDirection.from_int(v)

    @field_validator("entry_status", mode="before")
    @classmethod
    def convert_entry_status(cls, v: str | OrderStatus | None) -> OrderStatus | None:
        """Convert string to OrderStatus enum."""
        if v is None or isinstance(v, OrderStatus):
            return v
        try:
            return OrderStatus(v)
        except ValueError:
            return None

    @field_validator("exit_status", mode="before")
    @classmethod
    def convert_exit_status(cls, v: str | OrderStatus | None) -> OrderStatus | None:
        """Convert string to OrderStatus enum."""
        if v is None or isinstance(v, OrderStatus):
            return v
        try:
            return OrderStatus(v)
        except ValueError:
            return None

    # ============================================================
    # HELPER METHODS
    # ============================================================

    def round_price(self, price: Decimal | None) -> Decimal | None:
        """Round price to price_precision decimal places."""
        if price is None:
            return None
        return price.quantize(Decimal(10) ** -self.price_precision)

    # ============================================================
    # COMPUTED PROPERTIES
    # ============================================================

    @computed_field  # type: ignore[prop-decorator]
    @property
    def side(self) -> OrderSide:
        """Order side derived from trade direction."""
        return OrderSide.BUY if self.direction == TradeDirection.LONG else OrderSide.SELL

    @computed_field  # type: ignore[prop-decorator]
    @property
    def exit_side(self) -> OrderSide:
        """Exit side (opposite of entry)."""
        return OrderSide.SELL if self.direction == TradeDirection.LONG else OrderSide.BUY

    @computed_field  # type: ignore[prop-decorator]
    @property
    def current_entry_strategy(self) -> OrderStrategy:
        """Get current entry strategy based on entry_reason or hypo prices.

        For triggered trades, uses entry_reason from Rust Worker.
        For untriggered trades (entry_reason=NULL), infers strategy from hypo prices:
        - adverse_entry_hypo_price present → ADVERSE_DELAY_ENTRY (BUY_STOP/SELL_STOP)
        - favorable_entry_hypo_price present → FAVORABLE_DELAY_ENTRY (BUY_LIMIT/SELL_LIMIT)
        - neither present → IMMEDIATE_ENTRY
        """
        # Triggered trade: use entry_reason
        if self.entry_reason is not None:
            return OrderStrategy.from_int_or_default(
                self.entry_reason, OrderStrategy.IMMEDIATE_ENTRY
            )

        # Untriggered trade: infer from hypo prices
        # Priority: ADVERSE (STOP) > FAVORABLE (LIMIT) > IMMEDIATE
        if not self.is_adv_triggered:
            if self.adverse_entry_hypo_price is not None and self.adverse_entry_hypo_price > 0:
                return OrderStrategy.ADVERSE_DELAY_ENTRY
            if self.favorable_entry_hypo_price is not None and self.favorable_entry_hypo_price > 0:
                return OrderStrategy.FAVORABLE_DELAY_ENTRY

        return OrderStrategy.IMMEDIATE_ENTRY

    @computed_field  # type: ignore[prop-decorator]
    @property
    def current_exit_strategy(self) -> OrderStrategy:
        """Get current exit strategy based on exit_reason from Rust Worker."""
        return OrderStrategy.from_int_or_default(self.exit_reason, OrderStrategy.IMMEDIATE_EXIT)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def suggested_entry_price(self) -> Decimal | None:
        """Suggested entry price based on entry strategy, rounded to price_precision.

        - FAVORABLE_DELAY_ENTRY → favorable_entry_hypo_price (LIMIT order)
        - ADVERSE_DELAY_ENTRY → adverse_entry_hypo_price (STOP order)
        - IMMEDIATE_ENTRY → None (use market price)

        Returns:
            Decimal price rounded to price_precision, None for market orders.
        """
        strategy = self.current_entry_strategy
        if strategy == OrderStrategy.FAVORABLE_DELAY_ENTRY:
            return self.round_price(self.favorable_entry_hypo_price)
        elif strategy == OrderStrategy.ADVERSE_DELAY_ENTRY:
            return self.round_price(self.adverse_entry_hypo_price)
        return None

    @property
    def expected_loss_sl_price(self) -> Decimal | None:
        """Calculate SL price using expected_loss_pct.

        Fallback method when adverse_exit_hypo_price is NULL.
        Uses the entry order price (suggested_entry_price for pending,
        entry_price for triggered trades).

        Formula:
            LONG: sl = entry_price * (1 - expected_loss_pct)
            SHORT: sl = entry_price * (1 + expected_loss_pct)

        Returns:
            Calculated SL price, or None if insufficient data.
        """
        if self.expected_loss_pct is None or self.expected_loss_pct <= 0:
            return None

        # Use entry price: prefer suggested_entry_price (pending order)
        # then entry_price (triggered) or base_entry_price (fallback)
        entry_price = self.suggested_entry_price or self.entry_price or self.base_entry_price
        if entry_price is None or entry_price <= 0:
            return None

        if self.direction == TradeDirection.LONG:
            sl = entry_price * (1 - self.expected_loss_pct)
        else:  # SHORT
            sl = entry_price * (1 + self.expected_loss_pct)

        return self.round_price(sl)

    @property
    def effective_sl(self) -> Decimal | None:
        """Get effective SL price (theoretical, without spread), rounded to price_precision.

        Priority:
        1. adverse_exit_hypo_price (from Rust Worker Stage 4)
        2. expected_loss_sl_price (calculated from expected_loss_pct)

        Note: This returns theoretical price without spread adjustment.
        BrokerExecutor._get_spread_adjusted_prices() applies spread before order placement.

        This allows untriggered trades to have SL set from historical MAE
        when exit hypo prices are unavailable.
        """
        price = self.adverse_exit_hypo_price or self.expected_loss_sl_price
        return self.round_price(price)

    @property
    def effective_tp(self) -> Decimal | None:
        """Get effective TP price (theoretical, without spread), rounded to price_precision.

        Uses favorable_exit_hypo_price from Rust Worker Stage 4.
        """
        return self.round_price(self.favorable_exit_hypo_price)

    @property
    def effective_capital(self) -> Decimal:
        """Get effective capital considering override."""
        return self.capital_override if self.capital_override is not None else self.capital

    @property
    def risk_capital(self) -> Decimal:
        """Get risk capital per allocation."""
        if self.num_allocations <= 0:
            return self.effective_capital
        return self.effective_capital / self.num_allocations

    @property
    def is_terminal(self) -> bool:
        """Check if engagement is in terminal state."""
        return self.phase in (
            EngagementPhase.CLOSED,
            EngagementPhase.FAILED,
            EngagementPhase.CANCELLED,
            EngagementPhase.EXPIRED,
        )

    @property
    def has_open_position(self) -> bool:
        """Check if entry order is filled (position is open)."""
        return self.entry_status == OrderStatus.FILLED

    @property
    def needs_entry(self) -> bool:
        """Check if engagement needs entry execution."""
        return self.phase == EngagementPhase.PENDING and self.trade_status

    @property
    def is_limit_entry(self) -> bool:
        """Check if entry should use pending order based on current_entry_strategy."""
        return self.current_entry_strategy in (
            OrderStrategy.FAVORABLE_DELAY_ENTRY,
            OrderStrategy.ADVERSE_DELAY_ENTRY,
        )

    @property
    def needs_exit(self) -> bool:
        """Check if engagement needs exit execution.

        Returns False if:
        - Not in HOLDING phase
        - Trade signal still active (trade_status=True)
        - Exit order already filled (prevents duplicate exit submissions)
        """
        if self.phase != EngagementPhase.HOLDING:
            return False
        if self.trade_status:  # Signal still active
            return False
        # Check if exit order already filled
        if self.exit_status == OrderStatus.FILLED:
            return False
        return True

    @property
    def is_expired(self) -> bool:
        """Check if engagement should be marked as expired."""
        return self.phase == EngagementPhase.PENDING and not self.trade_status

    @property
    def has_pending_entry_order(self) -> bool:
        """Check if there's a pending entry order (ENTERING phase with unfilled order)."""
        return (
            self.phase == EngagementPhase.ENTERING
            and self.entry_broker_order_id is not None
            and self.entry_status in (OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED)
        )

    @property
    def needs_cancel_entry(self) -> bool:
        """Check if pending entry order should be cancelled.

        ENTERING + trade_status=False → cancel the pending order.
        """
        return self.has_pending_entry_order and not self.trade_status

    @property
    def needs_modify_entry(self) -> bool:
        """Check if pending entry order price should be modified.

        ENTERING + trade_status=True + suggested_entry_price differs from current.
        """
        if not self.has_pending_entry_order or not self.trade_status:
            return False

        # Check if suggested price differs from current order price
        return (
            self.suggested_entry_price is not None
            and self.current_entry_order_price is not None
            and self.suggested_entry_price != self.current_entry_order_price
        )

    @property
    def needs_modify(self) -> bool:
        """Check if SL/TP needs modification.

        Compares current orderbook SL/TP with effective values.
        Uses effective_sl/tp which falls back to exit hypo prices or expected_loss calculation.

        Uses tolerance-based comparison (0.1%) to account for spread adjustment:
        - Executor adjusts SL/TP prices for broker spread before sending orders
        - Orderbook records adjusted prices (with spread)
        - Effective prices are theoretical (without spread)
        - Direct equality comparison would always fail due to spread difference

        Returns False if:
        - Not in HOLDING phase
        - Trade signal not active (trade_status=False)
        - Exit order already filled (position already closed)
        """
        if self.phase != EngagementPhase.HOLDING or not self.trade_status:
            return False
        # Check if exit order already filled (position already closed)
        if self.exit_status == OrderStatus.FILLED:
            return False

        eff_sl = self.effective_sl
        eff_tp = self.effective_tp

        sl_needs_change = not self._is_price_within_tolerance(eff_sl, self.current_sl)
        tp_needs_change = not self._is_price_within_tolerance(eff_tp, self.current_tp)

        return sl_needs_change or tp_needs_change

    def _is_price_within_tolerance(
        self,
        suggested: Decimal | None,
        current: Decimal | None,
        tolerance_pct: Decimal = Decimal("0.001"),
    ) -> bool:
        """Check if current price is within tolerance of suggested price.

        Used to compare prices that may differ due to spread adjustment.
        Executor applies spread adjustment before sending orders to broker,
        so orderbook records adjusted prices while suggested prices are theoretical.

        Args:
            suggested: Theoretical price (from hypo prices, no spread)
            current: Actual price from orderbook (with spread adjustment)
            tolerance_pct: Tolerance percentage (default 0.1% = 0.001)

        Returns:
            True if prices are close enough (within tolerance) or no change needed
        """
        if suggested is None:
            return True  # No suggested price = no change needed
        if current is None:
            return False  # Has suggested but no current = need to set

        # Calculate tolerance based on suggested price
        tolerance = abs(suggested * tolerance_pct)
        return abs(suggested - current) <= tolerance

    # ============================================================
    # DECISION METHOD
    # ============================================================

    def determine_action(self) -> ActionType:
        """Determine next action based on phase, trade status, and order strategy.

        Decision logic:
        - Terminal phases → NONE (skip)
        - PENDING + trade closed → NONE (should mark EXPIRED, handled by caller)
        - PENDING + trade open + IMMEDIATE_ENTRY → MARKET_ENTRY
        - PENDING + trade open + FAVORABLE/ADVERSE_DELAY → LIMIT_ENTRY
        - ENTERING + trade closed → CANCEL_ORDER (cancel pending entry)
        - ENTERING + entry price changed → MODIFY_ORDER (modify pending entry)
        - HOLDING + trade closed → CLOSE_POSITION
        - HOLDING + trade open + SL/TP changed → MODIFY_POSITION
        - EXITING → NONE (waiting for broker callback)

        Returns:
            ActionType enum indicating what action to take.
        """
        # Terminal → skip
        if self.is_terminal:
            return ActionType.NONE

        # PENDING + trade closed → should mark EXPIRED (handled by caller)
        if self.is_expired:
            return ActionType.NONE

        # PENDING + trade open → entry (market or limit based on order_strategy)
        if self.needs_entry:
            if self.is_limit_entry:
                return ActionType.LIMIT_ENTRY
            return ActionType.MARKET_ENTRY

        # ENTERING + trade closed → cancel pending entry order
        if self.needs_cancel_entry:
            return ActionType.CANCEL_ORDER

        # ENTERING + entry price changed → modify pending entry order
        if self.needs_modify_entry:
            return ActionType.MODIFY_ORDER

        # HOLDING + trade closed → close position
        if self.needs_exit:
            return ActionType.CLOSE_POSITION

        # HOLDING + trade open + SL/TP changed → modify position
        if self.needs_modify:
            return ActionType.MODIFY_POSITION

        # EXITING / other → waiting
        return ActionType.NONE
