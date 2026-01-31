"""Configuration classes for RLM-REPL."""

from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Configuration for the DuckDB database layer.

    Attributes:
        persistent: If True, use persistent database. If False, use in-memory (default).
        db_path: Path to the database file. Required if persistent=True.
        table_name: Name of the documents table. Default: "documents".
    """

    persistent: bool = False
    db_path: Optional[str] = None
    table_name: str = "documents"

    def __post_init__(self):
        if self.persistent and not self.db_path:
            raise ValueError("db_path is required when persistent=True")
        if self.db_path:
            # Ensure parent directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    @property
    def connection_string(self) -> str:
        """Return the DuckDB connection string."""
        if self.persistent and self.db_path:
            return self.db_path
        return ":memory:"


@dataclass
class RLMConfig:
    """Main configuration for the RLM-REPL system.

    Attributes:
        base_url: Base URL for the AI model API (e.g., "http://localhost:11434/v1").
        api_key: API key for authentication.
        model: Model name/identifier to use.
        verbose: Enable verbose output. Default: True.
        max_iterations: Maximum reading iterations per question. Default: 6.
        temperature: Temperature for LLM responses. Default: 0.2.
        synthesis_temperature: Temperature for answer synthesis. Default: 0.3.
        database: Database configuration. Default: in-memory DuckDB.
        on_event: Optional callback for streaming events.
    """

    base_url: str
    api_key: str
    model: str
    verbose: bool = True
    max_iterations: int = 6
    temperature: float = 0.2
    synthesis_temperature: float = 0.3
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    on_event: Optional[Callable[[Any], None]] = None

    def __post_init__(self):
        # Validate required fields
        if not self.base_url:
            raise ValueError("base_url is required")
        if not self.api_key:
            raise ValueError("api_key is required")
        if not self.model:
            raise ValueError("model is required")

        # Validate ranges
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
        if not 0 <= self.temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")
        if not 0 <= self.synthesis_temperature <= 2:
            raise ValueError("synthesis_temperature must be between 0 and 2")

    @classmethod
    def from_env(cls, **overrides) -> "RLMConfig":
        """Create configuration from environment variables.

        Environment variables:
            RLM_BASE_URL: Base URL for the API
            RLM_API_KEY: API key
            RLM_MODEL: Model name
            RLM_VERBOSE: "true" or "false"
            RLM_MAX_ITERATIONS: Integer
            RLM_DB_PERSISTENT: "true" or "false"
            RLM_DB_PATH: Path to database file
        """
        import os

        base_url = overrides.get("base_url") or os.getenv("RLM_BASE_URL", "")
        api_key = overrides.get("api_key") or os.getenv("RLM_API_KEY", "")
        model = overrides.get("model") or os.getenv("RLM_MODEL", "")
        verbose = overrides.get(
            "verbose", os.getenv("RLM_VERBOSE", "true").lower() == "true"
        )
        max_iterations = overrides.get(
            "max_iterations", int(os.getenv("RLM_MAX_ITERATIONS", "6"))
        )

        # Database config from env
        db_persistent = os.getenv("RLM_DB_PERSISTENT", "false").lower() == "true"
        db_path = os.getenv("RLM_DB_PATH")

        database = DatabaseConfig(
            persistent=db_persistent,
            db_path=db_path,
        )

        return cls(
            base_url=base_url,
            api_key=api_key,
            model=model,
            verbose=verbose,
            max_iterations=max_iterations,
            database=database,
            **{k: v for k, v in overrides.items() if k not in ["base_url", "api_key", "model", "verbose", "max_iterations"]}
        )

    def with_callback(self, callback: Callable[[Any], None]) -> "RLMConfig":
        """Return a new config with the specified event callback."""
        return RLMConfig(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model,
            verbose=self.verbose,
            max_iterations=self.max_iterations,
            temperature=self.temperature,
            synthesis_temperature=self.synthesis_temperature,
            database=self.database,
            on_event=callback,
        )
