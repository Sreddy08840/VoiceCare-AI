from backend.utils.logging import get_logger, log_event

logger = get_logger("lang")


class LanguageService:
    def detect(self, text: str, hint: str | None = None) -> str:
        if hint in {"en", "hi", "ta"}:
            lang = hint
        elif any("\u0900" <= ch <= "\u097F" for ch in text):
            lang = "hi"
        elif any("\u0B80" <= ch <= "\u0BFF" for ch in text):
            lang = "ta"
        else:
            low = text.lower()
            if any(word in low for word in ["namaste", "kal", "doctor ji"]):
                lang = "hi"
            elif any(word in low for word in ["vanakkam", "naalai", "maruthuvam"]):
                lang = "ta"
            else:
                lang = "en"
        log_event(logger, "language_detected", language=lang)
        return lang
