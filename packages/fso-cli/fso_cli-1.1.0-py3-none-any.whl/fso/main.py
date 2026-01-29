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
from .config import Config, ConflictStrategy, VALID_CONFLICT_STRATEGIES, get_user_config_path, load_config
from .core import (
    DedupResult,
    OrganizeResult,
    find_duplicates,
    handle_duplicates,
    organize_directory,
    scan_directory,
    undo_last_operation,
    undo_operations,
)
from .utils import format_file_size
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
    on_conflict: Annotated[
        Optional[str],
        typer.Option(
            "--on-conflict",
            help="How to handle filename conflicts: skip, overwrite, or rename (default from config).",
        ),
    ] = None,
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
    
    # Override conflict strategy if specified via CLI
    if on_conflict is not None:
        if on_conflict not in VALID_CONFLICT_STRATEGIES:
            error_console.print(
                f"[red]Error:[/red] Invalid conflict strategy '{on_conflict}'. "
                f"Valid options: {', '.join(VALID_CONFLICT_STRATEGIES)}"
            )
            raise typer.Exit(1)
        config.conflict_strategy = on_conflict  # type: ignore
    
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
def undo(
    list_history: Annotated[
        bool,
        typer.Option(
            "--list", "-l",
            help="Show undo history without performing undo.",
        ),
    ] = False,
    count: Annotated[
        Optional[int],
        typer.Option(
            "--count", "-n",
            help="Number of operations to undo (default: 1).",
            min=1,
        ),
    ] = None,
    all_ops: Annotated[
        bool,
        typer.Option(
            "--all", "-a",
            help="Undo all operations in history.",
        ),
    ] = False,
) -> None:
    """Undo clean operations.
    
    By default, undoes the last operation. Use --count to undo multiple
    operations, --all to undo everything, or --list to view history.
    """
    history_manager = HistoryManager()
    
    # Handle --list flag
    if list_history:
        summaries = history_manager.get_entry_summaries()
        if not summaries:
            console.print("[yellow]No undo history available.[/yellow]")
            raise typer.Exit(0)
        
        table = Table(title="Undo History", show_header=True)
        table.add_column("#", justify="right", style="dim")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Directory")
        table.add_column("Files", justify="right", style="green")
        table.add_column("Folders", justify="right", style="blue")
        
        for summary in summaries:
            table.add_row(
                str(summary["display_index"]),
                summary["timestamp"],
                summary["target_directory"],
                str(summary["file_count"]),
                str(summary["folders_created"]),
            )
        
        console.print(table)
        console.print(f"\n[dim]Total: {len(summaries)} operation(s)[/dim]")
        raise typer.Exit(0)
    
    # Check if there's anything to undo
    if history_manager.entry_count == 0:
        console.print("[yellow]Nothing to undo.[/yellow]")
        raise typer.Exit(0)
    
    # Determine how many operations to undo
    if all_ops:
        undo_count = history_manager.entry_count
    elif count is not None:
        undo_count = min(count, history_manager.entry_count)
    else:
        undo_count = 1
    
    # Show what will be undone
    summaries = history_manager.get_entry_summaries()[:undo_count]
    total_files = sum(s["file_count"] for s in summaries)
    
    if undo_count == 1:
        entry = history_manager.get_last_entry()
        console.print(f"[cyan]Undoing operation from {entry.timestamp}[/cyan]")
        console.print(f"[dim]Target directory: {entry.target_directory}[/dim]")
        console.print(f"[dim]Files to restore: {len(entry.moves)}[/dim]\n")
    else:
        console.print(f"[cyan]Undoing {undo_count} operation(s)[/cyan]")
        console.print(f"[dim]Total files to restore: {total_files}[/dim]\n")
        
        # Show brief summary of each operation
        for summary in summaries:
            console.print(f"  [{summary['display_index']}] {summary['timestamp']} - {summary['file_count']} file(s)")
        console.print()
    
    # Confirm
    if not typer.confirm("Proceed with undo?"):
        console.print("[yellow]Cancelled.[/yellow]")
        raise typer.Exit(0)
    
    # Perform undo
    if undo_count == 1:
        result = undo_last_operation(history_manager)
        if result is None:
            console.print("[red]Failed to undo operation.[/red]")
            raise typer.Exit(1)
        results = [result]
    else:
        results = undo_operations(history_manager, undo_count)
        if not results:
            console.print("[red]Failed to undo operations.[/red]")
            raise typer.Exit(1)
    
    # Display results
    console.print()
    total_restored = sum(r.files_moved for r in results)
    total_folders_removed = sum(len(r.folders_created) for r in results)
    total_errors = sum(len(r.errors) for r in results)
    
    console.print(f"[green]OK[/green] Restored {total_restored} file(s) from {len(results)} operation(s)")
    
    if total_folders_removed > 0:
        console.print(f"[green]OK[/green] Removed {total_folders_removed} empty folder(s)")
    
    if total_errors > 0:
        console.print(f"\n[red]Errors ({total_errors}):[/red]")
        for result in results:
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
    on_conflict: Annotated[
        Optional[str],
        typer.Option(
            "--on-conflict",
            help="How to handle filename conflicts: skip, overwrite, or rename (default from config).",
        ),
    ] = None,
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
    
    # Override conflict strategy if specified via CLI
    if on_conflict is not None:
        if on_conflict not in VALID_CONFLICT_STRATEGIES:
            error_console.print(
                f"[red]Error:[/red] Invalid conflict strategy '{on_conflict}'. "
                f"Valid options: {', '.join(VALID_CONFLICT_STRATEGIES)}"
            )
            raise typer.Exit(1)
        config.conflict_strategy = on_conflict  # type: ignore
    
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


