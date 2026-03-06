# Sound Forge — Projektplan

**Zweck:** Desktop-App zur AI-gestützten Generierung von Game-SFX und Sprachausgaben.
**Output:** Audio-Files (WAV/MP3) direkt als Game-Assets verwendbar.
**Status:** Planung

---

## Tech Stack

| Komponente | Entscheidung | Begründung |
|---|---|---|
| Sprache | **Python 3.12+** | Beste AI/Audio-Library-Unterstützung |
| GUI | **CustomTkinter** | Modernes Dark Theme, pure Python |
| Audio-Playback | **pygame.mixer** | Einfach, zuverlässig, Cross-platform |
| HTTP-Calls | **httpx** (async) | Async API-Calls ohne Blocking |
| API-Keys | **keyring** | Sichere OS-native Schlüsselspeicherung |
| Build | **PyInstaller** | Einzelne .exe, keine Dependencies |
| Audio-Utils | **pydub** (optional) | Format-Konvertierung falls nötig |

---

## AI Provider Matrix

### Kommerzielle APIs (API-Key erforderlich)

| Provider | SFX | Stimmen | Kosten | Freie Tier |
|---|---|---|---|---|
| **ElevenLabs** | ✓ `/v1/sound-generation` | ✓ `/v1/text-to-speech` | ~$0.30/SFX | 10k Zeichen/Monat |
| **OpenAI TTS** | ✗ | ✓ `/v1/audio/speech` | $0.015/1k Zeichen | Keiner |

**ElevenLabs** ist der primäre Provider — deckt SFX und Stimmen mit einem API-Key ab.

### Open Source Alternativen (kostenlos)

| Provider | SFX | Stimmen | Ausführung | Anforderungen |
|---|---|---|---|---|
| **Hugging Face Inference API** | ✓ (AudioGen, audioldm2) | ✓ (Bark, Coqui, MMS) | Cloud, free tier | HF Token (kostenlos) |
| **Coqui TTS** | ✗ | ✓ Viele Modelle | Lokal | CPU/GPU, `pip install TTS` |
| **Bark (Suno)** | ✗ | ✓ Expressiv, Emotion | Lokal | ~4–8GB RAM/VRAM |
| **AudioCraft / AudioGen** (Meta) | ✓ Text-to-SFX | ✗ | Lokal | GPU empfohlen |
| **Kokoro TTS** | ✗ | ✓ Modern, leicht | Lokal | Läuft auf CPU |

**Empfehlung für Einstieg ohne Kosten:** Hugging Face Inference API — ein kostenloser Token, Zugriff auf viele Modelle.

---

## App-Struktur

```
sound-forge/
├── main.py                  ← Einstiegspunkt, App starten
├── ui/
│   ├── app.py               ← Haupt-CTk-Fenster, Navigation
│   ├── sfx_page.py          ← SFX-Generator-Seite
│   ├── voice_page.py        ← Stimmen-Generator-Seite
│   └── settings_page.py     ← API-Keys, Output-Ordner
├── api/
│   ├── elevenlabs.py        ← SFX + TTS via ElevenLabs
│   ├── openai_tts.py        ← TTS via OpenAI
│   └── huggingface.py       ← Open Source (AudioGen, Bark via HF)
├── core/
│   ├── audio.py             ← Playback, Format-Handling (pygame)
│   ├── config.py            ← API-Keys laden/speichern (keyring)
│   └── export.py            ← Datei speichern, Namensgebung
├── requirements.txt
├── build.spec               ← PyInstaller Konfiguration
└── README.md
```

---

## Seite 1: SFX-Generator

### UI-Elemente
- **Prompt-Eingabe** (Textfeld): `"metal sword clash with reverb"`
- **Quick-Tags** (Buttons): Explosion · UI-Click · Footstep · Magic · Impact · Ambient · Nature
- **Dauer-Slider**: 0.5s bis 22s (ElevenLabs-Limit)
- **Variationen**: 1 / 2 / 3 (mehrere parallel generieren)
- **Provider-Auswahl**: ElevenLabs | Hugging Face AudioGen
- **Generieren-Button**

### Ergebnis-Karten (pro Variation)
- Play/Stop-Button mit Fortschrittsanzeige
- Dateiname-Eingabe (editierbar, Vorschlag aus Prompt)
- Format-Auswahl: WAV | MP3
- Speichern-Button → öffnet Datei-Dialog (startet im konfigurierten Asset-Ordner)

---

## Seite 2: Stimmen-Generator

