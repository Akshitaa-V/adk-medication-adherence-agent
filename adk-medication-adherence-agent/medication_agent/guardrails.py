"""Safety guardrails and an audit trail.

* block_clinical_advice  runs before every model call. If the user asks for
  something only a clinician should answer (changing a dose, stopping a drug,
  a diagnosis), the agent answers with a fixed safe message and the model is
  never called.
* audit_tool_call        runs after every tool call and records what was read,
  so every answer can be traced back to the data it used.
"""

import re
from datetime import datetime, timezone

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools import BaseTool, ToolContext
from google.genai import types

CLINICAL_ADVICE_PATTERNS = [
    r"\b(increase|decrease|raise|lower|change|adjust|double|skip|halve)\b.{0,40}\b(dose|dosage|mg|mcg|pill|tablet)s?\b",
    r"\b(stop|quit|discontinue)\b.{0,30}\b(taking|medication|medicine|metformin|atorvastatin|levothyroxine)\b",
    r"\bshould i (take|stop|skip|double)\b",
    r"\b(diagnose|diagnosis|do i have)\b",
    r"\bwhat (dose|dosage) should\b",
]

SAFE_REPLY = (
    "I can't give advice on changing, stopping or skipping medication, or on "
    "diagnoses. Please talk to your doctor or pharmacist about this. I can show "
    "your medication schedule, your adherence summary or the doses you missed."
)


def needs_clinician(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(p, lowered) for p in CLINICAL_ADVICE_PATTERNS)


def _latest_user_text(llm_request: LlmRequest) -> str:
    for content in reversed(llm_request.contents or []):
        if content.role != "user":
            continue
        texts = [p.text for p in (content.parts or []) if p.text]
        if texts:
            return " ".join(texts)
        return ""  # newest user turn is a tool result, not a question
    return ""


def block_clinical_advice(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> LlmResponse | None:
    question = _latest_user_text(llm_request)
    if question and needs_clinician(question):
        callback_context.state["guardrail_blocks"] = callback_context.state.get("guardrail_blocks", 0) + 1
        return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=SAFE_REPLY)]))
    return None


def audit_tool_call(
    tool: BaseTool, args: dict, tool_context: ToolContext, tool_response: dict
) -> dict | None:
    log = list(tool_context.state.get("audit_log", []))
    log.append({
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": tool.name,
        "args": args,
        "status": tool_response.get("status") if isinstance(tool_response, dict) else None,
    })
    tool_context.state["audit_log"] = log
    return None  # keep the original tool response
