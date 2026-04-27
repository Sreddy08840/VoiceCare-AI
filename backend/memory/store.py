from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

DB_PATH = Path("data/voicecare.db")


class MemoryStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS patients(
                id TEXT PRIMARY KEY,
                name TEXT,
                language_preference TEXT DEFAULT 'en',
                notes TEXT DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS appointments(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT,
                doctor_id TEXT,
                starts_at TEXT,
                status TEXT,
                reason TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS session_memory(
                session_id TEXT PRIMARY KEY,
                payload TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS turn_logs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                patient_id TEXT,
                speaker TEXT,
                text TEXT,
                language TEXT,
                created_at TEXT
            );
            """
        )
        self.conn.commit()

    def upsert_patient(self, patient_id: str, name: str | None = None, language: str | None = None) -> None:
        cur = self.conn.execute("SELECT id, name, language_preference FROM patients WHERE id=?", (patient_id,))
        row = cur.fetchone()
        if row:
            self.conn.execute(
                "UPDATE patients SET name=?, language_preference=? WHERE id=?",
                (name or row["name"], language or row["language_preference"], patient_id),
            )
        else:
            self.conn.execute(
                "INSERT INTO patients(id, name, language_preference) VALUES (?, ?, ?)",
                (patient_id, name or patient_id, language or "en"),
            )
        self.conn.commit()

    def get_patient(self, patient_id: str) -> dict[str, Any]:
        row = self.conn.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
        if not row:
            self.upsert_patient(patient_id)
            row = self.conn.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
        return dict(row)

    def set_language_preference(self, patient_id: str, language: str) -> None:
        self.upsert_patient(patient_id, language=language)

    def append_turn(self, session_id: str, patient_id: str, speaker: str, text: str, language: str) -> None:
        self.conn.execute(
            "INSERT INTO turn_logs(session_id, patient_id, speaker, text, language, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, patient_id, speaker, text, language, datetime.utcnow().isoformat()),
        )
        self.conn.commit()

    def recent_turns(self, session_id: str, limit: int = 8) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT speaker, text, language, created_at FROM turn_logs WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def get_session(self, session_id: str) -> dict[str, Any]:
        row = self.conn.execute("SELECT payload FROM session_memory WHERE session_id=?", (session_id,)).fetchone()
        if not row:
            return {"pending_action": None, "context": {}}
        return json.loads(row["payload"])

    def set_session(self, session_id: str, payload: dict[str, Any]) -> None:
        blob = json.dumps(payload)
        self.conn.execute(
            "INSERT INTO session_memory(session_id, payload, updated_at) VALUES (?, ?, ?)"
            " ON CONFLICT(session_id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at",
            (session_id, blob, datetime.utcnow().isoformat()),
        )
        self.conn.commit()

    def add_appointment(self, patient_id: str, doctor_id: str, starts_at: str, reason: str, status: str = "booked") -> int:
        cur = self.conn.execute(
            "INSERT INTO appointments(patient_id, doctor_id, starts_at, status, reason, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (patient_id, doctor_id, starts_at, status, reason, datetime.utcnow().isoformat()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_appointment_status(self, appointment_id: int, status: str) -> None:
        self.conn.execute("UPDATE appointments SET status=? WHERE id=?", (status, appointment_id))
        self.conn.commit()

    def get_active_appointments(self, patient_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM appointments WHERE patient_id=? AND status='booked' ORDER BY starts_at",
            (patient_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_appointment(self, appointment_id: int) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM appointments WHERE id=?", (appointment_id,)).fetchone()
        return dict(row) if row else None
