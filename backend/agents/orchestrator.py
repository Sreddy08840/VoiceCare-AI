from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from backend.memory.store import MemoryStore
from backend.scheduling.service import SchedulingService
from backend.utils.logging import get_logger, log_event

logger = get_logger("agent")

LANG_TEXT = {
    "en": {
        "confirm_book": "I can book with {doctor} at {time}. Please confirm yes or no.",
        "ask_time": "Please tell me a preferred date and time in ISO format, for example 2026-04-28T10:00:00.",
        "booked": "Booked. Appointment #{id} with {doctor} at {time}.",
        "cancel_confirm": "Please share appointment id to cancel.",
        "cancelled": "Cancelled appointment #{id}.",
        "rescheduled": "Rescheduled to {time}. New appointment #{id}.",
        "fallback": "Sorry, I need a bit more detail. Do you want to book, reschedule, or cancel?",
    },
    "hi": {
        "confirm_book": "मैं {doctor} के साथ {time} पर बुक कर सकता हूँ। कृपया हाँ या ना कहें।",
        "ask_time": "कृपया ISO समय बताएं, जैसे 2026-04-28T10:00:00।",
        "booked": "बुक हो गया। अपॉइंटमेंट #{id} {doctor} के साथ {time} पर।",
        "cancel_confirm": "कैंसल करने के लिए अपॉइंटमेंट आईडी बताएं।",
        "cancelled": "अपॉइंटमेंट #{id} कैंसल कर दिया गया।",
        "rescheduled": "रीशेड्यूल हो गया {time} पर। नया अपॉइंटमेंट #{id}।",
        "fallback": "मुझे थोड़ी और जानकारी चाहिए। बुक, रीशेड्यूल या कैंसल?",
    },
    "ta": {
        "confirm_book": "{doctor} உடன் {time}க்கு பதிவு செய்யலாம். தயவு செய்து உறுதி செய்யவும்.",
        "ask_time": "ISO நேரத்தை சொல்லுங்கள், உதா: 2026-04-28T10:00:00.",
        "booked": "பதிவு முடிந்தது. #{id} {doctor} {time}.",
        "cancel_confirm": "ரத்து செய்ய appointment id கூறுங்கள்.",
        "cancelled": "#{id} appointment ரத்து செய்யப்பட்டது.",
        "rescheduled": "{time}க்கு மாற்றப்பட்டது. புதிய #{id} appointment.",
        "fallback": "மேலும் தகவல் வேண்டும். பதிவு, மாற்றம், ரத்து?",
    },
}


class AgentOrchestrator:
    def __init__(self, memory: MemoryStore, scheduler: SchedulingService):
        self.memory = memory
        self.scheduler = scheduler

    def _extract_iso(self, text: str) -> str | None:
        m = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", text)
        return m.group(0) if m else None

    def _extract_doctor(self, text: str) -> str:
        low = text.lower()
        if "rao" in low:
            return "dr_rao"
        if "meena" in low:
            return "dr_meena"
        if "singh" in low:
            return "dr_singh"
        return "dr_meena"

    def _intent(self, text: str) -> str:
        low = text.lower()
        if any(k in low for k in ["reschedule", "move", "change", "रीशेड्यूल", "மாற்ற"]):
            return "reschedule"
        if any(k in low for k in ["cancel", "drop", "रद्द", "ரத்து"]):
            return "cancel"
        if any(k in low for k in ["book", "appointment", "schedule", "बुक", "பதிவு"]):
            return "book"
        if any(k in low for k in ["yes", "confirm", "हाँ", "ஆமா"]):
            return "confirm"
        return "unknown"

    def handle_turn(self, session_id: str, patient_id: str, text: str, language: str) -> dict[str, Any]:
        traces: list[str] = []
        session = self.memory.get_session(session_id)
        self.memory.set_language_preference(patient_id, language)

        intent = self._intent(text)
        traces.append(f"intent={intent}")
        log_event(logger, "intent_detected", intent=intent, session_id=session_id)

        if session.get("pending_action") == "book_confirm" and intent == "confirm":
            data = session["context"]
            res = self.scheduler.book(patient_id, data["doctor_id"], data["starts_at"], data.get("reason", "general"))
            traces.append(f"tool=book result={res}")
            if res["ok"]:
                reply = LANG_TEXT[language]["booked"].format(id=res["appointment_id"], doctor=res["doctor"], time=res["starts_at"])
                session = {"pending_action": None, "context": {}}
            else:
                alt = ", ".join(res.get("alternatives", [])) or "none"
                reply = f"{res['message']}. Alternatives: {alt}."

            self.memory.set_session(session_id, session)
            return {"text": reply, "trace": traces}

        if intent == "book":
            starts_at = self._extract_iso(text)
            if not starts_at:
                if "tomorrow" in text.lower():
                    starts_at = (datetime.utcnow() + timedelta(days=1)).replace(minute=0, second=0, microsecond=0).isoformat()
                else:
                    return {"text": LANG_TEXT[language]["ask_time"], "trace": traces}

            doctor_id = self._extract_doctor(text)
            check = self.scheduler.check_slot(doctor_id, starts_at)
            traces.append(f"tool=check_slot result={check}")
            if not check.ok:
                alt = ", ".join(check.alternatives) if check.alternatives else "none"
                return {"text": f"{check.message}. Alternatives: {alt}", "trace": traces}

            session = {
                "pending_action": "book_confirm",
                "context": {"doctor_id": doctor_id, "starts_at": starts_at, "reason": "consultation"},
            }
            self.memory.set_session(session_id, session)
            doc_name = self.scheduler.doctors[doctor_id]["name"]
            return {
                "text": LANG_TEXT[language]["confirm_book"].format(doctor=doc_name, time=starts_at),
                "trace": traces,
            }

        if intent == "cancel":
            appointment_id = re.search(r"\d+", text)
            if not appointment_id:
                return {"text": LANG_TEXT[language]["cancel_confirm"], "trace": traces}
            res = self.scheduler.cancel(patient_id, int(appointment_id.group(0)))
            traces.append(f"tool=cancel result={res}")
            if res["ok"]:
                return {"text": LANG_TEXT[language]["cancelled"].format(id=res["appointment_id"]), "trace": traces}
            return {"text": res["message"], "trace": traces}

        if intent == "reschedule":
            appointment_id = re.search(r"\d+", text)
            new_time = self._extract_iso(text)
            if not appointment_id or not new_time:
                return {"text": "Need appointment id and new ISO time.", "trace": traces}
            res = self.scheduler.reschedule(patient_id, int(appointment_id.group(0)), new_time)
            traces.append(f"tool=reschedule result={res}")
            if res["ok"]:
                return {
                    "text": LANG_TEXT[language]["rescheduled"].format(time=res["starts_at"], id=res["new_appointment_id"]),
                    "trace": traces,
                }
            alt = ", ".join(res.get("alternatives", []))
            return {"text": f"{res['message']}. Alternatives: {alt}", "trace": traces}

        return {"text": LANG_TEXT[language]["fallback"], "trace": traces}
