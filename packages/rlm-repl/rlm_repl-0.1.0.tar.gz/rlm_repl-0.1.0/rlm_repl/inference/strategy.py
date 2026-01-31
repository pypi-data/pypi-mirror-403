"""Reading strategy prompts for RLM-REPL."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ReadingHistory:
    """Record of a single reading iteration."""

    iteration: int
    thought: str
    reading_mode: str
    goal: str
    sql: str
    row_count: int
    word_count: int
    satisfied: bool
    next_move: str
    sample_lines: List[Dict[str, Any]]


class ReadingStrategy:
    """Generates reading strategy prompts based on document schema and history."""

    def __init__(self, table_name: str = "documents"):
        self.table_name = table_name

    def build_schema_info(
        self,
        total_lines: int,
        total_words: int,
        strategic_lines: int,
        max_line: int,
    ) -> str:
        """Build database schema information for the prompt."""
        return f"""
DATABASE: {total_lines:,} lines ({total_words:,} words total)

Columns Available:
- line_num: Line number (INTEGER, 1 to {max_line:,})
- text: Actual content (STRING)
- word_count: Words per line (INTEGER)
- is_header: True if this is a header/title (BOOLEAN)
- is_strategic: True if header or section start (BOOLEAN) - {strategic_lines:,} lines

{'='*75}
CRITICAL FIX: WHAT WAS BROKEN
{'='*75}

BROKEN QUERY (Old Version):
   SELECT * FROM {self.table_name} WHERE is_strategic = true LIMIT 50

Problem: Returns ONLY headers like "CHAPTER 1", "INTRODUCTION"
Result: Only 50-100 words, all titles, NO ACTUAL CONTENT
Effect: Can't answer questions, makes up nonsense from titles

{'='*75}
CORRECTED HUMAN READING PATTERNS
{'='*75}

1. OVERVIEW READ (First Iteration - Read the Beginning):
   -- Read first 80-120 lines to understand document type
   SELECT line_num, text, word_count, is_header
   FROM {self.table_name}
   WHERE line_num BETWEEN 1 AND 100
   ORDER BY line_num

   Expected: ~1000-2000 words of ACTUAL CONTENT
   Purpose: Understand what kind of document this is

2. KEYWORD SEARCH (Second Iteration - Find Your Topic):
   -- Search for relevant terms to locate information
   SELECT line_num, text, word_count
   FROM {self.table_name}
   WHERE LOWER(text) LIKE '%keyword%'
   ORDER BY line_num
   LIMIT 40

   Expected: 20-40 lines containing your search term
   Purpose: Identify line numbers where topic is discussed

3. CONTEXT READ (Get Surrounding Lines):
   -- Read around interesting findings for full context
   WITH found AS (
       SELECT DISTINCT line_num
       FROM {self.table_name}
       WHERE LOWER(text) LIKE '%keyword%'
       LIMIT 5
   )
   SELECT d.line_num, d.text, d.word_count
   FROM {self.table_name} d
   CROSS JOIN found f
   WHERE d.line_num BETWEEN f.line_num - 20 AND f.line_num + 20
   ORDER BY d.line_num

   Expected: 200-400 lines (2000-4000 words)
   Purpose: Get full context around matches

4. SECTION READ (Deep Dive):
   -- Read complete section for detailed information
   SELECT line_num, text, word_count, is_header
   FROM {self.table_name}
   WHERE line_num BETWEEN 5000 AND 5080
   ORDER BY line_num

   Expected: 80 lines (~800-1200 words)
   Purpose: Detailed reading of specific area

5. SAMPLE SCAN (Survey Document):
   -- Read samples from different parts of document
   SELECT line_num, text, word_count
   FROM {self.table_name}
   WHERE line_num IN (
       100, 500, 1000, 2000, 3000, 5000, 8000, 10000, 15000
   )
   ORDER BY line_num

   Expected: 9 sample points across document
   Purpose: Quick survey of document structure

6. MULTI-KEYWORD SEARCH (Broader Search):
   -- Search multiple related terms
   SELECT line_num, text, word_count
   FROM {self.table_name}
   WHERE LOWER(text) LIKE '%manipulation%'
      OR LOWER(text) LIKE '%control%'
      OR LOWER(text) LIKE '%influence%'
   ORDER BY line_num
   LIMIT 50

{'='*75}
ITERATION STRATEGY (How to Use These Queries)
{'='*75}

