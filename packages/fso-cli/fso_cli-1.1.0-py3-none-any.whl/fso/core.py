"""Core file organization logic for fso (File System Organizer).

Handles scanning directories, matching files to rules, and moving files
to their destination folders with collision handling.
"""

import fnmatch
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from .config import Config, ConflictStrategy
from .utils import (
    FileMove,
    HistoryEntry,
    HistoryManager,
    compute_file_hash,
    format_file_size,
    get_unique_path,
    is_hidden_file,
)


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
    
    # Use os.scandir() for better performance - DirEntry objects cache
    # is_file()/is_dir() results, avoiding extra stat calls on most systems
    with os.scandir(path) as entries:
        for entry in entries:
            # Skip directories (uses cached result from DirEntry)
            if entry.is_dir():
                continue
            
            item = Path(entry.path)
            
            # Skip hidden files
            if is_hidden_file(item):
                continue
            
            # Skip files matching exclude patterns
            if should_exclude(entry.name, config.exclude_patterns):
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
    conflict_strategy: ConflictStrategy = "rename",
) -> tuple[Path | None, bool, bool]:
    """Move a file to its destination with configurable collision handling.
    
    Args:
        source: Source file path.
        destination: Desired destination path.
        dry_run: If True, don't actually move the file.
        conflict_strategy: How to handle conflicts:
            - "skip": Don't move if destination exists, return None.
            - "overwrite": Replace existing file.
            - "rename": Rename with numeric suffix (e.g., file_1.jpg).
        
    Returns:
        Tuple of (actual_destination, folder_created, was_skipped).
        actual_destination may be None if skipped, or differ from destination if renamed.
        folder_created is True if the destination folder was created.
        was_skipped is True if the file was skipped due to conflict.
    """
    folder_created = False
    was_skipped = False
    
    # Ensure destination folder exists
    dest_folder = destination.parent
    if not dest_folder.exists():
        if not dry_run:
            dest_folder.mkdir(parents=True, exist_ok=True)
        folder_created = True
    
    # Handle filename collisions based on strategy
    if destination.exists():
        if conflict_strategy == "skip":
            # Skip this file - don't move it
            return None, folder_created, True
        elif conflict_strategy == "overwrite":
            # Delete existing file and use same destination
            if not dry_run:
                destination.unlink()
            actual_destination = destination
        else:  # "rename" (default)
            # Rename with numeric suffix
            actual_destination = get_unique_path(destination)
    else:
        actual_destination = destination
    
    # Move the file
    if not dry_run:
        shutil.move(str(source), str(actual_destination))
    
    return actual_destination, folder_created, was_skipped


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
            
            # Move the file with configured conflict strategy
            actual_dest, folder_created, was_skipped = move_file(
                file, destination, dry_run, config.conflict_strategy
            )
            
            # Handle skipped files (due to conflict strategy)
            if was_skipped or actual_dest is None:
                result.add_skip()
                if progress_callback:
                    progress_callback(file, destination, index + 1, total_files)
                continue
            
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


def _undo_entry(entry: HistoryEntry) -> OrganizeResult:
    """Undo a single history entry.
    
    Internal helper that performs the actual undo operation.
    
    Args:
        entry: The HistoryEntry to undo.
        
    Returns:
        OrganizeResult with undo details.
    """
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
    
    return _undo_entry(entry)


def undo_operations(
    history_manager: HistoryManager,
    count: int,
) -> list[OrganizeResult]:
    """Undo multiple organize operations.
    
    Undoes the specified number of most recent operations, starting
    from the most recent.
    
    Args:
        history_manager: HistoryManager with operation history.
        count: Number of operations to undo. If greater than available,
               undoes all available operations.
        
    Returns:
        List of OrganizeResult objects, one per undone operation.
        Empty list if nothing to undo.
    """
    entries = history_manager.pop_entries(count)
    if not entries:
        return []
    
    results = []
    for entry in entries:
        result = _undo_entry(entry)
        results.append(result)
    
    return results


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
        actual_dest, folder_created, was_skipped = move_file(
            file, destination, dry_run=False, conflict_strategy=config.conflict_strategy
        )
        
        # Return None if skipped due to conflict
        if was_skipped or actual_dest is None:
            return None
        
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


