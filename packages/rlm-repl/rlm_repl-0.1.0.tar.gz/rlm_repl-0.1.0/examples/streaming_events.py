#!/usr/bin/env python3
"""Example showing streaming events in RLM-REPL.

This example demonstrates how to subscribe to events during processing
for real-time progress tracking.
"""

from rlm_repl import (
    RLMREPL,
    RLMConfig,
    Event,
    EventType,
    IterationStartEvent,
    ResultsEvent,
    AnswerEvent,
)


def event_handler(event: Event):
    """Handle streaming events."""
    if event.type == EventType.DOCUMENT_LOADED:
        print(f"[EVENT] Document loaded: {event.data.get('total_lines')} lines")

    elif event.type == EventType.QUESTION_START:
        print(f"[EVENT] Processing question: {event.data.get('question')}")

    elif event.type == EventType.ITERATION_START:
        data = event.data
        print(f"[EVENT] Starting iteration {data.get('iteration') + 1}/{data.get('max_iterations')}")

    elif event.type == EventType.SQL_EXECUTE:
        sql = event.data.get('sql', '')[:80]
        print(f"[EVENT] Executing SQL: {sql}...")

    elif event.type == EventType.RESULTS:
        print(f"[EVENT] Got {event.data.get('row_count')} rows, {event.data.get('word_count')} words")

    elif event.type == EventType.ITERATION_END:
        if event.data.get('satisfied'):
            print("[EVENT] LLM is satisfied with gathered information")
        else:
            print(f"[EVENT] Next: {event.data.get('next_move', '')[:60]}...")

    elif event.type == EventType.SYNTHESIS_START:
        print("[EVENT] Starting answer synthesis...")

    elif event.type == EventType.SYNTHESIS_END:
        print("[EVENT] Synthesis complete")

    elif event.type == EventType.ANSWER:
        print(f"[EVENT] Answer ready ({event.data.get('elapsed_time', 0):.1f}s)")

    elif event.type == EventType.ERROR:
        print(f"[EVENT] ERROR: {event.data.get('error')}")


def main():
    # Create config with event callback
    config = RLMConfig(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        model="qwen3-coder",
        verbose=False,  # Disable verbose to see only events
        max_iterations=4,
        on_event=event_handler,  # Subscribe to events
    )

    # Alternative: subscribe after creation
    # repl = RLMREPL(config)
    # repl.subscribe(event_handler)

    with RLMREPL(config) as repl:
        # Load sample text
        repl.load_text("""
        # Python Programming Guide

        Python is a high-level, interpreted programming language known for its
        simplicity and readability. Created by Guido van Rossum and first released
        in 1991, Python has become one of the most popular programming languages.

        ## Key Features

        1. Easy to Learn: Python has a simple syntax that emphasizes readability.
        2. Versatile: Used in web development, data science, AI, automation, etc.
        3. Large Standard Library: Comes with batteries included.
        4. Cross-platform: Runs on Windows, macOS, Linux, and more.

        ## Data Types

        Python supports several built-in data types:
        - Numbers: int, float, complex
        - Strings: str (immutable sequences of characters)
        - Lists: Mutable ordered sequences
        - Tuples: Immutable ordered sequences
        - Dictionaries: Key-value pairs
        - Sets: Unordered collections of unique elements

        ## Functions

        Functions in Python are defined using the 'def' keyword:

        def greet(name):
            return f"Hello, {name}!"

        Python also supports lambda functions for simple operations:

        square = lambda x: x ** 2

        ## Object-Oriented Programming

        Python supports object-oriented programming with classes:

        class Person:
            def __init__(self, name, age):
                self.name = name
                self.age = age

            def greet(self):
                return f"Hi, I'm {self.name}"
        """, "python_guide")

        print("\n" + "=" * 70)
        print("Event-driven processing")
        print("=" * 70 + "\n")

        result = repl.ask("What are Python's main data types?")

        print("\n" + "=" * 70)
        print("FINAL ANSWER:")
        print("=" * 70)
        print(result.answer)


if __name__ == "__main__":
    main()
