import io
import wave

try:
    import riva.client
    import riva.client.proto.riva_tts_pb2 as _tts_pb2
    _RIVA = True
except ImportError:
    _RIVA = False

from core.config import load

_SERVER  = "grpc.nvcf.nvidia.com:443"
_FUNC_ID = "877104f7-e885-42b9-8de8-f6e4c6303969"
_RATE    = 44100


def _require():
    if not _RIVA:
        raise RuntimeError(
            "nvidia-riva-client nicht installiert. "
            "Bitte ausführen: pip install nvidia-riva-client"
        )


def _auth():
    _require()
    key = load().get("api_keys", {}).get("nvidia", "")
    return riva.client.Auth(
        uri=_SERVER,
        use_ssl=True,
        metadata_args=[
            ["function-id", _FUNC_ID],
            ["authorization", f"Bearer {key}"],
        ],
    )


def _lang_from_voice(voice: str) -> str:
    """'Magpie-Multilingual.EN-US.Aria' → 'en-US'"""
    parts = voice.split(".")
    if len(parts) >= 2 and "-" in parts[1]:
        a, b = parts[1].split("-", 1)
        return f"{a.lower()}-{b}"
    return "en-US"


def check_key() -> str:
    _require()
    svc = riva.client.SpeechSynthesisService(_auth())
    svc.stub.GetRivaSynthesisConfig(_tts_pb2.RivaSynthesisConfigRequest())
    return "OK — NVIDIA Magpie TTS erreichbar"


def get_voices() -> list[dict]:
    _require()
    svc  = riva.client.SpeechSynthesisService(_auth())
    resp = svc.stub.GetRivaSynthesisConfig(_tts_pb2.RivaSynthesisConfigRequest())
    voices = []
    for mc in resp.model_config:
        lang       = mc.parameters.get("language_code", "")
        voice_name = mc.parameters.get("voice_name", "")
        subvoices  = [s.split(":")[0].strip() for s in mc.parameters.get("subvoices", "").split(",")]
        for sv in subvoices:
            if sv:
                voices.append({
                    "voice_id": f"{voice_name}.{sv}",
                    "name":     sv,
                    "desc":     lang,
                })
    return voices


def generate_tts(text: str, voice: str) -> tuple[bytes, str]:
    _require()
    svc  = riva.client.SpeechSynthesisService(_auth())
    resp = svc.synthesize(
        text=text,
        voice_name=voice,
        language_code=_lang_from_voice(voice),
        encoding=riva.client.AudioEncoding.LINEAR_PCM,
        sample_rate_hz=_RATE,
    )
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)   # 16-bit
        wf.setframerate(_RATE)
        wf.writeframes(resp.audio)
    return buf.getvalue(), "wav"
