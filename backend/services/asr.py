from backend.utils.logging import get_logger, log_event

logger = get_logger("asr")


class ASRService:
    def transcribe(self, audio_text: str) -> str:
        text = audio_text.strip()
        log_event(logger, "transcription", text=text)
        return text
