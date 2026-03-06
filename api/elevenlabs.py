import httpx
from core.config import get_key
from api._http import raise_for_status

_BASE = "https://api.elevenlabs.io/v1"

MODELS = [
    ("eleven_multilingual_v2", "Multilingual v2 (empfohlen)"),
    ("eleven_monolingual_v1", "Monolingual v1 (EN)"),
    ("eleven_turbo_v2_5", "Turbo v2.5 (schnell, multi)"),
    ("eleven_turbo_v2", "Turbo v2 (schnell, EN)"),
]


def _headers() -> dict:
    return {"xi-api-key": get_key("elevenlabs")}


def check_key() -> str:
    key = get_key("elevenlabs")
    if not key:
        return "Kein API-Key gesetzt"
    try:
        r = httpx.get(f"{_BASE}/user", headers=_headers(), timeout=10)
        if r.status_code == 401:
            return "Ungültiger API-Key"
        raise_for_status(r)
        data = r.json()
        tier = data.get("subscription", {}).get("tier", "unknown")
        return f"OK — Tier: {tier}"
    except httpx.TimeoutException:
        return "Timeout — Server nicht erreichbar"
    except Exception as e:
        return f"Fehler: {e}"


def get_voices() -> list[dict]:
    key = get_key("elevenlabs")
    if not key:
        return []
    r = httpx.get(f"{_BASE}/voices", headers=_headers(), timeout=15)
    raise_for_status(r)
    return r.json().get("voices", [])


def preview_voice(preview_url: str) -> bytes:
    r = httpx.get(preview_url, timeout=15)
    raise_for_status(r)
    return r.content


def generate_sfx(prompt: str, duration: float) -> tuple[bytes, str]:
    key = get_key("elevenlabs")
    if not key:
        raise ValueError("Kein ElevenLabs API-Key konfiguriert")
    r = httpx.post(
        f"{_BASE}/sound-generation",
        headers={**_headers(), "Accept": "audio/mpeg"},
        json={"text": prompt, "duration_seconds": duration, "prompt_influence": 0.3},
        timeout=45,
    )
    raise_for_status(r)
    ct = r.headers.get("content-type", "audio/mpeg")
    from core.audio import detect_ext
    return r.content, detect_ext(ct)


def generate_tts(
    text: str,
    voice_id: str,
    model_id: str = "eleven_multilingual_v2",
    stability: float = 0.7,
    similarity: float = 0.6,
    style: float = 0.1,
    speed: float = 1.0,
) -> tuple[bytes, str]:
    key = get_key("elevenlabs")
    if not key:
        raise ValueError("Kein ElevenLabs API-Key konfiguriert")
    r = httpx.post(
        f"{_BASE}/text-to-speech/{voice_id}",
        headers={**_headers(), "Accept": "audio/mpeg"},
        params={"optimize_streaming_latency": "0"},
        json={
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity,
                "style": style,
                "use_speaker_boost": True,
            },
        },
        timeout=45,
    )
    raise_for_status(r)
    return r.content, "mp3"
