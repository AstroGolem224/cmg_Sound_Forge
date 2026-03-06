import httpx
from core.config import get_key

_BASE = "https://api-inference.huggingface.co/models"

SFX_MODELS = [
    ("facebook/audiogen-medium", "AudioGen Medium (SFX)"),
    ("cvssp/audioldm2",          "AudioLDM 2 (SFX / Ambient)"),
]

VOICE_MODELS = [
    ("suno/bark",            "Bark (Expressiv, EN)"),
    ("facebook/mms-tts-eng", "MMS TTS (Englisch, leicht)"),
]


def _headers() -> dict:
    return {"Authorization": f"Bearer {get_key('huggingface')}"}


def check_key() -> str:
    token = get_key("huggingface")
    if not token:
        return "Kein Token gesetzt"
    try:
        r = httpx.get(
            "https://huggingface.co/api/whoami",
            headers=_headers(),
            timeout=10,
        )
        if r.status_code == 401:
            return "Ungültiger Token"
        r.raise_for_status()
        name = r.json().get("name", "?")
        return f"OK — {name}"
    except httpx.TimeoutException:
        return "Timeout"
    except Exception as e:
        return f"Fehler: {e}"


def _infer(model_id: str, inputs: str) -> tuple[bytes, str]:
    token = get_key("huggingface")
    if not token:
        raise ValueError("Kein Hugging Face Token konfiguriert")
    r = httpx.post(
        f"{_BASE}/{model_id}",
        headers=_headers(),
        json={"inputs": inputs},
        timeout=120,
    )
    if r.status_code == 503:
        raise RuntimeError(
            "Modell lädt gerade (Cold Start). Bitte in ~30 Sek. erneut versuchen."
        )
    r.raise_for_status()
    ct = r.headers.get("content-type", "audio/wav")
    from core.audio import detect_ext
    return r.content, detect_ext(ct)


def generate_sfx(prompt: str, model_id: str = "facebook/audiogen-medium") -> tuple[bytes, str]:
    return _infer(model_id, prompt)


def generate_tts(text: str, model_id: str = "suno/bark") -> tuple[bytes, str]:
    return _infer(model_id, text)
