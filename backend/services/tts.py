import base64

from backend.utils.logging import get_logger, log_event

logger = get_logger("tts")


class TTSService:
    def synthesize(self, text: str, language: str) -> str:
        payload = f"{language}:{text}".encode("utf-8")
        audio_b64 = base64.b64encode(payload).decode("ascii")
        log_event(logger, "tts_generated", chars=len(text), language=language)
        return audio_b64