Iteration 1 - OVERVIEW (Read Beginning):
   Goal: Understand document type and structure
   Query: SELECT ... WHERE line_num BETWEEN 1 AND 100
   Expected: 1000-2000 words to read

Iteration 2 - SEARCH (Find Topic):
   Goal: Locate where question's topic is discussed
   Query: SELECT ... WHERE LOWER(text) LIKE '%keyword%' LIMIT 40
   Expected: 20-40 matching lines with context

Iteration 3 - DEEP READ (Extract Details):
   Goal: Read carefully around findings
   Query: SELECT ... WHERE line_num BETWEEN X AND Y
   Expected: 30-80 lines of detailed content

Iteration 4+ - REFINE (If Needed):
   Goal: Fill in missing information
   Query: Search different keywords or read adjacent sections

{'='*75}
MANDATORY RULES
{'='*75}

1. ALWAYS include word_count in SELECT
2. ALWAYS use ORDER BY line_num for readability
3. ALWAYS aim for 500+ words per query (actual content!)
4. Use LOWER(text) LIKE for case-insensitive search
5. NEVER use "WHERE is_strategic = true" alone (headers only!)
6. NEVER return less than 200 words (except for keyword search)
7. Each reading should give you ACTUAL INFORMATION, not titles

{'='*75}
QUALITY CHECK
{'='*75}

After each query, verify:
- Did I get at least 500-1000 words? (Not just 94 words!)
- Did I get actual sentences and paragraphs? (Not just titles!)
- Can I answer the question from this content? (Not guessing from headers!)

If NO to any above -> Your query was wrong, try again with CONTENT queries!
"""

    def build_iteration_prompt(
        self,
        question: str,
        schema_info: str,
        history: List[ReadingHistory],
        max_iterations: int,
    ) -> str:
        """Build the complete strategy prompt for the current iteration."""
        prompt = f"""You are reading a document to answer: "{question}"

{schema_info}

CURRENT STATUS: Iteration {len(history) + 1}/{max_iterations}

"""

        # Add iteration-specific guidance
        if len(history) == 0:
            prompt += self._first_iteration_guidance()
        elif len(history) == 1:
            prompt += self._second_iteration_guidance(question, history[0])
        else:
            prompt += self._subsequent_iteration_guidance(history[-1])

        # Add history summary
        if history:
            prompt += self._format_history(history)

        # Add decision format
        prompt += self._decision_format()

        return prompt

    def _first_iteration_guidance(self) -> str:
        """Guidance for the first reading iteration."""
        return f"""
{'='*75}
FIRST ITERATION: Document Overview (Read the Beginning!)
{'='*75}

GOAL: Understand what kind of document this is

Like opening a book, you need to READ THE BEGINNING to understand:
- Document type (book, paper, manual, etc.)
- Writing style and tone
- Main topics covered
- Where your answer might be located

CORRECT FIRST QUERY (Copy this pattern):

SELECT line_num, text, word_count, is_header
FROM {self.table_name}
WHERE line_num BETWEEN 1 AND 100
ORDER BY line_num

This reads the first 100 lines (~1000-2000 words of ACTUAL CONTENT)

