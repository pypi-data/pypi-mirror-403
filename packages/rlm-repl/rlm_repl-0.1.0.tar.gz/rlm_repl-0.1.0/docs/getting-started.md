# Getting Started with RLM-REPL

This guide will help you get started with RLM-REPL, from installation to your first query.

## Installation

### Prerequisites

- Python 3.9 or higher
- A language model API endpoint (OpenAI-compatible)

### Install from PyPI

```bash
pip install rlm-repl
```

### Install from Source

```bash
git clone https://github.com/labKnowledge/rlm-repl-sql.git
cd rlm-repl-sql
pip install -e .
```

### Verify Installation

```bash
rlm-repl --version
```

## Setting Up Your Model

RLM-REPL works with any OpenAI-compatible API. Here are some common setups:

### Option 1: Ollama (Local Models)

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Pull a model:
   ```bash
   ollama pull qwen2.5-coder
   ```
3. Start Ollama (usually runs automatically)
4. Use in RLM-REPL:
   ```python
   config = RLMConfig(
       base_url="http://localhost:11434/v1",
       api_key="ollama",
       model="qwen2.5-coder",
   )
   ```

### Option 2: OpenAI

```python
config = RLMConfig(
    base_url="https://api.openai.com/v1",
    api_key="sk-your-api-key-here",
    model="gpt-4",
)
```

### Option 3: LMStudio

1. Install and start LMStudio
2. Load a model and start the local server
3. Use:
   ```python
   config = RLMConfig(
       base_url="http://localhost:1234/v1",
       api_key="lm-studio",
       model="your-model-name",
   )
   ```

### Option 4: Environment Variables

Set these environment variables to use defaults:

```bash
export RLM_BASE_URL="http://localhost:11434/v1"
export RLM_API_KEY="ollama"
export RLM_MODEL="qwen2.5-coder"
```

Then create config from environment:

```python
from rlm_repl import RLMConfig

config = RLMConfig.from_env()
```

## Your First Query

### Using the CLI

1. Create a text file (`document.txt`):
   ```
   # Introduction to Python
   
   Python is a high-level programming language known for its simplicity.
   
   ## Features
   
   - Easy to learn
   - Versatile
   - Large standard library
   ```

2. Run RLM-REPL:
   ```bash
   rlm-repl document.txt
   ```

3. In interactive mode, ask questions:
   ```
   > What are Python's features?
   ```

### Using the Python API

```python
from rlm_repl import RLMREPL, RLMConfig

# Create configuration
config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
)

# Create REPL instance
with RLMREPL(config) as repl:
    # Load document
    repl.load_document("document.txt")
    
    # Ask a question
    result = repl.ask("What are Python's features?")
    
    # Print answer
    print(result.answer)
    print(f"Read {result.total_words} words in {result.elapsed_time:.1f}s")
```

### Loading Text Directly

You can also load text directly without a file:

```python
text = """
# My Document

This is some content.
"""

with RLMREPL(config) as repl:
    repl.load_text(text, "my_document")
    result = repl.ask("What is this document about?")
    print(result.answer)
```

## Understanding the Output

When you ask a question, RLM-REPL will:

1. **Load the document** (if not already loaded)
2. **Perform reading iterations**:
   - Iteration 1: Overview (read beginning)
   - Iteration 2: Search (find keywords)
   - Iteration 3+: Deep read (extract details)
3. **Synthesize the answer** from gathered information

### Verbose Mode (Default)

With verbose mode enabled, you'll see:
- Each iteration's strategy
- SQL queries being executed
- Results retrieved
- Final answer

### Quiet Mode

For cleaner output:

```python
config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
    verbose=False,  # Disable verbose output
)
```

Or in CLI:
```bash
rlm-repl document.txt -q --question "Your question"
```

## Next Steps

- Read the [API Reference](api-reference.md) for detailed API documentation
- Check out [Examples](examples.md) for more use cases
- Learn about [Configuration](configuration.md) options
- Understand the [Architecture](architecture.md) behind RLM-REPL

## Common Issues

### "No document loaded"

Make sure to call `load_document()` or `load_text()` before asking questions:

```python
repl.load_document("file.txt")  # Must load first!
result = repl.ask("Question?")
```

### Connection Errors

If you see connection errors:
1. Verify your model API is running
2. Check the `base_url` is correct
3. Test the API endpoint directly (e.g., `curl http://localhost:11434/v1/models`)

### Model Not Found

Ensure:
- The model name matches exactly (case-sensitive)
- The model is installed/pulled (for local models)
- You have access to the model (for cloud APIs)

For more troubleshooting, see [Troubleshooting Guide](troubleshooting.md).

