"""Formatting utilities for RLM-REPL output."""

from typing import List, Dict, Any, Optional
import pandas as pd


def truncate_text(text: str, max_length: int = 80, suffix: str = "...") -> str:
    """Truncate text to a maximum length.

    Args:
        text: Text to truncate.
        max_length: Maximum length including suffix.
        suffix: Suffix to add when truncated.

    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_preview(
    results: pd.DataFrame,
    mode: str = "default",
    max_rows: int = 8,
    max_text_length: int = 90,
) -> str:
    """Format a preview of query results.

    Args:
        results: DataFrame with query results.
        mode: Reading mode ("search", "keyword", "overview", etc.).
        max_rows: Maximum rows to show.
        max_text_length: Maximum text length per line.

    Returns:
        Formatted preview string.
    """
    if len(results) == 0:
        return "(No results)"

    # Adjust max_rows based on mode
    if mode in ["search", "keyword"]:
        max_rows = min(max_rows, 5)
    else:
        max_rows = min(max_rows, 8)

    lines = ["Preview of results:"]

    for i, (_, row) in enumerate(results.head(max_rows).iterrows()):
        line_num = row.get("line_num", "?")
        text = str(row.get("text", ""))
        is_strategic = row.get("is_strategic", False)

        # Truncate long lines
        if len(text) > max_text_length:
            text = text[:max_text_length] + "..."

        marker = "[H]" if is_strategic else "   "
        lines.append(f"{marker} Line {line_num:5}: {text}")

    remaining = len(results) - max_rows
    if remaining > 0:
        lines.append(f"   ... and {remaining} more lines")

    return "\n".join(lines)


def format_stats(
    iterations: int,
    unique_lines: int,
    total_words: int,
    elapsed_time: float,
    questions_asked: int = 1,
) -> str:
    """Format statistics summary.

    Args:
        iterations: Number of reading iterations.
        unique_lines: Number of unique lines read.
        total_words: Total words read.
        elapsed_time: Time elapsed in seconds.
        questions_asked: Number of questions asked in session.

    Returns:
        Formatted statistics string.
    """
    lines = [
        "=" * 70,
        "STATISTICS",
        "=" * 70,
        f"Reading iterations: {iterations}",
        f"Unique lines read: {unique_lines:,}",
        f"Total words read: {total_words:,}",
        f"Time elapsed: {elapsed_time:.1f}s",
    ]

    if iterations > 0:
        lines.append(f"Avg words/iteration: {total_words / iterations:.0f}")

    if questions_asked > 1:
        lines.append(f"Questions asked: {questions_asked}")

    lines.append("=" * 70)

    return "\n".join(lines)


def format_context_blocks(
    results: pd.DataFrame,
    max_lines_per_block: int = 100,
) -> List[str]:
    """Format results into context blocks for display.

    Groups contiguous lines and returns formatted blocks.

    Args:
        results: DataFrame with query results.
        max_lines_per_block: Maximum lines per block.

    Returns:
        List of formatted block strings.
    """
    if len(results) == 0:
        return []

    if "line_num" not in results.columns:
        if "text" in results.columns:
            return ["\n".join(results["text"].astype(str).tolist())]
        return []

    # Sort by line number
    sorted_results = results.sort_values("line_num")

    # Group contiguous lines
    blocks = []
    current_block = []
    last_line = None

    for _, row in sorted_results.iterrows():
        current_line = row.get("line_num", 0)

        if last_line is None or current_line == last_line + 1:
            current_block.append(row)
        else:
            if current_block:
                blocks.append(current_block)
            current_block = [row]

        last_line = current_line

        # Split if block gets too large
        if len(current_block) >= max_lines_per_block:
            blocks.append(current_block)
            current_block = []
            last_line = None

    if current_block:
        blocks.append(current_block)

    # Format each block
    formatted = []
    for block in blocks:
        start_line = block[0].get("line_num", "?")
        end_line = block[-1].get("line_num", "?")

        text_lines = [str(row.get("text", "")) for row in block]
        text = "\n".join(text_lines)

        if start_line == end_line:
            header = f"[Line {start_line}]"
        else:
            header = f"[Lines {start_line}-{end_line}]"

        formatted.append(f"{header}\n{text}")

    return formatted


def format_sql_display(sql: str, max_length: int = 150) -> str:
    """Format SQL for display, truncating if needed.

    Args:
        sql: SQL query string.
        max_length: Maximum display length.

    Returns:
        Formatted SQL string.
    """
    sql = sql.strip()

    if len(sql) <= max_length:
        return sql

    # Show beginning and end
    half = (max_length - 10) // 2
    return f"{sql[:half]}...{sql[-half:]}"


def format_document_info(
    doc_name: str,
    total_lines: int,
    total_words: int,
    strategic_lines: int,
    line_range: tuple,
) -> str:
    """Format document information for display.

    Args:
        doc_name: Document name.
        total_lines: Total number of lines.
        total_words: Total word count.
        strategic_lines: Number of strategic marker lines.
        line_range: Tuple of (min_line, max_line).

    Returns:
        Formatted document info string.
    """
    return f"""Document: {doc_name}
  Lines: {total_lines:,} (Lines {line_range[0]} to {line_range[1]})
  Words: {total_words:,}
  Strategic markers: {strategic_lines:,}"""
