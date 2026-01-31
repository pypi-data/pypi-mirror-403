"""Tests for the streaming events system."""

import pytest
from datetime import datetime
from rlm_repl.events.streaming import (
    Event,
    EventType,
    EventEmitter,
    IterationStartEvent,
    IterationEndEvent,
    SQLExecuteEvent,
    ResultsEvent,
    AnswerEvent,
    ErrorEvent,
)


class TestEventType:
    """Tests for EventType enum."""

    def test_event_types_exist(self):
        """Test that expected event types exist."""
        assert EventType.SESSION_START
        assert EventType.DOCUMENT_LOADED
        assert EventType.QUESTION_START
        assert EventType.ITERATION_START
        assert EventType.SQL_EXECUTE
        assert EventType.RESULTS
        assert EventType.ANSWER
        assert EventType.ERROR


class TestEvent:
    """Tests for Event class."""

    def test_event_creation(self):
        """Test basic event creation."""
        event = Event(type=EventType.SESSION_START)
        assert event.type == EventType.SESSION_START
        assert isinstance(event.timestamp, datetime)
        assert event.data == {}

    def test_event_with_data(self):
        """Test event with custom data."""
        event = Event(
            type=EventType.QUESTION_START,
            data={"question": "Test question"},
        )
        assert event.data["question"] == "Test question"

    def test_event_to_dict(self):
        """Test event serialization."""
        event = Event(
            type=EventType.SESSION_START,
            data={"key": "value"},
        )
        result = event.to_dict()

        assert result["type"] == "session_start"
        assert "timestamp" in result
        assert result["data"]["key"] == "value"


class TestSpecializedEvents:
    """Tests for specialized event classes."""

    def test_iteration_start_event(self):
        """Test IterationStartEvent."""
        event = IterationStartEvent(iteration=2, max_iterations=6)

        assert event.type == EventType.ITERATION_START
        assert event.data["iteration"] == 2
        assert event.data["max_iterations"] == 6

    def test_iteration_end_event(self):
        """Test IterationEndEvent."""
        event = IterationEndEvent(
            iteration=1,
            thought="I found relevant info",
            reading_mode="search",
            goal="Find keywords",
            satisfied=False,
            next_move="Read more context",
        )

        assert event.type == EventType.ITERATION_END
        assert event.data["iteration"] == 1
        assert event.data["thought"] == "I found relevant info"
        assert event.data["satisfied"] is False

    def test_sql_execute_event(self):
        """Test SQLExecuteEvent."""
        event = SQLExecuteEvent(
            sql="SELECT * FROM documents",
            auto_fixed=True,
            original_sql="SELECT * FROM docs",
        )

        assert event.type == EventType.SQL_EXECUTE
        assert event.data["sql"] == "SELECT * FROM documents"
        assert event.data["auto_fixed"] is True

    def test_results_event(self):
        """Test ResultsEvent."""
        event = ResultsEvent(
            row_count=50,
            word_count=1000,
            preview=[{"line_num": 1, "text": "Test"}],
        )

        assert event.type == EventType.RESULTS
        assert event.data["row_count"] == 50
        assert event.data["word_count"] == 1000

    def test_answer_event(self):
        """Test AnswerEvent."""
        event = AnswerEvent(
            answer="The answer is 42",
            iterations=3,
            total_lines=100,
            total_words=5000,
            elapsed_time=2.5,
        )

        assert event.type == EventType.ANSWER
        assert event.data["answer"] == "The answer is 42"
        assert event.data["elapsed_time"] == 2.5

    def test_error_event(self):
        """Test ErrorEvent."""
        event = ErrorEvent(
            error="Connection failed",
            error_type="ConnectionError",
            recoverable=True,
        )

        assert event.type == EventType.ERROR
        assert event.data["error"] == "Connection failed"
        assert event.data["recoverable"] is True


class TestEventEmitter:
    """Tests for EventEmitter."""

    def test_subscribe_and_emit(self):
        """Test subscribing and emitting events."""
        emitter = EventEmitter()
        received = []

        def callback(event):
            received.append(event)

        emitter.subscribe(callback)
        event = Event(type=EventType.SESSION_START)
        emitter.emit(event)

        assert len(received) == 1
        assert received[0] == event

    def test_multiple_subscribers(self):
        """Test multiple subscribers receive events."""
        emitter = EventEmitter()
        received1 = []
        received2 = []

        emitter.subscribe(lambda e: received1.append(e))
        emitter.subscribe(lambda e: received2.append(e))

        event = Event(type=EventType.SESSION_START)
        emitter.emit(event)

        assert len(received1) == 1
        assert len(received2) == 1

    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        emitter = EventEmitter()
        received = []

        def callback(event):
            received.append(event)

        emitter.subscribe(callback)
        emitter.unsubscribe(callback)
        emitter.emit(Event(type=EventType.SESSION_START))

        assert len(received) == 0

    def test_clear(self):
        """Test clearing all subscribers."""
        emitter = EventEmitter()

        emitter.subscribe(lambda e: None)
        emitter.subscribe(lambda e: None)
        emitter.clear()

        # Should not raise
        emitter.emit(Event(type=EventType.SESSION_START))

    def test_callback_error_isolation(self):
        """Test that callback errors don't break other callbacks."""
        emitter = EventEmitter()
        received = []

        def bad_callback(event):
            raise ValueError("Error!")

        def good_callback(event):
            received.append(event)

        emitter.subscribe(bad_callback)
        emitter.subscribe(good_callback)

        event = Event(type=EventType.SESSION_START)
        emitter.emit(event)  # Should not raise

        assert len(received) == 1
