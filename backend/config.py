import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ENV = PROJECT_ROOT / "backend" / ".env"
ROOT_ENV = PROJECT_ROOT / ".env"

# Explicit process environment wins. Load backend/.env for server-side provider
# settings; keep root .env as a legacy fallback. Secret values are never logged.
load_dotenv(BACKEND_ENV, override=False)
load_dotenv(ROOT_ENV, override=False)

if any(os.getenv(key) for key in ("GROQ_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY")):
    _key_source = "process environment or project .env"
else:
    _key_source = "not configured"


class Settings:
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "groq").strip().lower()
    AI_FALLBACK_ENABLED: bool = os.getenv("AI_FALLBACK_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
    GROQ_API_KEY: str = (os.getenv("GROQ_API_KEY") or str((dotenv_values(BACKEND_ENV).get("GROQ_API_KEY") or ""))).strip()
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
    GEMINI_API_KEY: str = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
    MIN_TEXT_THRESHOLD: int = int(os.getenv("MIN_TEXT_THRESHOLD", "50"))
    MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe").strip()
    KEY_SOURCE: str = _key_source if any(os.getenv(k) for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY")) else "not configured"


settings = Settings()

