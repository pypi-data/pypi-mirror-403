"""Main CLI entry point for fso (File System Organizer).

Provides commands: clean, watch, undo
"""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table

from . import __version__
from .config import Config, get_user_config_path, load_config
from .core import OrganizeResult, organize_directory, scan_directory, undo_last_operation
from .utils import HistoryManager

# Initialize Typer app
app = typer.Typer(
    name="fso",
    help="fso (File System Organizer) - Automatically organize your files into categorized folders.",
    add_completion=False,
)

# Rich console for pretty output
console = Console()
error_console = Console(stderr=True)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"fso v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version", "-v",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """fso (File System Organizer) - A CLI tool for automatic file organization."""
    pass


@app.command()
def clean(
    path: Annotated[
        Path,
        typer.Argument(
            help="Directory to organize.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", "-n",
            help="Show what would be done without actually moving files.",
        ),
    ] = False,
    config_file: Annotated[
        Optional[Path],
        typer.Option(
            "--config", "-c",
            help="Path to custom config file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            help="Show detailed output.",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet", "-q",
            help="Suppress all output except errors.",
        ),
    ] = False,
) -> None:
    """Organize files in a directory into categorized folders.
    
    Scans the specified directory and moves files into subfolders
    based on their extensions (e.g., .jpg -> Images/).
    """
    # Load configuration
    try:
        config = load_config(config_file)
    except FileNotFoundError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    
    # Scan directory first to show preview
    try:
        files = scan_directory(path, config)
    except (FileNotFoundError, NotADirectoryError) as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    
    if not files:
        if not quiet:
            console.print("[yellow]No files to organize.[/yellow]")
        raise typer.Exit(0)
    
    if dry_run and not quiet:
        console.print("[cyan]Dry run mode - no files will be moved[/cyan]\n")
    
    # Initialize history manager (not used in dry run)
    history_manager = None if dry_run else HistoryManager()
    
    # Track progress
    result: OrganizeResult
    
    if quiet:
        # Silent mode - no progress bar
        result = organize_directory(path, config, dry_run, history_manager)
    else:
        # Show progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[cyan]{task.fields[filename]}[/cyan]"),
            console=console,
        ) as progress:
            task = progress.add_task(
                "Organizing files...",
                total=len(files),
                filename="",
            )
            
            def update_progress(src: Path, dest: Path, current: int, total: int) -> None:
                progress.update(task, completed=current, filename=src.name)
            
            result = organize_directory(
                path, config, dry_run, history_manager, update_progress
            )
    
    # Display results
    if not quiet:
        display_results(result, config, dry_run, verbose)
    
    # Exit with error code if there were errors
    if result.errors:
        raise typer.Exit(1)


