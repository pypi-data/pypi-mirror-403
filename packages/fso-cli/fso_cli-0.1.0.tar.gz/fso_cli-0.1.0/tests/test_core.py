"""Tests for the core module."""

import shutil
from pathlib import Path

import pytest

from fso.config import Config
from fso.core import (
    OrganizeResult,
    get_destination,
    move_file,
    organize_directory,
    scan_directory,
    should_exclude,
    undo_last_operation,
)
from fso.utils import HistoryManager, get_unique_path


@pytest.fixture
def sample_config() -> Config:
    """Create a sample configuration for testing."""
    return Config(
        rules={
            "Images": ["jpg", "png", "gif"],
            "Documents": ["pdf", "txt", "doc"],
            "Archives": ["zip", "tar"],
        },
        default_folder="Misc",
        exclude_patterns=["*.tmp", "*.part", "desktop.ini"],
    )


@pytest.fixture
def test_directory(tmp_path: Path) -> Path:
    """Create a test directory with sample files."""
    # Create some test files
    (tmp_path / "photo.jpg").touch()
    (tmp_path / "document.pdf").touch()
    (tmp_path / "readme.txt").touch()
    (tmp_path / "archive.zip").touch()
    (tmp_path / "unknown.xyz").touch()
    (tmp_path / ".hidden").touch()
    (tmp_path / "temp.tmp").touch()
    
    # Create a subdirectory (should be ignored)
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "nested.jpg").touch()
    
    return tmp_path


class TestShouldExclude:
    """Tests for the should_exclude function."""
    
    def test_matches_pattern(self) -> None:
        """Test that matching patterns return True."""
        patterns = ["*.tmp", "*.part"]
        
        assert should_exclude("file.tmp", patterns) is True
        assert should_exclude("download.part", patterns) is True
    
    def test_no_match(self) -> None:
        """Test that non-matching files return False."""
        patterns = ["*.tmp", "*.part"]
        
        assert should_exclude("file.txt", patterns) is False
        assert should_exclude("photo.jpg", patterns) is False
    
    def test_case_insensitive(self) -> None:
        """Test that matching is case insensitive."""
        patterns = ["*.tmp"]
        
        assert should_exclude("file.TMP", patterns) is True
        assert should_exclude("file.Tmp", patterns) is True
    
    def test_exact_match(self) -> None:
        """Test exact filename patterns."""
        patterns = ["desktop.ini", "Thumbs.db"]
        
        assert should_exclude("desktop.ini", patterns) is True
        assert should_exclude("Thumbs.db", patterns) is True
        assert should_exclude("other.ini", patterns) is False


class TestScanDirectory:
    """Tests for the scan_directory function."""
    
    def test_finds_regular_files(self, test_directory: Path, sample_config: Config) -> None:
        """Test that regular files are found."""
        files = scan_directory(test_directory, sample_config)
        filenames = [f.name for f in files]
        
        assert "photo.jpg" in filenames
        assert "document.pdf" in filenames
        assert "readme.txt" in filenames
    
    def test_excludes_directories(self, test_directory: Path, sample_config: Config) -> None:
        """Test that directories are not included."""
        files = scan_directory(test_directory, sample_config)
        filenames = [f.name for f in files]
        
        assert "subdir" not in filenames
    
    def test_excludes_hidden_files(self, test_directory: Path, sample_config: Config) -> None:
        """Test that hidden files are excluded."""
        files = scan_directory(test_directory, sample_config)
        filenames = [f.name for f in files]
        
        assert ".hidden" not in filenames
    
    def test_excludes_pattern_matches(self, test_directory: Path, sample_config: Config) -> None:
        """Test that files matching exclude patterns are excluded."""
        files = scan_directory(test_directory, sample_config)
        filenames = [f.name for f in files]
        
        assert "temp.tmp" not in filenames
    
    def test_raises_for_nonexistent(self, sample_config: Config) -> None:
        """Test that nonexistent directory raises error."""
        with pytest.raises(FileNotFoundError):
            scan_directory(Path("/nonexistent/path"), sample_config)
    
    def test_raises_for_file(self, test_directory: Path, sample_config: Config) -> None:
        """Test that file path raises error."""
        file_path = test_directory / "photo.jpg"
        
        with pytest.raises(NotADirectoryError):
            scan_directory(file_path, sample_config)


class TestGetDestination:
    """Tests for the get_destination function."""
    
    def test_known_extension(self, test_directory: Path, sample_config: Config) -> None:
        """Test destination for known extension."""
        file = test_directory / "photo.jpg"
        dest = get_destination(file, sample_config, test_directory)
        
        assert dest == test_directory / "Images" / "photo.jpg"
    
    def test_unknown_extension(self, test_directory: Path, sample_config: Config) -> None:
        """Test destination for unknown extension."""
        file = test_directory / "unknown.xyz"
        dest = get_destination(file, sample_config, test_directory)
        
        assert dest == test_directory / "Misc" / "unknown.xyz"


