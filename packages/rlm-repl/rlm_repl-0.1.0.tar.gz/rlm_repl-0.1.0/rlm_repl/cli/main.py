"""Command-line interface for RLM-REPL."""

import argparse
import sys
import os
from typing import Optional

from rlm_repl import RLMREPL, RLMConfig, DatabaseConfig


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="rlm-repl",
        description=(
            "RLM-REPL: Recursive Language Model with SQL Retrieval\n\n"
            "A tool for querying large documents using AI-powered SQL-based retrieval."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode with a document
  rlm-repl document.txt

  # With custom model endpoint
  rlm-repl document.txt --base-url http://localhost:11434/v1 --model qwen3-coder

  # Ask a single question (non-interactive)
  rlm-repl document.txt --question "What is the main topic?"

  # Use persistent database
  rlm-repl document.txt --db-path ./cache.db

  # Quiet mode (less output)
  rlm-repl document.txt -q

Environment Variables:
  RLM_BASE_URL      Base URL for the API
  RLM_API_KEY       API key
  RLM_MODEL         Model name
  RLM_VERBOSE       "true" or "false"
  RLM_MAX_ITERATIONS Maximum reading iterations
""",
    )

    # Positional arguments
    parser.add_argument(
        "document",
        nargs="?",
        help="Path to the document file to load",
    )

    # Model configuration
    model_group = parser.add_argument_group("Model Configuration")
    model_group.add_argument(
        "--base-url", "-u",
        default=os.getenv("RLM_BASE_URL", "http://localhost:11434/v1"),
        help="Base URL for the API (default: %(default)s)",
    )
    model_group.add_argument(
        "--api-key", "-k",
        default=os.getenv("RLM_API_KEY", "ollama"),
        help="API key for authentication (default: %(default)s)",
    )
    model_group.add_argument(
        "--model", "-m",
        default=os.getenv("RLM_MODEL", "qwen3-coder"),
        help="Model name to use (default: %(default)s)",
    )

    # Processing options
    proc_group = parser.add_argument_group("Processing Options")
    proc_group.add_argument(
        "--max-iterations", "-i",
        type=int,
        default=int(os.getenv("RLM_MAX_ITERATIONS", "6")),
        help="Maximum reading iterations (default: %(default)s)",
    )
    proc_group.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.2,
        help="Temperature for LLM responses (default: %(default)s)",
    )

    # Database options
    db_group = parser.add_argument_group("Database Options")
    db_group.add_argument(
        "--db-path",
        help="Path for persistent database (default: in-memory)",
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode (less verbose output)",
    )
    output_group.add_argument(
        "--question",
        help="Ask a single question and exit (non-interactive mode)",
    )

    # Version
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="%(prog)s 0.1.0",
    )

    return parser


def run_interactive(repl: RLMREPL):
    """Run the interactive REPL loop."""
    print("\n" + "=" * 70)
    print("INTERACTIVE MODE")
    print("=" * 70)
    print("Commands:")
    print("  - Ask any question about the document")
    print("  - 'stats' - Show statistics")
    print("  - 'sql: <query>' - Execute raw SQL query")
    print("  - 'schema' - Show database schema")
    print("  - 'quit' - Exit")
    print("=" * 70)

    while True:
        try:
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            # Handle commands
            lower_input = user_input.lower()

            if lower_input in ["quit", "exit", "q"]:
                print("\nExiting...")
                repl.print_stats()
                break

            if lower_input == "stats":
                repl.print_stats()
                continue

            if lower_input == "schema":
                schema = repl.get_schema()
                if schema.get("loaded"):
                    print(f"\nDocument: {schema['doc_name']}")
                    print(f"Table: {schema['table_name']}")
                    print(f"Lines: {schema['total_lines']:,}")
                    print(f"Words: {schema['total_words']:,}")
                    print(f"\nColumns:")
                    for col in schema["columns"]:
                        print(f"  {col['name']:15} {col['type']:10} - {col['description']}")
                else:
                    print("No document loaded")
                continue

            if lower_input.startswith("sql:"):
                sql_query = user_input[4:].strip()
                if sql_query:
                    try:
                        repl.query(sql_query)
                    except Exception as e:
                        print(f"SQL Error: {e}")
                else:
                    print("Please provide a SQL query after 'sql:'")
                continue

            # Ask question
            try:
                repl.ask(user_input)
            except Exception as e:
                print(f"Error: {e}")

        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            repl.print_stats()
            break
        except EOFError:
            print("\nExiting...")
            break


def main(args: Optional[list] = None) -> int:
    """Main entry point for the CLI.

    Args:
        args: Command line arguments (uses sys.argv if None).

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parser = create_parser()
    parsed = parser.parse_args(args)

    # Validate document path if provided
    if parsed.document and not os.path.exists(parsed.document):
        print(f"Error: File not found: {parsed.document}", file=sys.stderr)
        return 1

    # Create configuration
    db_config = DatabaseConfig(
        persistent=bool(parsed.db_path),
        db_path=parsed.db_path,
    )

    config = RLMConfig(
        base_url=parsed.base_url,
        api_key=parsed.api_key,
        model=parsed.model,
        verbose=not parsed.quiet,
        max_iterations=parsed.max_iterations,
        temperature=parsed.temperature,
        database=db_config,
    )

    # Create REPL
    try:
        with RLMREPL(config) as repl:
            # Load document if provided
            if parsed.document:
                try:
                    repl.load_document(parsed.document)
                except Exception as e:
                    print(f"Error loading document: {e}", file=sys.stderr)
                    return 1

                # Show initial stats
                if not parsed.quiet:
                    repl.print_stats()

                # Single question mode or interactive
                if parsed.question:
                    try:
                        result = repl.ask(parsed.question)
                        if parsed.quiet:
                            print(result.answer)
                        return 0
                    except Exception as e:
                        print(f"Error: {e}", file=sys.stderr)
                        return 1
                else:
                    run_interactive(repl)
            else:
                # No document - prompt for one
                print("=" * 70)
                print("RLM-REPL - Recursive Language Model with SQL Retrieval")
                print("=" * 70)
                print("\nNo document specified. Enter a document path to begin:")

                while True:
                    try:
                        doc_path = input("\nDocument path: ").strip()
                        if not doc_path:
                            continue

                        if doc_path.lower() in ["quit", "exit", "q"]:
                            return 0

                        if not os.path.exists(doc_path):
                            print(f"File not found: {doc_path}")
                            continue

                        repl.load_document(doc_path)
                        if not parsed.quiet:
                            repl.print_stats()
                        run_interactive(repl)
                        break

                    except KeyboardInterrupt:
                        print("\nExiting...")
                        return 0
                    except Exception as e:
                        print(f"Error: {e}")

    except KeyboardInterrupt:
        print("\nExiting...")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
