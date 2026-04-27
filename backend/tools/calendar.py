from typing import Dict, Any, List

# In-memory mock schedule
# Format: { "date": { "doctor_name": ["time1", "time2"] } }
MOCK_SCHEDULE = {
    "2026-03-15": {
        "Dr. Rao": ["10:00", "11:00", "15:00"],
        "Dr. Meena": ["09:00", "14:00"]
    },
    "2026-03-16": {
        "Dr. Rao": ["10:00", "12:00", "16:00"],
        "Dr. Patel": ["10:00", "11:00"]
    }
}

# In-memory database of booked appointments
BOOKINGS = []

def check_availability(date: str, doctor: str) -> Dict[str, Any]:
    """Check if a doctor is available on a specific date."""
    print(f"Checking availability for {doctor} on {date}")
    
    date_schedule = MOCK_SCHEDULE.get(date, {})
    available_times = date_schedule.get(doctor, [])
    
    if available_times:
        return {
            "status": "available",
            "available_times": available_times,
            "message": f"{doctor} is available at {', '.join(available_times)}."
        }
    else:
        return {
            "status": "unavailable",
            "available_times": [],
            "message": f"{doctor} is not available on {date}."
        }

def book_appointment(patient_name: str, date: str, time: str, doctor: str) -> Dict[str, Any]:
    """Book an appointment and remove the slot from availability."""
    print(f"Booking appointment for {patient_name} with {doctor} on {date} at {time}")
    
    date_schedule = MOCK_SCHEDULE.get(date)
    if not date_schedule or doctor not in date_schedule:
        return {"status": "error", "message": f"{doctor} has no schedule on {date}."}
        
    if time not in date_schedule[doctor]:
        return {"status": "error", "message": f"The slot {time} is not available for {doctor} on {date}."}
        
    # Remove slot
    date_schedule[doctor].remove(time)
    
    # Save booking
    booking = {
        "id": f"A-{len(BOOKINGS)+100}",
        "patient_name": patient_name,
        "date": date,
        "time": time,
        "doctor": doctor,
        "status": "confirmed"
    }
    BOOKINGS.append(booking)
    
    return {
        "status": "success",
        "booking_id": booking["id"],
        "message": "Appointment successfully booked."
    }
