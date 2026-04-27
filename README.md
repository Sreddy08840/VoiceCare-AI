# 🏥 ClinicVoice AI

> A production-grade, real-time **multilingual voice AI agent** for booking, rescheduling, and cancelling clinical appointments — no human intervention needed.

![Languages](https://img.shields.io/badge/Languages-English%20%7C%20Hindi%20%7C%20Tamil-blue)
![Stack](https://img.shields.io/badge/Stack-React%20%7C%20Node.js%20%7C%20Python%20%7C%20Groq-green)
![DB](https://img.shields.io/badge/DB-PostgreSQL%20%7C%20Qdrant%20Cloud-orange)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Setup & Configuration](#-setup--configuration)
- [Running the Project](#-running-the-project)
- [Testing the Agent](#-testing-the-agent)
- [Skills & Agent Behavior](#-skills--agent-behavior)

---

## ✨ Features

- 🎙️ **Real-time voice interaction** via WebSocket streaming
- 🌐 **Multilingual**: English, हिंदी (Hindi), தமிழ் (Tamil) — auto-detected
- 🧠 **Context-aware memory** — recalls past appointments and preferences (Qdrant Cloud)
- 📅 **Appointment scheduling** — book, reschedule, cancel with conflict resolution
- 📲 **Outbound notifications** — SMS/call reminders (Twilio stub, ready to activate)
- 🤖 **Groq LLM** (Llama 3 70B) powering the agent with function calling
- 💊 **Scope enforcement** — politely declines non-medical requests

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                 React Frontend                   │
│  (Voice Button · Live Transcription · Dashboard) │
└───────────────────┬─────────────────────────────┘
                    │ WebSocket (ws://localhost:3001)
┌───────────────────▼─────────────────────────────┐
│           Node.js API Gateway (port 3001)        │
│   REST /api/appointments  ·  WS Proxy            │
└───────────────────┬─────────────────────────────┘
                    │ WebSocket (ws://localhost:8000)
┌─────────────────────────────────────────────────┐
│        Python AI Orchestrator (port 8000)        │
│                                                  │
│  ┌──────────────┐  ┌────────────┐  ┌──────────┐ │
│  │ Groq LLM     │  │ Booking    │  │ Memory   │ │
│  │ Chat Engine  │→ │ Agent      │  │ Agent    │ │
│  │ (Llama 3.3)  │  │ (Demo Mode)│  │ (Cloud)  │ │
│  └──────────────┘  └────────────┘  └──────────┘ │
└─────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
clinicVoice-AI/
│
├── AGENTS.md               # Agent role, language rules, conversation style
├── SKILL.md                # Booking, Memory, and Error Handling skills
├── start_servers.ps1       # One-click startup script (Windows)
│
├── backend/                # Python AI Orchestrator (FastAPI + WebSocket)
│   ├── .env                # API Keys (Groq, Qdrant)
│   ├── main.py             # WebSocket endpoint + agent wiring
│   ├── requirements.txt    # Python dependencies
│   ├── agents/
│   │   ├── chat_engine.py  # Groq LLM + function calling
│   │   ├── booking.py      # In-Memory appointment logic
│   │   ├── memory.py       # Qdrant Cloud memory store
│   └── tools/              # (Legacy mocks)
│
├── api-gateway/            # Node.js API Gateway (Express + WebSocket)
│   └── index.js            # REST routes + WS proxy to Python
│
└── frontend/               # React + Vite + Tailwind CSS UI
    └── src/
        ├── App.tsx          # Main UI: mic button, transcription, dashboard
```

---

## 🛠️ Prerequisites

Make sure you have these installed:

| Tool | Version | Check |
|------|---------|-------|
| **Python** | 3.10+ | `py --version` |
| **Node.js** | 18+ | `node --version` |
| **npm** | 8+ | `npm --version` |

---

## ⚙️ Setup & Configuration

### 1. Configure API Keys

Edit `backend/.env`:
```env
# Required — Groq LLM
GROQ_API_KEY=your_groq_api_key_here

# Required — Qdrant Cloud
QDRANT_URL=https://your-cluster.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here
```

### 2. Install Dependencies

**Python Backend:**
```powershell
cd backend
py -m pip install -r requirements.txt
```

**API Gateway:**
```powershell
cd api-gateway
npm install
```

**Frontend:**
```powershell
cd frontend
npm install
```

---

## 🚀 Running the Project

### One-Click Start (Windows)
From the project root, run:
```powershell
.\start_servers.ps1
```

This opens **3 terminal windows** automatically:
1. 🐍 Python AI Orchestrator
2. 🟢 Node.js API Gateway
3. ⚛️ React Frontend

### Manual Start (run each in a separate terminal)

**Terminal 1 — Python Backend:**
```powershell
cd backend
py -m uvicorn main:app --reload --port 8000
```

**Terminal 2 — Node.js API Gateway:**
```powershell
cd api-gateway
node index.js
```

**Terminal 3 — React Frontend:**
```powershell
cd frontend
npm run dev
```

---

## ✅ Verify All Services Are Running

| Service | URL | Expected Response |
|---------|-----|-------------------|
| Python AI | http://localhost:8000 | `{"status":"Python Orchestrator is running"}` |
| API Gateway | http://localhost:3001/api/appointments | `[]` (or list of appointments) |
| React UI | http://localhost:5173 | ClinicVoice AI web app |

---

## 🧪 Testing the Agent

1. Open **http://localhost:5173** in your browser
2. Click the **blue microphone button** to start a session
3. Wait for the **"Listening..."** status and 7 test buttons to appear
4. Click any test button to simulate a patient speaking:

| Button | Input Sent | Expected Behavior |
|--------|-----------|-------------------|
| 1. Book tomorrow | `"Book appointment tomorrow"` | Asks for missing details (doctor, time) |
| 2. Change to 5pm | `"Change my appointment to 5pm"` | Asks for confirmation before updating |
| 3. Evening slot | `"I want an evening slot"` | Suggests available evening times |
| 4. Hindi test | `"कल की अपॉइंटमेंट बुक कर दो"` | Responds entirely in Hindi |
| 5. Tamil test | `"நாளை ஒரு அப்பாயிண்ட்மெண்ட் வேண்டும்"` | Responds entirely in Tamil |
| 6. Conflict test | `"Book with Dr. Rao tomorrow at 8 AM"` | Detects conflict, suggests alternatives |
| 7. Random input | `"Can you order me a pizza?"` | Politely declines, redirects to appointments |

---

## 🧠 Skills & Agent Behavior

The agent's behavior is defined in two files you can edit freely:

### `AGENTS.md` — Core Rules
- Language detection and response rules
- Scope enforcement (medical appointments only)
- Slot filling requirements
- Conversation style (short, polite, natural)

### `SKILL.md` — Skill Workflows
- **Appointment Booking**: 8-step flow (intent → slots → validate → availability → confirm → book → notify)
- **Memory Manager**: recall at session start, store during conversation, summarize at end
- **Error Handling**: unclear input, missing info, conflicts, out-of-scope, change of mind

> Any changes to `AGENTS.md` or `SKILL.md` are automatically reflected in the LLM's system prompt on the next backend restart.

---

## 🔑 Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for Llama 3 70B LLM | ✅ Yes |
| `QDRANT_URL` | Qdrant Cloud cluster URL | ⚡ Recommended |
| `QDRANT_API_KEY` | Qdrant Cloud API key | ⚡ Recommended |
| `DATABASE_URL` | PostgreSQL connection string | ❌ Optional (uses mock if absent) |

---

## 🤝 Built With

- [Groq](https://groq.com) — Ultra-fast LLM inference (Llama 3 70B)
- [Qdrant](https://qdrant.tech) — Vector database for semantic memory
- [FastAPI](https://fastapi.tiangolo.com) — Python async web framework
- [React](https://react.dev) + [Vite](https://vitejs.dev) — Frontend
- [Tailwind CSS v4](https://tailwindcss.com) — Styling
- [PostgreSQL](https://postgresql.org) — Appointment database

---

## ✍️ Author

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/Sreddy08840">
        <img src="https://github.com/Sreddy08840.png" width="100px;" alt="Sreddy08840"/><br/>
        <sub><b>Sreddy08840</b></sub>
      </a><br/>
      <sub>🌱 Creator & Lead Developer</sub><br/>
      <sub>Full-Stack · Voice AI · ML Integration</sub>
    </td>
  </tr>
</table>

