# RLM-REPL

**Recursive Language Model with REPL Inference Strategy**

A Python library that enables any language model to manage unlimited context using SQL-based retrieval with DuckDB.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

RLM-REPL implements a human-like reading strategy for processing large documents:

1. **Overview** - Read the beginning to understand document structure
2. **Search** - Find relevant sections using keyword search
3. **Deep Read** - Extract detailed information from located sections
4. **Synthesize** - Combine findings into a comprehensive answer

This approach allows small context window models to effectively work with documents of any size.

## Features

- **Two-sided architecture**: Separate Data and Inference layers
- **In-memory default**: Fast DuckDB in-memory database (no setup required)
- **Persistent option**: Optional persistent database for caching
- **CLI tool**: Instant testing from command line
- **Python API**: Full programmatic control
- **Streaming events**: Real-time progress tracking
- **Configurable verbosity**: Control output detail level
- **OpenAI-compatible**: Works with any OpenAI-compatible API

## Installation

```bash
pip install rlm-repl
```

Or install from source:

```bash
git clone https://github.com/labKnowledge/rlm-repl-sql.git
cd rlm-repl-sql
pip install -e .
```

## Quick Start

### CLI Usage

```bash
# Interactive mode
rlm-repl document.txt

# With custom model
rlm-repl document.txt --base-url http://localhost:11434/v1 --model qwen3-coder

# Single question mode
rlm-repl document.txt --question "What is the main topic?"

# Quiet mode
rlm-repl document.txt -q --question "Summarize the document"
```

### Python API

```python
from rlm_repl import RLMREPL, RLMConfig

# Configure for Ollama (local)
config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen3-coder",
)

# Create REPL and load document
with RLMREPL(config) as repl:
    repl.load_document("large_book.txt")
    
    result = repl.ask("What are the main themes?")
    print(result.answer)
    print(f"Read {result.total_words} words in {result.elapsed_time:.1f}s")
```

## Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

- **[Getting Started](docs/getting-started.md)** - Installation, setup, and first steps
- **[API Reference](docs/api-reference.md)** - Complete API documentation
- **[Configuration](docs/configuration.md)** - All configuration options
- **[Examples](docs/examples.md)** - Detailed usage examples
- **[Architecture](docs/architecture.md)** - How the system works
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

## Supported Models

Any OpenAI-compatible API:
- **Ollama** (local): llama3, qwen3, mistral, etc.
- **OpenAI**: gpt-4, gpt-3.5-turbo
- **vLLM**: Any hosted model
- **LMStudio**: Local models
- **Together AI**, **Groq**, etc.

## Examples

See the [`examples/`](examples/) directory for complete examples:
- `basic_usage.py` - Simple document Q&A
- `streaming_events.py` - Real-time progress tracking
- `persistent_database.py` - Caching documents
- `api_usage.py` - Building applications with RLM-REPL

## How It Works

1. **Document Loading**: Text is parsed into lines with metadata (headers, code blocks, list items)
2. **SQL Storage**: Lines are stored in DuckDB with indexes for efficient querying
3. **Reading Strategy**: LLM decides what to read using SQL queries
4. **Iterative Reading**: Multiple passes gather relevant information
5. **Answer Synthesis**: Final answer is generated from gathered context

### Reading Modes

- **overview**: Read document beginning (lines 1-100)
- **search**: Find keywords with `LIKE '%term%'`
- **read**: Focused reading (20-50 lines)
- **deep_read**: Detailed analysis (50-100 lines)

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
ruff format rlm_repl

# Type checking
mypy rlm_repl
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## Background & History

RLM-REPL was created by **Remy Gakwaya** after reading the MIT paper on Recursive Language Models. The initial implementation attempted to use a REPL approach where the LLM would generate Python functions to process documents. However, this approach proved challenging, especially with smaller language models that struggled to create complex Python functions reliably.

After **hundreds of iterations and experiments**, Remy developed the **RLM-REPL v8 concept** - a human-like reading strategy specifically designed to work with local, smaller language models on limited computational resources. The philosophy was simple: *if it can work reliably with poor and small models in limited computation, it would perform exceptionally well when powered by leading LLMs.*

The library evolved to use **SQL-based retrieval** instead of LLM-generated Python functions, leveraging DuckDB for efficient document storage and querying. This approach:
- Works reliably with models of all sizes, from small local models to leading cloud-based LLMs
- Provides a structured, predictable interface (SQL) that even smaller models can handle
- Enables efficient querying with database indexes
- Implements the human-like reading strategy (overview → search → deep read → synthesize) developed in v8

## Acknowledgments

**Author:** Remy Gakwaya

**Inspiration:** Based on the MIT paper on Recursive Language Models

**Innovation:** The RLM-REPL v8 concept - human-like reading strategies for LLM document processing - was developed by Remy after extensive experimentation (hundreds of iterations) to create a solution that works reliably with local, smaller language models.

**Evolution:** This implementation uses SQL-based retrieval instead of LLM-generated Python functions, making it more reliable and accessible for smaller language models while maintaining the proven v8 reading strategy.
