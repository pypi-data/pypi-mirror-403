"""AI model client abstraction for RLM-REPL."""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import json
import re

from openai import OpenAI


@dataclass
class LLMResponse:
    """Structured response from the LLM."""

    content: str
    thought: str = ""
    reading_mode: str = ""
    goal: str = ""
    sql_query: str = ""
    satisfied: bool = False
    next_move: str = ""
    raw_response: str = ""
    parse_error: Optional[str] = None


class InferenceClient:
    """Client for interacting with OpenAI-compatible LLM APIs.

    Supports any OpenAI-compatible API including:
    - OpenAI
    - Ollama (local models)
    - vLLM
    - LMStudio
    - Any other compatible provider

    Example:
        client = InferenceClient(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            model="qwen3-coder"
        )
        response = client.chat([{"role": "user", "content": "Hello"}])
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        temperature: float = 0.2,
    ):
        """Initialize the inference client.

        Args:
            base_url: Base URL for the API.
            api_key: API key for authentication.
            model: Model identifier to use.
            temperature: Default temperature for responses.
        """
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self._client = OpenAI(base_url=base_url, api_key=api_key)

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
    ) -> str:
        """Send a chat completion request.

        Args:
            messages: List of message dicts with "role" and "content".
            temperature: Override default temperature.

        Returns:
            The assistant's response content.
        """
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature if temperature is not None else self.temperature,
        )
        return response.choices[0].message.content

    def get_reading_strategy(
        self,
        system_prompt: str,
        user_question: str,
    ) -> LLMResponse:
        """Get a reading strategy decision from the LLM.

        Args:
            system_prompt: System prompt with database schema and instructions.
            user_question: The user's question to answer.

        Returns:
            LLMResponse with parsed strategy or error.
        """
        raw_response = self.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question},
        ])

        return self._parse_strategy_response(raw_response)

    def synthesize_answer(
        self,
        synthesis_prompt: str,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate a final answer from gathered context.

        Args:
            synthesis_prompt: Prompt with question and gathered context.
            temperature: Temperature for synthesis (usually slightly higher).

        Returns:
            The synthesized answer.
        """
        return self.chat(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that provides accurate answers "
                        "based on provided context. Always cite line numbers when making "
                        "specific claims."
                    ),
                },
                {"role": "user", "content": synthesis_prompt},
            ],
            temperature=temperature,
        )

    def _parse_strategy_response(self, raw_response: str) -> LLMResponse:
        """Parse LLM response into structured format.

        Attempts to extract JSON from the response, handling various formats
        including markdown code blocks.
        """
        json_str = raw_response.strip()

        # Try to find JSON block
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            parts = json_str.split("```")
            if len(parts) >= 2:
                json_str = parts[1].split("```")[0].strip()

        # Try to parse
        try:
            strategy = json.loads(json_str)
            return LLMResponse(
                content=raw_response,
                thought=strategy.get("thought", ""),
                reading_mode=strategy.get("reading_mode", ""),
                goal=strategy.get("goal", ""),
                sql_query=strategy.get("sql_query", ""),
                satisfied=strategy.get("satisfied", False),
                next_move=strategy.get("next_move", ""),
                raw_response=raw_response,
            )
        except json.JSONDecodeError as e:
            # Try to find JSON pattern in response
            json_match = re.search(
                r'\{[^{}]*"thought"[^{}]*"sql_query"[^{}]*\}',
                raw_response,
                re.DOTALL,
            )
            if json_match:
                try:
                    strategy = json.loads(json_match.group(0))
                    return LLMResponse(
                        content=raw_response,
                        thought=strategy.get("thought", ""),
                        reading_mode=strategy.get("reading_mode", ""),
                        goal=strategy.get("goal", ""),
                        sql_query=strategy.get("sql_query", ""),
                        satisfied=strategy.get("satisfied", False),
                        next_move=strategy.get("next_move", ""),
                        raw_response=raw_response,
                    )
                except json.JSONDecodeError:
                    pass

            return LLMResponse(
                content=raw_response,
                raw_response=raw_response,
                parse_error=f"JSON parsing error: {e}",
            )
