from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path

from core.config import load, save, get_key, set_key
from api import elevenlabs, openai_tts, huggingface, openrouter, nvidia_nim, nvidia_tts

app = FastAPI(title="Sound Forge")

_STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")


@app.get("/")
def root():
    return FileResponse(str(_STATIC / "index.html"))


# ── Config ────────────────────────────────────────────────────────────────────

@app.get("/api/config")
def get_config():
    cfg = load()
    return {
        "keys_set": {k: bool(v) for k, v in cfg["api_keys"].items()},
        "output_folder": cfg.get("output_folder", ""),
        "default_format": cfg.get("default_format", "mp3"),
    }


class ConfigBody(BaseModel):
    api_keys: dict[str, str] = {}
    output_folder: str = ""
    default_format: str = "mp3"


@app.post("/api/config")
def update_config(body: ConfigBody):
    cfg = load()
    for provider, key in body.api_keys.items():
        if key:
            cfg["api_keys"][provider] = key
    if body.output_folder:
        cfg["output_folder"] = body.output_folder
    cfg["default_format"] = body.default_format
    save(cfg)
    return {"ok": True}


# ── Key test ──────────────────────────────────────────────────────────────────

class TestKeyBody(BaseModel):
    provider: str
    key: str


@app.post("/api/test-key")
def test_key(body: TestKeyBody):
    set_key(body.provider, body.key)
    fn = {
        "elevenlabs":  elevenlabs.check_key,
        "openai":      openai_tts.check_key,
        "huggingface": huggingface.check_key,
        "openrouter":  openrouter.check_key,
        "nvidia":      nvidia_nim.check_key,
    }.get(body.provider)
    if not fn:
        raise HTTPException(400, "Unbekannter Provider")
    return {"result": fn()}


# ── SFX ───────────────────────────────────────────────────────────────────────

class SFXBody(BaseModel):
    prompt: str
    duration: float = 3.0
    provider: str = "elevenlabs"
    hf_model: str = "facebook/audiogen-medium"


@app.post("/api/sfx/generate")
def generate_sfx(body: SFXBody):
    try:
        if body.provider == "elevenlabs":
            data, ext = elevenlabs.generate_sfx(body.prompt, body.duration)
        else:
            data, ext = huggingface.generate_sfx(body.prompt, body.hf_model)
        return Response(content=data, media_type=f"audio/{ext}",
                        headers={"X-Audio-Ext": ext})
    except (RuntimeError, ValueError) as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Voices ────────────────────────────────────────────────────────────────────

@app.get("/api/voices/elevenlabs")
def voices_el():
    try:
        return elevenlabs.get_voices()
    except Exception as e:
        raise HTTPException(400, str(e))


@app.get("/api/voices/openai")
def voices_oai():
    return openai_tts.get_voices()


@app.get("/api/voices/huggingface")
def voices_hf():
    return [{"voice_id": m, "name": label} for m, label in huggingface.VOICE_MODELS]


@app.get("/api/voices/nvidia")
def voices_nv():
    try:
        return nvidia_tts.get_voices()
    except Exception as e:
        raise HTTPException(400, str(e))


@app.get("/api/voice/preview")
def voice_preview(url: str):
    try:
        data = elevenlabs.preview_voice(url)
        return Response(content=data, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(400, str(e))


# ── TTS ───────────────────────────────────────────────────────────────────────

class TTSBody(BaseModel):
    text: str
    provider: str = "elevenlabs"
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    model_id: str = "eleven_multilingual_v2"
    stability: float = 0.7
    similarity: float = 0.6
    style: float = 0.1
    speed: float = 1.0


@app.post("/api/voice/generate")
def generate_voice(body: TTSBody):
    try:
        p = body.provider
        if p == "elevenlabs":
            data, ext = elevenlabs.generate_tts(
                body.text, body.voice_id, model_id=body.model_id,
                stability=body.stability, similarity=body.similarity,
                style=body.style, speed=body.speed,
            )
        elif p == "openai":
            data, ext = openai_tts.generate_tts(
                body.text, body.voice_id, model=body.model_id, speed=body.speed
            )
        elif p == "nvidia":
            data, ext = nvidia_tts.generate_tts(body.text, body.voice_id)
        elif p == "bark":
            data, ext = huggingface.generate_tts(body.text, "suno/bark")
        else:
            data, ext = huggingface.generate_tts(body.text, "facebook/mms-tts-eng")
        return Response(content=data, media_type=f"audio/{ext}",
                        headers={"X-Audio-Ext": ext})
    except (RuntimeError, ValueError) as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Prompt Refinement Providers ───────────────────────────────────────────────

@app.get("/api/openrouter/models")
def or_models():
    return openrouter.get_cheap_models()


@app.get("/api/nvidia/models")
def nv_models():
    return nvidia_nim.get_models()


class RefineBody(BaseModel):
    prompt: str
    type: str = "sfx"
    model: str = "google/gemma-3-4b-it:free"
    provider: str = "openrouter"


@app.post("/api/prompt/refine")
def refine(body: RefineBody):
    try:
        if body.provider == "nvidia":
            result = nvidia_nim.refine_prompt(body.prompt, body.type, body.model)
        else:
            result = openrouter.refine_prompt(body.prompt, body.type, body.model)
        return {"refined": result}
    except Exception as e:
        raise HTTPException(400, str(e))
