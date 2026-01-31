"""Main REPL engine for RLM-REPL."""

import time
from typing import Optional, List, Dict, Any, Generator, Callable
from dataclasses import dataclass
import pandas as pd

from rlm_repl.core.config import RLMConfig
from rlm_repl.core.database import DocumentDatabase, DocumentStats, QueryResult
from rlm_repl.inference.client import InferenceClient, LLMResponse
from rlm_repl.inference.strategy import ReadingStrategy, ReadingHistory
from rlm_repl.inference.synthesizer import AnswerSynthesizer
from rlm_repl.events.streaming import (
    Event,
    EventType,
    EventEmitter,
    IterationStartEvent,
    IterationEndEvent,
    SQLExecuteEvent,
    ResultsEvent,
    SynthesisEvent,
    AnswerEvent,
    ErrorEvent,
)
from rlm_repl.utils.formatting import (
    format_preview,
    format_stats,
    truncate_text,
)


@dataclass
class QuestionResult:
    """Result of asking a question."""

    answer: str
    iterations: int
    unique_lines: int
    total_words: int
    elapsed_time: float
    history: List[ReadingHistory]


class RLMREPL:
    """Recursive Language Model REPL for unlimited context management.

    The main class that orchestrates document loading, SQL-based retrieval,
    and LLM-powered question answering with human-like reading strategies.

    Example:
        from rlm_repl import RLMREPL, RLMConfig

        config = RLMConfig(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            model="qwen3-coder"
        )

        repl = RLMREPL(config)
        repl.load_document("book.txt")
        result = repl.ask("What are the main themes?")
        print(result.answer)

    For streaming events:
        def on_event(event):
            print(f"Event: {event.type.value}")

        config = config.with_callback(on_event)
        repl = RLMREPL(config)
    """

    def __init__(self, config: RLMConfig):
        """Initialize the REPL.

        Args:
            config: Configuration for the REPL.
        """
        self.config = config
        self._db = DocumentDatabase(config.database)
        self._client = InferenceClient(
            base_url=config.base_url,
            api_key=config.api_key,
            model=config.model,
            temperature=config.temperature,
        )
        self._strategy = ReadingStrategy(config.database.table_name)
        self._synthesizer = AnswerSynthesizer(
            self._client,
            self._strategy,
            temperature=config.synthesis_temperature,
        )
        self._events = EventEmitter()
        self._conversation_history: List[Dict[str, Any]] = []

        # Set up event callback if provided
        if config.on_event:
            self._events.subscribe(config.on_event)

        if config.verbose:
            self._print_init_info()

    def _print_init_info(self):
        """Print initialization information."""
        print("=" * 70)
        print("RLM-REPL - Recursive Language Model with SQL Retrieval")
        print("=" * 70)
        print(f"Model: {self.config.model}")
        print(f"Strategy: Overview -> Search -> Deep Read")
        print(f"Max iterations: {self.config.max_iterations}")
        print(f"Database: {'Persistent' if self.config.database.persistent else 'In-memory'}")

    @property
    def database(self) -> DocumentDatabase:
        """Access the underlying database."""
        return self._db

    @property
    def is_loaded(self) -> bool:
        """Check if a document is loaded."""
        return self._db.is_loaded

    @property
    def stats(self) -> Optional[DocumentStats]:
        """Get document statistics."""
        return self._db.stats

    def load_document(
        self,
        filepath: str,
        doc_name: Optional[str] = None,
    ) -> DocumentStats:
        """Load a document from file.

        Args:
            filepath: Path to the text file.
            doc_name: Optional name for the document.

        Returns:
            DocumentStats with information about the loaded document.
        """
        if self.config.verbose:
            print(f"\nLoading: {filepath}")

        stats = self._db.load_document(filepath, doc_name)

        self._emit(Event(
            type=EventType.DOCUMENT_LOADED,
            data={
                "filepath": filepath,
                "doc_name": stats.doc_name,
                "total_lines": stats.total_lines,
                "total_words": stats.total_words,
            },
        ))

        if self.config.verbose:
            print(f"Loaded {stats.total_lines:,} lines ({stats.total_words:,} words)")
            print(f"Strategic markers: {stats.strategic_lines:,}")

        return stats

    def load_text(self, text: str, doc_name: str = "text") -> DocumentStats:
        """Load text content directly.

        Args:
            text: Text content to load.
            doc_name: Name for the document.

        Returns:
            DocumentStats with information about the loaded document.
        """
        stats = self._db.load_text(text, doc_name)

        self._emit(Event(
            type=EventType.DOCUMENT_LOADED,
            data={
                "doc_name": stats.doc_name,
                "total_lines": stats.total_lines,
                "total_words": stats.total_words,
            },
        ))

        if self.config.verbose:
            print(f"Loaded {stats.total_lines:,} lines ({stats.total_words:,} words)")

        return stats

    def load_dataframe(
        self,
        df: pd.DataFrame,
        doc_name: str = "dataframe",
    ) -> DocumentStats:
        """Load a pandas DataFrame.

        Args:
            df: DataFrame with at minimum a 'text' column.
            doc_name: Name for the document.

        Returns:
            DocumentStats with information about the loaded document.
        """
        stats = self._db.load_dataframe(df, doc_name)

        self._emit(Event(
            type=EventType.DOCUMENT_LOADED,
            data={
                "doc_name": stats.doc_name,
                "total_lines": stats.total_lines,
                "total_words": stats.total_words,
            },
        ))

        return stats

    def ask(self, question: str) -> QuestionResult:
        """Ask a question about the loaded document.

        This is the main entry point for querying. It performs multiple
        reading iterations using human-like strategies (overview, search,
        deep read) and synthesizes a final answer.

        Args:
            question: The question to answer.

        Returns:
            QuestionResult with answer and statistics.

        Raises:
            RuntimeError: If no document is loaded.
        """
        if not self.is_loaded:
            raise RuntimeError("No document loaded. Call load_document() first.")

        self._emit(Event(
            type=EventType.QUESTION_START,
            data={"question": question},
        ))

        if self.config.verbose:
            print(f"\nQuestion: {question}")
            print("=" * 70)

        start_time = time.time()
        reading_history: List[ReadingHistory] = []
        all_results: List[pd.DataFrame] = []

        # Main reading loop
        for iteration in range(self.config.max_iterations):
            if self.config.verbose:
                print(f"\n{'='*70}")
                print(f"Reading Iteration {iteration + 1}/{self.config.max_iterations}")
                print(f"{'='*70}")

            self._emit(IterationStartEvent(
                iteration=iteration,
                max_iterations=self.config.max_iterations,
            ))

            try:
                result = self._execute_iteration(
                    question,
                    reading_history,
                    iteration,
                )

                if result is None:
                    continue

                history_entry, df_result = result
                reading_history.append(history_entry)
                all_results.append(df_result)

                self._emit(IterationEndEvent(
                    iteration=iteration,
                    thought=history_entry.thought,
                    reading_mode=history_entry.reading_mode,
                    goal=history_entry.goal,
                    satisfied=history_entry.satisfied,
                    next_move=history_entry.next_move,
                ))

                if history_entry.satisfied:
                    if self.config.verbose:
                        print("\nLLM satisfied - sufficient information gathered")
                    break

            except KeyboardInterrupt:
                if self.config.verbose:
                    print("\nInterrupted by user")
                break
            except Exception as e:
                self._emit(ErrorEvent(
                    error=str(e),
                    error_type=type(e).__name__,
                    recoverable=True,
                ))
                if self.config.verbose:
                    print(f"Error in iteration: {e}")
                continue

        # Synthesize answer
        if self.config.verbose:
            print(f"\n{'='*70}")
            print("Synthesizing final answer...")
            print(f"{'='*70}")

        self._emit(SynthesisEvent(
            stage="start",
            total_lines=sum(len(df) for df in all_results),
            total_words=sum(h.word_count for h in reading_history),
        ))

        answer = self._synthesizer.synthesize(question, all_results, reading_history)

        elapsed = time.time() - start_time

        # Calculate stats
        combined = pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()
        if "line_num" in combined.columns:
            combined = combined.drop_duplicates(subset=["line_num"])
        unique_lines = len(combined)
        total_words = sum(h.word_count for h in reading_history)

        result = QuestionResult(
            answer=answer,
            iterations=len(reading_history),
            unique_lines=unique_lines,
            total_words=total_words,
            elapsed_time=elapsed,
            history=reading_history,
        )

        self._emit(AnswerEvent(
            answer=answer,
            iterations=result.iterations,
            total_lines=result.unique_lines,
            total_words=result.total_words,
            elapsed_time=result.elapsed_time,
        ))

        self._emit(SynthesisEvent(
            stage="complete",
            total_lines=result.unique_lines,
            total_words=result.total_words,
        ))

        # Store in conversation history
        self._conversation_history.append({
            "question": question,
            "answer": answer,
            "iterations": result.iterations,
            "lines": result.unique_lines,
            "words": result.total_words,
            "time": result.elapsed_time,
        })

        if self.config.verbose:
            print("\n" + "=" * 70)
            print("FINAL ANSWER")
            print("=" * 70)
            print(answer)
            print("=" * 70)
            print(f"\nStatistics:")
            print(f"  Reading iterations: {result.iterations}")
            print(f"  Unique lines read: {result.unique_lines:,}")
            print(f"  Total words read: {result.total_words:,}")
            print(f"  Time elapsed: {result.elapsed_time:.1f}s")

        self._emit(Event(
            type=EventType.QUESTION_END,
            data={"question": question, "elapsed_time": elapsed},
        ))

        return result

    def ask_stream(self, question: str) -> Generator[Event, None, QuestionResult]:
        """Ask a question with streaming events.

        Yields events as they occur during processing. The final QuestionResult
        is returned when the generator completes.

        Args:
            question: The question to answer.

        Yields:
            Events during processing.

        Returns:
            QuestionResult with answer and statistics.

        Example:
            events = []
            for event in repl.ask_stream("What is the main topic?"):
                events.append(event)
                print(f"Event: {event.type.value}")
            # After iteration completes, get the result
            result = events[-1] if events else None
        """
        collected_events: List[Event] = []

        def collector(event: Event):
            collected_events.append(event)

        # Temporarily add collector
        self._events.subscribe(collector)
        old_verbose = self.config.verbose
        self.config.verbose = False

        try:
            # This will trigger events
            result = self.ask(question)

            # Yield all collected events
            for event in collected_events:
                yield event

            return result

        finally:
            self._events.unsubscribe(collector)
            self.config.verbose = old_verbose

    def query(self, sql: str) -> QueryResult:
        """Execute a raw SQL query.

        Useful for debugging and exploration.

        Args:
            sql: SQL query string.

        Returns:
            QueryResult with DataFrame and statistics.
        """
        if self.config.verbose:
            print(f"\nExecuting SQL query...")

        result = self._db.execute(sql)

        if self.config.verbose:
            print(f"Retrieved {result.row_count} rows ({result.word_count:,} words)")
            if result.row_count > 0:
                print(result.dataframe.head(30).to_string(index=False))
                if result.row_count > 30:
                    print(f"\n... and {result.row_count - 30} more rows")

        return result

    def get_schema(self) -> Dict[str, Any]:
        """Get database schema information.

        Returns:
            Dictionary with schema details.
        """
        return self._db.get_schema_info()

    def session_stats(self) -> Dict[str, Any]:
        """Get session statistics.

        Returns:
            Dictionary with session statistics.
        """
        if not self._conversation_history:
            return {"questions_asked": 0}

        total_iterations = sum(h["iterations"] for h in self._conversation_history)
        total_lines = sum(h["lines"] for h in self._conversation_history)
        total_words = sum(h["words"] for h in self._conversation_history)
        total_time = sum(h["time"] for h in self._conversation_history)
        n = len(self._conversation_history)

        return {
            "questions_asked": n,
            "total_iterations": total_iterations,
            "total_lines_read": total_lines,
            "total_words_read": total_words,
            "total_time": total_time,
            "avg_iterations_per_question": total_iterations / n,
            "avg_lines_per_question": total_lines / n,
            "avg_words_per_question": total_words / n,
            "avg_time_per_question": total_time / n,
        }

    def print_stats(self):
        """Print session statistics to console."""
        print("\n" + "=" * 70)
        print("SESSION STATISTICS")
        print("=" * 70)

        # Document stats
        if self.is_loaded and self.stats:
            print(f"\nDocument:")
            print(f"  Lines: {self.stats.total_lines:,}")
            print(f"  Words: {self.stats.total_words:,}")
            print(f"  Strategic markers: {self.stats.strategic_lines:,}")

        # Session stats
        stats = self.session_stats()
        if stats["questions_asked"] > 0:
            print(f"\nSession:")
            print(f"  Questions asked: {stats['questions_asked']}")
            print(f"  Total iterations: {stats['total_iterations']}")
            print(f"  Total lines read: {stats['total_lines_read']:,}")
            print(f"  Total words read: {stats['total_words_read']:,}")
            print(f"  Total time: {stats['total_time']:.1f}s")
            print(f"\n  Averages per question:")
            print(f"    Iterations: {stats['avg_iterations_per_question']:.1f}")
            print(f"    Lines: {stats['avg_lines_per_question']:.0f}")
            print(f"    Words: {stats['avg_words_per_question']:.0f}")
            print(f"    Time: {stats['avg_time_per_question']:.1f}s")
        else:
            print("\nNo questions asked yet")

        print("=" * 70)

    def subscribe(self, callback: Callable[[Event], None]):
        """Subscribe to streaming events.

        Args:
            callback: Function that takes an Event as argument.
        """
        self._events.subscribe(callback)

    def unsubscribe(self, callback: Callable[[Event], None]):
        """Unsubscribe from streaming events.

        Args:
            callback: Previously subscribed callback.
        """
        self._events.unsubscribe(callback)

    def close(self):
        """Close the REPL and release resources."""
        self._db.close()
        self._events.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _emit(self, event: Event):
        """Emit an event to subscribers."""
        self._events.emit(event)

    def _execute_iteration(
        self,
        question: str,
        history: List[ReadingHistory],
        iteration: int,
    ) -> Optional[tuple]:
        """Execute a single reading iteration.

        Returns:
            Tuple of (ReadingHistory, DataFrame) or None on failure.
        """
        # Build schema info
        stats = self.stats
        schema_info = self._strategy.build_schema_info(
            total_lines=stats.total_lines,
            total_words=stats.total_words,
            strategic_lines=stats.strategic_lines,
            max_line=stats.max_line,
        )

        # Build iteration prompt
        prompt = self._strategy.build_iteration_prompt(
            question=question,
            schema_info=schema_info,
            history=history,
            max_iterations=self.config.max_iterations,
        )

        # Get LLM decision
        self._emit(Event(type=EventType.LLM_REQUEST))
        response = self._client.get_reading_strategy(prompt, question)
        self._emit(Event(
            type=EventType.LLM_RESPONSE,
            data={"has_error": response.parse_error is not None},
        ))

        if response.parse_error:
            if self.config.verbose:
                print(f"Parse error: {response.parse_error}")
                print(f"Raw response: {truncate_text(response.raw_response, 200)}")
            return None

        if not response.sql_query:
            if self.config.verbose:
                print("No SQL query provided")
            return None

        # Display strategy
        if self.config.verbose:
            print(f"\nThought: {truncate_text(response.thought, 120)}")
            print(f"Reading mode: {response.reading_mode}")
            print(f"Goal: {truncate_text(response.goal, 100)}")

        # Process and fix SQL
        sql, auto_fixed = self._process_sql(response.sql_query, response.reading_mode)

        self._emit(SQLExecuteEvent(
            sql=sql,
            auto_fixed=auto_fixed,
            original_sql=response.sql_query if auto_fixed else None,
        ))

        if self.config.verbose:
            if auto_fixed:
                print("Auto-fixed SQL for better results")
            print(f"SQL: {truncate_text(sql, 150)}")

        # Execute query
        try:
            result = self._db.execute(sql)
        except Exception as e:
            self._emit(ErrorEvent(
                error=str(e),
                error_type="DatabaseError",
                recoverable=True,
            ))
            if self.config.verbose:
                print(f"Database error: {e}")
            return None

        self._emit(ResultsEvent(
            row_count=result.row_count,
            word_count=result.word_count,
            preview=result.dataframe.head(5).to_dict("records") if result.row_count > 0 else None,
        ))

        if self.config.verbose:
            print(f"\nRetrieved {result.row_count} lines ({result.word_count:,} words)")

            # Quality warning
            if result.word_count < 200 and response.reading_mode not in ["search", "keyword"]:
                print(f"WARNING: Only {result.word_count} words - might be header-only!")

            # Show preview
            if result.row_count > 0:
                print(format_preview(result.dataframe, response.reading_mode))

            if not response.satisfied:
                print(f"\nNot satisfied yet")
                print(f"Next move: {truncate_text(response.next_move, 150)}")

        # Build history entry
        sample_lines = result.dataframe.head(5).to_dict("records") if result.row_count > 0 else []

        history_entry = ReadingHistory(
            iteration=iteration,
            thought=response.thought,
            reading_mode=response.reading_mode,
            goal=response.goal,
            sql=sql,
            row_count=result.row_count,
            word_count=result.word_count,
            satisfied=response.satisfied,
            next_move=response.next_move,
            sample_lines=sample_lines,
        )

        return history_entry, result.dataframe

    def _process_sql(self, sql: str, reading_mode: str) -> tuple:
        """Process and auto-fix SQL query.

        Returns:
            Tuple of (processed_sql, was_fixed).
        """
        original_sql = sql
        fixed = False

        # Fix 1: Ensure ORDER BY line_num
        if "ORDER BY" not in sql.upper():
            if "LIMIT" in sql.upper():
                sql = sql.replace("LIMIT", "ORDER BY line_num LIMIT")
            else:
                sql += " ORDER BY line_num"
            fixed = True

        # Fix 2: Ensure LIMIT for searches
        if "LIMIT" not in sql.upper() and "LIKE" in sql.upper():
            sql += " LIMIT 50"
            fixed = True

        # Fix 3: Ensure word_count in SELECT
        if "SELECT *" not in sql.upper() and "word_count" not in sql.lower():
            sql = sql.replace("SELECT ", "SELECT line_num, text, word_count, ", 1)
            fixed = True

        # Fix 4: Detect header-only query (critical)
        if "is_strategic = true" in sql.lower() and "BETWEEN" not in sql.upper():
            sql = f"""
            SELECT line_num, text, word_count, is_header
            FROM {self.config.database.table_name}
            WHERE line_num BETWEEN 1 AND 100
            ORDER BY line_num
            """
            fixed = True

        return sql.strip(), fixed
