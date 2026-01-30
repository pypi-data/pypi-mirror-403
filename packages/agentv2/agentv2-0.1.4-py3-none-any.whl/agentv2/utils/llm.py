import warnings
from typing import Any, Dict, List, Optional, Type

from litellm import completion
from pydantic import BaseModel

# LiteLLM sometimes emits noisy serializer warnings from Pydantic internals.
# They don't affect runtime correctness for our use-case (we only need `message.content`).
warnings.filterwarnings(
    "ignore",
    message=r"Pydantic serializer warnings:.*",
    category=UserWarning,
)


class LLM:

    def __init__(
        self,
        model: str,
        system_prompt: str,
        api_base: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.api_base = api_base
        self.tools = tools

    def invoke(self, prompt: str, response_format: Type[BaseModel] = None) -> str:

        api_base = self.api_base if self.api_base else None

        # NOTE:
        # Passing `response_format` into LiteLLM can trigger noisy Pydantic serialization warnings
        # (and provider-side schema validation errors). We rely on our prompt to return JSON and
        # validate locally with Pydantic instead.
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            "api_base": api_base,
        }

        if self.tools:
            kwargs["tools"] = self.tools
        else:
            # Explicitly disable tools to prevent the model from trying to call them
            kwargs["tool_choice"] = "none"

        response = completion(**kwargs)

        # Extract message content from either dict or object responses
        if hasattr(response, "choices"):
            content = response.choices[0].message.content
        elif isinstance(response, dict):
            content = response["choices"][0]["message"]["content"]
        else:
            content = str(response)

        if response_format:
            return response_format.model_validate_json(content, strict=True)
        return content
