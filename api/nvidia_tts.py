"""
NVIDIA Magpie TTS Multilingual via NVCF REST API.
Kein grpcio / kein C-Compiler nötig — nutzt httpx.
Voices: https://docs.nvidia.com/nim/riva/tts/latest/support-matrix.html
"""
import io
import wave
import base64
import httpx

from core.config import load
from api._http import raise_for_status

_FUNC_ID  = "877104f7-e885-42b9-8de8-f6e4c6303969"
_NVCF_URL = f"https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/{_FUNC_ID}"
_RATE     = 22050   # model card: 22.05 kHz mono 16-bit PCM


# ── Voice list (from NVIDIA NIM Riva TTS Support Matrix) ─────────────────────
# Emotional variants: Voice.Emotion (e.g. Ray.Happy, Mia.Sad)
# Base voices haben kein Emotion-Suffix
_VOICES: list[dict] = [
    # English (en-US)
    {"voice_id": "Magpie-Multilingual.EN-US.Aria",          "name": "Aria",          "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Aria.Angry",    "name": "Aria · Angry",  "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Aria.Calm",     "name": "Aria · Calm",   "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Aria.Happy",    "name": "Aria · Happy",  "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Aria.Neutral",  "name": "Aria · Neutral","desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Aria.Sad",      "name": "Aria · Sad",    "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Diego",         "name": "Diego",         "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Isabela",       "name": "Isabela",       "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Jason",         "name": "Jason",         "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Jason.Angry",   "name": "Jason · Angry", "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Jason.Happy",   "name": "Jason · Happy", "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Leo",           "name": "Leo",           "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Leo.Calm",      "name": "Leo · Calm",    "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Leo.Angry",     "name": "Leo · Angry",   "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Leo.Neutral",   "name": "Leo · Neutral", "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Leo.Sad",       "name": "Leo · Sad",     "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Louise",        "name": "Louise",        "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Mia",           "name": "Mia",           "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Mia.Angry",     "name": "Mia · Angry",   "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Mia.Calm",      "name": "Mia · Calm",    "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Mia.Happy",     "name": "Mia · Happy",   "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Mia.Neutral",   "name": "Mia · Neutral", "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Mia.Sad",       "name": "Mia · Sad",     "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Pascal",        "name": "Pascal",        "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Ray",           "name": "Ray",           "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Ray.Angry",     "name": "Ray · Angry",   "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Ray.Calm",      "name": "Ray · Calm",    "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Ray.Happy",     "name": "Ray · Happy",   "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Ray.Neutral",   "name": "Ray · Neutral", "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Sofia",         "name": "Sofia",         "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Sofia.Happy",   "name": "Sofia · Happy", "desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Sofia.Neutral", "name": "Sofia · Neutral","desc": "EN-US"},
    {"voice_id": "Magpie-Multilingual.EN-US.Sofia.Calm",    "name": "Sofia · Calm",  "desc": "EN-US"},
    # Spanish (es-US)
    {"voice_id": "Magpie-Multilingual.ES-US.Aria",          "name": "Aria",          "desc": "ES-US"},
    {"voice_id": "Magpie-Multilingual.ES-US.Diego",         "name": "Diego",         "desc": "ES-US"},
    {"voice_id": "Magpie-Multilingual.ES-US.Diego.Happy",   "name": "Diego · Happy", "desc": "ES-US"},
    {"voice_id": "Magpie-Multilingual.ES-US.Diego.Neutral", "name": "Diego · Neutral","desc": "ES-US"},
    {"voice_id": "Magpie-Multilingual.ES-US.Isabela",       "name": "Isabela",       "desc": "ES-US"},
    {"voice_id": "Magpie-Multilingual.ES-US.Jason",         "name": "Jason",         "desc": "ES-US"},
    {"voice_id": "Magpie-Multilingual.ES-US.Leo",           "name": "Leo",           "desc": "ES-US"},
    {"voice_id": "Magpie-Multilingual.ES-US.Louise",        "name": "Louise",        "desc": "ES-US"},
    {"voice_id": "Magpie-Multilingual.ES-US.Mia",           "name": "Mia",           "desc": "ES-US"},
    {"voice_id": "Magpie-Multilingual.ES-US.Pascal",        "name": "Pascal",        "desc": "ES-US"},
    {"voice_id": "Magpie-Multilingual.ES-US.Ray",           "name": "Ray",           "desc": "ES-US"},
    {"voice_id": "Magpie-Multilingual.ES-US.Sofia",         "name": "Sofia",         "desc": "ES-US"},
    # French (fr-FR)
    {"voice_id": "Magpie-Multilingual.FR-FR.Aria",          "name": "Aria",          "desc": "FR-FR"},
    {"voice_id": "Magpie-Multilingual.FR-FR.Diego",         "name": "Diego",         "desc": "FR-FR"},
    {"voice_id": "Magpie-Multilingual.FR-FR.Isabela",       "name": "Isabela",       "desc": "FR-FR"},
    {"voice_id": "Magpie-Multilingual.FR-FR.Jason",         "name": "Jason",         "desc": "FR-FR"},
    {"voice_id": "Magpie-Multilingual.FR-FR.Leo",           "name": "Leo",           "desc": "FR-FR"},
    {"voice_id": "Magpie-Multilingual.FR-FR.Louise",        "name": "Louise",        "desc": "FR-FR"},
    {"voice_id": "Magpie-Multilingual.FR-FR.Mia",           "name": "Mia",           "desc": "FR-FR"},
    {"voice_id": "Magpie-Multilingual.FR-FR.Pascal",        "name": "Pascal",        "desc": "FR-FR"},
    {"voice_id": "Magpie-Multilingual.FR-FR.Pascal.Happy",  "name": "Pascal · Happy","desc": "FR-FR"},
    {"voice_id": "Magpie-Multilingual.FR-FR.Pascal.Neutral","name": "Pascal · Neutral","desc": "FR-FR"},
    {"voice_id": "Magpie-Multilingual.FR-FR.Ray",           "name": "Ray",           "desc": "FR-FR"},
    {"voice_id": "Magpie-Multilingual.FR-FR.Sofia",         "name": "Sofia",         "desc": "FR-FR"},
    # German (de-DE)
    {"voice_id": "Magpie-Multilingual.DE-DE.Diego",         "name": "Diego",         "desc": "DE-DE"},
    {"voice_id": "Magpie-Multilingual.DE-DE.Mia",           "name": "Mia",           "desc": "DE-DE"},
    {"voice_id": "Magpie-Multilingual.DE-DE.Pascal",        "name": "Pascal",        "desc": "DE-DE"},
    {"voice_id": "Magpie-Multilingual.DE-DE.Sofia",         "name": "Sofia",         "desc": "DE-DE"},
    # Mandarin (zh-CN)
    {"voice_id": "Magpie-Multilingual.ZH-CN.Aria",          "name": "Aria",          "desc": "ZH-CN"},
    {"voice_id": "Magpie-Multilingual.ZH-CN.Diego",         "name": "Diego",         "desc": "ZH-CN"},
    {"voice_id": "Magpie-Multilingual.ZH-CN.HouZhen",       "name": "HouZhen",       "desc": "ZH-CN"},
    {"voice_id": "Magpie-Multilingual.ZH-CN.Isabela",       "name": "Isabela",       "desc": "ZH-CN"},
    {"voice_id": "Magpie-Multilingual.ZH-CN.Long",          "name": "Long",          "desc": "ZH-CN"},
    {"voice_id": "Magpie-Multilingual.ZH-CN.Louise",        "name": "Louise",        "desc": "ZH-CN"},
    {"voice_id": "Magpie-Multilingual.ZH-CN.Mia",           "name": "Mia",           "desc": "ZH-CN"},
    {"voice_id": "Magpie-Multilingual.ZH-CN.North",         "name": "North",         "desc": "ZH-CN"},
    {"voice_id": "Magpie-Multilingual.ZH-CN.Pascal",        "name": "Pascal",        "desc": "ZH-CN"},
    {"voice_id": "Magpie-Multilingual.ZH-CN.Ray",           "name": "Ray",           "desc": "ZH-CN"},
    {"voice_id": "Magpie-Multilingual.ZH-CN.Siwei",         "name": "Siwei",         "desc": "ZH-CN"},
    # Italian (it-IT)
    {"voice_id": "Magpie-Multilingual.IT-IT.Isabela",       "name": "Isabela",       "desc": "IT-IT"},
    {"voice_id": "Magpie-Multilingual.IT-IT.Pascal",        "name": "Pascal",        "desc": "IT-IT"},
    # Vietnamese (vi-VN)
    {"voice_id": "Magpie-Multilingual.VI-VN.Aria",          "name": "Aria",          "desc": "VI-VN"},
    {"voice_id": "Magpie-Multilingual.VI-VN.Diego",         "name": "Diego",         "desc": "VI-VN"},
    {"voice_id": "Magpie-Multilingual.VI-VN.Isabela",       "name": "Isabela",       "desc": "VI-VN"},
    {"voice_id": "Magpie-Multilingual.VI-VN.Jason",         "name": "Jason",         "desc": "VI-VN"},
    {"voice_id": "Magpie-Multilingual.VI-VN.Le",            "name": "Le",            "desc": "VI-VN"},
    {"voice_id": "Magpie-Multilingual.VI-VN.Long",          "name": "Long",          "desc": "VI-VN"},
    {"voice_id": "Magpie-Multilingual.VI-VN.Long.Happy",    "name": "Long · Happy",  "desc": "VI-VN"},
    {"voice_id": "Magpie-Multilingual.VI-VN.Long.Neutral",  "name": "Long · Neutral","desc": "VI-VN"},
    {"voice_id": "Magpie-Multilingual.VI-VN.Louise",        "name": "Louise",        "desc": "VI-VN"},
    {"voice_id": "Magpie-Multilingual.VI-VN.Mia",           "name": "Mia",           "desc": "VI-VN"},
    {"voice_id": "Magpie-Multilingual.VI-VN.North",         "name": "North",         "desc": "VI-VN"},
    {"voice_id": "Magpie-Multilingual.VI-VN.Pascal",        "name": "Pascal",        "desc": "VI-VN"},
    {"voice_id": "Magpie-Multilingual.VI-VN.Ray",           "name": "Ray",           "desc": "VI-VN"},
    {"voice_id": "Magpie-Multilingual.VI-VN.Sofia",         "name": "Sofia",         "desc": "VI-VN"},
]


