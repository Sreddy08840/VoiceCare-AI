import requests
import json

# URL of your local FastAPI backend
URL = "http://127.0.0.1:8000/api/tools"

def send_mock_tool_call(function_name, arguments):
    payload = {
        "message": {
            "type": "toolCalls",
            "toolCalls": [
                {
                    "id": "call_12345",
                    "type": "function",
                    "function": {
                        "name": function_name,
                        "arguments": arguments
                    }
                }
            ]
        }
    }
    
    print(f"\n--- Testing {function_name} ---")
    try:
        response = requests.post(URL, json=payload)
        print("Status Code:", response.status_code)
        print("Response:", json.dumps(response.json(), indent=2))
    except Exception as e:
        print("Error connecting to the backend:", e)

if __name__ == "__main__":
    print("Testing ClinicVoice AI Tool Endpoints...")
    
    # Test checking availability
    send_mock_tool_call(
        "check_availability", 
        {"date": "2026-03-15", "doctor": "Dr. Rao"}
    )
    
    # Test booking an appointment
    send_mock_tool_call(
        "book_appointment", 
        {"patient_name": "Asha Patel", "date": "2026-03-15", "time": "10:00", "doctor": "Dr. Rao"}
    )
    
    # Test checking availability again (should now be missing 10:00)
    send_mock_tool_call(
        "check_availability", 
        {"date": "2026-03-15", "doctor": "Dr. Rao"}
    )
    
    # Test storing memory
    send_mock_tool_call(
        "store_memory", 
        {"phone_number": "+1234567890", "key": "preferred_time", "value": "Afternoons"}
    )
    
    # Test recalling memory
    send_mock_tool_call(
        "recall_memory", 
        {"phone_number": "+1234567890"}
    )
