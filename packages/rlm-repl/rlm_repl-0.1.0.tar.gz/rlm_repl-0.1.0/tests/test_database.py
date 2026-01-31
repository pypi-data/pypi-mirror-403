"""Tests for the database layer."""

import pytest
import pandas as pd
from rlm_repl.core.database import DocumentDatabase, DocumentStats, QueryResult
from rlm_repl.core.config import DatabaseConfig


class TestDocumentDatabase:
    """Tests for DocumentDatabase."""

    def test_default_initialization(self):
        """Test default database initialization."""
        db = DocumentDatabase()
        assert db.config.persistent is False
        assert db.is_loaded is False
        assert db.stats is None

    def test_load_text(self):
        """Test loading text content."""
        db = DocumentDatabase()
        text = """# Introduction

        This is a test document with multiple lines.

        ## Section 1

        Content for section 1.

        ## Section 2

        Content for section 2.
        """

        stats = db.load_text(text, "test_doc")

        assert db.is_loaded is True
        assert stats.doc_name == "test_doc"
        assert stats.total_lines > 0
        assert stats.total_words > 0
        assert stats.strategic_lines > 0

    def test_execute_query(self):
        """Test executing SQL queries."""
        db = DocumentDatabase()
        db.load_text("Line 1\nLine 2\nLine 3", "test")

        result = db.execute("SELECT * FROM documents ORDER BY line_num")

        assert isinstance(result, QueryResult)
        assert result.row_count == 3
        assert "text" in result.dataframe.columns
        assert "line_num" in result.dataframe.columns

    def test_query_with_filter(self):
        """Test query with WHERE filter."""
        db = DocumentDatabase()
        db.load_text("# Header\nContent line\nAnother line", "test")

        result = db.execute(
            "SELECT * FROM documents WHERE is_header = true"
        )

        assert result.row_count == 1
        assert "Header" in result.dataframe.iloc[0]["text"]

    def test_strategic_detection(self):
        """Test strategic line detection."""
        db = DocumentDatabase()
        db.load_text("""# Title
        Regular content here.
        UPPERCASE HEADER
        More content.
        Section:
        """, "test")

        result = db.execute(
            "SELECT * FROM documents WHERE is_strategic = true"
        )

        # Should detect: # Title, UPPERCASE HEADER, Section:
        assert result.row_count >= 2

    def test_word_count(self):
        """Test word count calculation."""
        db = DocumentDatabase()
        db.load_text("One two three\nFour five", "test")

        result = db.execute("SELECT SUM(word_count) as total FROM documents")

        assert result.dataframe.iloc[0]["total"] == 5

    def test_get_schema_info(self):
        """Test schema information retrieval."""
        db = DocumentDatabase()
        db.load_text("Test content", "test_doc")

        schema = db.get_schema_info()

        assert schema["loaded"] is True
        assert schema["doc_name"] == "test_doc"
        assert "columns" in schema
        assert len(schema["columns"]) > 0

    def test_schema_info_when_empty(self):
        """Test schema info when no document loaded."""
        db = DocumentDatabase()
        schema = db.get_schema_info()

        assert schema["loaded"] is False

    def test_load_dataframe(self):
        """Test loading pandas DataFrame."""
        db = DocumentDatabase()
        df = pd.DataFrame({
            "text": ["Line 1", "Line 2", "Line 3"],
        })

        stats = db.load_dataframe(df, "df_doc")

        assert db.is_loaded is True
        assert stats.total_lines == 3

    def test_load_dataframe_requires_text(self):
        """Test that DataFrame must have text column."""
        db = DocumentDatabase()
        df = pd.DataFrame({"other": [1, 2, 3]})

        with pytest.raises(ValueError, match="must have a 'text' column"):
            db.load_dataframe(df)

    def test_context_manager(self):
        """Test database as context manager."""
        with DocumentDatabase() as db:
            db.load_text("Test", "test")
            assert db.is_loaded is True

    def test_close(self):
        """Test closing database connection."""
        db = DocumentDatabase()
        db.load_text("Test", "test")
        db.close()
        # Should not raise on repeated close
        db.close()


class TestQueryResult:
    """Tests for QueryResult."""

    def test_empty_result(self):
        """Test empty result properties."""
        result = QueryResult(
            dataframe=pd.DataFrame(),
            row_count=0,
            word_count=0,
        )
        assert result.is_empty is True

    def test_non_empty_result(self):
        """Test non-empty result properties."""
        result = QueryResult(
            dataframe=pd.DataFrame({"text": ["hello"]}),
            row_count=1,
            word_count=1,
        )
        assert result.is_empty is False
