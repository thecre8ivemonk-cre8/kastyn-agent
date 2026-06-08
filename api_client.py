import httpx
from typing import Optional
from config import API_URL, API_TOKEN, STATION_ID
from rich.console import Console

console = Console()

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}

def submit_track(
    file_path: str,
    file_hash: str,
    duration: float,
    fingerprint: str,
    metadata: dict
) -> Optional[dict]:
    """Submit track fingerprint and metadata to Kastyn API."""
    try:
        payload = {
            "station_id": STATION_ID,
            "file_path": file_path,
            "file_hash": file_hash,
            "duration": duration,
            "fingerprint": fingerprint,
            "original_title": metadata.get("title"),
            "original_artist": metadata.get("artist"),
            "original_album": metadata.get("album"),
            "original_year": metadata.get("year"),
            "original_genre": metadata.get("genre"),
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(f"{API_URL}/tracks/submit", json=payload, headers=HEADERS)
            if response.status_code in (200, 201):
                return response.json()
            else:
                console.print(f"[red]API error {response.status_code}: {response.text}[/red]")
                return None
    except Exception as e:
        console.print(f"[red]API connection error: {e}[/red]")
        return None

def get_track_status(track_id: str) -> Optional[dict]:
    """Poll track correction status from API."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{API_URL}/tracks/{track_id}", headers=HEADERS)
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        console.print(f"[red]API error: {e}[/red]")
        return None
