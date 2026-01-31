#!/usr/bin/env python3
"""Example showing programmatic API usage of RLM-REPL.

This example demonstrates how to use RLM-REPL as a library in your
Python applications, including error handling and custom configuration.
"""

import sys
from typing import List, Dict, Any

from rlm_repl import RLMREPL, RLMConfig, DatabaseConfig
from rlm_repl.core.database import DocumentDatabase, QueryResult
from rlm_repl.events.streaming import Event, EventType


class DocumentQA:
    """A simple document Q&A system built on RLM-REPL."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "ollama",
        model: str = "qwen3-coder",
    ):
        """Initialize the Q&A system."""
        self.config = RLMConfig(
            base_url=base_url,
            api_key=api_key,
            model=model,
            verbose=False,  # We'll handle output ourselves
            max_iterations=6,
        )
        self._repl = RLMREPL(self.config)
        self._questions_asked = 0

    def load_file(self, filepath: str) -> Dict[str, Any]:
        """Load a document file.

        Args:
            filepath: Path to the text file.

        Returns:
            Dictionary with document statistics.

        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        stats = self._repl.load_document(filepath)
        return {
            "name": stats.doc_name,
            "lines": stats.total_lines,
            "words": stats.total_words,
            "strategic_markers": stats.strategic_lines,
        }

    def load_content(self, content: str, name: str = "document") -> Dict[str, Any]:
        """Load text content directly.

        Args:
            content: Text content to load.
            name: Name for the document.

        Returns:
            Dictionary with document statistics.
        """
        stats = self._repl.load_text(content, name)
        return {
            "name": stats.doc_name,
            "lines": stats.total_lines,
            "words": stats.total_words,
            "strategic_markers": stats.strategic_lines,
        }

    def ask(self, question: str) -> Dict[str, Any]:
        """Ask a question about the loaded document.

        Args:
            question: The question to ask.

        Returns:
            Dictionary with answer and metadata.

        Raises:
            RuntimeError: If no document is loaded.
        """
        if not self._repl.is_loaded:
            raise RuntimeError("No document loaded")

        result = self._repl.ask(question)
        self._questions_asked += 1

        return {
            "question": question,
            "answer": result.answer,
            "iterations": result.iterations,
            "lines_read": result.unique_lines,
            "words_read": result.total_words,
            "time_seconds": result.elapsed_time,
        }

    def execute_sql(self, sql: str) -> List[Dict[str, Any]]:
        """Execute a raw SQL query.

        Args:
            sql: SQL query string.

        Returns:
            List of result rows as dictionaries.
        """
        result = self._repl.query(sql)
        return result.dataframe.to_dict("records")

    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics.

        Returns:
            Dictionary with session statistics.
        """
        stats = self._repl.session_stats()
        stats["document"] = None

        if self._repl.is_loaded:
            doc_stats = self._repl.stats
            stats["document"] = {
                "name": doc_stats.doc_name,
                "lines": doc_stats.total_lines,
                "words": doc_stats.total_words,
            }

        return stats

    def close(self):
        """Close the Q&A system and release resources."""
        self._repl.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """Demonstrate API usage."""
    print("=" * 70)
    print("RLM-REPL API Usage Example")
    print("=" * 70)

    # Create the Q&A system
    with DocumentQA() as qa:
        # Load a document
        content = qa.load_file("examples/library.txt")

        print("\n1. Loading document...")
        print(f"   Loaded: {content['lines']} lines, {content['words']} words")

        print("\n2. Asking questions...")

        # Ask multiple questions
        questions = [
            "What is the main topic of this document?",
            "What are the key sections or chapters?",
        ]

        for question in questions:
            print(f"\n   Q: {question}")
            try:
                result = qa.ask(question)
                print(f"   A: {result['answer']}")  # Show full answer, not truncated
                print(f"   (Read {result['lines_read']} lines in {result['time_seconds']:.1f}s)")
            except Exception as e:
                print(f"   Error: {e}")

        print("\n3. Direct SQL query...")
        rows = qa.execute_sql(
            "SELECT line_num, text FROM documents WHERE is_header = true LIMIT 5"
        )
        print("   Headers found:")
        for row in rows:
            print(f"   - Line {row['line_num']}: {row['text']}")

        print("\n4. Session statistics...")
        session_stats = qa.get_stats()
        print(f"   Questions asked: {session_stats['questions_asked']}")
        print(f"   Total words read: {session_stats.get('total_words_read', 0)}")

    print("\n" + "=" * 70)
    print("Done!")


if __name__ == "__main__":
    main()
