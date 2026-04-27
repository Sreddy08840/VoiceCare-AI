class NotificationAgent:
    """
    Handles outbound notifications (SMS/Calls).
    In a real implementation, this connects to Twilio or a similar SMS provider.
    """
    def __init__(self):
        self.twilio_stub = True

    async def send_sms_reminder(self, phone_number: str, message: str) -> bool:
        """Sends an SMS reminder to the patient."""
        print(f"[Twilio Stub] Sending SMS to {phone_number}: {message}")
        return True

    async def initiate_voice_call(self, phone_number: str, message: str) -> bool:
        """Initiates an outbound voice call reminder."""
        print(f"[Twilio Stub] Calling {phone_number} to say: {message}")
        return True
