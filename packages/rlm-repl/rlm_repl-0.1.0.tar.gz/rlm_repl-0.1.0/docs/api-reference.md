# API Reference

Complete reference for the RLM-REPL Python API.

## Core Classes

### RLMREPL

Main class for document querying and question answering.

```python
from rlm_repl import RLMREPL, RLMConfig

repl = RLMREPL(config)
```

#### Constructor

```python
RLMREPL(config: RLMConfig)
```

**Parameters:**
- `config` (RLMConfig): Configuration object with model settings

**Example:**
```python
config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
)
repl = RLMREPL(config)
```

#### Methods

##### `load_document(filepath: str, doc_name: Optional[str] = None) -> DocumentStats`

Load a document from a file.

**Parameters:**
- `filepath` (str): Path to the text file
- `doc_name` (str, optional): Name for the document (defaults to filename)

**Returns:**
- `DocumentStats`: Statistics about the loaded document

**Raises:**
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If file is empty

**Example:**
```python
stats = repl.load_document("book.txt", "my_book")
print(f"Loaded {stats.total_lines} lines")
```

##### `load_text(text: str, doc_name: str = "text") -> DocumentStats`

Load text content directly.

**Parameters:**
- `text` (str): Text content to load
- `doc_name` (str): Name for the document

**Returns:**
- `DocumentStats`: Statistics about the loaded document

**Example:**
```python
stats = repl.load_text("Some text content", "my_doc")
```

##### `load_dataframe(df: pd.DataFrame, doc_name: str = "dataframe") -> DocumentStats`

Load a pandas DataFrame.

**Parameters:**
- `df` (pd.DataFrame): DataFrame with at minimum a 'text' column
- `doc_name` (str): Name for the document

**Returns:**
- `DocumentStats`: Statistics about the loaded document

**Example:**
```python
import pandas as pd
df = pd.DataFrame({"text": ["Line 1", "Line 2", "Line 3"]})
stats = repl.load_dataframe(df, "my_data")
```

##### `ask(question: str) -> QuestionResult`

Ask a question about the loaded document.

**Parameters:**
- `question` (str): The question to answer

**Returns:**
- `QuestionResult`: Result object with answer and statistics

**Raises:**
- `RuntimeError`: If no document is loaded

**Example:**
```python
result = repl.ask("What is the main topic?")
print(result.answer)
print(f"Iterations: {result.iterations}")
print(f"Lines read: {result.unique_lines}")
```

##### `ask_stream(question: str) -> Generator[Event, None, QuestionResult]`

Ask a question with streaming events.

**Parameters:**
- `question` (str): The question to answer

**Yields:**
- `Event`: Events during processing

**Returns:**
- `QuestionResult`: Final result when generator completes

**Example:**
```python
for event in repl.ask_stream("What is the topic?"):
    print(f"Event: {event.type.value}")
    if event.type == EventType.ANSWER:
        print(event.data['answer'])
```

##### `query(sql: str) -> QueryResult`

Execute a raw SQL query.

**Parameters:**
- `sql` (str): SQL query string

**Returns:**
- `QueryResult`: Result with DataFrame and statistics

**Example:**
```python
result = repl.query("SELECT * FROM documents WHERE line_num < 100")
print(result.dataframe)
```

##### `get_schema() -> Dict[str, Any]`

Get database schema information.

**Returns:**
- `Dict[str, Any]`: Schema details including columns and statistics

**Example:**
```python
schema = repl.get_schema()
print(f"Document: {schema['doc_name']}")
print(f"Total lines: {schema['total_lines']}")
```

##### `session_stats() -> Dict[str, Any]`

Get session statistics.

**Returns:**
- `Dict[str, Any]`: Statistics about questions asked in this session

**Example:**
```python
stats = repl.session_stats()
print(f"Questions asked: {stats['questions_asked']}")
print(f"Total words read: {stats['total_words_read']}")
```

##### `print_stats()`

Print session statistics to console.

**Example:**
```python
repl.print_stats()
```

##### `subscribe(callback: Callable[[Event], None])`

Subscribe to streaming events.

**Parameters:**
- `callback` (Callable): Function that takes an Event as argument

**Example:**
```python
def on_event(event):
    print(f"Event: {event.type.value}")

repl.subscribe(on_event)
```

##### `unsubscribe(callback: Callable[[Event], None])`

Unsubscribe from streaming events.

**Parameters:**
- `callback` (Callable): Previously subscribed callback

##### `close()`

Close the REPL and release resources.

**Example:**
```python
repl.close()
```

#### Context Manager

RLMREPL supports context manager protocol:

```python
with RLMREPL(config) as repl:
    repl.load_document("file.txt")
    result = repl.ask("Question?")
# Automatically closes when exiting context
```

#### Properties

##### `database: DocumentDatabase`

Access the underlying database.

##### `is_loaded: bool`

Check if a document is loaded.

##### `stats: Optional[DocumentStats]`

Get document statistics.

---

### RLMConfig

Configuration class for RLM-REPL.

```python
from rlm_repl import RLMConfig, DatabaseConfig

config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
)
```

