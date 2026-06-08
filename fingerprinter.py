import subprocess
import mutagen
from typing import Optional
from rich.console import Console

console = Console()

def get_fingerprint(filepath: str) -> Optional[tuple]:
    """Generate AcoustID fingerprint using fpcalc binary."""
    try:
        # Use default output (DURATION and FINGERPRINT on separate lines)
        result = subprocess.run(
            ["fpcalc", filepath],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            console.print(f"[yellow]fpcalc error: {result.stderr}[/yellow]")
            return None

        duration = None
        fingerprint = None

        for line in result.stdout.strip().split("\n"):
            if line.startswith("DURATION="):
                duration = float(line.split("=", 1)[1])
            elif line.startswith("FINGERPRINT="):
                fingerprint = line.split("=", 1)[1]

        if duration and fingerprint:
            return duration, fingerprint

        console.print(f"[yellow]Could not parse fpcalc output for {filepath}[/yellow]")
        return None

    except subprocess.TimeoutExpired:
        console.print(f"[yellow]fpcalc timeout for {filepath}[/yellow]")
        return None
    except Exception as e:
        console.print(f"[yellow]Fingerprint error for {filepath}: {e}[/yellow]")
        return None

def get_metadata(filepath: str) -> dict:
    """Extract existing ID3/metadata tags from audio file."""
    meta = {
        "title": None,
        "artist": None,
        "album": None,
        "year": None,
        "genre": None,
    }
    try:
        audio = mutagen.File(filepath, easy=True)
        if audio:
            meta["title"] = str(audio.get("title", [None])[0]) if audio.get("title") else None
            meta["artist"] = str(audio.get("artist", [None])[0]) if audio.get("artist") else None
            meta["album"] = str(audio.get("album", [None])[0]) if audio.get("album") else None
            meta["year"] = str(audio.get("date", [None])[0]) if audio.get("date") else None
            meta["genre"] = str(audio.get("genre", [None])[0]) if audio.get("genre") else None
    except Exception as e:
        console.print(f"[yellow]Metadata read error for {filepath}: {e}[/yellow]")
    return meta

def write_metadata(filepath: str, corrections: dict) -> bool:
    """Write corrected metadata back to audio file."""
    try:
        audio = mutagen.File(filepath, easy=True)
        if not audio:
            return False
        if corrections.get("title"):
            audio["title"] = corrections["title"]
        if corrections.get("artist"):
            audio["artist"] = corrections["artist"]
        if corrections.get("album"):
            audio["album"] = corrections["album"]
        if corrections.get("year"):
            audio["date"] = corrections["year"]
        if corrections.get("genre"):
            audio["genre"] = corrections["genre"]
        audio.save()
        return True
    except Exception as e:
        console.print(f"[red]Metadata write error for {filepath}: {e}[/red]")
        return False
