import os
import tempfile

_mixer_ok = False
_temp_files: list[str] = []
_current_file: str | None = None


def init() -> bool:
    global _mixer_ok
    try:
        import pygame
        pygame.init()
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        _mixer_ok = True
    except Exception:
        _mixer_ok = False
    return _mixer_ok


def play_bytes(audio_bytes: bytes, ext: str = "mp3") -> str | None:
    if not _mixer_ok:
        return None
    import pygame
    stop()
    global _current_file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
    tmp.write(audio_bytes)
    tmp.close()
    _temp_files.append(tmp.name)
    _current_file = tmp.name
    pygame.mixer.music.load(tmp.name)
    pygame.mixer.music.play()
    return tmp.name


def stop():
    if not _mixer_ok:
        return
    import pygame
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()


def is_playing() -> bool:
    if not _mixer_ok:
        return False
    import pygame
    return pygame.mixer.music.get_busy()


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
