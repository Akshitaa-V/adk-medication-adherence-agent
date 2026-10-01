"""Tools the agent can call. Each one reads from the SQLite data source and
returns a plain dict with a "status" key, so the model always gets a clear
success or error instead of an exception."""

import re

from .data_source import get_connection

PATIENT_ID_PATTERN = re.compile(r"^P\d{3}$")


def _check_patient(conn, patient_id: str) -> dict | None:
    if not PATIENT_ID_PATTERN.match(patient_id or ""):
        return {"status": "error", "message": f"'{patient_id}' is not a valid patient ID (expected e.g. P001)."}
    row = conn.execute("SELECT 1 FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
    if row is None:
        return {"status": "error", "message": f"No patient with ID {patient_id}."}
    return None


def get_medication_schedule(patient_id: str) -> dict:
    """Returns the medications, doses and daily times for one patient.

    Args:
        patient_id: The patient's ID, for example "P001".
    """
    with get_connection() as conn:
        error = _check_patient(conn, patient_id)
        if error:
            return error
        rows = conn.execute(
            "SELECT name, dose, times FROM medications WHERE patient_id = ? ORDER BY name",
            (patient_id,),
        ).fetchall()
    return {
        "status": "success",
        "patient_id": patient_id,
        "medications": [
            {"name": r["name"], "dose": r["dose"], "times": r["times"].split(",")} for r in rows
        ],
    }


def get_adherence_summary(patient_id: str) -> dict:
    """Returns how many scheduled doses were taken or missed, overall and per medication.

    Args:
        patient_id: The patient's ID, for example "P001".
    """
    with get_connection() as conn:
        error = _check_patient(conn, patient_id)
        if error:
            return error
        rows = conn.execute(
            """
            SELECT m.name, COUNT(*) AS scheduled, SUM(l.taken) AS taken
            FROM intake_log l JOIN medications m ON m.med_id = l.med_id
            WHERE m.patient_id = ?
            GROUP BY m.name ORDER BY m.name
            """,
            (patient_id,),
        ).fetchall()

    per_med = []
    total_scheduled = total_taken = 0
    for r in rows:
        total_scheduled += r["scheduled"]
        total_taken += r["taken"]
        per_med.append({
            "name": r["name"],
            "scheduled": r["scheduled"],
            "taken": r["taken"],
            "adherence_percent": round(100 * r["taken"] / r["scheduled"], 1),
        })
    overall = round(100 * total_taken / total_scheduled, 1) if total_scheduled else None
    return {
        "status": "success",
        "patient_id": patient_id,
        "scheduled_doses": total_scheduled,
        "taken_doses": total_taken,
        "adherence_percent": overall,
        "per_medication": per_med,
    }


def list_missed_doses(patient_id: str) -> dict:
    """Lists every scheduled dose the patient did not take, oldest first.

    Args:
        patient_id: The patient's ID, for example "P001".
    """
    with get_connection() as conn:
        error = _check_patient(conn, patient_id)
        if error:
            return error
        rows = conn.execute(
            """
            SELECT m.name, l.scheduled_at
            FROM intake_log l JOIN medications m ON m.med_id = l.med_id
            WHERE m.patient_id = ? AND l.taken = 0
            ORDER BY l.scheduled_at
            """,
            (patient_id,),
        ).fetchall()
    return {
        "status": "success",
        "patient_id": patient_id,
        "missed": [{"medication": r["name"], "scheduled_at": r["scheduled_at"]} for r in rows],
    }