@app.command()
def dedup(
    path: Annotated[
        Path,
        typer.Argument(
            help="Directory to scan for duplicate files.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    action: Annotated[
        str,
        typer.Option(
            "--action", "-a",
            help="How to handle duplicates: report (default), move, or delete.",
        ),
    ] = "report",
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", "-n",
            help="Show what would be done without actually modifying files.",
        ),
    ] = False,
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive", "-i",
            help="Prompt for confirmation on each duplicate group.",
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
) -> None:
    """Find and handle duplicate files.
    
    Scans the specified directory for files with identical content
    using SHA-256 hashing. By default, just reports duplicates.
    Use --action to move or delete duplicates.
    """
    # Validate action
    valid_actions = ("report", "move", "delete")
    if action not in valid_actions:
        error_console.print(
            f"[red]Error:[/red] Invalid action '{action}'. "
            f"Valid options: {', '.join(valid_actions)}"
        )
        raise typer.Exit(1)
    
    # Load configuration
    try:
        cfg = load_config(config_file)
    except FileNotFoundError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    
    if dry_run:
        console.print("[cyan]Dry run mode - no files will be modified[/cyan]\n")
    
    # Find duplicates with progress
    console.print(f"[cyan]Scanning for duplicates in:[/cyan] {path}\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning...", total=None)
        
        def update_progress(phase: str, current: int, total: int) -> None:
            progress.update(task, description=phase, completed=current, total=total)
        
        result = find_duplicates(path, cfg, update_progress)
    
    # Display results
    if not result.groups:
        console.print("[green]No duplicate files found![/green]")
        raise typer.Exit(0)
    
    # Summary table
    table = Table(title="Duplicate Files Found", show_header=True)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Size", justify="right", style="cyan")
    table.add_column("Duplicates", justify="right", style="yellow")
    table.add_column("Wasted", justify="right", style="red")
    table.add_column("Files")
    
    for i, group in enumerate(result.groups, 1):
        # Show first few files
        file_list = [f.name for f in group.files[:3]]
        if len(group.files) > 3:
            file_list.append(f"... +{len(group.files) - 3} more")
        
        table.add_row(
            str(i),
            format_file_size(group.size),
            str(group.duplicate_count),
            format_file_size(group.wasted_space),
            "\n".join(file_list),
        )
    
    console.print(table)
    
    # Summary stats
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Files scanned: {result.files_processed}")
    console.print(f"  Duplicate groups: {len(result.groups)}")
    console.print(f"  Total duplicates: {result.duplicates_found}")
    console.print(f"  Wasted space: [red]{format_file_size(result.total_wasted_space)}[/red]")
    
    if action == "report":
        console.print(f"\n[dim]Use --action move or --action delete to handle duplicates.[/dim]")
        raise typer.Exit(0)
    
    # Handle duplicates
    if interactive:
        # Interactive mode: prompt for each group
        for i, group in enumerate(result.groups, 1):
            console.print(f"\n[bold]Group {i}:[/bold] {format_file_size(group.size)} x {len(group.files)} files")
            console.print(f"  Original: [green]{group.files[0]}[/green]")
            for dupe in group.files[1:]:
                console.print(f"  Duplicate: [yellow]{dupe}[/yellow]")
            
            if action == "delete":
                prompt = "Delete duplicates?"
            else:
                prompt = "Move duplicates to Duplicates folder?"
            
            if typer.confirm(prompt, default=False):
                # Handle this group
                single_result = DedupResult(groups=[group])
                history_manager = HistoryManager() if action == "move" and not dry_run else None
                handle_duplicates(single_result, action, path, dry_run, history_manager)
                result.duplicates_handled += single_result.duplicates_handled
                result.space_recovered += single_result.space_recovered
    else:
        # Non-interactive: confirm once then process all
        if action == "delete":
            prompt = f"Delete {result.duplicates_found} duplicate file(s)?"
        else:
            prompt = f"Move {result.duplicates_found} duplicate file(s) to Duplicates folder?"
        
        if not typer.confirm(prompt):
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)
        
        history_manager = HistoryManager() if action == "move" and not dry_run else None
        result = handle_duplicates(result, action, path, dry_run, history_manager)
    
    # Display handling results
    if result.duplicates_handled > 0:
        action_word = "Would handle" if dry_run else "Handled"
        console.print(f"\n[green]OK[/green] {action_word} {result.duplicates_handled} duplicate(s)")
        console.print(f"[green]OK[/green] Space recovered: {format_file_size(result.space_recovered)}")
    
    if result.errors:
        console.print("\n[red]Errors:[/red]")
        for error in result.errors:
            console.print(f"  [red]*[/red] {error}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
