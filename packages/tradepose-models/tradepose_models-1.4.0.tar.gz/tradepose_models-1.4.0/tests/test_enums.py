"""Tests for new trading enums."""

import json

import pytest
from tradepose_models.enums import (
    ActionType,
    ExitReason,
    FillType,
    RejectReason,
    TimeInForce,
)


class TestActionType:
    """Tests for ActionType enum."""

    def test_action_type_values(self):
        """Test ActionType has all expected values."""
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
        """Test ActionType values are strings for JSON serialization."""
        for action in ActionType:
            assert isinstance(action.value, str)

    def test_action_type_member_count(self):
        """Test ActionType has exactly 7 members."""
        assert len(ActionType) == 7

    def test_action_type_from_string(self):
        """Test ActionType can be created from string."""
        assert ActionType("MARKET_ENTRY") == ActionType.MARKET_ENTRY
        assert ActionType("CLOSE_POSITION") == ActionType.CLOSE_POSITION

    def test_action_type_json_serialization(self):
        """Test ActionType serializes to JSON correctly."""
        data = {"action": ActionType.MARKET_ENTRY}
        json_str = json.dumps(data, default=str)
        assert "MARKET_ENTRY" in json_str


class TestExitReason:
    """Tests for ExitReason enum."""

    def test_exit_reason_values(self):
        """Test ExitReason has all expected values."""
        assert ExitReason.STOP_LOSS == "SL"
        assert ExitReason.TAKE_PROFIT == "TP"
        assert ExitReason.MANUAL == "MANUAL"
        assert ExitReason.SIGNAL == "SIGNAL"
        assert ExitReason.UNKNOWN == "UNKNOWN"

    def test_exit_reason_member_count(self):
        """Test ExitReason has exactly 5 members."""
        assert len(ExitReason) == 5

    def test_exit_reason_is_string_enum(self):
        """Test ExitReason values are strings."""
        for reason in ExitReason:
            assert isinstance(reason.value, str)

    def test_exit_reason_from_string(self):
        """Test ExitReason can be created from string value."""
        assert ExitReason("SL") == ExitReason.STOP_LOSS
        assert ExitReason("TP") == ExitReason.TAKE_PROFIT
        assert ExitReason("SIGNAL") == ExitReason.SIGNAL


class TestFillType:
    """Tests for FillType enum."""

    def test_fill_type_values(self):
        """Test FillType has all expected values."""
        assert FillType.FULL == "FULL"
        assert FillType.PARTIAL == "PARTIAL"

    def test_fill_type_member_count(self):
        """Test FillType has exactly 2 members."""
        assert len(FillType) == 2

    def test_fill_type_is_string_enum(self):
        """Test FillType values are strings."""
        for fill in FillType:
            assert isinstance(fill.value, str)

    def test_fill_type_from_string(self):
        """Test FillType can be created from string."""
        assert FillType("FULL") == FillType.FULL
        assert FillType("PARTIAL") == FillType.PARTIAL


class TestRejectReason:
    """Tests for RejectReason enum."""

    def test_reject_reason_values(self):
        """Test RejectReason has all expected values."""
        assert RejectReason.MARGIN_INSUFFICIENT == "MARGIN_INSUFFICIENT"
        assert RejectReason.PRICE_INVALID == "PRICE_INVALID"
        assert RejectReason.SYMBOL_INVALID == "SYMBOL_INVALID"
        assert RejectReason.VOLUME_INVALID == "VOLUME_INVALID"
        assert RejectReason.MARKET_CLOSED == "MARKET_CLOSED"
        assert RejectReason.POSITION_LIMIT == "POSITION_LIMIT"
        assert RejectReason.TRADE_DISABLED == "TRADE_DISABLED"
        assert RejectReason.REQUOTE == "REQUOTE"
        assert RejectReason.BROKER_REJECT == "BROKER_REJECT"
        assert RejectReason.INVALID_ORDER == "INVALID_ORDER"
        assert RejectReason.RISK_LIMIT_EXCEEDED == "RISK_LIMIT_EXCEEDED"
        assert RejectReason.UNKNOWN == "UNKNOWN"

    def test_reject_reason_member_count(self):
        """Test RejectReason has exactly 12 members."""
        assert len(RejectReason) == 12

    def test_reject_reason_is_string_enum(self):
        """Test RejectReason values are strings."""
        for reason in RejectReason:
            assert isinstance(reason.value, str)

    def test_reject_reason_from_string(self):
        """Test RejectReason can be created from string."""
        assert RejectReason("MARGIN_INSUFFICIENT") == RejectReason.MARGIN_INSUFFICIENT
        assert RejectReason("UNKNOWN") == RejectReason.UNKNOWN

    def test_reject_reason_common_mappings(self):
        """Test common reject reasons that map from broker error codes."""
        # These are commonly mapped from MT5 retcodes
        common_reasons = [
            RejectReason.MARGIN_INSUFFICIENT,
            RejectReason.PRICE_INVALID,
            RejectReason.VOLUME_INVALID,
            RejectReason.MARKET_CLOSED,
            RejectReason.BROKER_REJECT,
        ]
        for reason in common_reasons:
            assert reason in RejectReason


