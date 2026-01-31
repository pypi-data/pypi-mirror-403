"""Streaming events for RLM-REPL progress tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
import pandas as pd


class EventType(Enum):
    """Types of events emitted during REPL execution."""

    # Lifecycle events
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    DOCUMENT_LOADED = "document_loaded"

    # Question processing events
    QUESTION_START = "question_start"
    QUESTION_END = "question_end"

    # Iteration events
    ITERATION_START = "iteration_start"
    ITERATION_END = "iteration_end"

    # SQL execution events
    SQL_EXECUTE = "sql_execute"
    SQL_RESULT = "sql_result"

    # LLM events
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"

    # Results and synthesis
    RESULTS = "results"
    SYNTHESIS_START = "synthesis_start"
    SYNTHESIS_END = "synthesis_end"
    ANSWER = "answer"

    # Error events
    ERROR = "error"
    WARNING = "warning"


@dataclass
class Event:
    """Base event class for all streaming events."""

    type: Optional[EventType] = None
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }


@dataclass
class IterationStartEvent(Event):
    """Event emitted when a reading iteration starts."""

    iteration: int = 0
    max_iterations: int = 6

    def __post_init__(self):
        self.type = EventType.ITERATION_START
        self.data = {
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
        }


@dataclass
class IterationEndEvent(Event):
    """Event emitted when a reading iteration ends."""

    iteration: int = 0
    thought: str = ""
    reading_mode: str = ""
    goal: str = ""
    satisfied: bool = False
    next_move: str = ""

    def __post_init__(self):
        self.type = EventType.ITERATION_END
        self.data = {
            "iteration": self.iteration,
            "thought": self.thought,
            "reading_mode": self.reading_mode,
            "goal": self.goal,
            "satisfied": self.satisfied,
            "next_move": self.next_move,
        }


@dataclass
class SQLExecuteEvent(Event):
    """Event emitted when a SQL query is about to be executed."""

    sql: str = ""
    auto_fixed: bool = False
    original_sql: Optional[str] = None

    def __post_init__(self):
        self.type = EventType.SQL_EXECUTE
        self.data = {
            "sql": self.sql,
            "auto_fixed": self.auto_fixed,
            "original_sql": self.original_sql,
        }


@dataclass
class ResultsEvent(Event):
    """Event emitted when query results are received."""

    row_count: int = 0
    word_count: int = 0
    preview: Optional[List[Dict[str, Any]]] = None

    def __post_init__(self):
        self.type = EventType.RESULTS
        self.data = {
            "row_count": self.row_count,
            "word_count": self.word_count,
            "preview": self.preview,
        }


@dataclass
class SynthesisEvent(Event):
    """Event emitted during answer synthesis."""

    stage: str = ""  # "start", "processing", "complete"
    total_lines: int = 0
    total_words: int = 0

    def __post_init__(self):
        self.type = EventType.SYNTHESIS_START if self.stage == "start" else EventType.SYNTHESIS_END
        self.data = {
            "stage": self.stage,
            "total_lines": self.total_lines,
            "total_words": self.total_words,
        }


@dataclass
class AnswerEvent(Event):
    """Event emitted when the final answer is ready."""

    answer: str = ""
    iterations: int = 0
    total_lines: int = 0
    total_words: int = 0
    elapsed_time: float = 0.0

    def __post_init__(self):
        self.type = EventType.ANSWER
        self.data = {
            "answer": self.answer,
            "iterations": self.iterations,
            "total_lines": self.total_lines,
            "total_words": self.total_words,
            "elapsed_time": self.elapsed_time,
        }


@dataclass
class ErrorEvent(Event):
    """Event emitted when an error occurs."""

    error: str = ""
    error_type: str = ""
    recoverable: bool = True

    def __post_init__(self):
        self.type = EventType.ERROR
        self.data = {
            "error": self.error,
            "error_type": self.error_type,
            "recoverable": self.recoverable,
        }


class EventEmitter:
    """Manages event emission and subscription."""

    def __init__(self):
        self._callbacks: List[callable] = []

    def subscribe(self, callback: callable):
        """Subscribe to events.

        Args:
            callback: Function that takes an Event as argument.
        """
        self._callbacks.append(callback)

    def unsubscribe(self, callback: callable):
        """Unsubscribe from events."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def emit(self, event: Event):
        """Emit an event to all subscribers."""
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception:
                # Don't let callback errors break the main flow
                pass

    def clear(self):
        """Remove all subscribers."""
        self._callbacks.clear()
