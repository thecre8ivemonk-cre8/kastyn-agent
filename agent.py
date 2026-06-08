import click
import time
import schedule
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from scanner import scan_library
from fingerprinter import get_fingerprint, get_metadata, write_metadata
from api_client import submit_track, get_track_status
from scanner import get_file_hash

console = Console()

def process_library(library_path: str = None, write_back: bool = False):
    """Main processing loop - scan, fingerprint, submit, write back."""
    console.print("\n[bold cyan]Kastyn Agent — Starting library scan[/bold cyan]\n")

    files = scan_library(library_path)
    if not files:
        return

    results = {"submitted": 0, "corrected": 0, "failed": 0, "skipped": 0}
    track_ids = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing tracks...", total=len(files))

        for filepath in files:
            fp_str = str(filepath)
            progress.update(task, description=f"[cyan]{filepath.name[:40]}[/cyan]")

            # Get fingerprint
            fp_result = get_fingerprint(fp_str)
            if not fp_result:
                results["failed"] += 1
                progress.advance(task)
                continue

            duration, fingerprint = fp_result
            file_hash = get_file_hash(fp_str)
            metadata = get_metadata(fp_str)

            # Submit to API
            response = submit_track(fp_str, file_hash, duration, fingerprint, metadata)
            if response:
                results["submitted"] += 1
                track_ids.append((fp_str, response.get("id")))
            else:
                results["failed"] += 1

            progress.advance(task)

    # Poll for corrections
    if track_ids:
        console.print(f"\n[cyan]Waiting for corrections on {len(track_ids)} tracks...[/cyan]")
        time.sleep(5)

        corrected_tracks = []
        for filepath, track_id in track_ids:
            if not track_id:
                continue
            status = get_track_status(track_id)
            if status and status.get("status") == "corrected":
                corrected_tracks.append((filepath, status))
                results["corrected"] += 1

        # Write corrections back to files
        if write_back and corrected_tracks:
            console.print(f"\n[green]Writing corrections to {len(corrected_tracks)} files...[/green]")
            for filepath, track_data in corrected_tracks:
                corrections = track_data.get("corrected", {})
                if write_metadata(filepath, corrections):
                    console.print(f"[green]✓[/green] {Path(filepath).name}")
                else:
                    console.print(f"[red]✗[/red] {Path(filepath).name}")

    # Summary table
    table = Table(title="\nKastyn Scan Summary", style="cyan")
    table.add_column("Result", style="bold")
    table.add_column("Count")
    table.add_row("Submitted", str(results["submitted"]))
    table.add_row("Corrected", str(results["corrected"]))
    table.add_row("Failed", str(results["failed"]))
    console.print(table)

@click.group()
def cli():
    """Kastyn local agent — broadcast metadata cleanup."""
    pass

@cli.command()
@click.option("--path", "-p", default=None, help="Path to music library")
@click.option("--write-back", "-w", is_flag=True, default=False, help="Write corrections back to files")
def scan(path, write_back):
    """Scan library and submit tracks for metadata correction."""
    process_library(path, write_back)

@cli.command()
@click.option("--path", "-p", default=None, help="Path to music library")
@click.option("--write-back", "-w", is_flag=True, default=False, help="Write corrections back to files")
@click.option("--interval", "-i", default=60, help="Scan interval in minutes")
def watch(path, write_back, interval):
    """Watch library and scan on a schedule."""
    console.print(f"[cyan]Watching library every {interval} minutes...[/cyan]")
    process_library(path, write_back)
    schedule.every(interval).minutes.do(process_library, path, write_back)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    cli()