class TestTimeInForce:
    """Tests for TimeInForce enum."""

    def test_time_in_force_values(self):
        """Test TimeInForce has all expected values."""
        assert TimeInForce.GTC == "gtc"
        assert TimeInForce.IOC == "ioc"
        assert TimeInForce.FOK == "fok"

    def test_time_in_force_member_count(self):
        """Test TimeInForce has exactly 3 members."""
        assert len(TimeInForce) == 3

    def test_time_in_force_is_string_enum(self):
        """Test TimeInForce is a StrEnum with lowercase values."""
        for tif in TimeInForce:
            assert isinstance(tif.value, str)
            assert tif.value.islower()

    def test_time_in_force_from_string(self):
        """Test TimeInForce can be created from string."""
        assert TimeInForce("gtc") == TimeInForce.GTC
        assert TimeInForce("ioc") == TimeInForce.IOC
        assert TimeInForce("fok") == TimeInForce.FOK

    def test_time_in_force_str_representation(self):
        """Test TimeInForce str() returns the value directly."""
        # StrEnum makes str(enum) == enum.value
        assert str(TimeInForce.GTC) == "gtc"
        assert str(TimeInForce.IOC) == "ioc"
        assert str(TimeInForce.FOK) == "fok"


class TestEnumJsonSerialization:
    """Tests for JSON serialization of all new enums."""

    def test_all_enums_serialize_to_json(self):
        """Test all enums can be serialized in JSON."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            action: ActionType
            exit_reason: ExitReason
            fill_type: FillType
            reject_reason: RejectReason
            time_in_force: TimeInForce

        model = TestModel(
            action=ActionType.MARKET_ENTRY,
            exit_reason=ExitReason.STOP_LOSS,
            fill_type=FillType.FULL,
            reject_reason=RejectReason.MARGIN_INSUFFICIENT,
            time_in_force=TimeInForce.GTC,
        )

        # Serialize to dict
        data = model.model_dump()
        assert data["action"] == "MARKET_ENTRY"
        assert data["exit_reason"] == "SL"
        assert data["fill_type"] == "FULL"
        assert data["reject_reason"] == "MARGIN_INSUFFICIENT"
        assert data["time_in_force"] == "gtc"

        # Serialize to JSON
        json_str = model.model_dump_json()
        assert "MARKET_ENTRY" in json_str
        assert "SL" in json_str

    def test_all_enums_deserialize_from_json(self):
        """Test all enums can be deserialized from JSON."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            action: ActionType
            exit_reason: ExitReason
            fill_type: FillType
            reject_reason: RejectReason
            time_in_force: TimeInForce

        json_str = """
        {
            "action": "CLOSE_POSITION",
            "exit_reason": "TP",
            "fill_type": "PARTIAL",
            "reject_reason": "UNKNOWN",
            "time_in_force": "ioc"
        }
        """

        model = TestModel.model_validate_json(json_str)
        assert model.action == ActionType.CLOSE_POSITION
        assert model.exit_reason == ExitReason.TAKE_PROFIT
        assert model.fill_type == FillType.PARTIAL
        assert model.reject_reason == RejectReason.UNKNOWN
        assert model.time_in_force == TimeInForce.IOC


class TestEnumInvalidValues:
    """Tests for handling invalid enum values."""

    def test_action_type_invalid_value_raises(self):
        """Test invalid ActionType value raises ValueError."""
        with pytest.raises(ValueError):
            ActionType("INVALID")

    def test_exit_reason_invalid_value_raises(self):
        """Test invalid ExitReason value raises ValueError."""
        with pytest.raises(ValueError):
            ExitReason("INVALID")

    def test_fill_type_invalid_value_raises(self):
        """Test invalid FillType value raises ValueError."""
        with pytest.raises(ValueError):
            FillType("INVALID")

    def test_reject_reason_invalid_value_raises(self):
        """Test invalid RejectReason value raises ValueError."""
        with pytest.raises(ValueError):
            RejectReason("INVALID")

    def test_time_in_force_invalid_value_raises(self):
        """Test invalid TimeInForce value raises ValueError."""
        with pytest.raises(ValueError):
            TimeInForce("invalid")