### UI-Elemente
- **Text-Eingabe** (Multiline): Skript / Dialogzeile
- **Provider-Auswahl**: ElevenLabs | OpenAI TTS | Hugging Face | Coqui (lokal) | Bark (lokal)

### Voice-Browser (Provider-abhängig)
- **ElevenLabs**: Grid mit Voice-Karten (Name, Geschlecht, Akzent, Sprache + [▶ Probe])
- **OpenAI**: 6 Stimmen (alloy, echo, fable, onyx, nova, shimmer) + [▶ Probe]
- **Hugging Face / Lokal**: Modell-Dropdown + verfügbare Speaker-IDs

### Voice-Settings (ElevenLabs)
- Stabilität: 0.0 – 1.0 (Slider)
- Similarity Boost: 0.0 – 1.0 (Slider)
- Stil: 0.0 – 1.0 (Slider)
- Geschwindigkeit: 0.25 – 4.0 (Slider)

### Vergleich-Modus
- 2–3 Stimmen auswählen → gleicher Text → parallel generieren
- Nebeneinander vorhören → beste wählen → speichern

### Ergebnis
- Play/Stop + Dateiname-Eingabe + Format + Speichern (wie SFX-Seite)

---

## Seite 3: Einstellungen

```
API Keys
  ElevenLabs API Key:      [●●●●●●●●●●●●●●]  [TESTEN]
  OpenAI API Key:          [●●●●●●●●●●●●●●]  [TESTEN]
  Hugging Face Token:      [                ]  [TESTEN]

Lokal installierte Modelle
  Coqui TTS:     [ ] Installiert   [INSTALLIEREN]
  Bark:          [ ] Installiert   [INSTALLIEREN]
  AudioCraft:    [ ] Installiert   [INSTALLIEREN]
  (Installiert via pip in der App, Download der Modelle beim ersten Run)

Output
  Standard-Ordner:   [C:/Games/MMC/assets/audio/]  [DURCHSUCHEN]
  Standard-Format:   [WAV ▼]

Info: Sound Forge v0.1.0
```

---

## Output-Formate

| Format | Verwendung | Godot-Support |
|---|---|---|
| **WAV** | Standard, lossless | ✓ Nativ (empfohlen) |
| **MP3** | Kleinere Dateien | ✓ |
| OGG | — | Godot importiert WAV → OGG intern |

**Empfehlung:** WAV speichern. Godot-Importer komprimiert automatisch beim Build.

---

## Godot-Integration

Asset-Files landen direkt im konfigurierten Ordner → Godot erkennt sie sofort beim nächsten Editor-Fokus. Keine extra Schritte nötig.

**Empfohlene Ordnerstruktur in Godot:**
```
res://assets/audio/
├── sfx/
│   ├── sword_clash_01.wav
│   └── explosion_big.wav
└── voice/
    ├── npc_warning.wav
    └── player_hurt.wav
```

---

## MVP-Scope (v0.1)

| Feature | Status |
|---|---|
| SFX-Generator (ElevenLabs) | MVP |
| Voice-Generator (ElevenLabs + OpenAI) | MVP |
| Voice-Browser mit Probe-Playback | MVP |
| API-Key-Verwaltung (Settings) | MVP |
| WAV/MP3 speichern | MVP |
| Hugging Face open-source Provider | MVP |
| Vergleich-Modus (2–3 Stimmen) | MVP |
| Coqui / Bark lokal (in-App-Install) | v0.2 |
| Local AudioCraft SFX | v0.2 |
| Asset-Library / Browser | v0.3 |
| Presets speichern | v0.3 |
| Batch-Export | v0.3 |

---

## Abhängigkeiten (requirements.txt)

```
customtkinter>=5.2.0
httpx>=0.27.0
pygame>=2.5.0
keyring>=25.0.0
pydub>=0.25.0     # optional, für Format-Konvertierung
Pillow>=10.0.0    # für CTk-Icons
pyinstaller>=6.0  # dev dependency für Build
```

### Optionale lokale Modelle (on demand installiert)
```
TTS>=0.22.0       # Coqui TTS
git+https://github.com/suno-ai/bark   # Bark
audiocraft        # Meta AudioCraft / AudioGen
transformers      # Hugging Face Transformers
```

---

## Build

```bash
# Entwicklung
python main.py

# .exe bauen
pyinstaller build.spec
# Output: dist/SoundForge.exe (standalone, keine Python-Installation nötig)
```

---

*Erstellt: 2026-03-06 | Forge (Claude Code Agent)*
