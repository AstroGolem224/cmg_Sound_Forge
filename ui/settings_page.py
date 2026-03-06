import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from core import config
from api import elevenlabs, openai_tts, huggingface
from ui.widgets import StatusLabel


class SettingsPage(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(1, weight=1)

        row = 0

        # ── API Keys ──────────────────────────────────────────────
        ctk.CTkLabel(self, text="API Keys", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=row, column=0, columnspan=3, pady=(20, 10), padx=20, sticky="w"
        )
        row += 1

        cfg = config.load()
        keys = cfg.get("api_keys", {})

        self._el_entry, self._el_status = self._add_key_row(
            row, "ElevenLabs", keys.get("elevenlabs", ""),
            "https://elevenlabs.io — SFX + Stimmen",
            lambda: self._test("elevenlabs"),
        )
        row += 2

        self._oai_entry, self._oai_status = self._add_key_row(
            row, "OpenAI", keys.get("openai", ""),
            "https://platform.openai.com — TTS",
            lambda: self._test("openai"),
        )
        row += 2

        self._hf_entry, self._hf_status = self._add_key_row(
            row, "Hugging Face", keys.get("huggingface", ""),
            "https://huggingface.co/settings/tokens — kostenlos",
            lambda: self._test("huggingface"),
        )
        row += 2

        ctk.CTkButton(self, text="Alle Keys speichern", command=self._save_all).grid(
            row=row, column=0, columnspan=3, pady=16, padx=20, sticky="w"
        )
        row += 1

        # ── Output ────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Ausgabe", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=row, column=0, columnspan=3, pady=(20, 10), padx=20, sticky="w"
        )
        row += 1

        ctk.CTkLabel(self, text="Standard-Ordner").grid(
            row=row, column=0, padx=20, pady=6, sticky="w"
        )
        self._folder_entry = ctk.CTkEntry(self, width=340)
        self._folder_entry.insert(0, cfg.get("output_folder", str(Path.home() / "Desktop")))
        self._folder_entry.grid(row=row, column=1, padx=6, pady=6, sticky="ew")
        ctk.CTkButton(self, text="Durchsuchen", width=110, command=self._pick_folder).grid(
            row=row, column=2, padx=(0, 20), pady=6
        )
        row += 1

        ctk.CTkLabel(self, text="Standard-Format").grid(
            row=row, column=0, padx=20, pady=6, sticky="w"
        )
        self._fmt_var = ctk.StringVar(value=cfg.get("default_format", "mp3").upper())
        ctk.CTkSegmentedButton(self, values=["MP3", "WAV"], variable=self._fmt_var).grid(
            row=row, column=1, padx=6, pady=6, sticky="w"
        )
        row += 1

        ctk.CTkButton(self, text="Ausgabe-Einstellungen speichern", command=self._save_output).grid(
            row=row, column=0, columnspan=3, pady=16, padx=20, sticky="w"
        )
        row += 1

        # ── Info ──────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="Sound Forge v0.1  •  Python + CustomTkinter",
            text_color="gray",
            font=ctk.CTkFont(size=11),
        ).grid(row=row, column=0, columnspan=3, pady=(30, 10), padx=20, sticky="w")

    def _add_key_row(self, row: int, label: str, value: str, hint: str, test_cmd):
        ctk.CTkLabel(self, text=label, font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, padx=20, pady=(8, 2), sticky="w"
        )
        status = StatusLabel(self, text="")
        status.grid(row=row, column=1, columnspan=2, padx=6, pady=(8, 2), sticky="w")

        entry = ctk.CTkEntry(self, show="•", width=340, placeholder_text=f"{label} API-Key")
        if value:
            entry.insert(0, value)
        entry.grid(row=row + 1, column=0, columnspan=2, padx=20, pady=(0, 4), sticky="ew")

        btn = ctk.CTkButton(self, text="Testen", width=90, command=test_cmd)
        btn.grid(row=row + 1, column=2, padx=(0, 20), pady=(0, 4))

        ctk.CTkLabel(self, text=hint, text_color="gray", font=ctk.CTkFont(size=11)).grid(
            row=row + 1, column=0, columnspan=2, padx=24, sticky="w"
        )
        # hint overlaps — place below
        ctk.CTkLabel(self, text=hint, text_color="gray", font=ctk.CTkFont(size=11)).grid(
            row=row + 2, column=0, columnspan=2, padx=24, pady=(0, 2), sticky="w"
        )
        return entry, status

    def _test(self, provider: str):
        entry_map = {
            "elevenlabs": self._el_entry,
            "openai": self._oai_entry,
            "huggingface": self._hf_entry,
        }
        status_map = {
            "elevenlabs": self._el_status,
            "openai": self._oai_status,
            "huggingface": self._hf_status,
        }
        entry = entry_map[provider]
        status = status_map[provider]

        key = entry.get().strip()
        if not key:
            status.err("Kein Key eingegeben")
            return

        config.set_key(provider, key)
        status.info("Teste…")

        def run():
            check_fns = {
                "elevenlabs": elevenlabs.check_key,
                "openai": openai_tts.check_key,
                "huggingface": huggingface.check_key,
            }
            result = check_fns[provider]()
            if result.startswith("OK"):
                self.after(0, lambda: status.ok(result))
            else:
                self.after(0, lambda: status.err(result))

        threading.Thread(target=run, daemon=True).start()

    def _save_all(self):
        cfg = config.load()
        cfg["api_keys"]["elevenlabs"] = self._el_entry.get().strip()
        cfg["api_keys"]["openai"] = self._oai_entry.get().strip()
        cfg["api_keys"]["huggingface"] = self._hf_entry.get().strip()
        config.save(cfg)
        self._el_status.ok("Gespeichert")
        self._oai_status.ok("Gespeichert")
        self._hf_status.ok("Gespeichert")

    def _pick_folder(self):
        folder = filedialog.askdirectory(initialdir=self._folder_entry.get())
        if folder:
            self._folder_entry.delete(0, "end")
            self._folder_entry.insert(0, folder)

    def _save_output(self):
        cfg = config.load()
        cfg["output_folder"] = self._folder_entry.get().strip()
        cfg["default_format"] = self._fmt_var.get().lower()
        config.save(cfg)
