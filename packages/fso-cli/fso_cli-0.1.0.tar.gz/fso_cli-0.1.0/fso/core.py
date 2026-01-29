"""Core file organization logic for fso (File System Organizer).

Handles scanning directories, matching files to rules, and moving files
to their destination folders with collision handling.
"""

import fnmatch
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from .config import Config
from .utils import FileMove, HistoryEntry, HistoryManager, get_unique_path, is_hidden_file


@dataclass
class OrganizeResult:
    """Result of an organize operation."""
    
    files_moved: int = 0
    files_skipped: int = 0
    folders_created: list[str] = field(default_factory=list)
    moves: list[FileMove] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    
    def add_move(self, original: Path, destination: Path) -> None:
        """Record a file move."""
        self.files_moved += 1
        self.moves.append(FileMove(
            original_path=str(original),
            new_path=str(destination),
        ))
    
    def add_folder(self, folder: Path) -> None:
        """Record a created folder."""
        self.folders_created.append(str(folder))
    
    def add_skip(self) -> None:
        """Record a skipped file."""
        self.files_skipped += 1
    
    def add_error(self, message: str) -> None:
        """Record an error."""
        self.errors.append(message)


def scan_directory(path: Path, config: Config) -> list[Path]:
    """Scan a directory and return list of files to organize.
    
    Excludes:
    - Directories
    - Hidden files (starting with '.')
    - Files matching exclude patterns from config
    
    Args:
        path: Directory to scan.
        config: Configuration with exclude patterns.
        
    Returns:
        List of file paths that should be organized.
    """
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    
    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")
    
    files: list[Path] = []
    
    for item in path.iterdir():
        # Skip directories
        if item.is_dir():
            continue
        
        # Skip hidden files
        if is_hidden_file(item):
            continue
        
        # Skip files matching exclude patterns
        if should_exclude(item.name, config.exclude_patterns):
            continue
        
        files.append(item)
    
    return sorted(files, key=lambda p: p.name.lower())


def should_exclude(filename: str, patterns: list[str]) -> bool:
    """Check if a filename matches any exclude pattern.
    
    Args:
        filename: Name of the file to check.
        patterns: List of glob patterns to match against.
        
    Returns:
        True if the file should be excluded, False otherwise.
    """
    for pattern in patterns:
        if fnmatch.fnmatch(filename, pattern):
            return True
        # Also check case-insensitive on Windows
        if fnmatch.fnmatch(filename.lower(), pattern.lower()):
            return True
    return False


def get_destination(file: Path, config: Config, base_path: Path) -> Path:
    """Determine the destination path for a file.
    
    Args:
        file: The file to move.
        config: Configuration with folder rules.
        base_path: The base directory where destination folders will be created.
        
    Returns:
        Full destination path for the file.
    """
    extension = file.suffix.lstrip(".").lower()
    folder_name = config.get_destination_folder(extension)
    return base_path / folder_name / file.name


def move_file(
    source: Path,
    destination: Path,
    dry_run: bool = False,
) -> tuple[Path, bool]:
    """Move a file to its destination with collision handling.
    
    If a file with the same name exists at the destination,
    the file is renamed with a numeric suffix (e.g., file_1.jpg).
    
    Args:
        source: Source file path.
        destination: Desired destination path.
        dry_run: If True, don't actually move the file.
        
    Returns:
        Tuple of (actual_destination, folder_created).
        actual_destination may differ from destination if renamed.
        folder_created is True if the destination folder was created.
    """
    folder_created = False
    
    # Ensure destination folder exists
    dest_folder = destination.parent
    if not dest_folder.exists():
        if not dry_run:
            dest_folder.mkdir(parents=True, exist_ok=True)
        folder_created = True
    
    # Handle filename collisions
    actual_destination = get_unique_path(destination)
    
    # Move the file
    if not dry_run:
        shutil.move(str(source), str(actual_destination))
    
    return actual_destination, folder_created


