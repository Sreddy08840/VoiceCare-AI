import asyncpg
import os
import httpx
from typing import Dict, Any

class BookingAgent:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgres://clinic_user:clinic_password@127.0.0.1:5432/clinic_db")
        self.gateway_url = "http://127.0.0.1:3001/api/appointments"
        self._pool = None
        self._fallback_appointments = []
        self.db_available = False

    async def _get_pool(self):
        if self._pool: return self._pool
        try:
            self._pool = await asyncpg.create_pool(self.db_url, timeout=2)
            self.db_available = True
            return self._pool
        except Exception as e:
            print(f"⚠️  PostgreSQL not available ({e}). Using in-memory fallback.")
            self.db_available = False
            return None

    async def check_availability(self, doctor_name: str, date: str) -> Dict[str, Any]:
        pool = await self._get_pool()
        all_times = ["09:00:00", "10:00:00", "11:00:00", "14:00:00", "15:00:00"]
        
        if not self.db_available:
            booked = [a['time'] for a in self._fallback_appointments if a['doctor'] == doctor_name and a['date'] == date]
            return {"status": "success", "available_times": [t for t in all_times if t not in booked]}

        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT a.appointment_time FROM appointments a
                    JOIN doctors d ON a.doctor_id = d.id
                    WHERE d.name = $1 AND a.appointment_date = $2 AND a.status = 'booked'
                ''', doctor_name, date)
                booked = [str(row['appointment_time']) for row in rows]
                return {"status": "success", "available_times": [t for t in all_times if t not in booked]}
        except Exception:
            self.db_available = False
            return await self.check_availability(doctor_name, date)

    async def _sync_to_gateway(self, appointment_data: Dict[str, Any]):
        """Syncs demo bookings to the Node.js API Gateway dashboard."""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(self.gateway_url, json=appointment_data, timeout=2)
        except Exception as e:
            print(f"⚠️  Failed to sync to gateway: {e}")

    async def book_appointment(self, phone_number: str, doctor_name: str, date: str, time: str) -> Dict[str, Any]:
        pool = await self._get_pool()
        
        apt_data = {
            "patient_name": "Demo Patient", # In real app, look up by phone
            "doctor_name": doctor_name,
            "appointment_date": date,
            "appointment_time": time,
            "status": "booked"
        }

        if not self.db_available:
            self._fallback_appointments.append({"phone": phone_number, "doctor": doctor_name, "date": date, "time": time})
            await self._sync_to_gateway(apt_data)
            return {"status": "success", "message": f"Booked successfully (Demo Mode) with {doctor_name} on {date} at {time}."}

        try:
            async with pool.acquire() as conn:
                patient = await conn.fetchrow("SELECT id, name FROM patients WHERE phone_number = $1", phone_number)
                doctor = await conn.fetchrow("SELECT id FROM doctors WHERE name = $1", doctor_name)
                if not patient or not doctor: return {"status": "error", "message": "Record not found."}
                
                await conn.execute('INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, status) VALUES ($1, $2, $3, $4, \'booked\')', patient['id'], doctor['id'], date, time)
                
                apt_data["patient_name"] = patient['name']
                await self._sync_to_gateway(apt_data)
                
                return {"status": "success", "message": f"Booked for {patient['name']} with {doctor_name} on {date} at {time}."}
        except Exception:
            self.db_available = False
            return await self.book_appointment(phone_number, doctor_name, date, time)

