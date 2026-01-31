# Architecture

Understanding how RLM-REPL works under the hood.

## Background

RLM-REPL was created by **Remy Gakwaya** after reading the MIT paper on Recursive Language Models. The original concept involved using a REPL where the language model would generate Python functions to process and query documents. However, this approach faced significant challenges:

- **Smaller LLMs struggled** to generate complex, correct Python functions
- **Reliability issues** with function execution and error handling
- **Complexity** in managing dynamically generated code

After **hundreds of iterations and experiments**, Remy developed the **RLM-REPL v8 concept** - a human-like reading strategy specifically optimized for local, smaller language models. The development philosophy was: *if it works reliably with poor and small models on limited computation, it will perform exceptionally well with leading LLMs.*

The library evolved to use **SQL-based retrieval** with DuckDB, which provides:
- **Structured interface**: SQL is more predictable than generated Python code
- **Universal compatibility**: Works reliably with models of all sizes, from small local models to leading cloud-based LLMs
- **Performance**: Database indexes enable efficient querying
- **Safety**: No dynamic code execution required

This SQL-based approach implements the proven v8 human-like reading strategy (overview → search → deep read → synthesize) while being more practical and reliable for production use. The strategy was refined through extensive testing to ensure it works effectively even with resource-constrained local models.

## Overview

RLM-REPL implements a two-sided architecture that separates data storage from inference logic:

```
┌─────────────────────────────────────────────────────────┐
│                    RLM-REPL System                       │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────┐      ┌──────────────────┐         │
│  │   Data Layer     │      │ Inference Layer  │         │
│  │                  │      │                  │         │
│  │  DocumentDatabase│◄────►│  ReadingStrategy │         │
│  │  (DuckDB)        │      │  InferenceClient │         │
│  │                  │      │  AnswerSynthesizer│        │
│  └──────────────────┘      └──────────────────┘         │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Data Layer (DocumentDatabase)

**Purpose:** Store and query documents efficiently using SQL.

**Technology:** DuckDB (in-memory or persistent)

**Responsibilities:**
- Parse documents into line-level records
- Detect strategic markers (headers, section starts)
- Provide SQL query interface
- Maintain indexes for fast queries

**Schema:**
```sql
CREATE TABLE documents (
    line_num INTEGER,        -- Line number (1-indexed)
    text STRING,             -- Line content
    word_count INTEGER,      -- Words in this line
    is_header BOOLEAN,       -- True if header/title
    is_list_item BOOLEAN,    -- True if list item
    is_code BOOLEAN,         -- True if code content
    is_section_start BOOLEAN,-- True if section start
    is_strategic BOOLEAN     -- True if header or section start
);
```

**Key Features:**
- Automatic strategic marker detection
- Indexes on `line_num` and `is_strategic`
- Support for in-memory and persistent storage

### 2. Inference Layer

#### ReadingStrategy

**Purpose:** Generate prompts that guide the LLM to read documents strategically.

**Strategy Pattern:**
1. **Overview** - Read beginning (lines 1-100)
2. **Search** - Find keywords using `LIKE '%term%'`
3. **Read** - Focused reading (20-50 lines)
4. **Deep Read** - Detailed analysis (50-100 lines)

**Prompt Engineering:**
- Provides schema information
- Shows reading history
- Guides iteration-specific behavior
- Includes examples of correct queries

#### InferenceClient

**Purpose:** Abstract interface to LLM APIs.

**Features:**
- OpenAI-compatible API support
- Handles authentication
- Manages API calls
- Parses LLM responses

**Response Format:**
```json
{
    "thought": "What I've learned...",
    "reading_mode": "overview|search|read|deep_read",
    "goal": "What I hope to find",
    "sql_query": "SELECT ...",
    "satisfied": false,
    "next_move": "What I'll do next"
}
```

#### AnswerSynthesizer

**Purpose:** Combine gathered information into a final answer.

**Process:**
1. Collects all reading results
2. Builds context from gathered lines
3. Generates synthesis prompt
4. Calls LLM to generate answer

## Reading Process

### Iteration Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Question Asked                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Iteration 1: Overview                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 1. Build schema info (total lines, columns)      │   │
│  │ 2. Generate iteration prompt                     │   │
│  │ 3. Call LLM for reading strategy                  │   │
│  │ 4. Parse LLM response (SQL query)                │   │
│  │ 5. Auto-fix SQL if needed                         │   │
│  │ 6. Execute SQL query                               │   │
│  │ 7. Store results in history                       │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Iteration 2: Search                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 1. Build prompt with history                      │   │
│  │ 2. Guide toward keyword search                    │   │
│  │ 3. Call LLM for search strategy                   │   │
│  │ 4. Execute search query                           │   │
│  │ 5. Store results                                  │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         Iteration 3+: Deep Read (if needed)              │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 1. Read around findings                           │   │
│  │ 2. Extract detailed information                   │   │
│  │ 3. Continue until satisfied or max iterations    │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Answer Synthesis                             │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 1. Combine all reading results                    │   │
│  │ 2. Build synthesis prompt                        │   │
│  │ 3. Generate final answer                          │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
              Final Answer
```

### SQL Auto-Fixing

RLM-REPL includes automatic SQL query fixing to improve results:

1. **Missing ORDER BY**: Adds `ORDER BY line_num` for readability
2. **Missing LIMIT**: Adds `LIMIT 50` for search queries
3. **Missing word_count**: Ensures `word_count` is in SELECT
4. **Header-only queries**: Detects and fixes queries that would return only headers

Example fix:
```sql
-- LLM generates:
SELECT * FROM documents WHERE is_strategic = true LIMIT 50

-- Auto-fixed to:
SELECT line_num, text, word_count, is_header
FROM documents
WHERE line_num BETWEEN 1 AND 100
ORDER BY line_num
```

## Event System

### Event Flow

```
Document Loaded → Question Start → Iteration Start → SQL Execute → 
Results → Iteration End → [Repeat] → Synthesis Start → Answer → 
Question End
```

### Event Types

- **Lifecycle**: `SESSION_START`, `SESSION_END`, `DOCUMENT_LOADED`
- **Question Processing**: `QUESTION_START`, `QUESTION_END`
- **Iterations**: `ITERATION_START`, `ITERATION_END`
- **SQL**: `SQL_EXECUTE`, `SQL_RESULT`
- **LLM**: `LLM_REQUEST`, `LLM_RESPONSE`
- **Results**: `RESULTS`, `SYNTHESIS_START`, `SYNTHESIS_END`, `ANSWER`
- **Errors**: `ERROR`, `WARNING`

### EventEmitter

Manages event subscription and emission:
- Subscribers register callbacks
- Events are emitted to all subscribers
- Errors in callbacks don't break main flow

## Document Processing

### Line Parsing

When a document is loaded:

1. **Read file** line by line
2. **Detect metadata** for each line:
   - Headers: Lines starting with `#` or all uppercase short lines
   - List items: Lines starting with `-`, `*`, or numbers
   - Code: Lines containing code markers
   - Section starts: Headers or lines ending with `:`
3. **Calculate word count** per line
4. **Store in DuckDB** with all metadata

### Strategic Markers

Strategic markers help the LLM navigate the document:
- `is_header`: True for headers/titles
- `is_strategic`: True for headers or section starts
- Used to find document structure quickly

## Reading Strategies

### Overview Strategy

**Goal:** Understand document type and structure

**Query Pattern:**
```sql
SELECT line_num, text, word_count, is_header
FROM documents
WHERE line_num BETWEEN 1 AND 100
ORDER BY line_num
```

**Expected Result:** 1000-2000 words of actual content

### Search Strategy

**Goal:** Find where topic is discussed

**Query Pattern:**
```sql
SELECT line_num, text, word_count
FROM documents
WHERE LOWER(text) LIKE '%keyword%'
ORDER BY line_num
LIMIT 40
```

**Expected Result:** 20-40 matching lines

### Deep Read Strategy

**Goal:** Extract detailed information

**Query Pattern:**
```sql
SELECT line_num, text, word_count, is_header
FROM documents
WHERE line_num BETWEEN X AND Y
ORDER BY line_num
```

**Expected Result:** 500-1200 words of detailed content

## Answer Synthesis

### Process

1. **Collect Results**: All DataFrames from reading iterations
2. **Deduplicate**: Remove duplicate lines by `line_num`
3. **Build Context**: Combine text from all unique lines
4. **Generate Prompt**: Include question, reading history, and context
5. **Synthesize**: Call LLM to generate final answer

### Synthesis Prompt Structure

```
Answer the question based on the document excerpts provided.

QUESTION: [user question]

READING PROCESS:
  - Iteration 1 (overview): X lines, Y words
  - Iteration 2 (search): X lines, Y words
  ...

DOCUMENT EXCERPTS:
[combined text from all readings]

INSTRUCTIONS:
- Provide a clear, comprehensive answer
- Base answer ONLY on excerpts
- Cite line numbers: [Lines X-Y]
- Acknowledge missing information if incomplete
```

## Performance Considerations

### Database Performance

- **Indexes**: Created on `line_num` and `is_strategic`
- **In-memory**: Fast for single-session use
- **Persistent**: Cached for multi-session use

### LLM API Performance

- **Temperature**: Lower for reading strategy (more focused)
- **Max Iterations**: Balance between thoroughness and speed
- **Parallel Queries**: Not currently supported (sequential)

### Memory Usage

- **In-memory DB**: Stores entire document in memory
- **DataFrames**: Reading results stored temporarily
- **History**: Reading history kept for context

## Extensibility

### Custom Reading Strategies

You can influence reading by:
- Asking specific questions
- Using direct SQL queries
- Adjusting `max_iterations`
- Modifying temperature settings

### Custom Event Handlers

Subscribe to events for:
- Progress tracking
- Logging
- Metrics collection
- Custom UI updates

### Database Customization

- Custom table names
- Persistent storage paths
- Additional metadata columns (via DataFrame loading)

## Limitations

1. **Sequential Processing**: Iterations run sequentially
2. **Context Window**: Still limited by LLM's context window for synthesis
3. **SQL Complexity**: LLM must generate valid SQL
4. **Document Format**: Works best with structured text documents

## Future Improvements

Potential enhancements:
- Parallel iteration processing
- Advanced query optimization
- Multi-document support
- Custom reading strategy plugins
- Vector similarity search integration