# ============================================================================
# Deduplication Functions
# ============================================================================

@dataclass
class DuplicateGroup:
    """A group of duplicate files sharing the same content hash."""
    
    hash: str
    size: int
    files: list[Path]
    
    @property
    def duplicate_count(self) -> int:
        """Number of duplicate files (excluding the original)."""
        return len(self.files) - 1
    
    @property
    def wasted_space(self) -> int:
        """Total space wasted by duplicates."""
        return self.size * self.duplicate_count


@dataclass
class DedupResult:
    """Result of a deduplication operation."""
    
    groups: list[DuplicateGroup] = field(default_factory=list)
    files_processed: int = 0
    duplicates_found: int = 0
    duplicates_handled: int = 0
    space_recovered: int = 0
    errors: list[str] = field(default_factory=list)
    
    @property
    def total_wasted_space(self) -> int:
        """Total space wasted by all duplicates."""
        return sum(g.wasted_space for g in self.groups)
    
    def add_error(self, message: str) -> None:
        """Record an error."""
        self.errors.append(message)


def find_duplicates(
    path: Path,
    config: Config,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> DedupResult:
    """Find duplicate files in a directory using content hashing.
    
    Uses a two-phase approach for efficiency:
    1. Group files by size (files with different sizes can't be duplicates)
    2. Hash files within same-size groups
    
    Args:
        path: Directory to scan for duplicates.
        config: Configuration with exclude patterns.
        progress_callback: Optional callback(phase, current, total) for progress.
        
    Returns:
        DedupResult containing groups of duplicate files.
    """
    result = DedupResult()
    
    # Phase 1: Scan and group files by size
    size_groups: dict[int, list[Path]] = {}
    
    try:
        files = scan_directory(path, config)
    except (FileNotFoundError, NotADirectoryError) as e:
        result.add_error(str(e))
        return result
    
    result.files_processed = len(files)
    
    if progress_callback:
        progress_callback("Scanning files", 0, len(files))
    
    for i, file in enumerate(files):
        try:
            size = file.stat().st_size
            if size > 0:  # Skip empty files
                if size not in size_groups:
                    size_groups[size] = []
                size_groups[size].append(file)
        except OSError:
            pass  # Skip files we can't stat
        
        if progress_callback and (i + 1) % 100 == 0:
            progress_callback("Scanning files", i + 1, len(files))
    
    # Filter to only groups with potential duplicates
    potential_dupes = {size: files for size, files in size_groups.items() if len(files) > 1}
    
    if not potential_dupes:
        return result
    
    # Phase 2: Hash files to find actual duplicates
    total_to_hash = sum(len(files) for files in potential_dupes.values())
    hashed = 0
    
    if progress_callback:
        progress_callback("Hashing files", 0, total_to_hash)
    
    # Quick hash threshold: files smaller than this go straight to full hash
    QUICK_HASH_THRESHOLD = 65536  # 64KB
    
    for size, same_size_files in potential_dupes.items():
        # For small files, skip quick hash and go straight to full hash
        # (quick hash reads first 64KB, so for files <= 64KB it's the same)
        if size <= QUICK_HASH_THRESHOLD:
            # Direct full hash for small files
            full_hash_groups: dict[str, list[Path]] = {}
            
            for file in same_size_files:
                try:
                    full = compute_file_hash(file, quick_hash=False)
                    if full not in full_hash_groups:
                        full_hash_groups[full] = []
                    full_hash_groups[full].append(file)
                except (OSError, PermissionError):
                    pass
                
                hashed += 1
                if progress_callback and hashed % 50 == 0:
                    progress_callback("Hashing files", hashed, total_to_hash)
            
            # Record duplicate groups
            for full_hash, dupes in full_hash_groups.items():
                if len(dupes) > 1:
                    dupes.sort(key=lambda p: p.stat().st_mtime)
                    group = DuplicateGroup(hash=full_hash, size=size, files=dupes)
                    result.groups.append(group)
                    result.duplicates_found += group.duplicate_count
            continue
        
        # For large files, use two-phase approach
        # First pass: quick hash (first 64KB)
        quick_hash_groups: dict[str, list[Path]] = {}
        
        for file in same_size_files:
            try:
                quick = compute_file_hash(file, quick_hash=True)
                if quick not in quick_hash_groups:
                    quick_hash_groups[quick] = []
                quick_hash_groups[quick].append(file)
            except (OSError, PermissionError):
                pass
            
            hashed += 1
            if progress_callback and hashed % 50 == 0:
                progress_callback("Hashing files", hashed, total_to_hash)
        
        # Second pass: full hash for files with matching quick hashes
        for quick_hash, candidates in quick_hash_groups.items():
            if len(candidates) < 2:
                continue
            
            full_hash_groups: dict[str, list[Path]] = {}
            
            for file in candidates:
                try:
                    full = compute_file_hash(file, quick_hash=False)
                    if full not in full_hash_groups:
                        full_hash_groups[full] = []
                    full_hash_groups[full].append(file)
                except (OSError, PermissionError):
                    pass
            
            # Record duplicate groups
            for full_hash, dupes in full_hash_groups.items():
                if len(dupes) > 1:
                    # Sort by modification time (oldest first = original)
                    dupes.sort(key=lambda p: p.stat().st_mtime)
                    
                    group = DuplicateGroup(
                        hash=full_hash,
                        size=size,
                        files=dupes,
                    )
                    result.groups.append(group)
                    result.duplicates_found += group.duplicate_count
    
    if progress_callback:
        progress_callback("Hashing files", total_to_hash, total_to_hash)
    
    return result


def handle_duplicates(
    result: DedupResult,
    action: str,
    base_path: Path,
    dry_run: bool = False,
    history_manager: Optional[HistoryManager] = None,
) -> DedupResult:
    """Handle duplicate files according to the specified action.
    
    Args:
        result: DedupResult from find_duplicates().
        action: How to handle duplicates:
            - "report": Just report, don't modify files (default).
            - "move": Move duplicates to a 'Duplicates' folder.
            - "delete": Delete duplicates (keep oldest file).
        base_path: Base directory for organizing.
        dry_run: If True, simulate but don't actually modify files.
        history_manager: Optional HistoryManager to record moves for undo.
        
    Returns:
        Updated DedupResult with handling statistics.
    """
    if action == "report" or not result.groups:
        return result
    
    moves: list[FileMove] = []
    folders_created: list[str] = []
    
    for group in result.groups:
        # Keep the first file (oldest), handle the rest
        original = group.files[0]
        duplicates = group.files[1:]
        
        for dupe in duplicates:
            try:
                if action == "delete":
                    if not dry_run:
                        dupe.unlink()
                    result.duplicates_handled += 1
                    result.space_recovered += group.size
                    
                elif action == "move":
                    # Move to Duplicates folder
                    dest_folder = base_path / "Duplicates"
                    dest = dest_folder / dupe.name
                    
                    if not dry_run:
                        if not dest_folder.exists():
                            dest_folder.mkdir(parents=True, exist_ok=True)
                            if str(dest_folder) not in folders_created:
                                folders_created.append(str(dest_folder))
                        
                        # Handle name collisions in Duplicates folder
                        actual_dest = get_unique_path(dest)
                        shutil.move(str(dupe), str(actual_dest))
                        
                        moves.append(FileMove(
                            original_path=str(dupe),
                            new_path=str(actual_dest),
                        ))
                    
                    result.duplicates_handled += 1
                    result.space_recovered += group.size
                    
            except Exception as e:
                result.add_error(f"Failed to handle {dupe.name}: {e}")
    
    # Record in history for undo (only for move action)
    if history_manager and moves and not dry_run:
        entry = HistoryEntry(
            timestamp=datetime.now().isoformat(),
            target_directory=str(base_path),
            moves=moves,
            folders_created=folders_created,
        )
        history_manager.add_entry(entry)
    
    return result
