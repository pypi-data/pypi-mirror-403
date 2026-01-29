"""Unit tests for Trade Event models.

Tests for:
- TradesPersistedEvent
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError
from tradepose_models.events import TradesPersistedEvent


class TestTradesPersistedEvent:
    """Tests for TradesPersistedEvent model."""

    def test_create_with_all_fields(self):
        """Test creating TradesPersistedEvent with all fields."""
        user_id = uuid4()
        task_id = uuid4()
        timestamp = datetime.now(timezone.utc)

        event = TradesPersistedEvent(
            user_id=user_id,
            task_id=task_id,
            trades_count=100,
            strategy_names=["Strategy1", "Strategy2"],
            timestamp=timestamp,
        )

        assert event.event_type == "trades_persisted"
        assert event.user_id == user_id
        assert event.task_id == task_id
        assert event.trades_count == 100
        assert event.strategy_names == ["Strategy1", "Strategy2"]
        assert event.timestamp == timestamp

    def test_default_event_type(self):
        """Test that event_type defaults to 'trades_persisted'."""
        event = TradesPersistedEvent(
            user_id=uuid4(),
            task_id=uuid4(),
            trades_count=50,
            timestamp=datetime.now(timezone.utc),
        )

        assert event.event_type == "trades_persisted"

    def test_default_strategy_names(self):
        """Test that strategy_names defaults to empty list."""
        event = TradesPersistedEvent(
            user_id=uuid4(),
            task_id=uuid4(),
            trades_count=0,
            timestamp=datetime.now(timezone.utc),
        )

        assert event.strategy_names == []

    def test_required_fields_validation(self):
        """Test that required fields raise validation error when missing."""
        with pytest.raises(ValidationError) as exc_info:
            TradesPersistedEvent(
                user_id=uuid4(),
                # missing task_id, trades_count, timestamp
            )

        errors = exc_info.value.errors()
        error_fields = {e["loc"][0] for e in errors}
        assert "task_id" in error_fields
        assert "trades_count" in error_fields
        assert "timestamp" in error_fields

    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        user_id = uuid4()
        task_id = uuid4()
        timestamp = datetime.now(timezone.utc)

        event = TradesPersistedEvent(
            user_id=user_id,
            task_id=task_id,
            trades_count=75,
            strategy_names=["StrategyA", "StrategyB"],
            timestamp=timestamp,
        )

        json_str = event.model_dump_json()
        assert "trades_persisted" in json_str
        assert str(user_id) in json_str
        assert str(task_id) in json_str

        # Deserialize and verify
        restored = TradesPersistedEvent.model_validate_json(json_str)
        assert restored.event_type == event.event_type
        assert restored.user_id == event.user_id
        assert restored.task_id == event.task_id
        assert restored.trades_count == event.trades_count
        assert restored.strategy_names == event.strategy_names

    def test_single_strategy(self):
        """Test with single strategy name."""
        event = TradesPersistedEvent(
            user_id=uuid4(),
            task_id=uuid4(),
            trades_count=25,
            strategy_names=["SingleStrategy"],
            timestamp=datetime.now(timezone.utc),
        )

        assert len(event.strategy_names) == 1
        assert event.strategy_names[0] == "SingleStrategy"

    def test_many_strategies(self):
        """Test with many strategy names."""
        strategies = [f"Strategy{i}" for i in range(10)]

        event = TradesPersistedEvent(
            user_id=uuid4(),
            task_id=uuid4(),
            trades_count=500,
            strategy_names=strategies,
            timestamp=datetime.now(timezone.utc),
        )

        assert len(event.strategy_names) == 10
        assert event.strategy_names == strategies

    def test_zero_trades_count(self):
        """Test with zero trades count."""
        event = TradesPersistedEvent(
            user_id=uuid4(),
            task_id=uuid4(),
            trades_count=0,
            strategy_names=[],
            timestamp=datetime.now(timezone.utc),
        )

        assert event.trades_count == 0