def display_results(
    result: OrganizeResult,
    config: Config,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Display the results of an organize operation."""
    console.print()
    
    if result.files_moved == 0 and result.files_skipped == 0:
        console.print("[yellow]No files were organized.[/yellow]")
        return
    
    # Summary table
    action_word = "Would move" if dry_run else "Moved"
    
    # Group moves by destination folder
    folder_counts: dict[str, int] = {}
    for move in result.moves:
        dest_path = Path(move.new_path)
        folder_name = dest_path.parent.name
        folder_counts[folder_name] = folder_counts.get(folder_name, 0) + 1
    
    if folder_counts:
        table = Table(title=f"{action_word} Files Summary", show_header=True)
        table.add_column("Folder", style="cyan")
        table.add_column("Files", justify="right", style="green")
        
        for folder, count in sorted(folder_counts.items()):
            table.add_row(folder, str(count))
        
        table.add_section()
        table.add_row("[bold]Total[/bold]", f"[bold]{result.files_moved}[/bold]")
        
        console.print(table)
    
    # Verbose: show individual files
    if verbose and result.moves:
        console.print("\n[bold]Details:[/bold]")
        for move in result.moves:
            src = Path(move.original_path).name
            dest = Path(move.new_path)
            dest_folder = dest.parent.name
            console.print(f"  {src} -> {dest_folder}/")
    
    # Show skipped files
    if result.files_skipped > 0:
        console.print(f"\n[dim]Skipped {result.files_skipped} files (already in correct folder)[/dim]")
    
    # Show errors
    if result.errors:
        console.print("\n[red]Errors:[/red]")
        for error in result.errors:
            console.print(f"  [red]*[/red] {error}")
    
    # Show new folders created
    if result.folders_created and not dry_run:
        console.print(f"\n[dim]Created {len(result.folders_created)} new folder(s)[/dim]")


@app.command()
def undo() -> None:
    """Undo the last clean operation.
    
    Moves all files back to their original locations and removes
    any empty folders that were created.
    """
    history_manager = HistoryManager()
    
    last_entry = history_manager.get_last_entry()
    if not last_entry:
        console.print("[yellow]Nothing to undo.[/yellow]")
        raise typer.Exit(0)
    
    # Show what will be undone
    console.print(f"[cyan]Undoing operation from {last_entry.timestamp}[/cyan]")
    console.print(f"[dim]Target directory: {last_entry.target_directory}[/dim]")
    console.print(f"[dim]Files to restore: {len(last_entry.moves)}[/dim]\n")
    
    # Confirm
    if not typer.confirm("Proceed with undo?"):
        console.print("[yellow]Cancelled.[/yellow]")
        raise typer.Exit(0)
    
    # Perform undo
    result = undo_last_operation(history_manager)
    
    if result is None:
        console.print("[red]Failed to undo operation.[/red]")
        raise typer.Exit(1)
    
    # Display results
    console.print()
    console.print(f"[green]OK[/green] Restored {result.files_moved} file(s)")
    
    if result.folders_created:
        console.print(f"[green]OK[/green] Removed {len(result.folders_created)} empty folder(s)")
    
    if result.errors:
        console.print("\n[red]Errors:[/red]")
        for error in result.errors:
            console.print(f"  [red]*[/red] {error}")
        raise typer.Exit(1)


@app.command()
def watch(
    path: Annotated[
        Path,
        typer.Argument(
            help="Directory to watch for new files.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    config_file: Annotated[
        Optional[Path],
        typer.Option(
            "--config", "-c",
            help="Path to custom config file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ] = None,
    delay: Annotated[
        float,
        typer.Option(
            "--delay", "-d",
            help="Seconds to wait before organizing a new file (for downloads to complete).",
            min=0.1,
            max=60.0,
        ),
    ] = 1.0,
) -> None:
    """Watch a directory and automatically organize new files.
    
    Monitors the specified directory for new files and moves them
    into categorized subfolders as they appear. Press Ctrl+C to stop.
    """
    from .observers import DirectoryWatcher
    
    # Load configuration
    try:
        config = load_config(config_file)
    except FileNotFoundError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    
    # Initialize history manager
    history_manager = HistoryManager()
    
    # Callback for when files are organized
    def on_file_organized(source: Path, destination: Path) -> None:
        dest_folder = destination.parent.name
        console.print(f"[green]->[/green] {source.name} [dim]moved to[/dim] [cyan]{dest_folder}/[/cyan]")
    
    # Create and start watcher
    watcher = DirectoryWatcher(
        watch_path=path,
        config=config,
        history_manager=history_manager,
        on_file_organized=on_file_organized,
        delay=delay,
    )
    
    console.print(f"[cyan]Watching:[/cyan] {path}")
    console.print(f"[dim]Delay: {delay}s | Press Ctrl+C to stop[/dim]\n")
    
    try:
        watcher.start()
        watcher.wait()
    except KeyboardInterrupt:
        pass
    finally:
        watcher.stop()
        console.print("\n[yellow]Stopped watching.[/yellow]")


@app.command()
def config(
    show: Annotated[
        bool,
        typer.Option(
            "--show", "-s",
            help="Show current configuration.",
        ),
    ] = False,
    path: Annotated[
        bool,
        typer.Option(
            "--path", "-p",
            help="Show config file path.",
        ),
    ] = False,
) -> None:
    """Show or manage configuration.
    
    By default, shows the user config file location.
    """
    if show:
        # Show current configuration
        cfg = load_config()
        
        table = Table(title="Current Configuration", show_header=True)
        table.add_column("Folder", style="cyan")
        table.add_column("Extensions", style="green")
        
        for folder, extensions in cfg.rules.items():
            table.add_row(folder, ", ".join(extensions))
        
        console.print(table)
        console.print(f"\n[dim]Default folder: {cfg.default_folder}[/dim]")
        console.print(f"[dim]Exclude patterns: {', '.join(cfg.exclude_patterns)}[/dim]")
    elif path:
        config_path = get_user_config_path()
        console.print(f"Config file: {config_path}")
        if config_path.exists():
            console.print("[green]OK File exists[/green]")
        else:
            console.print("[yellow]File does not exist (using defaults)[/yellow]")
    else:
        # Default: show path
        config_path = get_user_config_path()
        console.print(f"User config location: [cyan]{config_path}[/cyan]")
        if not config_path.exists():
            console.print("[dim]No user config found. Using default settings.[/dim]")
            console.print(f"[dim]Copy the default config.yaml to this location to customize.[/dim]")


if __name__ == "__main__":
    app()
