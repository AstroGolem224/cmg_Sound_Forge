import httpx
from core.config import get_key

VOICES = [
    {"id": "alloy",   "name": "Alloy",   "desc": "Neutral, vielseitig"},
    {"id": "echo",    "name": "Echo",    "desc": "Sanft, jung"},
    {"id": "fable",   "name": "Fable",   "desc": "Britisch, Autorität"},
    {"id": "onyx",    "name": "Onyx",    "desc": "Tief, markant"},
    {"id": "nova",    "name": "Nova",    "desc": "Energetisch, hell"},
    {"id": "shimmer", "name": "Shimmer", "desc": "Ausdrucksstark, warm"},
]

MODELS = [
    ("tts-1",    "TTS-1 (schnell)"),
    ("tts-1-hd", "TTS-1 HD (höhere Qualität)"),
]


def get_voices() -> list:
    return VOICES


def check_key() -> str:
    key = get_key("openai")
    if not key:
        return "Kein API-Key gesetzt"
    try:
        r = httpx.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10,
        )
        if r.status_code == 401:
            return "Ungültiger API-Key"
        r.raise_for_status()
        return "OK"
    except httpx.TimeoutException:
        return "Timeout"
    except Exception as e:
        return f"Fehler: {e}"


def generate_tts(
    text: str,
    voice: str = "alloy",
    model: str = "tts-1",
    speed: float = 1.0,
) -> tuple[bytes, str]:
    key = get_key("openai")
    if not key:
        raise ValueError("Kein OpenAI API-Key konfiguriert")
    r = httpx.post(
        "https://api.openai.com/v1/audio/speech",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": model,
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": "mp3",
        },
        timeout=45,
    )
    r.raise_for_status()
    return r.content, "mp3"
