"""Answer synthesis from gathered context."""

from typing import List, Dict, Any
import pandas as pd

from rlm_repl.inference.client import InferenceClient
from rlm_repl.inference.strategy import ReadingHistory, ReadingStrategy


class AnswerSynthesizer:
    """Synthesizes final answers from gathered document context.

    Handles:
    - Combining and deduplicating results from multiple iterations
    - Building context blocks for the LLM
    - Generating the final answer with citations
    """

    def __init__(
        self,
        client: InferenceClient,
        strategy: ReadingStrategy,
        temperature: float = 0.3,
    ):
        """Initialize the synthesizer.

        Args:
            client: Inference client for LLM calls.
            strategy: Reading strategy for prompt building.
            temperature: Temperature for synthesis (default slightly higher).
        """
        self.client = client
        self.strategy = strategy
        self.temperature = temperature

    def synthesize(
        self,
        question: str,
        results: List[pd.DataFrame],
        history: List[ReadingHistory],
    ) -> str:
        """Synthesize a final answer from gathered results.

        Args:
            question: The original question.
            results: List of DataFrames from each iteration.
            history: Reading history for context.

        Returns:
            The synthesized answer string.
        """
        if not results:
            return "Could not gather sufficient information from the document."

        # Combine and deduplicate results
        combined = self._combine_results(results)

        if len(combined) == 0:
            return "Could not gather sufficient information from the document."

        # Build context from combined results
        context = self._build_context(combined)

        # Generate synthesis prompt
        prompt = self.strategy.build_synthesis_prompt(question, context, history)

        # Get answer from LLM
        try:
            answer = self.client.synthesize_answer(prompt, self.temperature)
            return answer
        except Exception as e:
            return (
                f"Error synthesizing answer: {e}\n\n"
                f"Gathered context:\n{context[:1000]}..."
            )

    def _combine_results(self, results: List[pd.DataFrame]) -> pd.DataFrame:
        """Combine and deduplicate results from multiple iterations."""
        if not results:
            return pd.DataFrame()

        # Filter out empty DataFrames
        non_empty = [df for df in results if len(df) > 0]
        if not non_empty:
            return pd.DataFrame()

        # Concatenate all results
        combined = pd.concat(non_empty, ignore_index=True)

        # Deduplicate by line_num if present
        if "line_num" in combined.columns:
            combined = combined.drop_duplicates(subset=["line_num"])
            combined = combined.sort_values("line_num")

        return combined

    def _build_context(self, results: pd.DataFrame) -> str:
        """Build context string from results, grouping contiguous blocks.

        Groups consecutive lines together and formats them as blocks
        with line number ranges for easier citation.
        """
        if len(results) == 0:
            return ""

        # Ensure we have line_num column
        if "line_num" not in results.columns:
            # Just concatenate all text
            if "text" in results.columns:
                return "\n".join(results["text"].astype(str).tolist())
            return ""

        # Group contiguous line numbers
        blocks = []
        current_block = []
        last_line = None

        for _, row in results.iterrows():
            current_line = row.get("line_num", 0)

            if last_line is None or current_line == last_line + 1:
                current_block.append(row)
            else:
                if current_block:
                    blocks.append(current_block)
                current_block = [row]

            last_line = current_line

        if current_block:
            blocks.append(current_block)

        # Format blocks
        context_parts = []
        for block in blocks:
            start_line = block[0].get("line_num", "?")
            end_line = block[-1].get("line_num", "?")

            text_lines = [str(row.get("text", "")) for row in block]
            text = "\n".join(text_lines)

            if start_line == end_line:
                context_parts.append(f"[Line {start_line}]\n{text}")
            else:
                context_parts.append(f"[Lines {start_line}-{end_line}]\n{text}")

        return "\n\n".join(context_parts)

    def get_stats(
        self,
        results: List[pd.DataFrame],
        history: List[ReadingHistory],
    ) -> Dict[str, Any]:
        """Get statistics about the synthesis process.

        Args:
            results: List of result DataFrames.
            history: Reading history.

        Returns:
            Dictionary with statistics.
        """
        combined = self._combine_results(results)

        total_words = sum(h.word_count for h in history)

        return {
            "iterations": len(history),
            "unique_lines": len(combined),
            "total_words_read": total_words,
            "avg_words_per_iteration": (
                total_words / len(history) if history else 0
            ),
        }
