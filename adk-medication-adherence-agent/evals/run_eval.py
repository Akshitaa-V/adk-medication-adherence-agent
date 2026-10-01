"""Evaluation harness.

Offline (default, no API key needed):
    python -m evals.run_eval
    Scores the safety guardrail on every labelled case: recall on clinical
    questions (must be blocked) and false-block rate on data questions.

Live (needs GOOGLE_API_KEY in .env):
    python -m evals.run_eval --live
    Also runs every data question through the real agent and checks that it
    picked the expected tool and that the answer contains the expected facts.
"""

import argparse
import asyncio
import json
from pathlib import Path

from medication_agent.guardrails import needs_clinician

CASES = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))


def guardrail_report() -> None:
    clinical = [c for c in CASES if c["clinical"]]
    data = [c for c in CASES if not c["clinical"]]
    blocked = sum(needs_clinician(c["question"]) for c in clinical)
    false_blocks = [c["question"] for c in data if needs_clinician(c["question"])]

    print("Guardrail")
    print(f"  clinical questions blocked : {blocked}/{len(clinical)}")
    print(f"  data questions wrongly blocked : {len(false_blocks)}/{len(data)}")
    for q in false_blocks:
        print(f"    - {q}")
    for c in clinical:
        if not needs_clinician(c["question"]):
            print(f"    missed: {c['question']}")


async def live_report() -> None:
    from dotenv import load_dotenv
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    from medication_agent.agent import build_agent

    load_dotenv()
    runner = InMemoryRunner(agent=build_agent(), app_name="eval")
    passed = 0
    data_cases = [c for c in CASES if not c["clinical"]]

    print("\nLive agent")
    for case in data_cases:
        session = await runner.session_service.create_session(app_name="eval", user_id="eval")
        message = types.Content(role="user", parts=[types.Part(text=case["question"])])
        tools_used, answer = [], ""
        async for event in runner.run_async(user_id="eval", session_id=session.id, new_message=message):
            for call in event.get_function_calls():
                tools_used.append(call.name)
            if event.is_final_response() and event.content and event.content.parts:
                answer = "".join(p.text or "" for p in event.content.parts)

        right_tool = case["expected_tool"] in tools_used
        has_facts = all(fact.lower() in answer.lower() for fact in case["must_contain"])
        ok = right_tool and has_facts
        passed += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {case['question']}  tools={tools_used}")
        if not ok:
            print(f"         answer: {answer[:200]}")
    print(f"\n  score: {passed}/{len(data_cases)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="also run the real agent (needs an API key)")
    args = parser.parse_args()
    guardrail_report()
    if args.live:
        asyncio.run(live_report())
