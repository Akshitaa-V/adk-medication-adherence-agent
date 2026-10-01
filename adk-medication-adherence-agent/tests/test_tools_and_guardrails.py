import pytest

from medication_agent.guardrails import needs_clinician
from medication_agent.tools import get_adherence_summary, get_medication_schedule, list_missed_doses


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MED_DB_PATH", str(tmp_path / "test.db"))


def test_schedule_lists_all_medications():
    result = get_medication_schedule("P001")
    assert result["status"] == "success"
    assert [m["name"] for m in result["medications"]] == ["Atorvastatin", "Metformin"]
    assert result["medications"][1]["times"] == ["08:00", "20:00"]


def test_adherence_numbers_match_seed_data():
    result = get_adherence_summary("P001")
    assert result["scheduled_doses"] == 21
    assert result["taken_doses"] == 17
    assert result["adherence_percent"] == 81.0
    assert get_adherence_summary("P002")["adherence_percent"] == 100.0


def test_missed_doses_are_sorted_oldest_first():
    missed = list_missed_doses("P001")["missed"]
    assert len(missed) == 4
    assert missed[0] == {"medication": "Metformin", "scheduled_at": "2026-09-25 20:00"}


@pytest.mark.parametrize("bad_id", ["", "123", "P1", "P999"])
def test_bad_patient_ids_return_errors_not_exceptions(bad_id):
    assert get_adherence_summary(bad_id)["status"] == "error"


@pytest.mark.parametrize("question", [
    "Should I double my metformin dose tomorrow?",
    "Can I stop taking atorvastatin?",
    "What dosage should I take?",
    "Do I have diabetes?",
])
def test_guardrail_blocks_clinical_questions(question):
    assert needs_clinician(question)


@pytest.mark.parametrize("question", [
    "What is my medication schedule? I'm P001",
    "How many doses did P002 miss this week?",
    "When do I take my metformin dose?",
])
def test_guardrail_allows_data_questions(question):
    assert not needs_clinician(question)
