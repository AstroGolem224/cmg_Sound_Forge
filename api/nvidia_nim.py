import httpx
from core.config import load
from api._http import raise_for_status

_BASE = "https://integrate.api.nvidia.com/v1"

FALLBACK_MODELS = [
    {"id": "nvidia/llama-3.1-nemotron-70b-instruct", "name": "Nemotron 70B Instruct"},
    {"id": "meta/llama-3.1-8b-instruct",              "name": "Llama 3.1 8B Instruct"},
    {"id": "mistralai/mistral-7b-instruct-v0.3",      "name": "Mistral 7B Instruct"},
    {"id": "qwen/qwen2-7b-instruct",                  "name": "Qwen 2 7B Instruct"},
]

_KEEP_KEYWORDS = ("instruct", "chat", "nemotron", "llama", "mistral", "qwen", "gemma")


def _headers() -> dict:
    key = load().get("api_keys", {}).get("nvidia", "")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def check_key() -> str:
    with httpx.Client(verify=True) as c:
        r = c.get(f"{_BASE}/models", headers=_headers(), timeout=10)
        raise_for_status(r)
    return "OK — NVIDIA NIM erreichbar"


def get_models() -> list[dict]:
    try:
        with httpx.Client(verify=True) as c:
            r = c.get(f"{_BASE}/models", headers=_headers(), timeout=10)
            raise_for_status(r)
        data = r.json().get("data", [])
        models = [
            {"id": m["id"], "name": m["id"]}
            for m in data
            if any(k in m.get("id", "").lower() for k in _KEEP_KEYWORDS)
        ]
        return models or FALLBACK_MODELS
    except Exception:
        return FALLBACK_MODELS


def refine_prompt(prompt: str, type_: str, model: str) -> str:
    if type_ == "sfx":
        system = (
            "You are a sound design expert for video games. "
            "Rewrite the given prompt to be more descriptive and effective for AI audio generation tools like ElevenLabs or AudioGen. "
            "Return only the refined prompt, no explanations."
        )
    else:
        system = (
            "You are a voice acting director for video games. "
            "Rewrite the given text to be more expressive and natural for text-to-speech synthesis. "
            "Return only the refined text, no explanations."
        )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        "max_tokens": 250,
        "temperature": 0.7,
    }
    with httpx.Client(verify=True) as c:
        r = c.post(f"{_BASE}/chat/completions", headers=_headers(), json=payload, timeout=30)
        raise_for_status(r)
    return r.json()["choices"][0]["message"]["content"].strip()
