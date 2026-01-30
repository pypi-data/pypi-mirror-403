import json
import logging
import os
import textwrap
from typing import Any, Optional

from openai import OpenAI as OpenAIClient

from ..agent import Agent
from ..structs import Grid, SessionState

logger = logging.getLogger()


class LLM(Agent):
    MAX_QUERIES: int = 20
    MODEL: str = "gpt-4o-mini"

    messages: list[dict[str, Any]]
    token_counter: int

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.messages = []
        self.token_counter = 0

    @property
    def name(self) -> str:
        sanitized_model_name = self.MODEL.replace("/", "-").replace(":", "-")
        return f"{super().name}.{sanitized_model_name}"

    def query(self, session: SessionState) -> Optional[Grid]:
        logging.getLogger("openai").setLevel(logging.CRITICAL)
        logging.getLogger("httpx").setLevel(logging.CRITICAL)

        client = OpenAIClient(api_key=os.environ.get("OPENAI_API_KEY", ""))

        if session.query_count >= self.MAX_QUERIES:
            return None

        prompt = self._build_query_prompt(session)
        self.messages.append({"role": "user", "content": prompt})

        tools = self._build_query_tools()

        try:
            response = client.chat.completions.create(
                model=self.MODEL,
                messages=self.messages,
                tools=tools,
                tool_choice="required",
            )
        except Exception as e:
            logger.warning(f"LLM query failed: {e}")
            return None

        if response.usage:
            self.token_counter += response.usage.total_tokens

        message = response.choices[0].message
        self.messages.append(message)

        if message.tool_calls:
            tool_call = message.tool_calls[0]
            if tool_call.function.name == "done_learning":
                return None
            elif tool_call.function.name == "query_oracle":
                try:
                    args = json.loads(tool_call.function.arguments)
                    grid = args.get("grid", [[0]])
                    return grid
                except (json.JSONDecodeError, KeyError):
                    return None

        return None

    def submit(self, session: SessionState) -> Grid:
        logging.getLogger("openai").setLevel(logging.CRITICAL)
        logging.getLogger("httpx").setLevel(logging.CRITICAL)

        client = OpenAIClient(api_key=os.environ.get("OPENAI_API_KEY", ""))

        prompt = self._build_predict_prompt(session)
        self.messages.append({"role": "user", "content": prompt})

        try:
            response = client.chat.completions.create(
                model=self.MODEL,
                messages=self.messages,
                response_format={"type": "json_object"},
            )
        except Exception as e:
            logger.warning(f"LLM predict failed: {e}")
            if session.test_input:
                return [row[:] for row in session.test_input]
            return [[0]]

        if response.usage:
            self.token_counter += response.usage.total_tokens

        try:
            content = response.choices[0].message.content or "{}"
            result = json.loads(content)
            return result.get("output", [[0]])
        except (json.JSONDecodeError, KeyError):
            if session.test_input:
                return [row[:] for row in session.test_input]
            return [[0]]

    def _build_query_prompt(self, session: SessionState) -> str:
        history = ""
        for i, q in enumerate(session.queries):
            history += f"\nQuery {i+1} Input:\n{self._format_grid(q.input)}\n"
            if q.output:
                history += f"Query {i+1} Output:\n{self._format_grid(q.output)}\n"
            else:
                history += f"Query {i+1} Output: null (input is out of domain)\n"

        return textwrap.dedent(f"""
You are solving an ARC task. Your goal is to discover the transformation rule.

You can query the oracle with any grid to see what output it produces.
When you have enough information, call done_learning to proceed to the test phase.

Query history ({session.query_count} queries so far):
{history if history else "(no queries yet)"}

Choose your next action: either query_oracle with a grid, or done_learning if ready.
        """).strip()

    def _build_predict_prompt(self, session: SessionState) -> str:
        history = ""
        for i, q in enumerate(session.queries):
            history += f"\nQuery {i+1} Input:\n{self._format_grid(q.input)}\n"
            if q.output:
                history += f"Query {i+1} Output:\n{self._format_grid(q.output)}\n"
            else:
                history += f"Query {i+1} Output: null (input is out of domain)\n"

        test_input_str = self._format_grid(session.test_input) if session.test_input else "[[0]]"

        return textwrap.dedent(f"""
You are in the TEST phase of an ARC task.

Based on your learning from the queries:
{history if history else "(no queries made)"}

Test Input:
{test_input_str}

Predict the output grid. Respond with JSON in this format:
{{"output": [[...], [...], ...]}}
        """).strip()

    def _build_query_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_oracle",
                    "description": "Query the oracle with an input grid to see what output it produces.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "grid": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": {"type": "integer", "minimum": 0, "maximum": 9}
                                },
                                "description": "A 2D grid of integers (0-9)"
                            }
                        },
                        "required": ["grid"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "done_learning",
                    "description": "Signal that you have learned enough and are ready for the test phase.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
        ]

    def _format_grid(self, grid: Optional[Grid]) -> str:
        if not grid:
            return "null"
        return "\n".join(str(row) for row in grid)

    def get_query_reasoning(self, session: SessionState, query_input: Grid) -> Any:
        return {
            "model": self.MODEL,
            "query_count": session.query_count,
            "tokens": self.token_counter,
        }

    def get_submit_reasoning(self, session: SessionState, answer: Grid) -> Any:
        return {
            "model": self.MODEL,
            "total_queries": session.query_count,
            "total_tokens": self.token_counter,
        }
