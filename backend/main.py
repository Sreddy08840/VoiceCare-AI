from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import json
import asyncio

from agents.booking import BookingAgent
from agents.memory import MemoryAgent
from agents.speech import SpeechAgent
from agents.notification import NotificationAgent

app = FastAPI(title="ClinicVoice AI - Python Orchestrator")

booking_agent = BookingAgent()
memory_agent = MemoryAgent()
speech_agent = SpeechAgent()
notification_agent = NotificationAgent()

from agents.chat_engine import ChatEngine

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("API Gateway WebSocket Connected.")
    
    patient_phone = "+1234567890" # Hardcoded for demo
    
    # Initialize the LLM Chat Engine
    chat_engine = ChatEngine(booking_agent, memory_agent, patient_phone)
    
    try:
        # Recall memory to inject context and construct a welcome message
        memories = await chat_engine.inject_memory_context()
        if memories:
            welcome_text = "Welcome back. " + " ".join(memories[:1]) + " How can I help you today?"
        else:
            welcome_text = "Welcome to ClinicVoice AI. How can I help you book an appointment today?"
            
        await websocket.send_text(json.dumps({
            "type": "text",
            "text": welcome_text
        }))
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "user_text":
                text = message.get("text", "")
            else:
                continue
                
            print(f"[WebSocket] Received user text: {text}")
            
            # Send to Groq LLM
            response_text = await chat_engine.process_user_input(text)
            
            # Detect language for TTS UI tagging
            lang = speech_agent.detect_language(response_text)
            
            # If the response indicates success, send notification (LLM naturally says "booked")
            if "booked" in response_text.lower() and "successfully" in response_text.lower():
                await notification_agent.send_sms_reminder(patient_phone, "Your appointment is confirmed!")
            
            # Send back TTS/text
            await websocket.send_text(json.dumps({
                "type": "agent_text",
                "text": response_text,
                "language": lang
            }))
            
    except WebSocketDisconnect:
        print("API Gateway WebSocket Disconnected.")
    except Exception as e:
        print(f"Error in WebSocket: {e}")


@app.get("/")
def read_root():
    return {"status": "Python Orchestrator is running"}
