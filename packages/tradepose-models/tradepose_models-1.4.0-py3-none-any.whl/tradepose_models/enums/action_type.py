"""Action types for engagement signal execution."""

from enum import Enum


class ActionType(str, Enum):
    """Engagement action type determined by EngagementContext.determine_action().

    Used by BrokerExecutor.process_engagement() to route to appropriate method:
    - MARKET_ENTRY → execute_market_entry()
    - LIMIT_ENTRY → execute_limit_entry()
    - CLOSE_POSITION → execute_close_position()
    - MODIFY_POSITION → execute_modify_position()
    - MODIFY_ORDER → execute_modify_order()
    - CANCEL_ORDER → execute_cancel_order()
    - NONE → no action
    """

    # Entry actions
    MARKET_ENTRY = "MARKET_ENTRY"
    LIMIT_ENTRY = "LIMIT_ENTRY"

    # Position actions
    CLOSE_POSITION = "CLOSE_POSITION"
    MODIFY_POSITION = "MODIFY_POSITION"

    # Order actions
    MODIFY_ORDER = "MODIFY_ORDER"
    CANCEL_ORDER = "CANCEL_ORDER"

    # No action
    NONE = "NONE"