class TestGetUniquePath:
    """Tests for the get_unique_path function."""
    
    def test_no_collision(self, tmp_path: Path) -> None:
        """Test that non-existing path is returned as-is."""
        path = tmp_path / "newfile.txt"
        result = get_unique_path(path)
        
        assert result == path
    
    def test_with_collision(self, tmp_path: Path) -> None:
        """Test that collision adds numeric suffix."""
        existing = tmp_path / "file.txt"
        existing.touch()
        
        result = get_unique_path(existing)
        
        assert result == tmp_path / "file_1.txt"
    
    def test_multiple_collisions(self, tmp_path: Path) -> None:
        """Test handling of multiple collisions."""
        (tmp_path / "file.txt").touch()
        (tmp_path / "file_1.txt").touch()
        (tmp_path / "file_2.txt").touch()
        
        result = get_unique_path(tmp_path / "file.txt")
        
        assert result == tmp_path / "file_3.txt"


class TestMoveFile:
    """Tests for the move_file function."""
    
    def test_moves_file(self, tmp_path: Path) -> None:
        """Test that file is moved to destination."""
        source = tmp_path / "source.txt"
        source.write_text("content")
        dest_folder = tmp_path / "dest"
        dest = dest_folder / "source.txt"
        
        actual_dest, folder_created = move_file(source, dest)
        
        assert actual_dest == dest
        assert folder_created is True
        assert dest.exists()
        assert not source.exists()
    
    def test_handles_collision(self, tmp_path: Path) -> None:
        """Test that collision is handled with rename."""
        source = tmp_path / "file.txt"
        source.write_text("new content")
        dest_folder = tmp_path / "dest"
        dest_folder.mkdir()
        existing = dest_folder / "file.txt"
        existing.write_text("existing content")
        
        dest = dest_folder / "file.txt"
        actual_dest, folder_created = move_file(source, dest)
        
        assert actual_dest == dest_folder / "file_1.txt"
        assert folder_created is False
        assert existing.exists()  # Original still there
        assert actual_dest.exists()
    
    def test_dry_run(self, tmp_path: Path) -> None:
        """Test that dry run doesn't move file."""
        source = tmp_path / "source.txt"
        source.write_text("content")
        dest = tmp_path / "dest" / "source.txt"
        
        actual_dest, folder_created = move_file(source, dest, dry_run=True)
        
        assert source.exists()  # Still exists
        assert not dest.exists()  # Not moved


class TestOrganizeDirectory:
    """Tests for the organize_directory function."""
    
    def test_organizes_files(self, test_directory: Path, sample_config: Config) -> None:
        """Test that files are organized into correct folders."""
        result = organize_directory(test_directory, sample_config)
        
        assert result.files_moved > 0
        assert (test_directory / "Images" / "photo.jpg").exists()
        assert (test_directory / "Documents" / "document.pdf").exists()
        assert (test_directory / "Documents" / "readme.txt").exists()
        assert (test_directory / "Archives" / "archive.zip").exists()
        assert (test_directory / "Misc" / "unknown.xyz").exists()
    
    def test_dry_run(self, test_directory: Path, sample_config: Config) -> None:
        """Test that dry run doesn't move files."""
        result = organize_directory(test_directory, sample_config, dry_run=True)
        
        assert result.files_moved > 0  # Counted as moved
        # But files are still in original location
        assert (test_directory / "photo.jpg").exists()
        assert not (test_directory / "Images").exists()
    
    def test_records_history(self, test_directory: Path, sample_config: Config, tmp_path: Path) -> None:
        """Test that history is recorded."""
        history_file = tmp_path / "history.json"
        history_manager = HistoryManager(history_file)
        
        organize_directory(test_directory, sample_config, history_manager=history_manager)
        
        assert history_manager.entry_count == 1
        entry = history_manager.get_last_entry()
        assert entry is not None
        assert len(entry.moves) > 0


class TestUndoLastOperation:
    """Tests for the undo_last_operation function."""
    
    def test_undo_restores_files(self, test_directory: Path, sample_config: Config, tmp_path: Path) -> None:
        """Test that undo restores files to original location."""
        history_file = tmp_path / "history.json"
        history_manager = HistoryManager(history_file)
        
        # First organize
        organize_directory(test_directory, sample_config, history_manager=history_manager)
        
        # Verify files were moved
        assert (test_directory / "Images" / "photo.jpg").exists()
        assert not (test_directory / "photo.jpg").exists()
        
        # Now undo
        result = undo_last_operation(history_manager)
        
        assert result is not None
        assert result.files_moved > 0
        # Files should be back
        assert (test_directory / "photo.jpg").exists()
    
    def test_undo_nothing(self, tmp_path: Path) -> None:
        """Test undo with no history returns None."""
        history_file = tmp_path / "history.json"
        history_manager = HistoryManager(history_file)
        
        result = undo_last_operation(history_manager)
        
        assert result is None
