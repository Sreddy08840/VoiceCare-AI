from typing import Dict, Any

# In-memory mock database for Episodic & Semantic Memory
# Format: { "phone_number": { "preferences": {}, "sessions": [] } }
PATIENT_DB = {
    "+1234567890": {
        "preferences": {
            "favorite_doctor": "Dr. Rao",
            "preferred_time": "morning",
            "language": "Hindi"
        },
        "sessions": [
            "User called to ask about cardiology appointment, prefers Dr. Rao."
        ]
    }
}

def recall_patient_memory(phone_number: str) -> Dict[str, Any]:
    """Fetch past facts and preferences for a patient."""
    print(f"Recalling memory for {phone_number}")
    
    patient_data = PATIENT_DB.get(phone_number)
    if not patient_data:
        return {"status": "not_found", "message": "No past memory found for this patient."}
        
    return {
        "status": "success",
        "preferences": patient_data.get("preferences", {}),
        "recent_session_summaries": patient_data.get("sessions", [])[-3:] # Last 3 sessions
    }

def store_patient_memory(phone_number: str, key: str, value: Any) -> Dict[str, Any]:
    """Store a specific preference or fact for a patient."""
    print(f"Storing memory for {phone_number}: {key} = {value}")
    
    if phone_number not in PATIENT_DB:
        PATIENT_DB[phone_number] = {"preferences": {}, "sessions": []}
        
    PATIENT_DB[phone_number]["preferences"][key] = value
    return {"status": "success", "message": f"Successfully stored {key}."}

def summarize_session(phone_number: str, summary: str) -> Dict[str, Any]:
    """Save a summary of the current session to episodic memory."""
    print(f"Summarizing session for {phone_number}")
    
    if phone_number not in PATIENT_DB:
        PATIENT_DB[phone_number] = {"preferences": {}, "sessions": []}
        
    PATIENT_DB[phone_number]["sessions"].append(summary)
    return {"status": "success", "message": "Session summarized and saved."}
