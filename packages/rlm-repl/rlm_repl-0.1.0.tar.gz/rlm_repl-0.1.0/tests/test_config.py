"""Tests for configuration classes."""

import pytest
from rlm_repl.core.config import RLMConfig, DatabaseConfig


class TestDatabaseConfig:
    """Tests for DatabaseConfig."""

    def test_default_config(self):
        """Test default configuration is in-memory."""
        config = DatabaseConfig()
        assert config.persistent is False
        assert config.db_path is None
        assert config.table_name == "documents"
        assert config.connection_string == ":memory:"

    def test_persistent_requires_path(self):
        """Test that persistent mode requires db_path."""
        with pytest.raises(ValueError, match="db_path is required"):
            DatabaseConfig(persistent=True)

    def test_persistent_with_path(self):
        """Test persistent configuration with path."""
        config = DatabaseConfig(persistent=True, db_path="/tmp/test.db")
        assert config.persistent is True
        assert config.db_path == "/tmp/test.db"
        assert config.connection_string == "/tmp/test.db"

    def test_custom_table_name(self):
        """Test custom table name."""
        config = DatabaseConfig(table_name="my_docs")
        assert config.table_name == "my_docs"


class TestRLMConfig:
    """Tests for RLMConfig."""

    def test_required_fields(self):
        """Test that required fields are validated."""
        with pytest.raises(ValueError, match="base_url is required"):
            RLMConfig(base_url="", api_key="key", model="model")

        with pytest.raises(ValueError, match="api_key is required"):
            RLMConfig(base_url="http://localhost", api_key="", model="model")

        with pytest.raises(ValueError, match="model is required"):
            RLMConfig(base_url="http://localhost", api_key="key", model="")

    def test_valid_config(self):
        """Test valid configuration."""
        config = RLMConfig(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            model="qwen3-coder",
        )
        assert config.base_url == "http://localhost:11434/v1"
        assert config.api_key == "ollama"
        assert config.model == "qwen3-coder"
        assert config.verbose is True
        assert config.max_iterations == 6

    def test_custom_values(self):
        """Test custom configuration values."""
        config = RLMConfig(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            model="qwen3-coder",
            verbose=False,
            max_iterations=10,
            temperature=0.5,
        )
        assert config.verbose is False
        assert config.max_iterations == 10
        assert config.temperature == 0.5

    def test_invalid_max_iterations(self):
        """Test that max_iterations must be positive."""
        with pytest.raises(ValueError, match="max_iterations must be at least 1"):
            RLMConfig(
                base_url="http://localhost",
                api_key="key",
                model="model",
                max_iterations=0,
            )

    def test_invalid_temperature(self):
        """Test that temperature must be in valid range."""
        with pytest.raises(ValueError, match="temperature must be between"):
            RLMConfig(
                base_url="http://localhost",
                api_key="key",
                model="model",
                temperature=3.0,
            )

    def test_with_callback(self):
        """Test creating config with callback."""
        config = RLMConfig(
            base_url="http://localhost",
            api_key="key",
            model="model",
        )

        callback = lambda e: None
        new_config = config.with_callback(callback)

        assert new_config.on_event == callback
        assert config.on_event is None  # Original unchanged
