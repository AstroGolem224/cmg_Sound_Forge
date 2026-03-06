import threading
import customtkinter as ctk
from api import elevenlabs, openai_tts, huggingface
from core import audio
from ui.widgets import ResultCard, StatusLabel

_PROVIDERS = ["ElevenLabs", "OpenAI TTS", "Hugging Face — Bark", "Hugging Face — MMS"]


class VoiceCard(ctk.CTkFrame):
    """Klickbare Stimmen-Karte im Browser."""

    def __init__(self, master, voice: dict, on_select, **kwargs):
        super().__init__(master, corner_radius=8, width=175, height=120, **kwargs)
        self.grid_propagate(False)
        self._voice = voice
        self._on_select = on_select
        self._selected = False

        self.grid_columnconfigure(0, weight=1)

        name = voice.get("name", "?")
        labels = voice.get("labels", {})
        gender = labels.get("gender", "")
        accent = labels.get("accent", "")
        age = labels.get("age", "")
        info = " · ".join(x for x in [gender, age, accent] if x)

        ctk.CTkLabel(
            self, text=name, font=ctk.CTkFont(size=13, weight="bold"), wraplength=155
        ).grid(row=0, column=0, padx=8, pady=(10, 2), sticky="ew")

        ctk.CTkLabel(
            self, text=info or "—", font=ctk.CTkFont(size=10), text_color="gray", wraplength=155
        ).grid(row=1, column=0, padx=8, pady=(0, 6), sticky="ew")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=8, pady=(0, 8))

        preview_url = voice.get("preview_url")
        if preview_url:
            ctk.CTkButton(
                btn_frame, text="▶ Probe", width=70, height=24, font=ctk.CTkFont(size=11),
                fg_color=("gray65", "gray30"),
                command=lambda: threading.Thread(
                    target=self._play_preview, args=(preview_url,), daemon=True
                ).start(),
            ).pack(side="left", padx=(0, 4))

        self.bind("<Button-1>", lambda _: self._toggle())
        for w in self.winfo_children():
            w.bind("<Button-1>", lambda _: self._toggle())

    def _play_preview(self, url: str):
        try:
            data = elevenlabs.preview_voice(url)
            audio.play_bytes(data, "mp3")
        except Exception:
            pass

    def _toggle(self):
        self._selected = not self._selected
        color = ("#3a7ebf", "#1f538d") if self._selected else ("gray75", "gray20")
        self.configure(fg_color=color)
        self._on_select(self._voice, self._selected)

    def deselect(self):
        self._selected = False
        self.configure(fg_color=("gray75", "gray20"))


