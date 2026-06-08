import os
import hashlib
from pathlib import Path
from config import LIBRARY_PATH, SUPPORTED_EXTENSIONS
from rich.console import Console

console = Console()

def get_file_hash(filepath: str) -> str:
    """Generate MD5 hash of file for deduplication."""
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def scan_library(path: str = None) -> list:
    """Recursively scan library path for audio files."""
    library = path or LIBRARY_PATH
    if not library:
        console.print("[red]Error: No library path set.[/red]")
        return []

    audio_files = []
    library_path = Path(library)

    if not library_path.exists():
        console.print(f"[red]Error: Library path does not exist: {library}[/red]")
        return []

    console.print(f"[cyan]Scanning library: {library}[/cyan]")

    for ext in SUPPORTED_EXTENSIONS:
        files = list(library_path.rglob(f"*{ext}"))
        audio_files.extend(files)

    console.print(f"[green]Found {len(audio_files)} audio files[/green]")
    return audio_files
