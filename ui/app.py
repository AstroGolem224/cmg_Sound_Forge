import customtkinter as ctk
from core import audio
from ui.sfx_page import SFXPage
from ui.voice_page import VoicePage
from ui.settings_page import SettingsPage


class SoundForgeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sound Forge")
        self.geometry("1100x780")
        self.minsize(900, 650)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        if not audio.init():
            ctk.CTkLabel(
                self,
                text="⚠ Audio-Device nicht verfügbar — Playback deaktiviert",
                text_color="#F44336",
            ).grid(row=0, column=0, pady=(6, 0))

        tabs = ctk.CTkTabview(self)
        tabs.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)

        tabs.add("SFX")
        tabs.add("Stimmen")
        tabs.add("Einstellungen")

        SFXPage(tabs.tab("SFX")).pack(fill="both", expand=True)
        VoicePage(tabs.tab("Stimmen")).pack(fill="both", expand=True)
        SettingsPage(tabs.tab("Einstellungen")).pack(fill="both", expand=True)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        audio.cleanup()
        self.destroy()