class VoicePage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        self._selected_voices: list[dict] = []
        self._voice_cards: list[VoiceCard] = []
        self._el_voices: list[dict] = []

        # ── Text-Eingabe ──────────────────────────────────────────
        ctk.CTkLabel(self, text="Text / Skript", anchor="w").grid(
            row=0, column=0, padx=20, pady=(20, 4), sticky="ew"
        )
        self._text = ctk.CTkTextbox(self, height=80)
        self._text.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")

        # ── Controls ──────────────────────────────────────────────
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.grid(row=2, column=0, padx=20, pady=(0, 6), sticky="ew")

        ctk.CTkLabel(ctrl, text="Provider").grid(row=0, column=0, padx=(0, 6), sticky="w")
        self._provider = ctk.CTkComboBox(
            ctrl, values=_PROVIDERS, width=220, command=self._on_provider_change
        )
        self._provider.set("ElevenLabs")
        self._provider.grid(row=0, column=1, padx=(0, 20))

        # ElevenLabs Modell
        self._model_label = ctk.CTkLabel(ctrl, text="Modell")
        self._model_label.grid(row=0, column=2, padx=(0, 6))
        el_models = [label for _, label in elevenlabs.MODELS]
        self._el_model = ctk.CTkComboBox(ctrl, values=el_models, width=240)
        self._el_model.set(el_models[0])
        self._el_model.grid(row=0, column=3, padx=(0, 20))

        # OpenAI Modell
        oai_models = [label for _, label in openai_tts.MODELS]
        self._oai_model = ctk.CTkComboBox(ctrl, values=oai_models, width=200)
        self._oai_model.set(oai_models[0])

        # HF Modell
        hf_voice_models = [label for _, label in huggingface.VOICE_MODELS]
        self._hf_model = ctk.CTkComboBox(ctrl, values=hf_voice_models, width=220)
        self._hf_model.set(hf_voice_models[0])

        # ── Voice Settings (ElevenLabs) ───────────────────────────
        self._settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._settings_frame.grid(row=3, column=0, padx=20, pady=(0, 6), sticky="ew")
        self._settings_frame.grid_columnconfigure((1, 3, 5, 7), weight=1)
        self._build_settings()

        # ── Voice Browser ─────────────────────────────────────────
        browser_header = ctk.CTkFrame(self, fg_color="transparent")
        browser_header.grid(row=4, column=0, padx=20, pady=(0, 4), sticky="ew")
        ctk.CTkLabel(
            browser_header, text="Stimme wählen (klicken zum Auswählen / Vergleich: bis 3)",
            text_color="gray"
        ).pack(side="left")
        self._load_btn = ctk.CTkButton(
            browser_header, text="Stimmen laden", width=130, command=self._load_voices
        )
        self._load_btn.pack(side="right")

        self._browser = ctk.CTkScrollableFrame(self, height=200)
        self._browser.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="nsew")

        # ── Generate ──────────────────────────────────────────────
        gen_frame = ctk.CTkFrame(self, fg_color="transparent")
        gen_frame.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="e")
        self._gen_status = StatusLabel(gen_frame, text="")
        self._gen_status.pack(side="left", padx=(0, 12))
        self._btn = ctk.CTkButton(
            gen_frame, text="● GENERIEREN", width=160, command=self._generate
        )
        self._btn.pack(side="left")

        # ── Results ───────────────────────────────────────────────
        self._results = ctk.CTkScrollableFrame(self, height=220, label_text="Ergebnisse")
        self._results.grid(row=7, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.grid_rowconfigure(7, weight=1)

        self._on_provider_change("ElevenLabs")

    def _build_settings(self):
        f = self._settings_frame
        self._stab_var = ctk.DoubleVar(value=0.7)
        self._sim_var  = ctk.DoubleVar(value=0.6)
        self._style_var = ctk.DoubleVar(value=0.1)
        self._speed_var = ctk.DoubleVar(value=1.0)

        sliders = [
            ("Stabilität",  self._stab_var,  0.0, 1.0),
            ("Similarity",  self._sim_var,   0.0, 1.0),
            ("Stil",        self._style_var, 0.0, 1.0),
            ("Geschw.",     self._speed_var, 0.25, 4.0),
        ]
        for col, (lbl, var, lo, hi) in enumerate(sliders):
            lbl_w = ctk.CTkLabel(f, text=lbl, font=ctk.CTkFont(size=12))
            lbl_w.grid(row=0, column=col * 2, padx=(12, 4), pady=4, sticky="w")
            val_lbl = ctk.CTkLabel(f, text=f"{var.get():.2f}", width=36)
            val_lbl.grid(row=1, column=col * 2 + 1, padx=(2, 12), pady=4)
            ctk.CTkSlider(
                f, from_=lo, to=hi, variable=var, width=120,
                command=lambda v, vl=val_lbl: vl.configure(text=f"{v:.2f}"),
            ).grid(row=1, column=col * 2, padx=(12, 2), pady=4)

    def _on_provider_change(self, value: str):
        # Show/hide provider-specific widgets
        for w in [self._model_label, self._el_model]:
            if "ElevenLabs" in value:
                w.grid()
            else:
                w.grid_remove()

        if "OpenAI" in value:
            self._oai_model.grid(row=0, column=3, padx=(0, 20))
            self._hf_model.grid_remove()
        elif "Hugging Face" in value:
            self._hf_model.grid(row=0, column=3, padx=(0, 20))
            self._oai_model.grid_remove()
        else:
            self._oai_model.grid_remove()
            self._hf_model.grid_remove()

        show_settings = "ElevenLabs" in value
        if show_settings:
            self._settings_frame.grid()
        else:
            self._settings_frame.grid_remove()

        # Show/hide voice browser load button
        if "ElevenLabs" in value or "OpenAI" in value:
            self._load_btn.configure(state="normal")
        elif not value:
            self._load_btn.configure(state="disabled")

        self._clear_browser()
        if "OpenAI" in value:
            self._load_openai_voices()

    def _clear_browser(self):
        for w in self._browser.winfo_children():
            w.destroy()
        self._voice_cards.clear()
        self._selected_voices.clear()

    def _load_voices(self):
        provider = self._provider.get()
        self._clear_browser()

        if "OpenAI" in provider:
            self._load_openai_voices()
        elif "ElevenLabs" in provider:
            self._load_btn.configure(state="disabled", text="Lade…")
            threading.Thread(target=self._fetch_el_voices, daemon=True).start()

    def _load_openai_voices(self):
        self._clear_browser()
        voices = openai_tts.get_voices()
        self._populate_browser([
            {"voice_id": v["id"], "name": v["name"],
             "labels": {"description": v["desc"]}}
            for v in voices
        ], cols=3)

    def _fetch_el_voices(self):
        try:
            voices = elevenlabs.get_voices()
            self.after(0, lambda: self._populate_browser(voices, cols=4))
        except Exception as e:
            self.after(0, lambda: self._gen_status.err(f"Voices: {e}"))
        finally:
            self.after(0, lambda: self._load_btn.configure(state="normal", text="Stimmen laden"))

    def _populate_browser(self, voices: list[dict], cols: int = 4):
        self._el_voices = voices
        for i, v in enumerate(voices):
            card = VoiceCard(
                self._browser, voice=v, on_select=self._on_voice_select,
                fg_color=("gray75", "gray20"),
            )
            card.grid(row=i // cols, column=i % cols, padx=6, pady=6)
            self._voice_cards.append(card)

    def _on_voice_select(self, voice: dict, selected: bool):
        if selected:
            if len(self._selected_voices) >= 3:
                # Deselect oldest
                oldest = self._selected_voices.pop(0)
                for card in self._voice_cards:
                    if card._voice.get("voice_id") == oldest.get("voice_id"):
                        card.deselect()
                        break
            self._selected_voices.append(voice)
        else:
            self._selected_voices = [
                v for v in self._selected_voices
                if v.get("voice_id") != voice.get("voice_id")
            ]

        n = len(self._selected_voices)
        if n == 0:
            self._btn.configure(text="● GENERIEREN")
        elif n == 1:
            self._btn.configure(text=f"● GENERIEREN ({self._selected_voices[0]['name']})")
        else:
            self._btn.configure(text=f"● {n} STIMMEN VERGLEICHEN")

    def _generate(self):
        text = self._text.get("1.0", "end").strip()
        if not text:
            self._gen_status.err("Text leer")
            return

        voices_to_gen = self._selected_voices if self._selected_voices else [None]
        provider = self._provider.get()

        self._btn.configure(state="disabled")
        self._gen_status.info("Generiere…")
        for w in self._results.winfo_children():
            w.destroy()

        threading.Thread(
            target=self._run, args=(text, provider, voices_to_gen), daemon=True
        ).start()

    def _run(self, text: str, provider: str, voices: list):
        errors = []
        for voice in voices:
            try:
                if "ElevenLabs" in provider:
                    vid = voice["voice_id"] if voice else "21m00Tcm4TlvDq8ikWAM"
                    model_label = self._el_model.get()
                    model_id = next(
                        (m for m, l in elevenlabs.MODELS if l == model_label),
                        "eleven_multilingual_v2",
                    )
                    data, ext = elevenlabs.generate_tts(
                        text, vid, model_id=model_id,
                        stability=self._stab_var.get(),
                        similarity=self._sim_var.get(),
                        style=self._style_var.get(),
                        speed=self._speed_var.get(),
                    )
                    label = voice["name"] if voice else "ElevenLabs"

                elif "OpenAI" in provider:
                    vid = voice["voice_id"] if voice else "alloy"
                    model_label = self._oai_model.get()
                    model_id = next(
                        (m for m, l in openai_tts.MODELS if l == model_label), "tts-1"
                    )
                    data, ext = openai_tts.generate_tts(
                        text, vid, model=model_id, speed=self._speed_var.get()
                    )
                    label = voice["name"] if voice else vid

                elif "Bark" in provider:
                    data, ext = huggingface.generate_tts(text, "suno/bark")
                    label = "Bark"

                else:  # MMS
                    data, ext = huggingface.generate_tts(text, "facebook/mms-tts-eng")
                    label = "MMS TTS"

                self.after(0, lambda d=data, e=ext, l=label: self._add_card(d, e, l))

            except Exception as ex:
                errors.append(str(ex))

        def finish():
            self._btn.configure(state="normal")
            if errors:
                self._gen_status.err(errors[0])
            else:
                n = len(voices)
                self._gen_status.ok(f"{n} Stimme(n) generiert")

        self.after(0, finish)

    def _add_card(self, data: bytes, ext: str, label: str):
        card = ResultCard(self._results, label=label, audio_bytes=data, ext=ext)
        card.pack(fill="x", padx=4, pady=4)
