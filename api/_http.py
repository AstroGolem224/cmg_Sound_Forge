"""Gemeinsame HTTP-Fehlerbehandlung für alle API-Clients."""
import httpx


def raise_for_status(r: httpx.Response):
    if r.is_success:
        return
    code = r.status_code
    if code == 401:
        raise RuntimeError("Ungültiger API-Key (401)")
    if code == 403:
        raise RuntimeError("Kein Zugriff — Tier oder Quota-Limit (403)")
    if code == 429:
        raise RuntimeError("Rate-Limit erreicht (429) — bitte kurz warten und erneut versuchen")
    if code == 500:
        raise RuntimeError("Server-Fehler beim Provider (500) — bitte später erneut versuchen")
    if code == 503:
        raise RuntimeError("Provider nicht erreichbar (503) — bitte später erneut versuchen")
    # Fallback: kurze Meldung ohne httpx-Kauderwelsch
    try:
        detail = r.json().get("detail") or r.json().get("error", {}).get("message", "")
    except Exception:
        detail = ""
    raise RuntimeError(f"HTTP {code}{': ' + detail if detail else ''}")
