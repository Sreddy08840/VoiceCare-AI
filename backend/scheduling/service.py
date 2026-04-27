from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from backend.memory.store import MemoryStore


@dataclass
class SlotResult:
    ok: bool
    message: str
    alternatives: list[str]


class SchedulingService:
    def __init__(self, memory: MemoryStore):
        self.memory = memory
        self.doctors = {
            "dr_rao": {"name": "Dr. Rao", "specialty": "Cardiology"},
            "dr_meena": {"name": "Dr. Meena", "specialty": "General Medicine"},
            "dr_singh": {"name": "Dr. Singh", "specialty": "Dermatology"},
        }

    def _parse(self, starts_at: str) -> datetime:
        return datetime.fromisoformat(starts_at)

    def _doctor_booked(self, doctor_id: str, starts_at: str) -> bool:
        rows = self.memory.conn.execute(
            "SELECT id FROM appointments WHERE doctor_id=? AND starts_at=? AND status='booked'",
            (doctor_id, starts_at),
        ).fetchall()
        return bool(rows)

    def check_slot(self, doctor_id: str, starts_at: str) -> SlotResult:
        if doctor_id not in self.doctors:
            return SlotResult(False, "Doctor unavailable", [])
        target = self._parse(starts_at)
        if target < datetime.utcnow():
            return SlotResult(False, "Cannot book past time", self.alternative_slots(doctor_id, datetime.utcnow()))
        if self._doctor_booked(doctor_id, starts_at):
            return SlotResult(False, "Selected slot is already booked", self.alternative_slots(doctor_id, target))
        return SlotResult(True, "Slot available", [])

    def alternative_slots(self, doctor_id: str, around: datetime) -> list[str]:
        choices: list[str] = []
        hour = around.replace(minute=0, second=0, microsecond=0)
        for i in range(1, 8):
            candidate = hour + timedelta(hours=i)
            if candidate.hour < 9 or candidate.hour > 17:
                continue
            iso = candidate.isoformat()
            if not self._doctor_booked(doctor_id, iso):
                choices.append(iso)
            if len(choices) == 3:
                break
        return choices

    def book(self, patient_id: str, doctor_id: str, starts_at: str, reason: str) -> dict:
        check = self.check_slot(doctor_id, starts_at)
        if not check.ok:
            return {"ok": False, "message": check.message, "alternatives": check.alternatives}

        for appt in self.memory.get_active_appointments(patient_id):
            if appt["starts_at"] == starts_at:
                return {"ok": False, "message": "You already have another appointment at that time", "alternatives": check.alternatives}

        appointment_id = self.memory.add_appointment(patient_id, doctor_id, starts_at, reason)
        return {"ok": True, "appointment_id": appointment_id, "doctor": self.doctors[doctor_id]["name"], "starts_at": starts_at}

    def cancel(self, patient_id: str, appointment_id: int) -> dict:
        appt = self.memory.get_appointment(appointment_id)
        if not appt or appt["patient_id"] != patient_id or appt["status"] != "booked":
            return {"ok": False, "message": "Appointment not found"}
        self.memory.update_appointment_status(appointment_id, "cancelled")
        return {"ok": True, "message": "Appointment cancelled", "appointment_id": appointment_id}

    def reschedule(self, patient_id: str, appointment_id: int, new_time: str) -> dict:
        appt = self.memory.get_appointment(appointment_id)
        if not appt or appt["patient_id"] != patient_id or appt["status"] != "booked":
            return {"ok": False, "message": "Appointment not found"}
        check = self.check_slot(appt["doctor_id"], new_time)
        if not check.ok:
            return {"ok": False, "message": check.message, "alternatives": check.alternatives}

        self.memory.update_appointment_status(appointment_id, "rescheduled")
        new_id = self.memory.add_appointment(patient_id, appt["doctor_id"], new_time, appt["reason"], "booked")
        return {"ok": True, "message": "Appointment rescheduled", "new_appointment_id": new_id, "starts_at": new_time}
