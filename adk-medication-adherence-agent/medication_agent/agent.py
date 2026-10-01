"""Root agent. `adk web` and `adk run` look for `root_agent` in this module."""

import os

from google.adk.agents import LlmAgent

from .guardrails import audit_tool_call, block_clinical_advice
from .tools import get_adherence_summary, get_medication_schedule, list_missed_doses

INSTRUCTION = """
You help patients and care teams understand medication adherence data.

Rules:
- Only state facts that come from your tools. Never guess numbers.
- If the patient ID is missing, ask for it before calling a tool.
- If a tool returns status "error", explain the problem in plain words.
- Keep answers short and friendly, in plain language a patient understands.
- Never give medical advice. For questions about changing, stopping or
  skipping medication, tell the user to speak to their doctor or pharmacist.
"""


def build_agent(model=None) -> LlmAgent:
    return LlmAgent(
        name="medication_adherence_agent",
        model=model or os.getenv("MODEL", "gemini-2.5-flash"),
        description="Answers questions about a patient's medication schedule and adherence.",
        instruction=INSTRUCTION,
        tools=[get_medication_schedule, get_adherence_summary, list_missed_doses],
        before_model_callback=block_clinical_advice,
        after_tool_callback=audit_tool_call,
    )


root_agent = build_agent()
