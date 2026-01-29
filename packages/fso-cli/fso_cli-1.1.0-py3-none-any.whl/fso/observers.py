"""File system observers for fso (File System Organizer).

Provides watchdog-based file monitoring for the 'watch' command.
"""

import threading
import time
from pathlib import Path
from typing import Callable, Optional

from watchdog.events import FileCreatedEvent, FileMovedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .config import Config
from .core import organize_single_file, should_exclude
from .utils import FileMove, HistoryManager, is_hidden_file


class FsoEventHandler(FileSystemEventHandler):
    """Event handler for file system changes.
    
    Watches for new files and organizes them after a short delay
    to ensure downloads are complete.
    """
    
    def __init__(
        self,
        watch_path: Path,
        config: Config,
        history_manager: Optional[HistoryManager] = None,
        on_file_organized: Optional[Callable[[Path, Path], None]] = None,
        delay: float = 1.0,
    ):
        """Initialize the event handler.
        
        Args:
            watch_path: The directory being watched.
            config: Configuration with folder rules.
            history_manager: Optional HistoryManager for undo support.
            on_file_organized: Callback when a file is organized.
            delay: Seconds to wait before organizing (for download completion).
        """
        super().__init__()
        self.watch_path = watch_path
        self.config = config
        self.history_manager = history_manager
        self.on_file_organized = on_file_organized
        self.delay = delay
        
        # Track pending files to avoid duplicate processing
        self._pending: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()
    
    def _schedule_organize(self, file_path: Path) -> None:
        """Schedule a file to be organized after the delay period.
        
        If the file is already scheduled, the timer is reset.
        
        Args:
            file_path: Path to the file to organize.
        """
        file_key = str(file_path)
        
        with self._lock:
            # Cancel existing timer if any
            if file_key in self._pending:
                self._pending[file_key].cancel()
            
            # Schedule new timer
            timer = threading.Timer(self.delay, self._organize_file, args=[file_path])
            self._pending[file_key] = timer
            timer.start()
    
    def _organize_file(self, file_path: Path) -> None:
        """Organize a single file.
        
        Args:
            file_path: Path to the file to organize.
        """
        file_key = str(file_path)
        
        with self._lock:
            # Remove from pending
            if file_key in self._pending:
                del self._pending[file_key]
        
        # Check if file still exists (might have been moved/deleted)
        if not file_path.exists():
            return
        
        # Skip files in subdirectories (only organize top-level files)
        if file_path.parent != self.watch_path:
            return
        
        # Organize the file
        result = organize_single_file(
            file_path,
            self.watch_path,
            self.config,
            self.history_manager,
        )
        
        # Call the callback if file was moved
        if result and self.on_file_organized:
            self.on_file_organized(
                Path(result.original_path),
                Path(result.new_path),
            )
    
    def on_created(self, event: FileCreatedEvent) -> None:
        """Handle file creation events.
        
        Args:
            event: The file creation event.
        """
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Quick checks before scheduling
        if is_hidden_file(file_path):
            return
        
        if should_exclude(file_path.name, self.config.exclude_patterns):
            return
        
        # Schedule for organization
        self._schedule_organize(file_path)
    
    def on_moved(self, event: FileMovedEvent) -> None:
        """Handle file move events (e.g., temp file renamed to final name).
        
        Args:
            event: The file move event.
        """
        if event.is_directory:
            return
        
        # The destination is the new file
        file_path = Path(event.dest_path)
        
        # Only handle if moved into the watch directory (not subdirs)
        if file_path.parent != self.watch_path:
            return
        
        # Quick checks before scheduling
        if is_hidden_file(file_path):
            return
        
        if should_exclude(file_path.name, self.config.exclude_patterns):
            return
        
        # Schedule for organization
        self._schedule_organize(file_path)
    
    def stop(self) -> None:
        """Cancel all pending timers."""
        with self._lock:
            for timer in self._pending.values():
                timer.cancel()
            self._pending.clear()


class DirectoryWatcher:
    """Watches a directory and organizes new files.
    
    Uses watchdog to monitor file system events and automatically
    organize files as they appear.
    """
    
    def __init__(
        self,
        watch_path: Path,
        config: Config,
        history_manager: Optional[HistoryManager] = None,
        on_file_organized: Optional[Callable[[Path, Path], None]] = None,
        delay: float = 1.0,
    ):
        """Initialize the directory watcher.
        
        Args:
            watch_path: The directory to watch.
            config: Configuration with folder rules.
            history_manager: Optional HistoryManager for undo support.
            on_file_organized: Callback when a file is organized.
            delay: Seconds to wait before organizing new files.
        """
        self.watch_path = watch_path
        self.config = config
        self.delay = delay
        
        self.event_handler = FsoEventHandler(
            watch_path=watch_path,
            config=config,
            history_manager=history_manager,
            on_file_organized=on_file_organized,
            delay=delay,
        )
        
        self.observer = Observer()
        self._running = False
    
    def start(self) -> None:
        """Start watching the directory."""
        if self._running:
            return
        
        self.observer.schedule(
            self.event_handler,
            str(self.watch_path),
            recursive=False,  # Only watch the top-level directory
        )
        self.observer.start()
        self._running = True
    
    def stop(self) -> None:
        """Stop watching the directory."""
        if not self._running:
            return
        
        self.event_handler.stop()
        self.observer.stop()
        self.observer.join()
        self._running = False
    
    def wait(self) -> None:
        """Wait for the watcher to be stopped (blocks until Ctrl+C)."""
        try:
            while self._running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    @property
    def is_running(self) -> bool:
        """Check if the watcher is currently running."""
        return self._running
