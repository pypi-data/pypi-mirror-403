# RLM-REPL Documentation

Welcome to the RLM-REPL documentation! This directory contains comprehensive guides for using the library.

## Documentation Index

### Getting Started
- **[Getting Started Guide](getting-started.md)** - Installation, setup, and your first query
  - Installation instructions
  - Model setup (Ollama, OpenAI, etc.)
  - First examples
  - Common issues

### API Reference
- **[API Reference](api-reference.md)** - Complete API documentation
  - Core classes (`RLMREPL`, `RLMConfig`, `DatabaseConfig`)
  - All methods and parameters
  - Data classes and events
  - Complete examples

### Configuration
- **[Configuration Guide](configuration.md)** - All configuration options
  - `RLMConfig` parameters
  - `DatabaseConfig` options
  - Environment variables
  - Best practices
  - Configuration examples

### Examples
- **[Examples](examples.md)** - Comprehensive usage examples
  - Basic usage
  - Streaming events
  - Persistent database
  - Building applications
  - Advanced queries
  - Error handling

### Architecture
- **[Architecture](architecture.md)** - How the system works
  - System overview
  - Core components
  - Reading process
  - Event system
  - Performance considerations

### Troubleshooting
- **[Troubleshooting Guide](troubleshooting.md)** - Common issues and solutions
  - Installation issues
  - Configuration problems
  - API connection issues
  - Query problems
  - Performance issues

## Quick Links

- [Main README](../README.md) - Project overview and quick start
- [Examples Directory](../examples/) - Working code examples
- [GitHub Repository](https://github.com/labKnowledge/rlm-repl-sql) - Source code

## Documentation Structure

```
docs/
├── README.md              # This file
├── getting-started.md     # Installation and first steps
├── api-reference.md       # Complete API documentation
├── configuration.md       # Configuration options
├── examples.md            # Usage examples
├── architecture.md        # System architecture
└── troubleshooting.md     # Common issues and solutions
```

## Getting Help

1. **Start here**: [Getting Started Guide](getting-started.md)
2. **Need examples?**: [Examples](examples.md)
3. **API questions?**: [API Reference](api-reference.md)
4. **Having issues?**: [Troubleshooting Guide](troubleshooting.md)

## About

**Author:** Remy Gakwaya

**Background:** RLM-REPL was created after reading the MIT paper on Recursive Language Models. The initial approach used a REPL where LLMs would generate Python functions, but this proved challenging with smaller models. 

After hundreds of iterations, Remy developed the **RLM-REPL v8 concept** - a human-like reading strategy optimized for local, smaller language models. The philosophy: if it works with poor and small models on limited computation, it will excel with leading LLMs.

The library evolved to use SQL-based retrieval with DuckDB, implementing the proven v8 reading strategy (overview → search → deep read → synthesize) in a more reliable way that works with models of all sizes.

## Contributing

Found an error or want to improve the documentation? Contributions are welcome!

1. Check existing issues
2. Open a new issue or pull request
3. Follow the existing documentation style

