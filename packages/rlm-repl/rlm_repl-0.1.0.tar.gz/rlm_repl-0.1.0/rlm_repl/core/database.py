"""DuckDB database layer for document storage and querying."""

import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass

import duckdb
import pandas as pd

from rlm_repl.core.config import DatabaseConfig


@dataclass
class DocumentStats:
    """Statistics about a loaded document."""

    total_lines: int
    total_words: int
    strategic_lines: int
    min_line: int
    max_line: int
    doc_name: str


@dataclass
class QueryResult:
    """Result of a SQL query."""

    dataframe: pd.DataFrame
    row_count: int
    word_count: int

    @property
    def is_empty(self) -> bool:
        return self.row_count == 0


class DocumentDatabase:
    """DuckDB-backed document storage with strategic line detection.

    This class handles loading documents into DuckDB with line-level metadata
    including strategic markers (headers, section starts) for efficient navigation.

    Example:
        db = DocumentDatabase()
        stats = db.load_document("book.txt", "my_book")
        result = db.execute("SELECT * FROM documents WHERE line_num < 100")
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        """Initialize the database.

        Args:
            config: Database configuration. Defaults to in-memory database.
        """
        self.config = config or DatabaseConfig()
        self._connection: Optional[duckdb.DuckDBPyConnection] = None
        self._current_doc: Optional[str] = None
        self._stats: Optional[DocumentStats] = None

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Lazy initialization of database connection."""
        if self._connection is None:
            self._connection = duckdb.connect(self.config.connection_string)
        return self._connection

    @property
    def table_name(self) -> str:
        """Return the documents table name."""
        return self.config.table_name

    @property
    def stats(self) -> Optional[DocumentStats]:
        """Return statistics for the currently loaded document."""
        return self._stats

    @property
    def is_loaded(self) -> bool:
        """Check if a document is currently loaded."""
        return self._stats is not None

    def load_document(
        self,
        filepath: str,
        doc_name: Optional[str] = None,
    ) -> DocumentStats:
        """Load a document into the database with strategic markers.

        Args:
            filepath: Path to the text file.
            doc_name: Optional name for the document. Defaults to filename.

        Returns:
            DocumentStats with information about the loaded document.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is empty.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        if doc_name is None:
            doc_name = path.stem

        # Read and process lines
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if not lines:
            raise ValueError(f"File is empty: {filepath}")

        line_data = self._process_lines(lines)

        if not line_data:
            raise ValueError(f"No content found in file: {filepath}")

        # Create DataFrame and load into DuckDB
        df = pd.DataFrame(line_data)

        # Drop existing table and create new one
        self.connection.execute(f"DROP TABLE IF EXISTS {self.table_name}")
        self.connection.execute(
            f"CREATE TABLE {self.table_name} AS SELECT * FROM df"
        )

        # Create indexes for efficient querying
        self._create_indexes()

        # Calculate statistics
        self._stats = self._calculate_stats(doc_name)
        self._current_doc = doc_name

        return self._stats

    def load_dataframe(
        self,
        df: pd.DataFrame,
        doc_name: str = "dataframe",
    ) -> DocumentStats:
        """Load a pandas DataFrame directly.

        The DataFrame should have at minimum a 'text' column.
        If 'line_num' is not present, it will be added.

        Args:
            df: DataFrame with document content.
            doc_name: Name for the document.

        Returns:
            DocumentStats with information about the loaded document.
        """
        if "text" not in df.columns:
            raise ValueError("DataFrame must have a 'text' column")

        # Add line_num if not present
        if "line_num" not in df.columns:
            df = df.copy()
            df["line_num"] = range(1, len(df) + 1)

        # Process to add metadata if not present
        if "is_header" not in df.columns:
            df = self._add_metadata_columns(df)

        # Load into DuckDB
        self.connection.execute(f"DROP TABLE IF EXISTS {self.table_name}")
        self.connection.execute(
            f"CREATE TABLE {self.table_name} AS SELECT * FROM df"
        )
        self._create_indexes()

        self._stats = self._calculate_stats(doc_name)
        self._current_doc = doc_name

        return self._stats

    def load_text(
        self,
        text: str,
        doc_name: str = "text",
    ) -> DocumentStats:
        """Load text content directly.

        Args:
            text: Text content to load.
            doc_name: Name for the document.

        Returns:
            DocumentStats with information about the loaded document.
        """
        lines = text.split("\n")
        line_data = self._process_lines([line + "\n" for line in lines])

        if not line_data:
            raise ValueError("No content found in text")

        df = pd.DataFrame(line_data)
        return self.load_dataframe(df, doc_name)

    def execute(self, sql: str) -> QueryResult:
        """Execute a SQL query and return results.

        Args:
            sql: SQL query string.

        Returns:
            QueryResult with DataFrame and statistics.

        Raises:
            duckdb.Error: If the query fails.
        """
        result_df = self.connection.execute(sql).fetchdf()

        # Calculate word count
        if "word_count" in result_df.columns and len(result_df) > 0:
            word_count = int(result_df["word_count"].sum())
        elif "text" in result_df.columns and len(result_df) > 0:
            word_count = result_df["text"].apply(
                lambda x: len(str(x).split())
            ).sum()
        else:
            word_count = 0

        return QueryResult(
            dataframe=result_df,
            row_count=len(result_df),
            word_count=word_count,
        )

    def get_schema_info(self) -> Dict[str, Any]:
        """Get schema information for the documents table.

        Returns:
            Dictionary with schema details and statistics.
        """
        if not self.is_loaded:
            return {"loaded": False}

        return {
            "loaded": True,
            "doc_name": self._current_doc,
            "table_name": self.table_name,
            "total_lines": self._stats.total_lines,
            "total_words": self._stats.total_words,
            "strategic_lines": self._stats.strategic_lines,
            "line_range": (self._stats.min_line, self._stats.max_line),
            "columns": [
                {"name": "line_num", "type": "INTEGER", "description": "Line number (1-indexed)"},
                {"name": "text", "type": "STRING", "description": "Line content"},
                {"name": "word_count", "type": "INTEGER", "description": "Words in this line"},
                {"name": "is_header", "type": "BOOLEAN", "description": "True if header/title"},
                {"name": "is_list_item", "type": "BOOLEAN", "description": "True if list item"},
                {"name": "is_code", "type": "BOOLEAN", "description": "True if code content"},
                {"name": "is_section_start", "type": "BOOLEAN", "description": "True if section start"},
                {"name": "is_strategic", "type": "BOOLEAN", "description": "True if header or section start"},
            ],
        }

    def close(self):
        """Close the database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _process_lines(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Process lines and extract metadata."""
        line_data = []

        for line_num, line_text in enumerate(lines, 1):
            text = line_text.strip()
            if not text:
                continue

            # Detect strategic markers
            is_header = text.startswith("#") or (
                text.isupper() and len(text.split()) < 10
            )
            is_list_item = bool(re.match(r"^[\-\*\d]+[\.\)]\s", text))
            is_code = any(
                marker in text
                for marker in ["```", "def ", "class ", "function ", "import "]
            )
            is_section_start = is_header or (
                text.endswith(":") and len(text.split()) < 8
            )

            line_data.append({
                "line_num": line_num,
                "text": text,
                "word_count": len(text.split()),
                "is_header": is_header,
                "is_list_item": is_list_item,
                "is_code": is_code,
                "is_section_start": is_section_start,
                "is_strategic": is_header or is_section_start,
            })

        return line_data

    def _add_metadata_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add metadata columns to a DataFrame."""
        df = df.copy()

        def detect_header(text):
            text = str(text).strip()
            return text.startswith("#") or (
                text.isupper() and len(text.split()) < 10
            )

        def detect_list_item(text):
            return bool(re.match(r"^[\-\*\d]+[\.\)]\s", str(text)))

        def detect_code(text):
            return any(
                marker in str(text)
                for marker in ["```", "def ", "class ", "function ", "import "]
            )

        def detect_section_start(text):
            text = str(text).strip()
            return detect_header(text) or (
                text.endswith(":") and len(text.split()) < 8
            )

        df["word_count"] = df["text"].apply(lambda x: len(str(x).split()))
        df["is_header"] = df["text"].apply(detect_header)
        df["is_list_item"] = df["text"].apply(detect_list_item)
        df["is_code"] = df["text"].apply(detect_code)
        df["is_section_start"] = df["text"].apply(detect_section_start)
        df["is_strategic"] = df["is_header"] | df["is_section_start"]

        return df

    def _create_indexes(self):
        """Create indexes for efficient querying."""
        table = self.table_name
        self.connection.execute(f"CREATE INDEX IF NOT EXISTS idx_line_num ON {table}(line_num)")
        self.connection.execute(f"CREATE INDEX IF NOT EXISTS idx_strategic ON {table}(is_strategic)")

    def _calculate_stats(self, doc_name: str) -> DocumentStats:
        """Calculate document statistics."""
        result = self.connection.execute(f"""
            SELECT
                COUNT(*) as total,
                SUM(word_count) as words,
                SUM(CASE WHEN is_strategic THEN 1 ELSE 0 END) as strategic,
                MIN(line_num) as min_line,
                MAX(line_num) as max_line
            FROM {self.table_name}
        """).fetchone()

        return DocumentStats(
            total_lines=result[0],
            total_words=result[1] or 0,
            strategic_lines=result[2] or 0,
            min_line=result[3] or 0,
            max_line=result[4] or 0,
            doc_name=doc_name,
        )
