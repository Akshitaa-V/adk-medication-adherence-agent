"""End-to-end test of the ADK loop: model -> tool -> model, plus the guardrail
and audit trail, using a scripted model instead of Gemini."""

import asyncio

import pytest
from google.adk.runners import InMemoryRunner
from google.genai import types

from medication_agent.agent import build_agent
from medication_agent.guardrails import SAFE_REPLY
from tests.scripted_llm import ScriptedLlm, text, tool_call


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MED_DB_PATH", str(tmp_path / "test.db"))


async def ask(llm: ScriptedLlm, question: str):
    runner = InMemoryRunner(agent=build_agent(model=llm), app_name="test")
    session = await runner.session_service.create_session(app_name="test", user_id="u1")
    message = types.Content(role="user", parts=[types.Part(text=question)])
    events = [e async for e in runner.run_async(user_id="u1", session_id=session.id, new_message=message)]
    session = await runner.session_service.get_session(app_name="test", user_id="u1", session_id=session.id)
    return events, session.state


def test_agent_calls_tool_and_sees_real_data():
    llm = ScriptedLlm(model="scripted", replies=[
        tool_call("get_adherence_summary", patient_id="P001"),
        text("You took 17 of 21 doses (81%)."),
    ], requests=[])
    events, state = asyncio.run(ask(llm, "How is P001 doing with their medication?"))

    # The second model call must contain the tool's real result.
    tool_result = llm.requests[1].contents[-1].parts[0].function_response.response
    assert tool_result["adherence_percent"] == 81.0

    assert events[-1].content.parts[0].text == "You took 17 of 21 doses (81%)."
    assert state["audit_log"][0]["tool"] == "get_adherence_summary"
    assert state["audit_log"][0]["status"] == "success"


def test_guardrail_answers_without_calling_the_model():
    llm = ScriptedLlm(model="scripted", replies=[], requests=[])
    events, state = asyncio.run(ask(llm, "Should I double my metformin dose?"))

    assert llm.requests == []  # model was never called
    assert events[-1].content.parts[0].text == SAFE_REPLY
    assert state["guardrail_blocks"] == 1