def _headers() -> dict:
    key = load().get("api_keys", {}).get("nvidia", "")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _lang_from_voice(voice: str) -> str:
    """'Magpie-Multilingual.EN-US.Ray.Happy' → 'en-US'"""
    parts = voice.split(".")
    if len(parts) >= 2 and "-" in parts[1]:
        a, b = parts[1].split("-", 1)
        return f"{a.lower()}-{b}"
    return "en-US"


def check_key() -> str:
    # Lightweight check: synthesize a single word
    generate_tts("test", "Magpie-Multilingual.EN-US.Ray")
    return "OK — NVIDIA Magpie TTS erreichbar"


def get_voices() -> list[dict]:
    return _VOICES


def generate_tts(text: str, voice: str) -> tuple[bytes, str]:
    payload = {
        "text":          text,
        "languageCode":  _lang_from_voice(voice),
        "encoding":      "LINEAR_PCM",
        "sampleRateHz":  _RATE,
        "voiceName":     voice,
    }
    with httpx.Client(timeout=30) as c:
        r = c.post(_NVCF_URL, json=payload, headers=_headers())
        raise_for_status(r)

    data  = r.json()
    audio = data.get("audio") or data.get("audio_content") or data.get("audioContent")
    if not audio:
        raise RuntimeError(f"Kein Audio in der Antwort. Felder: {list(data.keys())}")

    pcm = base64.b64decode(audio)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)   # 16-bit
        wf.setframerate(_RATE)
        wf.writeframes(pcm)
    return buf.getvalue(), "wav"
