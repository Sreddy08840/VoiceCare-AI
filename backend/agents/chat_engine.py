import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

from agents.booking import BookingAgent
from agents.memory import MemoryAgent

load_dotenv()

# Initialize Groq client using OpenAI SDK format
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)
MODEL_NAME = "llama-3.3-70b-versatile"

class ChatEngine:
    def __init__(self, booking_agent: BookingAgent, memory_agent: MemoryAgent, patient_phone: str):
        self.booking_agent = booking_agent
        self.memory_agent = memory_agent
        self.patient_phone = patient_phone
        self.messages = []
        self._initialize_system_prompt()

    def _initialize_system_prompt(self):
        # Load the rules directly from the markdown files (or hardcode their essence here)
        # Using the exact content from SKILL.md and AGENTS.md
        system_content = f"""
You are a real-time multilingual voice assistant for booking clinical appointments.
You help patients schedule, change, and manage their appointments.

You can speak English, हिंदी, and தமிழ்.
Rules:
- Detect user language automatically
- Always respond in same language
- If user mixes languages, adapt dynamically

CRITICAL RULES:
1. Scope Enforcement: You are strictly a clinical appointment assistant. If the user asks for unrelated tasks, apologize and state you can only book medical appointments.
2. Slot Filling: Always ensure Patient Name, Doctor, Date, and Time are filled before confirming.
3. Error Handling:
   - Unclear input -> ask to repeat
   - Missing info -> ask specific question
   - Conflict -> suggest alternatives
   - Change of mind -> confirm before updating

CONVERSATION STYLE:
Act as a natural voice assistant.
- Keep responses short and conversational
- Use polite tone
- Confirm important actions
- Avoid robotic responses

You have access to tools to check availability, book appointments, and store memory.
Available Doctors: Dr. Rao, Dr. Sharma, Dr. Patel.
Never confirm an appointment without checking availability first.
Always store important preferences using the store_memory tool.
Patient Phone Number: {self.patient_phone}
"""
        self.messages.append({"role": "system", "content": system_content.strip()})

    async def inject_memory_context(self):
        """Called at session start to inject past context."""
        mem = await self.memory_agent.recall_memory(self.patient_phone)
        if mem.get("memories"):
            context = "Past Context for this patient: " + " | ".join(mem["memories"])
            self.messages.append({"role": "system", "content": context})
            return mem["memories"]
        return None

    def _get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "check_availability",
                    "description": "Check if a doctor is available on a specific date.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doctor_name": {"type": "string"},
                            "date": {"type": "string", "description": "YYYY-MM-DD format"}
                        },
                        "required": ["doctor_name", "date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "book_appointment",
                    "description": "Book a new appointment after confirming availability and details.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doctor_name": {"type": "string"},
                            "date": {"type": "string", "description": "YYYY-MM-DD format"},
                            "time": {"type": "string", "description": "HH:MM:SS format"}
                        },
                        "required": ["doctor_name", "date", "time"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "store_memory",
                    "description": "Store an important preference or session summary for the patient.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "The fact or preference to remember"},
                            "memory_type": {"type": "string", "enum": ["preference", "summary"]}
                        },
                        "required": ["text", "memory_type"]
                    }
                }
            }
        ]

    async def process_user_input(self, text: str) -> str:
        self.messages.append({"role": "user", "content": text})

        # Call Groq LLM
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=self.messages,
            tools=self._get_tools(),
            tool_choice="auto",
            temperature=0.3
        )
        
        response_message = response.choices[0].message
        self.messages.append(response_message)
        
        # Handle Tool Calls
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                print(f"[LLM Tool Call] {function_name} {args}")
                
                tool_result = ""
                if function_name == "check_availability":
                    res = await self.booking_agent.check_availability(args["doctor_name"], args["date"])
                    tool_result = json.dumps(res)
                elif function_name == "book_appointment":
                    res = await self.booking_agent.book_appointment(
                        self.patient_phone, args["doctor_name"], args["date"], args["time"]
                    )
                    tool_result = json.dumps(res)
                elif function_name == "store_memory":
                    res = await self.memory_agent.store_memory(
                        self.patient_phone, args["text"], args["memory_type"]
                    )
                    tool_result = json.dumps(res)
                
                # Append tool result to conversation
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
                
            # Get final response from LLM after tool calls
            second_response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=self.messages,
                temperature=0.3
            )
            final_text = second_response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": final_text})
            return final_text
        else:
            return response_message.content