def organize_directory(
    path: Path,
    config: Config,
    dry_run: bool = False,
    history_manager: Optional[HistoryManager] = None,
    progress_callback: Optional[Callable[[Path, Path, int, int], None]] = None,
) -> OrganizeResult:
    """Organize all files in a directory according to config rules.
    
    Args:
        path: Directory to organize.
        config: Configuration with folder rules.
        dry_run: If True, simulate but don't actually move files.
        history_manager: Optional HistoryManager to record moves for undo.
        progress_callback: Optional callback(source, dest, current, total) for progress updates.
        
    Returns:
        OrganizeResult with details of the operation.
    """
    result = OrganizeResult()
    
    # Scan for files
    try:
        files = scan_directory(path, config)
    except (FileNotFoundError, NotADirectoryError) as e:
        result.add_error(str(e))
        return result
    
    if not files:
        return result
    
    total_files = len(files)
    
    for index, file in enumerate(files):
        try:
            # Get destination
            destination = get_destination(file, config, path)
            
            # Skip if source and destination are the same
            if file.parent == destination.parent:
                result.add_skip()
                continue
            
            # Move the file
            actual_dest, folder_created = move_file(file, destination, dry_run)
            
            # Record the move
            result.add_move(file, actual_dest)
            
            if folder_created and str(destination.parent) not in result.folders_created:
                result.add_folder(destination.parent)
            
            # Progress callback
            if progress_callback:
                progress_callback(file, actual_dest, index + 1, total_files)
                
        except Exception as e:
            result.add_error(f"Failed to move {file.name}: {e}")
    
    # Record in history for undo
    if history_manager and result.files_moved > 0 and not dry_run:
        entry = HistoryEntry(
            timestamp=datetime.now().isoformat(),
            target_directory=str(path),
            moves=result.moves,
            folders_created=result.folders_created,
        )
        history_manager.add_entry(entry)
    
    return result


def undo_last_operation(history_manager: HistoryManager) -> Optional[OrganizeResult]:
    """Undo the last organize operation.
    
    Moves all files back to their original locations and removes
    empty folders that were created.
    
    Args:
        history_manager: HistoryManager with operation history.
        
    Returns:
        OrganizeResult with undo details, or None if nothing to undo.
    """
    entry = history_manager.pop_last_entry()
    if not entry:
        return None
    
    result = OrganizeResult()
    
    # Move files back in reverse order
    for move in reversed(entry.moves):
        try:
            original = Path(move.original_path)
            current = Path(move.new_path)
            
            if current.exists():
                # Move back to original location
                shutil.move(str(current), str(original))
                result.add_move(current, original)
            else:
                result.add_error(f"File no longer exists: {current}")
                
        except Exception as e:
            result.add_error(f"Failed to restore {move.new_path}: {e}")
    
    # Remove empty folders that were created
    for folder_path in reversed(entry.folders_created):
        try:
            folder = Path(folder_path)
            if folder.exists() and folder.is_dir():
                # Only remove if empty
                if not any(folder.iterdir()):
                    folder.rmdir()
                    result.add_folder(folder)
        except Exception as e:
            result.add_error(f"Failed to remove folder {folder_path}: {e}")
    
    return result


def organize_single_file(
    file: Path,
    base_path: Path,
    config: Config,
    history_manager: Optional[HistoryManager] = None,
) -> Optional[FileMove]:
    """Organize a single file (used by the watcher).
    
    Args:
        file: The file to organize.
        base_path: The base directory where destination folders will be created.
        config: Configuration with folder rules.
        history_manager: Optional HistoryManager to record the move.
        
    Returns:
        FileMove record if file was moved, None otherwise.
    """
    # Skip if hidden or matches exclude patterns
    if is_hidden_file(file) or should_exclude(file.name, config.exclude_patterns):
        return None
    
    # Skip if not a file
    if not file.is_file():
        return None
    
    # Get destination
    destination = get_destination(file, config, base_path)
    
    # Skip if already in correct folder
    if file.parent == destination.parent:
        return None
    
    try:
        actual_dest, folder_created = move_file(file, destination, dry_run=False)
        
        file_move = FileMove(
            original_path=str(file),
            new_path=str(actual_dest),
        )
        
        # Record in history
        if history_manager:
            entry = HistoryEntry(
                timestamp=datetime.now().isoformat(),
                target_directory=str(base_path),
                moves=[file_move],
                folders_created=[str(destination.parent)] if folder_created else [],
            )
            history_manager.add_entry(entry)
        
        return file_move
        
    except Exception:
        return None
