"""A scripted stand-in for Gemini so the full ADK loop can be tested offline."""

from typing import AsyncGenerator

from google.adk.models import LlmRequest, LlmResponse
from google.adk.models.base_llm import BaseLlm
from google.adk.models import LlmCapabilities
from google.genai import types


class ScriptedLlm(BaseLlm):
    """Returns pre-written replies in order and records every request it got."""

    replies: list = []
    requests: list = []

    @property
    def capabilities(self) -> LlmCapabilities:
        return LlmCapabilities(output_schema_and_tools=True)

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        self.requests.append(llm_request)
        yield LlmResponse(content=self.replies.pop(0))


def tool_call(name: str, **args) -> types.Content:
    return types.Content(role="model", parts=[types.Part(function_call=types.FunctionCall(name=name, args=args))])


def text(message: str) -> types.Content:
    return types.Content(role="model", parts=[types.Part(text=message)])