#### Constructor

```python
RLMConfig(
    base_url: str,
    api_key: str,
    model: str,
    verbose: bool = True,
    max_iterations: int = 6,
    temperature: float = 0.2,
    synthesis_temperature: float = 0.3,
    database: DatabaseConfig = DatabaseConfig(),
    on_event: Optional[Callable[[Event], None]] = None,
)
```

**Parameters:**
- `base_url` (str): Base URL for the AI model API
- `api_key` (str): API key for authentication
- `model` (str): Model name/identifier
- `verbose` (bool): Enable verbose output (default: True)
- `max_iterations` (int): Maximum reading iterations (default: 6)
- `temperature` (float): Temperature for LLM responses (default: 0.2)
- `synthesis_temperature` (float): Temperature for answer synthesis (default: 0.3)
- `database` (DatabaseConfig): Database configuration (default: in-memory)
- `on_event` (Callable, optional): Event callback function

#### Class Methods

##### `from_env(**overrides) -> RLMConfig`

Create configuration from environment variables.

**Parameters:**
- `**overrides`: Override any environment variable values

**Example:**
```python
config = RLMConfig.from_env(model="custom-model")
```

#### Methods

##### `with_callback(callback: Callable[[Event], None]) -> RLMConfig`

Return a new config with the specified event callback.

**Parameters:**
- `callback` (Callable): Event callback function

**Returns:**
- `RLMConfig`: New configuration instance

---

### DatabaseConfig

Configuration for the DuckDB database layer.

```python
from rlm_repl import DatabaseConfig

db_config = DatabaseConfig(
    persistent=True,
    db_path="./cache.db",
)
```

#### Constructor

```python
DatabaseConfig(
    persistent: bool = False,
    db_path: Optional[str] = None,
    table_name: str = "documents",
)
```

**Parameters:**
- `persistent` (bool): Use persistent database (default: False, uses in-memory)
- `db_path` (str, optional): Path to database file (required if persistent=True)
- `table_name` (str): Name of documents table (default: "documents")

**Raises:**
- `ValueError`: If persistent=True but db_path is not provided

---

## Data Classes

### QuestionResult

Result of asking a question.

```python
@dataclass
class QuestionResult:
    answer: str                    # Final answer text
    iterations: int                # Number of reading iterations
    unique_lines: int              # Unique lines read
    total_words: int               # Total words read
    elapsed_time: float            # Time elapsed in seconds
    history: List[ReadingHistory]  # Reading history
```

### DocumentStats

Statistics about a loaded document.

```python
@dataclass
class DocumentStats:
    total_lines: int        # Total number of lines
    total_words: int        # Total number of words
    strategic_lines: int     # Number of strategic markers
    min_line: int           # Minimum line number
    max_line: int           # Maximum line number
    doc_name: str           # Document name
```

### QueryResult

Result of a SQL query.

```python
@dataclass
class QueryResult:
    dataframe: pd.DataFrame  # Result DataFrame
    row_count: int           # Number of rows
    word_count: int          # Total word count
    
    @property
    def is_empty(self) -> bool  # Check if result is empty
```

---

## Events

### EventType

Enumeration of event types.

```python
from rlm_repl import EventType

EventType.DOCUMENT_LOADED
EventType.QUESTION_START
EventType.QUESTION_END
EventType.ITERATION_START
EventType.ITERATION_END
EventType.SQL_EXECUTE
EventType.RESULTS
EventType.SYNTHESIS_START
EventType.SYNTHESIS_END
EventType.ANSWER
EventType.ERROR
```

### Event

Base event class.

```python
@dataclass
class Event:
    type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]
```

### Specific Event Classes

- `IterationStartEvent`: Emitted when iteration starts
- `IterationEndEvent`: Emitted when iteration ends
- `SQLExecuteEvent`: Emitted when SQL query executes
- `ResultsEvent`: Emitted when query results are received
- `SynthesisEvent`: Emitted during answer synthesis
- `AnswerEvent`: Emitted when final answer is ready
- `ErrorEvent`: Emitted when an error occurs

---

## Example: Complete Workflow

```python
from rlm_repl import RLMREPL, RLMConfig, DatabaseConfig, EventType

# Configure database
db_config = DatabaseConfig(
    persistent=True,
    db_path="./cache.db",
)

# Configure REPL
config = RLMConfig(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5-coder",
    verbose=True,
    max_iterations=6,
    database=db_config,
)

# Event handler
def on_event(event):
    if event.type == EventType.ITERATION_START:
        print(f"Starting iteration {event.data['iteration'] + 1}")

# Create REPL
with RLMREPL(config) as repl:
    # Load document
    stats = repl.load_document("large_document.txt")
    print(f"Loaded {stats.total_lines} lines")
    
    # Ask questions
    result = repl.ask("What is the main topic?")
    print(f"Answer: {result.answer}")
    print(f"Read {result.total_words} words in {result.elapsed_time:.1f}s")
    
    # Get session stats
    session_stats = repl.session_stats()
    print(f"Total questions: {session_stats['questions_asked']}")
```

