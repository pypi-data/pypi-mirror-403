# Configuration Guide

Complete guide to configuring RLM-REPL for your needs.

## Overview

RLM-REPL uses two main configuration classes:
- `RLMConfig`: Main configuration for the REPL system
- `DatabaseConfig`: Database-specific configuration

## RLMConfig

Main configuration class for RLM-REPL.

### Basic Configuration

```python
from rlm_repl import RLMConfig

config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
)
```

### All Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | str | **required** | Base URL for the AI model API |
| `api_key` | str | **required** | API key for authentication |
| `model` | str | **required** | Model name/identifier |
| `verbose` | bool | `True` | Enable verbose output |
| `max_iterations` | int | `6` | Maximum reading iterations per question |
| `temperature` | float | `0.2` | Temperature for LLM responses (0-2) |
| `synthesis_temperature` | float | `0.3` | Temperature for answer synthesis (0-2) |
| `database` | DatabaseConfig | `DatabaseConfig()` | Database configuration |
| `on_event` | Callable | `None` | Event callback function |

### Model Configuration

#### OpenAI

```python
config = RLMConfig(
    base_url="https://api.openai.com/v1",
    api_key="sk-your-api-key",
    model="gpt-4",
    temperature=0.2,
)
```

#### Ollama (Local)

```python
config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # Ollama doesn't require a real key
    model="qwen2.5-coder",
    temperature=0.2,
)
```

#### Custom Endpoint

```python
config = RLMConfig(
    base_url="http://your-server:8000/v1",
    api_key="your-key",
    model="your-model",
)
```

### Iteration Control

Control how many reading passes the system makes:

```python
config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
    max_iterations=4,  # Fewer iterations for faster responses
)
```

**Recommendations:**
- Simple questions: 3-4 iterations
- Complex questions: 6-8 iterations
- Very detailed analysis: 8-10 iterations

### Temperature Settings

Control randomness in responses:

```python
config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
    temperature=0.1,              # Lower = more deterministic (for reading strategy)
    synthesis_temperature=0.5,    # Higher = more creative (for final answer)
)
```

**Guidelines:**
- `temperature`: 0.1-0.3 for reading strategy (more focused)
- `synthesis_temperature`: 0.3-0.7 for answer synthesis (more natural)

### Verbosity

Control output detail:

```python
# Verbose (default) - shows all iterations and SQL queries
config = RLMConfig(..., verbose=True)

# Quiet - minimal output
config = RLMConfig(..., verbose=False)
```

### Event Callbacks

Subscribe to events for custom handling:

```python
from rlm_repl import Event, EventType

def on_event(event: Event):
    if event.type == EventType.ITERATION_START:
        print(f"Starting iteration {event.data['iteration'] + 1}")
    elif event.type == EventType.ANSWER:
        print(f"Answer ready: {event.data['answer']}")

config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
    on_event=on_event,
)
```

## DatabaseConfig

Configuration for the DuckDB database layer.

### In-Memory Database (Default)

Fast, no persistence:

```python
from rlm_repl import DatabaseConfig

db_config = DatabaseConfig()  # In-memory by default
```

### Persistent Database

Save document cache to disk:

```python
db_config = DatabaseConfig(
    persistent=True,
    db_path="./document_cache.db",
)

config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
    database=db_config,
)
```

**Benefits:**
- Faster subsequent loads (document already indexed)
- Persist across sessions
- Share cache between processes

**Note:** The database file will be created automatically if it doesn't exist.

### Custom Table Name

```python
db_config = DatabaseConfig(
    persistent=True,
    db_path="./cache.db",
    table_name="my_documents",  # Custom table name
)
```

## Environment Variables

Configure RLM-REPL using environment variables:

```bash
export RLM_BASE_URL="http://localhost:11434/v1"
export RLM_API_KEY="ollama"
export RLM_MODEL="qwen2.5-coder"
export RLM_VERBOSE="true"
export RLM_MAX_ITERATIONS="6"
export RLM_DB_PERSISTENT="false"
export RLM_DB_PATH="./cache.db"
```

### Loading from Environment

```python
from rlm_repl import RLMConfig

# Load all from environment
config = RLMConfig.from_env()

# Override specific values
config = RLMConfig.from_env(model="custom-model")
```

## Configuration Examples

### Example 1: Fast Local Development

```python
config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
    verbose=False,
    max_iterations=4,
    temperature=0.1,
)
```

### Example 2: Production with Caching

```python
db_config = DatabaseConfig(
    persistent=True,
    db_path="/var/cache/rlm-repl/documents.db",
)

config = RLMConfig(
    base_url="https://api.openai.com/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4",
    verbose=False,
    max_iterations=6,
    database=db_config,
)
```

### Example 3: Interactive Development

```python
def progress_handler(event):
    if event.type == EventType.ITERATION_START:
        print(f"🔄 Iteration {event.data['iteration'] + 1}")
    elif event.type == EventType.RESULTS:
        print(f"  ✓ Found {event.data['row_count']} lines")

config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
    verbose=True,
    on_event=progress_handler,
)
```

### Example 4: High-Quality Analysis

```python
config = RLMConfig(
    base_url="https://api.openai.com/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4",
    max_iterations=10,  # More thorough
    temperature=0.2,
    synthesis_temperature=0.4,
)
```

## Validation

RLMConfig validates parameters on creation:

```python
# This will raise ValueError
config = RLMConfig(
    base_url="",  # Empty base_url
    api_key="key",
    model="model",
)

# This will raise ValueError
config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="key",
    model="model",
    max_iterations=0,  # Must be at least 1
)

# This will raise ValueError
config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="key",
    model="model",
    temperature=3.0,  # Must be between 0 and 2
)
```

## Best Practices

1. **Use persistent databases** for large documents that you'll query multiple times
2. **Lower temperature** for reading strategy (0.1-0.3) to get more focused queries
3. **Higher synthesis temperature** (0.3-0.7) for more natural-sounding answers
4. **Adjust max_iterations** based on question complexity
5. **Use environment variables** for sensitive data like API keys
6. **Enable verbose mode** during development, disable in production
7. **Subscribe to events** for custom progress tracking and logging

## Troubleshooting Configuration

### "base_url is required"

Make sure to provide a valid base_url:
```python
config = RLMConfig(
    base_url="http://localhost:11434/v1",  # Must be non-empty
    api_key="ollama",
    model="model",
)
```

### "db_path is required when persistent=True"

If using persistent database, provide a path:
```python
db_config = DatabaseConfig(
    persistent=True,
    db_path="./cache.db",  # Required!
)
```

### Invalid Temperature

Temperature must be between 0 and 2:
```python
config = RLMConfig(
    ...,
    temperature=0.5,  # Valid: 0 <= 0.5 <= 2
)
```

