from __future__ import annotations

from datetime import datetime, timedelta

from backend.agents.orchestrator import AgentOrchestrator
from backend.memory.store import MemoryStore


class OutboundCampaignService:
    def __init__(self, memory: MemoryStore, orchestrator: AgentOrchestrator):
        self.memory = memory
        self.orchestrator = orchestrator

    def run_reminder(self, patient_id: str, session_id: str, simulated_response: str | None = None) -> dict:
        patient = self.memory.get_patient(patient_id)
        lang = patient["language_preference"] or "en"
        appointments = self.memory.get_active_appointments(patient_id)
        if not appointments:
            tomorrow = (datetime.utcnow() + timedelta(days=1)).replace(minute=0, second=0, microsecond=0).isoformat()
            self.memory.add_appointment(patient_id, "dr_meena", tomorrow, "checkup")
            appointments = self.memory.get_active_appointments(patient_id)

        prompt = {
            "en": f"Reminder: appointment #{appointments[0]['id']} at {appointments[0]['starts_at']}. Reply confirm, reschedule, or cancel.",
            "hi": f"रिमाइंडर: अपॉइंटमेंट #{appointments[0]['id']} {appointments[0]['starts_at']} पर है। confirm, reschedule या cancel कहें।",
            "ta": f"நினைவூட்டல்: appointment #{appointments[0]['id']} {appointments[0]['starts_at']}க்கு. confirm/reschedule/cancel சொல்லுங்கள்.",
        }[lang]

        response = None
        if simulated_response:
            response = self.orchestrator.handle_turn(session_id, patient_id, simulated_response, lang)

        return {"initial_prompt": prompt, "language": lang, "response": response}