WRONG QUERY (Don't do this):

SELECT * FROM {self.table_name} WHERE is_strategic = true LIMIT 50

This returns ONLY headers/titles (e.g., "CHAPTER 1", "INTRODUCTION")
You get ~94 words total, all titles, NO REAL CONTENT
You cannot answer questions from titles alone!

Expected result: 80-100 lines with 1000-2000 words to actually read
"""

    def _second_iteration_guidance(
        self,
        question: str,
        first_read: ReadingHistory,
    ) -> str:
        """Guidance for the second reading iteration."""
        max_line = "unknown"
        if first_read.sample_lines:
            max_line = max(line.get("line_num", 0) for line in first_read.sample_lines)

        return f"""
{'='*75}
SECOND ITERATION: Keyword Search (Find Your Topic)
{'='*75}

From first reading, you learned:
- Retrieved: {first_read.row_count} lines ({first_read.word_count:,} words)
- Document spans: Lines 1 to {max_line}

GOAL: Find where "{question}" is discussed in the document

Strategy: Search for relevant keywords

CORRECT SEARCH QUERY (Copy this pattern):

SELECT line_num, text, word_count
FROM {self.table_name}
WHERE LOWER(text) LIKE '%keyword%'
ORDER BY line_num
LIMIT 40

Replace 'keyword' with terms related to: {question}

Tips:
- Use multiple keywords if first search fails
- Try synonyms (e.g., 'manipulation' -> 'control', 'influence')
- Note the line numbers where matches appear
- Aim for 20-40 matches

Expected result: 20-40 lines where your topic is mentioned
"""

    def _subsequent_iteration_guidance(self, last_read: ReadingHistory) -> str:
        """Guidance for iterations after the second."""
        return f"""
{'='*75}
ITERATION {last_read.iteration + 2}: Deep Read (Extract Details)
{'='*75}

From previous search:
- Found: {last_read.row_count} matching lines
- Word count: {last_read.word_count:,}

GOAL: Read carefully around interesting findings

Strategy: Read 30-80 lines around promising locations

CORRECT DEEP READ QUERY (Copy this pattern):

SELECT line_num, text, word_count, is_header
FROM {self.table_name}
WHERE line_num BETWEEN 5000 AND 5060
ORDER BY line_num

Replace 5000-5060 with line numbers from your search results.
Read context around matches (+/-20-30 lines).

Expected result: 40-80 lines of detailed content (~500-1200 words)
"""

    def _format_history(self, history: List[ReadingHistory]) -> str:
        """Format reading history for the prompt."""
        lines = [
            f"\n\n{'='*70}",
            "YOUR READING HISTORY:",
            f"{'='*70}",
        ]

        for h in history[-2:]:  # Show last 2 iterations
            lines.append(f"\nIteration {h.iteration + 1} ({h.reading_mode}):")
            goal_display = h.goal[:80] + "..." if len(h.goal) > 80 else h.goal
            lines.append(f"  Goal: {goal_display}")
            lines.append(f"  Retrieved: {h.row_count} lines, {h.word_count:,} words")

            # Quality indicator
            if h.word_count < 200:
                lines.append("  WARNING: Very few words - likely header-only content!")
            elif h.word_count < 500:
                lines.append("  Low word count - consider reading more lines")
            else:
                lines.append("  Good amount of content")

            # Show sample
            if h.sample_lines:
                lines.append("  Sample:")
                for row in h.sample_lines[:3]:
                    line_num = row.get("line_num", "?")
                    text = str(row.get("text", ""))[:70]
                    lines.append(f"    Line {line_num}: {text}...")

        return "\n".join(lines)

    def _decision_format(self) -> str:
        """Format for the LLM's decision output."""
        return f"""

{'='*70}
YOUR DECISION - Return ONLY this JSON structure:
{'='*70}

{{
    "thought": "What I've learned and what I'll do next",
    "reading_mode": "overview|search|read|deep_read",
    "goal": "What I hope to find with this query",
    "sql_query": "SELECT line_num, text, word_count FROM {self.table_name} WHERE ... ORDER BY line_num",
    "satisfied": false,
    "next_move": "What I'll do if not satisfied"
}}

READING MODES:
- overview: Read beginning (lines 1-100) or samples
- search: Find keywords (use LIKE '%term%')
- read: Focused reading (20-50 lines around findings)
- deep_read: Detailed analysis (50-100 lines)

CRITICAL RULES:
1. ALWAYS include word_count in SELECT
2. ALWAYS use ORDER BY line_num
3. Aim for 500-2000 words per query (ACTUAL CONTENT!)
4. NEVER use "WHERE is_strategic = true" alone (headers only!)
5. Use LOWER(text) LIKE for searches
6. Set satisfied=true ONLY when you have complete answer
7. Return ONLY valid JSON, no extra text

Think: Overview -> Search -> Read -> Answer (with REAL CONTENT each time!)
"""

    def build_synthesis_prompt(
        self,
        question: str,
        context: str,
        history: List[ReadingHistory],
    ) -> str:
        """Build the prompt for answer synthesis."""
        # Build reading summary
        reading_summary = []
        for h in history:
            reading_summary.append(
                f"  - Iteration {h.iteration + 1} ({h.reading_mode}): "
                f"{h.row_count} lines, {h.word_count:,} words"
            )

        return f"""Answer the question based on the document excerpts provided.

QUESTION: {question}

READING PROCESS:
{chr(10).join(reading_summary)}

DOCUMENT EXCERPTS:
{context}

INSTRUCTIONS:
- Provide a clear, comprehensive answer to the question
- Base your answer ONLY on the excerpts provided
- Cite line numbers when making specific claims: [Lines X-Y]
- If information is incomplete, acknowledge what's missing
- Organize your answer logically
- Don't invent information not present in the excerpts

Answer the question directly and thoroughly:
"""
