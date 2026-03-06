import threading
import customtkinter as ctk
from core import audio, export


class ResultCard(ctk.CTkFrame):
    """Zeigt ein generiertes Audio-Result an: Play, Dateiname, Speichern."""

    def __init__(self, master, label: str, audio_bytes: bytes, ext: str = "mp3", **kwargs):
        super().__init__(master, corner_radius=8, **kwargs)
        self._bytes = audio_bytes
        self._ext = ext
        self._playing = False

        self.grid_columnconfigure(1, weight=1)

        # Play/Stop Button
        self._btn_play = ctk.CTkButton(
            self, text="▶", width=40, command=self._toggle_play
        )
        self._btn_play.grid(row=0, column=0, padx=(10, 6), pady=10, rowspan=2)

        # Label
        self._lbl = ctk.CTkLabel(self, text=label, anchor="w", font=ctk.CTkFont(size=13))
        self._lbl.grid(row=0, column=1, padx=4, pady=(10, 2), sticky="ew")

        # Dateiname-Eingabe
        default_name = label.lower().replace(" ", "_").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
        self._name_entry = ctk.CTkEntry(self, placeholder_text="Dateiname", width=200)
        self._name_entry.insert(0, default_name)
        self._name_entry.grid(row=1, column=1, padx=4, pady=(0, 10), sticky="w")

        # Format + Speichern
        frame_right = ctk.CTkFrame(self, fg_color="transparent")
        frame_right.grid(row=0, column=2, rowspan=2, padx=10, pady=8)

        self._fmt_var = ctk.StringVar(value=ext.upper())
        ctk.CTkLabel(frame_right, text=f".{ext}", text_color="gray").pack(side="top", pady=(0, 4))

        ctk.CTkButton(
            frame_right, text="SPEICHERN", width=100, command=self._save
        ).pack(side="top")

    def _toggle_play(self):
        if audio.is_playing():
            audio.stop()
            self._btn_play.configure(text="▶")
            self._playing = False
        else:
            self._btn_play.configure(text="■")
            self._playing = True
            audio.play_bytes(self._bytes, self._ext)
            self.after(200, self._check_playing)

    def _check_playing(self):
        if self._playing and not audio.is_playing():
            self._btn_play.configure(text="▶")
            self._playing = False
        elif self._playing:
            self.after(200, self._check_playing)

    def _save(self):
        name = self._name_entry.get().strip() or "sound"
        threading.Thread(
            target=lambda: export.save_audio(self._bytes, name, self._ext),
            daemon=True,
        ).start()


class StatusLabel(ctk.CTkLabel):
    """Zeigt Erfolg (grün) oder Fehler (rot) an."""

    def ok(self, msg: str):
        self.configure(text=f"✓ {msg}", text_color="#4CAF50")

    def err(self, msg: str):
        self.configure(text=f"✗ {msg}", text_color="#F44336")

    def info(self, msg: str):
        self.configure(text=msg, text_color="gray")

    def clear(self):
        self.configure(text="")
