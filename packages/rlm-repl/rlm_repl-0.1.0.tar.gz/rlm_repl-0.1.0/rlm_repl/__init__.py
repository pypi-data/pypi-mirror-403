"""
RLM-REPL: Recursive Language Model with REPL Inference Strategy

A Python library that enables any model to manage unlimited context
using SQL-based retrieval with DuckDB.

Example usage:
    from rlm_repl import RLMREPL, RLMConfig

    config = RLMConfig(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        model="qwen3-coder"
    )

    repl = RLMREPL(config)
    repl.load_document("large_document.txt")
    answer = repl.ask("What are the main themes?")
"""

__version__ = "0.1.0"
__author__ = "Remy Gakwaya"

from rlm_repl.core.config import RLMConfig, DatabaseConfig
from rlm_repl.core.database import DocumentDatabase
from rlm_repl.core.repl import RLMREPL
from rlm_repl.events.streaming import (
    Event,
    EventType,
    IterationStartEvent,
    IterationEndEvent,
    SQLExecuteEvent,
    ResultsEvent,
    SynthesisEvent,
    AnswerEvent,
    ErrorEvent,
)

__all__ = [
    # Core
    "RLMREPL",
    "RLMConfig",
    "DatabaseConfig",
    "DocumentDatabase",
    # Events
    "Event",
    "EventType",
    "IterationStartEvent",
    "IterationEndEvent",
    "SQLExecuteEvent",
    "ResultsEvent",
    "SynthesisEvent",
    "AnswerEvent",
    "ErrorEvent",
]
