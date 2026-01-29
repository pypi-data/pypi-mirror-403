"""Utility functions and classes for fso (File System Organizer).

Provides history tracking for undo operations and helper functions.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from platformdirs import user_data_dir

APP_NAME = "fso"


@dataclass
class FileMove:
    """Record of a single file move operation."""
    
    original_path: str
    new_path: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "FileMove":
        """Create FileMove from dictionary."""
        return cls(
            original_path=data["original_path"],
            new_path=data["new_path"],
            timestamp=data.get("timestamp", datetime.now().isoformat()),
        )


@dataclass
class HistoryEntry:
    """Record of a complete clean operation (multiple file moves)."""
    
    timestamp: str
    target_directory: str
    moves: list[FileMove]
    folders_created: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "target_directory": self.target_directory,
            "moves": [m.to_dict() for m in self.moves],
            "folders_created": self.folders_created,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        """Create HistoryEntry from dictionary."""
        return cls(
            timestamp=data["timestamp"],
            target_directory=data["target_directory"],
            moves=[FileMove.from_dict(m) for m in data.get("moves", [])],
            folders_created=data.get("folders_created", []),
        )


class HistoryManager:
    """Manages the history.json file for undo operations.
    
    History is stored in a platform-specific data directory:
    - Windows: %LOCALAPPDATA%/fso/history.json
    - macOS: ~/Library/Application Support/fso/history.json
    - Linux: ~/.local/share/fso/history.json
    """
    
    def __init__(self, history_path: Optional[Path] = None):
        """Initialize HistoryManager.
        
        Args:
            history_path: Optional custom path for history file.
                         If not provided, uses platform-specific location.
        """
        if history_path:
            self.history_path = history_path
        else:
            data_dir = Path(user_data_dir(APP_NAME, appauthor=False))
            self.history_path = data_dir / "history.json"
        
        self._entries: list[HistoryEntry] = []
        self._load()
    
    def _load(self) -> None:
        """Load history from disk."""
        if not self.history_path.exists():
            self._entries = []
            return
        
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._entries = [HistoryEntry.from_dict(e) for e in data.get("entries", [])]
        except (json.JSONDecodeError, KeyError):
            # Corrupted history file, start fresh
            self._entries = []
    
    def _save(self) -> None:
        """Save history to disk."""
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "version": "1.0",
            "entries": [e.to_dict() for e in self._entries],
        }
        
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def add_entry(self, entry: HistoryEntry) -> None:
        """Add a new history entry and save.
        
        Args:
            entry: The HistoryEntry to add.
        """
        self._entries.append(entry)
        self._save()
    
    def get_last_entry(self) -> Optional[HistoryEntry]:
        """Get the most recent history entry.
        
        Returns:
            The last HistoryEntry, or None if history is empty.
        """
        if not self._entries:
            return None
        return self._entries[-1]
    
    def pop_last_entry(self) -> Optional[HistoryEntry]:
        """Remove and return the most recent history entry.
        
        Returns:
            The last HistoryEntry, or None if history is empty.
        """
        if not self._entries:
            return None
        
        entry = self._entries.pop()
        self._save()
        return entry
    
    def get_all_entries(self) -> list[HistoryEntry]:
        """Get all history entries.
        
        Returns:
            List of all HistoryEntry objects, oldest first.
        """
        return self._entries.copy()
    
    def clear(self) -> None:
        """Clear all history entries."""
        self._entries = []
        self._save()
    
    @property
    def entry_count(self) -> int:
        """Get the number of history entries."""
        return len(self._entries)


def get_unique_path(path: Path) -> Path:
    """Generate a unique file path by appending _1, _2, etc. if file exists.
    
    Args:
        path: The desired file path.
        
    Returns:
        A path that doesn't exist. Either the original or with _N suffix.
        
    Example:
        If 'photo.jpg' exists, returns 'photo_1.jpg'
        If 'photo_1.jpg' also exists, returns 'photo_2.jpg'
    """
    if not path.exists():
        return path
    
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    
    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def is_hidden_file(path: Path) -> bool:
    """Check if a file is hidden.
    
    On Unix-like systems, files starting with '.' are hidden.
    On Windows, this also checks the file's hidden attribute.
    
    Args:
        path: Path to check.
        
    Returns:
        True if the file is hidden, False otherwise.
    """
    # Check for dot-prefix (works on all platforms)
    if path.name.startswith("."):
        return True
    
    # On Windows, also check the hidden attribute
    try:
        import ctypes
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        if attrs != -1:
            FILE_ATTRIBUTE_HIDDEN = 0x2
            return bool(attrs & FILE_ATTRIBUTE_HIDDEN)
    except (AttributeError, OSError):
        # Not on Windows or couldn't check attribute
        pass
    
    return False


def format_file_size(size_bytes: int) -> str:
    """Format a file size in bytes to a human-readable string.
    
    Args:
        size_bytes: Size in bytes.
        
    Returns:
        Formatted string like "1.5 MB" or "256 KB".
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            if unit == "B":
                return f"{size_bytes} {unit}"
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"
