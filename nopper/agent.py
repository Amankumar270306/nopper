"""Agent and Tool implementation."""

import inspect
import json
from collections.abc import Callable
from typing import Any

from nopper.models.messages import Message, Role
from nopper.wrapper.async_wrapper import AsyncAI
from nopper.wrapper.wrapper import AI


def _get_type_name(t: Any) -> str:
    if t == str:
        return "string"
    if t == int:
        return "integer"
    if t == float:
        return "number"
    if t == bool:
        return "boolean"
    if t == list or getattr(t, "__origin__", None) == list:
        return "array"
    if t == dict or getattr(t, "__origin__", None) == dict:
        return "object"
    return "string"


class Tool:
    """Encapsulates a Python function as an AI tool."""

    def __init__(self, func: Callable[..., Any]):
        self.func = func
        self.name = func.__name__
        self.description = inspect.getdoc(func) or f"Function {self.name}"

        sig = inspect.signature(func)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            param_type = (
                _get_type_name(param.annotation)
                if param.annotation != inspect.Parameter.empty
                else "string"
            )

            properties[param_name] = {
                "type": param_type,
            }
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        self.schema = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.func(*args, **kwargs)


def tool(func: Callable[..., Any]) -> Tool:
    """Decorator to convert a Python function into an AI tool."""
    return Tool(func)


class Agent:
    """Agent class implementing ReAct loop with tools."""

    def __init__(
        self,
        ai: AI | AsyncAI,
        system_prompt: str | None = None,
        tools: list[Tool] | None = None,
    ):
        self.ai = ai
        self.system_prompt = system_prompt
        self.tools = {t.name: t for t in (tools or [])}
        self.history: list[Message] = []
        if system_prompt:
            self.history.append(Message(role=Role.SYSTEM, content=system_prompt))

    def run(self, prompt: str, max_iterations: int = 10) -> str:
        """Run the agent loop synchronously."""
        self.history.append(Message(role=Role.USER, content=prompt))

        tool_schemas = [t.schema for t in self.tools.values()] if self.tools else None

        for _ in range(max_iterations):
            response = self.ai.chat(self.history, tools=tool_schemas, raw=True)
            if not hasattr(response, "message"):
                break
            self.history.append(response.message)

            if response.message.tool_calls:
                for tool_call in response.message.tool_calls:
                    func_name = tool_call.function.name
                    args_str = tool_call.function.arguments

                    try:
                        args = json.loads(args_str)
                    except json.JSONDecodeError:
                        args = {}

                    if func_name in self.tools:
                        try:
                            result = self.tools[func_name](**args)
                            tool_result_str = str(result)
                        except Exception as e:
                            tool_result_str = f"Error executing tool: {e!s}"
                    else:
                        tool_result_str = f"Tool {func_name} not found."

                    self.history.append(
                        Message(
                            role=Role.TOOL,
                            content=tool_result_str,
                            name=func_name,
                            tool_call_id=tool_call.id,
                        )
                    )
            else:
                return response.message.content or ""

        return "Max iterations reached without final answer."
