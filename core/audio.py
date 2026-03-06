"""
Audio playback — Windows: WinMM MCI (built-in, kein Install nötig).
Unterstützt MP3, WAV, FLAC, OGG.
"""
import os
import sys
import tempfile

_temp_files: list[str] = []
_backend: str = "none"   # "winmm" | "sounddevice" | "none"

# WinMM state
_winmm = None
_mci_alias = "sforge_sound"


def init() -> bool:
    global _backend, _winmm
    if sys.platform == "win32":
        try:
            import ctypes
            _winmm = ctypes.windll.winmm
            # Smoke-test
            _winmm.mciSendStringW(f"close {_mci_alias}", None, 0, None)
            _backend = "winmm"
            return True
        except Exception:
            pass

    # Fallback: sounddevice (cross-platform, pip install sounddevice soundfile)
    try:
        import sounddevice  # noqa: F401
        import soundfile    # noqa: F401
        _backend = "sounddevice"
        return True
    except ImportError:
        pass

    _backend = "none"
    return False


def play_bytes(audio_bytes: bytes, ext: str = "mp3") -> str | None:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
    tmp.write(audio_bytes)
    tmp.close()
    _temp_files.append(tmp.name)
    return _play_file(tmp.name)


def _play_file(path: str) -> str | None:
    if _backend == "winmm":
        _mci_stop()
        cmd_open = f'open "{path}" alias {_mci_alias}'
        _winmm.mciSendStringW(cmd_open, None, 0, None)
        _winmm.mciSendStringW(f"play {_mci_alias}", None, 0, None)
        return path

    if _backend == "sounddevice":
        import soundfile as sf
        import sounddevice as sd
        data, samplerate = sf.read(path, dtype="float32")
        sd.play(data, samplerate)
        return path

    return None


def stop():
    if _backend == "winmm":
        _mci_stop()
    elif _backend == "sounddevice":
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass


def _mci_stop():
    if _winmm is None:
        return
    _winmm.mciSendStringW(f"stop {_mci_alias}", None, 0, None)
    _winmm.mciSendStringW(f"close {_mci_alias}", None, 0, None)


def is_playing() -> bool:
    if _backend == "winmm" and _winmm:
        import ctypes
        buf = ctypes.create_unicode_buffer(128)
        _winmm.mciSendStringW(f"status {_mci_alias} mode", buf, 128, None)
        return buf.value.lower() == "playing"
    if _backend == "sounddevice":
        try:
            import sounddevice as sd
            return sd.get_stream().active
        except Exception:
            return False
    return False


def cleanup():
    stop()
    for f in _temp_files:
        try:
            os.unlink(f)
        except OSError:
            pass
    _temp_files.clear()


def detect_ext(content_type: str) -> str:
    ct = content_type.lower()
    if "mpeg" in ct or "mp3" in ct:
        return "mp3"
    if "flac" in ct:
        return "flac"
    if "ogg" in ct:
        return "ogg"
    return "wav"
