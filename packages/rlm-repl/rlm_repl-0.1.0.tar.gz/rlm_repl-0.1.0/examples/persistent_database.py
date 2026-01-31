#!/usr/bin/env python3
"""Example showing persistent database usage in RLM-REPL.

This example demonstrates how to use a persistent DuckDB database
to avoid reloading documents between sessions.
"""

import os
from rlm_repl import RLMREPL, RLMConfig, DatabaseConfig


def main():
    # Define database path
    db_path = "./document_cache.db"

    # Create configuration with persistent database
    db_config = DatabaseConfig(
        persistent=True,
        db_path=db_path,
    )

    config = RLMConfig(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        model="qwen3-coder",
        verbose=True,
        database=db_config,
    )

    with RLMREPL(config) as repl:
        # Check if database already has data
        schema = repl.get_schema()

        if schema.get("loaded"):
            print(f"Using cached document: {schema['doc_name']}")
            print(f"  Lines: {schema['total_lines']}")
            print(f"  Words: {schema['total_words']}")
        else:
            # Load document for the first time
            print("Loading document for the first time...")

            sample_text = """
            # Database Systems

            A database is an organized collection of structured information,
            or data, typically stored electronically in a computer system.

            ## Types of Databases

            1. Relational Databases (RDBMS)
               - Store data in tables with rows and columns
               - Use SQL for querying
               - Examples: PostgreSQL, MySQL, SQLite

            2. NoSQL Databases
               - Document stores (MongoDB)
               - Key-value stores (Redis)
               - Column-family stores (Cassandra)
               - Graph databases (Neo4j)

            ## SQL Fundamentals

            SQL (Structured Query Language) is used to manage relational databases.

            Basic operations:
            - SELECT: Retrieve data
            - INSERT: Add new records
            - UPDATE: Modify existing records
            - DELETE: Remove records

            Example query:
            SELECT name, age FROM users WHERE age > 21 ORDER BY name;

            ## Indexing

            Indexes improve query performance by creating efficient lookup structures.
            Types of indexes:
            - B-tree indexes (most common)
            - Hash indexes
            - Full-text indexes
            - Spatial indexes

            ## Transactions

            Transactions ensure data integrity with ACID properties:
            - Atomicity: All or nothing
            - Consistency: Valid state transitions
            - Isolation: Concurrent transaction safety
            - Durability: Committed data persists
            """

            repl.load_text(sample_text, "database_guide")

        # Ask questions
        result = repl.ask("What are the ACID properties?")

        print("\n" + "=" * 70)
        print("Answer:")
        print(result.answer)

    print(f"\nDatabase saved to: {db_path}")
    print("Next run will use the cached data.")

    # Note: To clear the cache, delete the database file:
    # os.remove(db_path)


if __name__ == "__main__":
    main()
