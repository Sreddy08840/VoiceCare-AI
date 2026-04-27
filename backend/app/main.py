from __future__ import annotations

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from backend.agents.orchestrator import AgentOrchestrator
from backend.app.schemas import OutboundRequest, VoiceTurnRequest, VoiceTurnResponse
from backend.campaigns.service import OutboundCampaignService
from backend.memory.store import MemoryStore
from backend.scheduling.service import SchedulingService
from backend.services.asr import ASRService
from backend.services.language import LanguageService
from backend.services.tts import TTSService
from backend.utils.latency import LatencyProfiler
from backend.utils.logging import get_logger, log_event

app = FastAPI(title="VoiceCare AI", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

logger = get_logger("api")

memory = MemoryStore()
scheduler = SchedulingService(memory)
agent = AgentOrchestrator(memory, scheduler)
asr = ASRService()
lang = LanguageService()
tts = TTSService()
campaign_service = OutboundCampaignService(memory, agent)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/voice/turn", response_model=VoiceTurnResponse)
def voice_turn(payload: VoiceTurnRequest) -> VoiceTurnResponse:
    profiler = LatencyProfiler()
    log_event(logger, "audio_input", session_id=payload.session_id, patient_id=payload.patient_id)

    text = asr.transcribe(payload.audio_text)
    profiler.mark("transcription_ms")

    detected = lang.detect(text, payload.language_hint)
    profiler.mark("language_detection_ms")

    memory.append_turn(payload.session_id, payload.patient_id, "user", text, detected)
    profiler.mark("memory_write_user_ms")

    result = agent.handle_turn(payload.session_id, payload.patient_id, text, detected)
    profiler.mark("agent_reasoning_ms")

    memory.append_turn(payload.session_id, payload.patient_id, "assistant", result["text"], detected)
    profiler.mark("memory_write_agent_ms")

    audio_b64 = tts.synthesize(result["text"], detected)
    profiler.mark("tts_ms")

    lat = profiler.summary()
    log_event(logger, "first_response_latency", latency_ms=lat)

    return VoiceTurnResponse(
        text=result["text"],
        language=detected,
        audio_b64=audio_b64,
        trace=result["trace"],
        latency_ms=lat,
    )


@app.post("/campaign/outbound")
def outbound(req: OutboundRequest) -> dict:
    return campaign_service.run_reminder(req.patient_id, req.session_id, req.simulated_response)


@app.websocket("/ws/voice")
async def ws_voice(websocket: WebSocket) -> None:
    await websocket.accept()
    while True:
        msg = await websocket.receive_json()
        req = VoiceTurnRequest(**msg)
        res = voice_turn(req)
        await websocket.send_json(res.model_dump())
