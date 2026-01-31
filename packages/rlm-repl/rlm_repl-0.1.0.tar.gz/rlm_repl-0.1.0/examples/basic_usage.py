#!/usr/bin/env python3
"""Basic usage example for RLM-REPL.

This example demonstrates how to use the RLM-REPL library to load a document
and ask questions about it.
"""

from rlm_repl import RLMREPL, RLMConfig


def main():
    # Create configuration
    # For Ollama (local):
    config = RLMConfig(
        base_url="http://localhost:11434/v1",
        api_key="ollama",  # Ollama doesn't require a real key
        model="qwen3-coder",  # or any model you have installed
        verbose=True,
        max_iterations=6,
    )

    # For OpenAI:
    # config = RLMConfig(
    #     base_url="https://api.openai.com/v1",
    #     api_key="your-api-key",
    #     model="gpt-4",
    # )

    # Create REPL instance
    with RLMREPL(config) as repl:
        # Load a document
        # repl.load_document("path/to/your/document.txt")

        # Or load text directly
        sample_text =  open("examples/library.txt", "r").read()

        repl.load_text(sample_text, "ml_intro")

        # Ask questions
        print("\n" + "=" * 70)
        print("Asking: how many books are in the library?")
        print("=" * 70)

        result = repl.ask("what are the titles of the books in the library?")

        # Access the result
        print(f"\nAnswer: {result.answer}")
        print(f"\nStatistics:")
        print(f"  Iterations: {result.iterations}")
        print(f"  Lines read: {result.unique_lines}")
        print(f"  Words read: {result.total_words}")
        print(f"  Time: {result.elapsed_time:.2f}s")


if __name__ == "__main__":
    main()
