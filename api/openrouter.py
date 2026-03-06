import httpx
from core.config import get_key
from api._http import raise_for_status

_BASE    = "https://openrouter.ai/api/v1"
_REFERER = "https://claymachinegames.com"

_SYSTEM_SFX = (
    "You are a sound design expert. Refine the user's rough description into a "
    "detailed, specific prompt for AI sound-effect generation. Be descriptive "
    "about texture, intensity, reverb, duration, and layers. "
    "Max 60 words. Output only the refined prompt, nothing else."
)
_SYSTEM_VOICE = (
    "You are a voice direction expert. Refine the following into a detailed "
    "prompt for AI text-to-speech generation. Describe tone, emotion, pacing, "
    "accent if relevant. Max 60 words. Output only the refined prompt, nothing else."
)

_FALLBACK_MODELS = [
    {"id": "google/gemma-3-4b-it:free",            "name": "Gemma 3 4B (free)",    "free": True},
    {"id": "meta-llama/llama-3.2-3b-instruct:free", "name": "Llama 3.2 3B (free)", "free": True},
    {"id": "mistralai/mistral-7b-instruct:free",    "name": "Mistral 7B (free)",    "free": True},
    {"id": "qwen/qwen-2.5-7b-instruct:free",        "name": "Qwen 2.5 7B (free)",  "free": True},
]


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {get_key('openrouter')}",
        "HTTP-Referer": _REFERER,
        "X-Title": "Sound Forge",
    }


def check_key() -> str:
    if not get_key("openrouter"):
        return "Kein Token gesetzt"
    try:
        r = httpx.get(f"{_BASE}/auth/key", headers=_headers(), timeout=10)
        if r.status_code == 401:
            return "Ungültiger Token"
        raise_for_status(r)
        label = r.json().get("data", {}).get("label") or "OK"
        return f"OK — {label}"
    except httpx.TimeoutException:
        return "Timeout"
    except Exception as e:
        return f"Fehler: {e}"


def get_cheap_models() -> list[dict]:
    if not get_key("openrouter"):
        return _FALLBACK_MODELS
    try:
        r = httpx.get(f"{_BASE}/models", headers=_headers(), timeout=15)
        raise_for_status(r)
        out = []
        for m in r.json().get("data", []):
            is_free = m["id"].endswith(":free")
            try:
                price = float(m.get("pricing", {}).get("prompt", "9999"))
            except (ValueError, TypeError):
                price = 9999
            if is_free or price <= 0.0000005:
                out.append({"id": m["id"], "name": m.get("name", m["id"]), "free": is_free})
        out.sort(key=lambda x: (0 if x["free"] else 1, x["name"]))
        return out[:40] or _FALLBACK_MODELS
    except Exception:
        return _FALLBACK_MODELS


def refine_prompt(prompt: str, type_: str, model: str) -> str:
    if not get_key("openrouter"):
        raise ValueError("Kein OpenRouter Token konfiguriert")
    r = httpx.post(
        f"{_BASE}/chat/completions",
        headers=_headers(),
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": _SYSTEM_SFX if type_ == "sfx" else _SYSTEM_VOICE},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 120,
            "temperature": 0.7,
        },
        timeout=30,
    )
    raise_for_status(r)
    return r.json()["choices"][0]["message"]["content"].strip()
