# Sound Forge

AI-gestützte Desktop-App zur Generierung von Game-SFX und Sprachausgaben.

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Provider

| Provider | SFX | Stimmen | Key |
|---|---|---|---|
| ElevenLabs | ✓ | ✓ | [elevenlabs.io](https://elevenlabs.io) |
| OpenAI TTS | — | ✓ | [platform.openai.com](https://platform.openai.com) |
| Hugging Face | ✓ AudioGen | ✓ Bark/MMS | [hf.co/settings/tokens](https://huggingface.co/settings/tokens) — kostenlos |

API-Keys in der App unter **Einstellungen** konfigurieren.
Keys werden lokal unter `~/.sound-forge/config.json` gespeichert.

## Build (.exe)

```bash
pip install pyinstaller
pyinstaller build.spec
# → dist/SoundForge.exe
```

## Features (v0.1)

- **SFX-Generator**: Textprompt, Quick-Tags, Dauer, 1–3 Variationen
- **Stimmen-Generator**: Voice-Browser (EL: 100+ Stimmen), Probe-Playback, Vergleich bis 3 Stimmen gleichzeitig
- **Voice-Settings**: Stabilität, Similarity, Stil, Geschwindigkeit (ElevenLabs)
- **Open Source**: Hugging Face AudioGen (SFX) + Bark/MMS (TTS), kostenlos
- **Output**: WAV/MP3 direkt in Godot-Asset-Ordner speichern
