# Medication Adherence Agent (Google ADK)

An AI agent built with **Google's Agent Development Kit (ADK)** that answers questions about a patient's medication schedule and adherence. It reads from a SQLite data source, refuses clinical advice with a safety guardrail, keeps an audit trail of every tool call, and ships with tests and an evaluation harness.

All data is **synthetic**. This is a learning project, not a medical device.

## Why I built it

I wanted to try Google ADK on a problem where output quality and safety actually matter. In health products, an agent that reports adherence data must never invent numbers, and it must never answer "should I change my dose?". This project is my attempt at an agent that can be trusted with exactly that much and no more.

## What it does

```
User question
   │
   ▼
before_model_callback ──► clinical question? ──► fixed safe reply (model never called)
   │ no
   ▼
Gemini (LlmAgent) ──► picks a tool ──► SQLite data source
   │                                      │
   │◄────────── tool result ◄─────────────┘
   │            after_tool_callback writes the audit log to session state
   ▼
Answer in plain language, using only tool data
```

| Part | File | What it shows |
|---|---|---|
| Agent | `medication_agent/agent.py` | `LlmAgent` with instruction, tools and callbacks |
| Tools | `medication_agent/tools.py` | 3 function tools with input validation and structured errors |
| Data source | `medication_agent/data_source.py`, `data/seed.sql` | SQLite, built from a seed script on first run |
| Guardrail + audit | `medication_agent/guardrails.py` | `before_model_callback` blocks clinical advice; `after_tool_callback` logs every tool call |
| Tests | `tests/` | Unit tests plus a full ADK loop test with a scripted model (no API key) |
| Evaluation | `evals/` | Guardrail recall / false-block rate offline; tool choice and answer facts with a live model |

## Run it

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # then paste your Gemini API key into .env
adk web                          # opens a chat UI in the browser, pick medication_agent
# or: adk run medication_agent   # chat in the terminal
```

Get a free Gemini API key at https://aistudio.google.com/apikey.

Try: *"How is P001 doing with their medication?"*, *"Which doses did P001 miss?"*, *"Should I double my metformin dose?"* (blocked).

## Tests and evaluation

```bash
python -m pytest -q              # 16 tests, no API key needed
python -m evals.run_eval         # guardrail scores, no API key needed
python -m evals.run_eval --live  # also scores the real agent (needs API key)
```

Current offline results on the 15 hand-written cases:

- Clinical questions blocked: 7/7
- Data questions wrongly blocked: 0/8

The case set is small and written by me, and the guardrail is a keyword baseline, so these numbers are a starting point rather than proof of safety. A next step would be a larger, independently written test set and an LLM-based classifier compared against this baseline.

## What I learned

- ADK callbacks are a clean place for safety logic: returning a response from `before_model_callback` skips the model entirely, so a blocked question costs nothing and cannot leak.
- Returning `{"status": "error", ...}` from tools instead of raising keeps the agent loop stable and lets the model explain the problem to the user.
- A scripted `BaseLlm` subclass makes the whole agent loop testable in CI without network calls.

## Ideas for next steps

- Swap the keyword guardrail for a small classifier and compare both on the eval set
- Add a second agent for care-team summaries and route between them
- Move the data source to PostgreSQL
