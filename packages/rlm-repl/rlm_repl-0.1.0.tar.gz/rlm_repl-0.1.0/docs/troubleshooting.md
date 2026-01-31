# Troubleshooting Guide

Common issues and solutions when using RLM-REPL.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Problems](#configuration-problems)
3. [Document Loading Errors](#document-loading-errors)
4. [API Connection Issues](#api-connection-issues)
5. [Query Problems](#query-problems)
6. [Performance Issues](#performance-issues)
7. [Error Messages](#error-messages)

## Installation Issues

### "Module not found: rlm_repl"

**Problem:** Python can't find the rlm_repl module.

**Solutions:**
1. Verify installation:
   ```bash
   pip show rlm-repl
   ```

2. Reinstall:
   ```bash
   pip install --upgrade rlm-repl
   ```

3. Check Python version (requires 3.9+):
   ```bash
   python --version
   ```

4. Use virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install rlm-repl
   ```

### "DuckDB installation failed"

**Problem:** DuckDB dependency fails to install.

**Solutions:**
1. Update pip:
   ```bash
   pip install --upgrade pip
   ```

2. Install system dependencies (Linux):
   ```bash
   sudo apt-get install build-essential
   ```

3. Install from source:
   ```bash
   pip install duckdb --no-binary duckdb
   ```

## Configuration Problems

### "base_url is required"

**Problem:** Configuration missing required parameter.

**Solution:**
```python
config = RLMConfig(
    base_url="http://localhost:11434/v1",  # Must provide
    api_key="ollama",
    model="qwen2.5-coder",
)
```

### "db_path is required when persistent=True"

**Problem:** Persistent database enabled but no path provided.

**Solution:**
```python
db_config = DatabaseConfig(
    persistent=True,
    db_path="./cache.db",  # Must provide path
)
```

### Invalid Temperature Value

**Problem:** Temperature outside valid range (0-2).

**Solution:**
```python
config = RLMConfig(
    ...,
    temperature=0.5,  # Must be 0 <= value <= 2
)
```

## Document Loading Errors

### "File not found"

**Problem:** Document file doesn't exist.

**Solutions:**
1. Check file path:
   ```python
   import os
   print(os.path.exists("document.txt"))  # Should be True
   ```

2. Use absolute path:
   ```python
   repl.load_document("/full/path/to/document.txt")
   ```

3. Check current directory:
   ```python
   import os
   print(os.getcwd())
   ```

### "File is empty"

**Problem:** Document has no content.

**Solution:**
- Verify file has content
- Check file encoding (should be UTF-8)
- Ensure file is not just whitespace

### "No content found in file"

**Problem:** File contains only empty lines.

**Solution:**
- Check file has actual text content
- Verify file encoding

### Encoding Issues

**Problem:** Special characters not displaying correctly.

**Solution:**
```python
# Ensure UTF-8 encoding
with open("document.txt", "r", encoding="utf-8") as f:
    content = f.read()
    repl.load_text(content, "document")
```

## API Connection Issues

### "Connection refused" or "Connection timeout"

**Problem:** Can't connect to model API.

**Solutions:**
1. Verify API is running:
   ```bash
   # For Ollama
   curl http://localhost:11434/v1/models
   
   # For OpenAI
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

2. Check base_url:
   ```python
   # Ollama default
   base_url="http://localhost:11434/v1"
   
   # LMStudio default
   base_url="http://localhost:1234/v1"
   ```

3. Check firewall/network settings

4. Verify API key:
   ```python
   # For Ollama, any string works
   api_key="ollama"
   
   # For OpenAI, must be valid key
   api_key="sk-..."
   ```

### "Model not found"

**Problem:** Model name doesn't exist.

**Solutions:**
1. List available models:
   ```bash
   # Ollama
   ollama list
   
   # Or via API
   curl http://localhost:11434/v1/models
   ```

2. Use exact model name (case-sensitive):
   ```python
   model="qwen2.5-coder"  # Exact name from ollama list
   ```

3. Pull model if missing (Ollama):
   ```bash
   ollama pull qwen2.5-coder
   ```

### "401 Unauthorized" or "403 Forbidden"

**Problem:** Invalid API key or insufficient permissions.

**Solutions:**
1. Verify API key is correct
2. Check API key has necessary permissions
3. For OpenAI, ensure account has credits
4. Check API key format:
   ```python
   # OpenAI format
   api_key="sk-..."
   
   # Ollama (any string)
   api_key="ollama"
   ```

### Rate Limiting

**Problem:** Too many API requests.

**Solutions:**
1. Reduce `max_iterations`:
   ```python
   config = RLMConfig(..., max_iterations=3)
   ```

2. Add delays between requests:
   ```python
   import time
   # Add delay in event handler
   ```

3. Use persistent database to cache results

## Query Problems

### "No document loaded"

**Problem:** Trying to query before loading document.

**Solution:**
```python
repl.load_document("file.txt")  # Load first!
result = repl.ask("Question?")
```

### SQL Query Errors

**Problem:** LLM generates invalid SQL.

**Solutions:**
1. RLM-REPL auto-fixes common issues, but some may slip through
2. Use direct SQL queries for debugging:
   ```python
   result = repl.query("SELECT * FROM documents LIMIT 10")
   ```

3. Check table name matches:
   ```python
   schema = repl.get_schema()
   table_name = schema["table_name"]
   ```

### Poor Quality Answers

**Problem:** Answers are incomplete or inaccurate.

**Solutions:**
1. Increase `max_iterations`:
   ```python
   config = RLMConfig(..., max_iterations=8)
   ```

2. Lower temperature for more focused reading:
   ```python
   config = RLMConfig(..., temperature=0.1)
   ```

3. Ask more specific questions:
   ```python
   # Instead of: "Tell me about this"
   # Use: "What are the main topics discussed in chapters 1-3?"
   ```

4. Check document quality (well-structured documents work better)

### "Only headers returned"

**Problem:** LLM queries return only headers, not content.

**Solution:**
- RLM-REPL includes auto-fixing for this, but if it persists:
  1. Check document has actual content (not just headers)
  2. Increase `max_iterations` to allow more reading
  3. The system should auto-fix queries that return only headers

## Performance Issues

### Slow Processing

**Problem:** Queries take too long.

**Solutions:**
1. Use persistent database:
   ```python
   db_config = DatabaseConfig(
       persistent=True,
       db_path="./cache.db",
   )
   ```

2. Reduce `max_iterations`:
   ```python
   config = RLMConfig(..., max_iterations=4)
   ```

3. Use faster model (if available)

4. Disable verbose mode:
   ```python
   config = RLMConfig(..., verbose=False)
   ```

### High Memory Usage

**Problem:** System using too much memory.

**Solutions:**
1. Use persistent database instead of in-memory:
   ```python
   db_config = DatabaseConfig(
       persistent=True,
       db_path="./cache.db",
   )
   ```

2. Process documents in smaller chunks
3. Close REPL when done:
   ```python
   with RLMREPL(config) as repl:
       # Use repl
   # Automatically closed
   ```

### Database Lock Errors

**Problem:** Multiple processes accessing same database.

**Solution:**
- Use separate database files per process
- Or use in-memory database for concurrent access

## Error Messages

### "RuntimeError: No document loaded"

**Cause:** Calling `ask()` before loading document.

**Fix:**
```python
repl.load_document("file.txt")  # Load first
repl.ask("Question?")
```

### "ValueError: max_iterations must be at least 1"

**Cause:** Invalid `max_iterations` value.

**Fix:**
```python
config = RLMConfig(..., max_iterations=6)  # Must be >= 1
```

### "duckdb.Error: Catalog Error"

**Cause:** Database file corruption or invalid SQL.

**Fix:**
1. Delete database file and reload:
   ```python
   import os
   os.remove("cache.db")
   ```

2. Check SQL query syntax

### "Parse error" in verbose output

**Cause:** LLM response not in expected JSON format.

**Fix:**
- Usually auto-handled, but if persistent:
  1. Try different model
  2. Lower temperature
  3. Check model supports structured output

## Getting Help

### Debug Mode

Enable verbose output to see what's happening:

```python
config = RLMConfig(
    ...,
    verbose=True,  # See all iterations and SQL
)
```

### Event Logging

Subscribe to events for debugging:

```python
def debug_handler(event):
    print(f"[{event.type.value}] {event.data}")

config = RLMConfig(
    ...,
    on_event=debug_handler,
)
```

### Check Schema

Inspect document structure:

```python
schema = repl.get_schema()
print(schema)
```

### Test SQL Directly

Test queries manually:

```python
result = repl.query("SELECT COUNT(*) FROM documents")
print(result.dataframe)
```

### Session Statistics

Check what happened:

```python
stats = repl.session_stats()
print(stats)
repl.print_stats()
```

## Common Patterns

### Pattern: Retry on Error

```python
import time

def ask_with_retry(repl, question, max_retries=3):
    for attempt in range(max_retries):
        try:
            return repl.ask(question)
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Retry {attempt + 1}/{max_retries}")
                time.sleep(1)
            else:
                raise
```

### Pattern: Validate Before Use

```python
def safe_ask(repl, question):
    if not repl.is_loaded:
        raise RuntimeError("Load document first")
    return repl.ask(question)
```

### Pattern: Error Handling

```python
try:
    with RLMREPL(config) as repl:
        repl.load_document("file.txt")
        result = repl.ask("Question?")
        print(result.answer)
except FileNotFoundError:
    print("Document not found")
except RuntimeError as e:
    print(f"Runtime error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

If you continue to experience issues, please:
1. Check the [API Reference](api-reference.md) for correct usage
2. Review [Examples](examples.md) for working code
3. Open an issue on GitHub with:
   - Error message
   - Code snippet
   - Configuration details
   - Python version

