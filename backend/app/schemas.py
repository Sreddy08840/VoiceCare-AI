from __future__ import annotations

from pydantic import BaseModel


class VoiceTurnRequest(BaseModel):
    session_id: str
    patient_id: str
    audio_text: str
    language_hint: str | None = None
    interrupt: bool = False


class VoiceTurnResponse(BaseModel):
    text: str
    language: str
    audio_b64: str
    trace: list[str]
    latency_ms: dict[str, float]


class OutboundRequest(BaseModel):
    patient_id: str
    campaign_type: str = "reminder"
    session_id: str = "outbound-session"
    simulated_response: str | None = None
