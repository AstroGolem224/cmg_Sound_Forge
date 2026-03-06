from pathlib import Path
from tkinter import filedialog
from core.config import load, save


def save_audio(audio_bytes: bytes, default_name: str, ext: str = "mp3") -> str | None:
    cfg = load()
    initial_dir = cfg.get("output_folder", str(Path.home() / "Desktop"))
    ext = ext.lower().lstrip(".")

    filepath = filedialog.asksaveasfilename(
        initialdir=initial_dir,
        initialfile=f"{default_name}.{ext}",
        defaultextension=f".{ext}",
        filetypes=[
            (f"{ext.upper()} Audio", f"*.{ext}"),
            ("Alle Dateien", "*.*"),
        ],
    )
    if not filepath:
        return None

    with open(filepath, "wb") as f:
        f.write(audio_bytes)

    cfg["output_folder"] = str(Path(filepath).parent)
    save(cfg)
    return filepath
