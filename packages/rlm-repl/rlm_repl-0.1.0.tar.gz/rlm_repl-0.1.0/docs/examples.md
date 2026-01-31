# Examples

Comprehensive examples demonstrating RLM-REPL usage.

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Streaming Events](#streaming-events)
3. [Persistent Database](#persistent-database)
4. [Building Applications](#building-applications)
5. [Advanced Queries](#advanced-queries)
6. [Custom Event Handlers](#custom-event-handlers)
7. [Batch Processing](#batch-processing)
8. [Error Handling](#error-handling)

## Basic Usage

### Simple Question Answering

```python
from rlm_repl import RLMREPL, RLMConfig

# Configure
config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
)

# Use REPL
with RLMREPL(config) as repl:
    # Load document
    repl.load_document("document.txt")
    
    # Ask question
    result = repl.ask("What is the main topic?")
    
    # Print answer
    print(result.answer)
    print(f"Read {result.total_words} words in {result.elapsed_time:.1f}s")
```

### Loading Text Directly

```python
text = """
# Introduction to Machine Learning

Machine learning is a subset of artificial intelligence...
"""

with RLMREPL(config) as repl:
    repl.load_text(text, "ml_intro")
    result = repl.ask("What is machine learning?")
    print(result.answer)
```

### Loading from DataFrame

```python
import pandas as pd

df = pd.DataFrame({
    "text": [
        "First paragraph about topic A.",
        "Second paragraph about topic B.",
        "Third paragraph about topic A again.",
    ]
})

with RLMREPL(config) as repl:
    repl.load_dataframe(df, "my_data")
    result = repl.ask("What is discussed about topic A?")
    print(result.answer)
```

## Streaming Events

### Basic Event Handling

```python
from rlm_repl import Event, EventType

def on_event(event: Event):
    if event.type == EventType.ITERATION_START:
        print(f"Starting iteration {event.data['iteration'] + 1}")
    elif event.type == EventType.RESULTS:
        print(f"Found {event.data['row_count']} lines")
    elif event.type == EventType.ANSWER:
        print(f"Answer ready!")

config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
    on_event=on_event,
)

with RLMREPL(config) as repl:
    repl.load_document("document.txt")
    result = repl.ask("What is the topic?")
```

### Using ask_stream()

```python
from rlm_repl import EventType

with RLMREPL(config) as repl:
    repl.load_document("document.txt")
    
    for event in repl.ask_stream("What is the topic?"):
        if event.type == EventType.ITERATION_START:
            print(f"🔄 Iteration {event.data['iteration'] + 1}")
        elif event.type == EventType.ANSWER:
            print(f"✅ {event.data['answer']}")
```

### Progress Bar Example

```python
from tqdm import tqdm

class ProgressTracker:
    def __init__(self):
        self.pbar = None
        self.current_iteration = 0
    
    def on_event(self, event: Event):
        if event.type == EventType.ITERATION_START:
            self.current_iteration = event.data['iteration'] + 1
            max_iterations = event.data['max_iterations']
            if self.pbar is None:
                self.pbar = tqdm(total=max_iterations, desc="Reading")
            self.pbar.update(1)
        elif event.type == EventType.ANSWER:
            if self.pbar:
                self.pbar.close()

tracker = ProgressTracker()
config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
    on_event=tracker.on_event,
)

with RLMREPL(config) as repl:
    repl.load_document("document.txt")
    result = repl.ask("Question?")
```

## Persistent Database

### Using Persistent Cache

```python
from rlm_repl import RLMREPL, RLMConfig, DatabaseConfig

# Configure persistent database
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

with RLMREPL(config) as repl:
    # First run: loads and caches
    # Subsequent runs: uses cached data
    repl.load_document("large_document.txt")
    result = repl.ask("Your question")
```

### Checking Cache Status

```python
with RLMREPL(config) as repl:
    schema = repl.get_schema()
    
    if schema.get("loaded"):
        print(f"Using cached document: {schema['doc_name']}")
        print(f"  Lines: {schema['total_lines']}")
        print(f"  Words: {schema['total_words']}")
    else:
        print("No cached document, loading...")
        repl.load_document("document.txt")
```

## Building Applications

### Document Q&A Class

```python
from rlm_repl import RLMREPL, RLMConfig
from typing import Dict, Any

class DocumentQA:
    def __init__(self, model_config: Dict[str, str]):
        self.config = RLMConfig(**model_config)
        self.repl = RLMREPL(self.config)
    
    def load(self, filepath: str) -> Dict[str, Any]:
        stats = self.repl.load_document(filepath)
        return {
            "lines": stats.total_lines,
            "words": stats.total_words,
        }
    
    def ask(self, question: str) -> Dict[str, Any]:
        result = self.repl.ask(question)
        return {
            "answer": result.answer,
            "iterations": result.iterations,
            "words_read": result.total_words,
            "time": result.elapsed_time,
        }
    
    def close(self):
        self.repl.close()

# Usage
qa = DocumentQA({
    "base_url": "http://localhost:11434/v1",
    "api_key": "ollama",
    "model": "qwen2.5-coder",
})

qa.load("document.txt")
response = qa.ask("What is the topic?")
print(response["answer"])
qa.close()
```

### Web API Wrapper

```python
from flask import Flask, request, jsonify
from rlm_repl import RLMREPL, RLMConfig

app = Flask(__name__)
repl = None

def init_repl():
    global repl
    config = RLMConfig(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        model="qwen2.5-coder",
        verbose=False,
    )
    repl = RLMREPL(config)

@app.route("/load", methods=["POST"])
def load_document():
    data = request.json
    stats = repl.load_document(data["filepath"])
    return jsonify({
        "lines": stats.total_lines,
        "words": stats.total_words,
    })

@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.json
    result = repl.ask(data["question"])
    return jsonify({
        "answer": result.answer,
        "iterations": result.iterations,
        "words_read": result.total_words,
    })

if __name__ == "__main__":
    init_repl()
    app.run()
```

## Advanced Queries

### Direct SQL Queries

```python
with RLMREPL(config) as repl:
    repl.load_document("document.txt")
    
    # Find all headers
    result = repl.query(
        "SELECT line_num, text FROM documents WHERE is_header = true"
    )
    print(result.dataframe)
    
    # Search for specific terms
    result = repl.query(
        "SELECT line_num, text FROM documents "
        "WHERE LOWER(text) LIKE '%machine learning%' LIMIT 10"
    )
    print(result.dataframe)
    
    # Get document statistics
    result = repl.query(
        "SELECT COUNT(*) as total, SUM(word_count) as words "
        "FROM documents"
    )
    print(result.dataframe)
```

### Custom Reading Strategy

```python
# You can guide the reading by asking specific questions
with RLMREPL(config) as repl:
    repl.load_document("book.txt")
    
    # First, get overview
    result1 = repl.ask("What is this book about?")
    
    # Then, ask specific questions
    result2 = repl.ask("What are the main chapters?")
    result3 = repl.ask("What is discussed in chapter 3?")
```

## Custom Event Handlers

### Logging Events

```python
import logging
from rlm_repl import Event, EventType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_events(event: Event):
    if event.type == EventType.ITERATION_START:
        logger.info(f"Iteration {event.data['iteration'] + 1} started")
    elif event.type == EventType.SQL_EXECUTE:
        logger.debug(f"SQL: {event.data['sql'][:100]}...")
    elif event.type == EventType.ERROR:
        logger.error(f"Error: {event.data['error']}")

config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
    on_event=log_events,
)
```

### Metrics Collection

```python
class MetricsCollector:
    def __init__(self):
        self.metrics = {
            "iterations": [],
            "sql_queries": [],
            "words_read": [],
        }
    
    def on_event(self, event: Event):
        if event.type == EventType.ITERATION_END:
            self.metrics["iterations"].append({
                "iteration": event.data["iteration"],
                "words": event.data.get("word_count", 0),
            })
        elif event.type == EventType.SQL_EXECUTE:
            self.metrics["sql_queries"].append(event.data["sql"])
    
    def get_summary(self):
        total_iterations = len(self.metrics["iterations"])
        total_words = sum(i["words"] for i in self.metrics["iterations"])
        return {
            "total_iterations": total_iterations,
            "total_words": total_words,
            "avg_words_per_iteration": total_words / total_iterations if total_iterations > 0 else 0,
        }

collector = MetricsCollector()
config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
    on_event=collector.on_event,
)

with RLMREPL(config) as repl:
    repl.load_document("document.txt")
    result = repl.ask("Question?")
    
    summary = collector.get_summary()
    print(f"Summary: {summary}")
```

## Batch Processing

### Multiple Questions

```python
questions = [
    "What is the main topic?",
    "What are the key points?",
    "What is the conclusion?",
]

with RLMREPL(config) as repl:
    repl.load_document("document.txt")
    
    results = []
    for question in questions:
        result = repl.ask(question)
        results.append({
            "question": question,
            "answer": result.answer,
            "iterations": result.iterations,
        })
    
    for r in results:
        print(f"Q: {r['question']}")
        print(f"A: {r['answer']}\n")
```

### Multiple Documents

```python
documents = ["doc1.txt", "doc2.txt", "doc3.txt"]
questions = ["What is the main topic?"]

for doc in documents:
    print(f"\nProcessing {doc}")
    with RLMREPL(config) as repl:
        repl.load_document(doc)
        for question in questions:
            result = repl.ask(question)
            print(f"Answer: {result.answer[:100]}...")
```

## Error Handling

### Basic Error Handling

```python
from rlm_repl import RLMREPL, RLMConfig

config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
)

try:
    with RLMREPL(config) as repl:
        repl.load_document("document.txt")
        result = repl.ask("Question?")
        print(result.answer)
except FileNotFoundError as e:
    print(f"Document not found: {e}")
except RuntimeError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Handling API Errors

```python
import time

def ask_with_retry(repl, question, max_retries=3):
    for attempt in range(max_retries):
        try:
            return repl.ask(question)
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

with RLMREPL(config) as repl:
    repl.load_document("document.txt")
    result = ask_with_retry(repl, "Question?")
    print(result.answer)
```

### Validating Document Load

```python
def safe_load_document(repl, filepath):
    try:
        stats = repl.load_document(filepath)
        if stats.total_lines == 0:
            raise ValueError("Document is empty")
        if stats.total_words < 100:
            print("Warning: Document is very short")
        return stats
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        raise
    except Exception as e:
        print(f"Error loading document: {e}")
        raise

with RLMREPL(config) as repl:
    stats = safe_load_document(repl, "document.txt")
    print(f"Loaded {stats.total_lines} lines")
```

## Complete Example: Research Assistant

```python
from rlm_repl import RLMREPL, RLMConfig, DatabaseConfig, EventType
from typing import List, Dict

class ResearchAssistant:
    def __init__(self, model_name: str = "qwen2.5-coder"):
        db_config = DatabaseConfig(
            persistent=True,
            db_path="./research_cache.db",
        )
        self.config = RLMConfig(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            model=model_name,
            database=db_config,
            verbose=False,
        )
        self.repl = RLMREPL(self.config)
        self.history = []
    
    def load_paper(self, filepath: str):
        """Load a research paper."""
        stats = self.repl.load_document(filepath)
        print(f"Loaded paper: {stats.total_lines} lines, {stats.total_words} words")
        return stats
    
    def ask(self, question: str) -> Dict:
        """Ask a question about the loaded paper."""
        result = self.repl.ask(question)
        entry = {
            "question": question,
            "answer": result.answer,
            "iterations": result.iterations,
            "words_read": result.total_words,
        }
        self.history.append(entry)
        return entry
    
    def summarize(self) -> str:
        """Get a summary of the paper."""
        result = self.ask("Provide a comprehensive summary of this paper.")
        return result["answer"]
    
    def get_key_points(self) -> List[str]:
        """Extract key points from the paper."""
        result = self.ask("What are the main key points or findings?")
        # Simple parsing (could be improved)
        points = [p.strip() for p in result["answer"].split("\n") if p.strip()]
        return points
    
    def close(self):
        """Close the assistant."""
        self.repl.close()

# Usage
assistant = ResearchAssistant()
assistant.load_paper("research_paper.txt")

print("Summary:")
print(assistant.summarize())

print("\nKey Points:")
for point in assistant.get_key_points():
    print(f"- {point}")

assistant.close()
```

These examples demonstrate the flexibility and power of RLM-REPL. For more information, see the [API Reference](api-reference.md) and [Architecture](architecture.md) documentation.

