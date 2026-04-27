# VoiceCare AI — Real-Time Multilingual Voice Agent Prototype

Production-shaped prototype for clinical appointment booking with real-time style voice flow, multilingual handling (English/Hindi/Tamil), explicit tool orchestration, persistent memory, outbound reminder workflows, and latency observability.

## Features

- **Voice turn pipeline**: `audio -> ASR -> language detect -> agent reasoning -> tools -> TTS`.
- **Tool calling + orchestration**: scheduler tools are called by the agent with visible reasoning trace per turn.
- **Multilingual**: English (`en`), Hindi (`hi`), Tamil (`ta`) detection + persisted preference.
- **Memory layers**:
  - Short-term session memory (active pending action, turn context).
  - Long-term memory (patients, appointments, language preferences, turn logs).
- **Scheduling logic**: deterministic constraints for past slots, double booking, unavailable doctor, alternatives.
- **Outbound campaign mode**: reminder flow that can confirm/reschedule/cancel.
- **Observability**: JSON structured logs + latency profiler breakdown including first-response budget.
- **FastAPI endpoints**: HTTP + WebSocket for near real-time interaction.
- **TypeScript demo client**: websocket conversational demo.

## Repository structure

- `backend/app` — FastAPI app, schemas, seeding
- `backend/agents` — orchestration + intent handling + tool routing
- `backend/services` — ASR, language detection, TTS
- `backend/memory` — SQLite persistence and retrieval logic
- `backend/scheduling` — deterministic appointment service + conflict resolution
- `backend/campaigns` — outbound reminder/follow-up flow
- `backend/utils` — structured logging + latency profiler
- `demo` — TypeScript websocket demo client
- `tests` — unit/integration-like tests for scheduling + agent flow
- `data` — sample patients and SQLite DB file
- `docs` — architecture diagram source + exported SVG

## Quickstart

### 1) Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Seed sample data

```bash
python -m backend.app.seed
```

### 3) Run API

```bash
uvicorn backend.app.main:app --reload
```

### 4) Demo via HTTP

```bash
curl -s http://127.0.0.1:8000/health

curl -s -X POST http://127.0.0.1:8000/voice/turn \
  -H 'content-type: application/json' \
  -d '{
    "session_id":"s1",
    "patient_id":"p003",
    "audio_text":"Book appointment with Dr Meena at 2026-04-28T10:00:00"
  }' | jq

curl -s -X POST http://127.0.0.1:8000/voice/turn \
  -H 'content-type: application/json' \
  -d '{
    "session_id":"s1",
    "patient_id":"p003",
    "audio_text":"yes"
  }' | jq
```

### 5) Demo via WebSocket TypeScript client

```bash
cd demo
npm install
npm run dev
```

### 6) Outbound campaign demo

```bash
curl -s -X POST http://127.0.0.1:8000/campaign/outbound \
  -H 'content-type: application/json' \
  -d '{
    "patient_id":"p001",
    "session_id":"out-1",
    "simulated_response":"reschedule 1 to 2026-04-29T11:00:00"
  }' | jq
```

## Architecture

- Mermaid source: `docs/architecture.mmd`
- Exported diagram: `docs/architecture.svg` (text-based, VCS-friendly)

## Memory design

### Short-term (session)
- Table: `session_memory`
- Stores pending actions (e.g., `book_confirm`) and contextual state needed for next turn.

### Long-term (cross-session)
- `patients`: profile + language preference
- `appointments`: booking history/state transitions
- `turn_logs`: conversation audit trail

### Retrieval logic
- Agent loads session context each turn.
- Language preference is updated and reused across sessions.
- Appointment lookup powers cancellation/rescheduling and reminder flows.

## Latency budget and breakdown

Each turn returns `latency_ms` stage metrics:
- `transcription_ms`
- `language_detection_ms`
- `memory_write_user_ms`
- `agent_reasoning_ms`
- `memory_write_agent_ms`
- `tts_ms`
- `first_response_ms`

Target is **<450 ms** from speech-end to first audio response. This prototype uses low-latency local components and deterministic tool logic to stay under budget in local runs.

## Tradeoffs

- ASR/TTS are mock implementations for local-first reproducibility.
- Intent recognition is rule-based instead of remote LLM to keep deterministic behavior and latency.
- Barge-in is represented by payload field (`interrupt`) but full duplex streaming VAD is not implemented.

## Known limitations

- No real audio codec handling yet (text-as-audio surrogate in `audio_b64`).
- ISO datetime parsing expected for precision scheduling.
- No auth, PII controls, or HIPAA deployment controls in this prototype.

## How to extend

- Replace ASR/TTS adapters with production providers.
- Add explicit function-calling LLM planner while keeping same tool interfaces.
- Move memory to PostgreSQL/Redis for distributed scaling.
- Add streaming partial response + true barge-in cancellation.

## Testing

```bash
pytest -q
```
