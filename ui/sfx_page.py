import threading
import customtkinter as ctk
from api import elevenlabs, huggingface
from ui.widgets import ResultCard, StatusLabel

_TAGS = {
    "Explosion":  "powerful explosion with debris and deep rumble",
    "UI-Click":   "short clean UI button click, satisfying",
    "Footstep":   "single footstep on stone floor",
    "Magic":      "magical sparkle and shimmer with whirlwind",
    "Impact":     "heavy blunt impact hit with deep thud",
    "Sword":      "metal sword clash and scrape",
    "Ambient":    "peaceful forest ambient with birds and wind",
    "Rain":       "rain falling on leaves, calming",
    "Fire":       "crackling fire with embers",
    "Laser":      "sci-fi laser shot with echo",
    "Pickup":     "small item pickup chime, 8-bit style",
    "Door":       "wooden door creaking open slowly",
}

_PROVIDERS = ["ElevenLabs", "Hugging Face — AudioGen", "Hugging Face — AudioLDM2"]


class SFXPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self._audio_cache: list[tuple[bytes, str]] = []

        # ── Prompt ───────────────────────────────────────────────
        ctk.CTkLabel(self, text="Beschreibe den Sound", anchor="w").grid(
            row=0, column=0, padx=20, pady=(20, 4), sticky="ew"
        )
        self._prompt = ctk.CTkEntry(
            self, placeholder_text='z.B. "metal sword clash with reverb"', height=40
        )
        self._prompt.grid(row=1, column=0, padx=20, pady=(0, 8), sticky="ew")

        # ── Quick Tags ────────────────────────────────────────────
        tag_frame = ctk.CTkFrame(self, fg_color="transparent")
        tag_frame.grid(row=2, column=0, padx=20, pady=(0, 12), sticky="ew")
        for i, tag in enumerate(_TAGS):
            ctk.CTkButton(
                tag_frame,
                text=tag,
                width=90,
                height=28,
                font=ctk.CTkFont(size=12),
                fg_color=("gray75", "gray25"),
                hover_color=("gray65", "gray35"),
                command=lambda t=tag: self._set_tag(t),
            ).grid(row=i // 6, column=i % 6, padx=3, pady=3)

        # ── Controls ──────────────────────────────────────────────
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.grid(row=3, column=0, padx=20, pady=(0, 12), sticky="ew")
        ctrl.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(ctrl, text="Provider").grid(row=0, column=0, padx=(0, 6), pady=4, sticky="w")
        self._provider = ctk.CTkComboBox(ctrl, values=_PROVIDERS, width=240)
        self._provider.set("ElevenLabs")
        self._provider.grid(row=0, column=1, padx=(0, 20), pady=4)

        ctk.CTkLabel(ctrl, text="Dauer (s)").grid(row=0, column=2, padx=(0, 6), pady=4)
        self._dur_var = ctk.DoubleVar(value=3.0)
        self._dur_label = ctk.CTkLabel(ctrl, text="3.0s", width=36)
        dur_slider = ctk.CTkSlider(
            ctrl, from_=0.5, to=22.0, variable=self._dur_var,
            command=lambda v: self._dur_label.configure(text=f"{v:.1f}s"),
            width=160,
        )
        dur_slider.grid(row=0, column=3, padx=4, pady=4, sticky="w")
        self._dur_label.grid(row=0, column=4, padx=(4, 20), pady=4)

        ctk.CTkLabel(ctrl, text="Variationen").grid(row=1, column=0, padx=(0, 6), pady=4, sticky="w")
        self._var_count = ctk.IntVar(value=1)
        for n in (1, 2, 3):
            ctk.CTkRadioButton(ctrl, text=str(n), variable=self._var_count, value=n).grid(
                row=1, column=n, padx=8, pady=4
            )

        # Generieren
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=20, sticky="e")
        self._status = StatusLabel(btn_frame, text="")
        self._status.pack(side="left", padx=(0, 12))
        self._btn = ctk.CTkButton(btn_frame, text="● GENERIEREN", width=160, command=self._generate)
        self._btn.pack(side="left")

        # ── Results ───────────────────────────────────────────────
        ctk.CTkLabel(self, text="Ergebnisse", anchor="w", text_color="gray").grid(
            row=4, column=0, padx=20, pady=(8, 4), sticky="w"
        )
        self._results = ctk.CTkScrollableFrame(self, label_text="")
        self._results.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.grid_rowconfigure(5, weight=1)

    def _set_tag(self, tag: str):
        self._prompt.delete(0, "end")
        self._prompt.insert(0, _TAGS[tag])

    def _generate(self):
        prompt = self._prompt.get().strip()
        if not prompt:
            self._status.err("Prompt leer")
            return

        self._btn.configure(state="disabled")
        self._status.info("Generiere…")

        for w in self._results.winfo_children():
            w.destroy()

        n = self._var_count.get()
        duration = round(self._dur_var.get(), 1)
        provider = self._provider.get()

        threading.Thread(
            target=self._run, args=(prompt, duration, provider, n), daemon=True
        ).start()

    def _run(self, prompt: str, duration: float, provider: str, n: int):
        errors = []
        for i in range(n):
            try:
                if provider == "ElevenLabs":
                    data, ext = elevenlabs.generate_sfx(prompt, duration)
                elif "AudioLDM2" in provider:
                    data, ext = huggingface.generate_sfx(prompt, "cvssp/audioldm2")
                else:
                    data, ext = huggingface.generate_sfx(prompt)

                label = f"Variation {i + 1}" if n > 1 else prompt[:40]
                self.after(0, lambda d=data, e=ext, l=label: self._add_card(d, e, l))

            except Exception as ex:
                errors.append(str(ex))

        def finish():
            self._btn.configure(state="normal")
            if errors:
                self._status.err(errors[0])
            else:
                self._status.ok(f"{n} Sound(s) generiert")

        self.after(0, finish)

    def _add_card(self, data: bytes, ext: str, label: str):
        card = ResultCard(self._results, label=label, audio_bytes=data, ext=ext)
        card.pack(fill="x", padx=4, pady=4)
