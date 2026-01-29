"""Tests for the core module."""

import shutil
from pathlib import Path

import pytest

from fso.config import Config
from fso.core import (
    DedupResult,
    DuplicateGroup,
    OrganizeResult,
    find_duplicates,
    get_destination,
    handle_duplicates,
    move_file,
    organize_directory,
    scan_directory,
    should_exclude,
    undo_last_operation,
    undo_operations,
)
from fso.utils import HistoryManager, compute_file_hash, get_unique_path


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
        
        actual_dest, folder_created, was_skipped = move_file(source, dest)
        
        assert actual_dest == dest
        assert folder_created is True
        assert was_skipped is False
        assert dest.exists()
        assert not source.exists()
    
    def test_handles_collision_rename(self, tmp_path: Path) -> None:
        """Test that collision is handled with rename (default)."""
        source = tmp_path / "file.txt"
        source.write_text("new content")
        dest_folder = tmp_path / "dest"
        dest_folder.mkdir()
        existing = dest_folder / "file.txt"
        existing.write_text("existing content")
        
        dest = dest_folder / "file.txt"
        actual_dest, folder_created, was_skipped = move_file(source, dest, conflict_strategy="rename")
        
        assert actual_dest == dest_folder / "file_1.txt"
        assert folder_created is False
        assert was_skipped is False
        assert existing.exists()  # Original still there
        assert actual_dest.exists()
    
    def test_handles_collision_skip(self, tmp_path: Path) -> None:
        """Test that collision with skip strategy skips the file."""
        source = tmp_path / "file.txt"
        source.write_text("new content")
        dest_folder = tmp_path / "dest"
        dest_folder.mkdir()
        existing = dest_folder / "file.txt"
        existing.write_text("existing content")
        
        dest = dest_folder / "file.txt"
        actual_dest, folder_created, was_skipped = move_file(source, dest, conflict_strategy="skip")
        
        assert actual_dest is None
        assert was_skipped is True
        assert source.exists()  # Source not moved
        assert existing.read_text() == "existing content"  # Original unchanged
    
    def test_handles_collision_overwrite(self, tmp_path: Path) -> None:
        """Test that collision with overwrite strategy replaces the file."""
        source = tmp_path / "file.txt"
        source.write_text("new content")
        dest_folder = tmp_path / "dest"
        dest_folder.mkdir()
        existing = dest_folder / "file.txt"
        existing.write_text("existing content")
        
        dest = dest_folder / "file.txt"
        actual_dest, folder_created, was_skipped = move_file(source, dest, conflict_strategy="overwrite")
        
        assert actual_dest == dest
        assert was_skipped is False
        assert not source.exists()  # Source moved
        assert dest.read_text() == "new content"  # Content replaced
    
    def test_dry_run(self, tmp_path: Path) -> None:
        """Test that dry run doesn't move file."""
        source = tmp_path / "source.txt"
        source.write_text("content")
        dest = tmp_path / "dest" / "source.txt"
        
        actual_dest, folder_created, was_skipped = move_file(source, dest, dry_run=True)
        
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


class TestBatchUndo:
    """Tests for batch undo functionality."""
    
    def test_undo_multiple_operations(self, tmp_path: Path) -> None:
        """Test undoing multiple operations at once."""
        history_file = tmp_path / "history.json"
        history_manager = HistoryManager(history_file)
        
        config = Config(
            rules={"Images": ["jpg"], "Documents": ["pdf"]},
            default_folder="Misc",
            exclude_patterns=[],
        )
        
        # Create and organize files in two separate operations
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        
        # First operation
        (test_dir / "photo1.jpg").touch()
        organize_directory(test_dir, config, history_manager=history_manager)
        
        # Second operation - add more files
        (test_dir / "photo2.jpg").touch()
        organize_directory(test_dir, config, history_manager=history_manager)
        
        # Should have 2 history entries
        assert history_manager.entry_count == 2
        
        # Undo both operations
        results = undo_operations(history_manager, count=2)
        
        assert len(results) == 2
        assert history_manager.entry_count == 0
    
    def test_get_entry_summaries(self, tmp_path: Path) -> None:
        """Test getting summaries of history entries."""
        history_file = tmp_path / "history.json"
        history_manager = HistoryManager(history_file)
        
        config = Config(
            rules={"Images": ["jpg"]},
            default_folder="Misc",
            exclude_patterns=[],
        )
        
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "photo.jpg").touch()
        organize_directory(test_dir, config, history_manager=history_manager)
        
        summaries = history_manager.get_entry_summaries()
        
        assert len(summaries) == 1
        assert summaries[0]["file_count"] == 1
        assert summaries[0]["display_index"] == 1
    
    def test_pop_entries(self, tmp_path: Path) -> None:
        """Test popping multiple entries from history."""
        history_file = tmp_path / "history.json"
        history_manager = HistoryManager(history_file)
        
        config = Config(
            rules={"Images": ["jpg"]},
            default_folder="Misc",
            exclude_patterns=[],
        )
        
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        
        # Create 3 operations
        for i in range(3):
            (test_dir / f"photo{i}.jpg").touch()
            organize_directory(test_dir, config, history_manager=history_manager)
        
        assert history_manager.entry_count == 3
        
        # Pop 2 entries
        entries = history_manager.pop_entries(2)
        
        assert len(entries) == 2
        assert history_manager.entry_count == 1


class TestFileHashing:
    """Tests for file hashing functionality."""
    
    def test_compute_file_hash(self, tmp_path: Path) -> None:
        """Test computing file hash."""
        file = tmp_path / "test.txt"
        file.write_text("Hello, World!")
        
        hash1 = compute_file_hash(file)
        hash2 = compute_file_hash(file)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex chars
    
    def test_different_content_different_hash(self, tmp_path: Path) -> None:
        """Test that different content produces different hashes."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content A")
        file2.write_text("Content B")
        
        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)
        
        assert hash1 != hash2
    
    def test_same_content_same_hash(self, tmp_path: Path) -> None:
        """Test that same content in different files produces same hash."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        content = "Same content"
        file1.write_text(content)
        file2.write_text(content)
        
        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)
        
        assert hash1 == hash2
    
    def test_quick_hash(self, tmp_path: Path) -> None:
        """Test quick hash mode."""
        file = tmp_path / "test.txt"
        file.write_text("Hello, World!")
        
        quick = compute_file_hash(file, quick_hash=True)
        full = compute_file_hash(file, quick_hash=False)
        
        # For small files, quick and full should be the same
        assert quick == full


class TestFindDuplicates:
    """Tests for duplicate finding functionality."""
    
    @pytest.fixture
    def duplicate_directory(self, tmp_path: Path) -> Path:
        """Create a directory with duplicate files."""
        # Create unique files
        (tmp_path / "unique1.txt").write_text("Unique content 1")
        (tmp_path / "unique2.txt").write_text("Unique content 2")
        
        # Create duplicates
        content = "This is duplicate content"
        (tmp_path / "original.txt").write_text(content)
        (tmp_path / "copy1.txt").write_text(content)
        (tmp_path / "copy2.txt").write_text(content)
        
        return tmp_path
    
    def test_finds_duplicates(self, duplicate_directory: Path) -> None:
        """Test that duplicates are found."""
        config = Config(
            rules={},
            default_folder="Misc",
            exclude_patterns=[],
        )
        
        result = find_duplicates(duplicate_directory, config)
        
        assert len(result.groups) == 1
        assert result.duplicates_found == 2  # 2 copies of original
        assert len(result.groups[0].files) == 3  # original + 2 copies
    
    def test_no_duplicates(self, tmp_path: Path) -> None:
        """Test directory with no duplicates."""
        (tmp_path / "file1.txt").write_text("Content 1")
        (tmp_path / "file2.txt").write_text("Content 2")
        (tmp_path / "file3.txt").write_text("Content 3")
        
        config = Config(
            rules={},
            default_folder="Misc",
            exclude_patterns=[],
        )
        
        result = find_duplicates(tmp_path, config)
        
        assert len(result.groups) == 0
        assert result.duplicates_found == 0


class TestHandleDuplicates:
    """Tests for duplicate handling functionality."""
    
    def test_handle_delete(self, tmp_path: Path) -> None:
        """Test deleting duplicate files."""
        content = "Duplicate content"
        original = tmp_path / "original.txt"
        copy = tmp_path / "copy.txt"
        original.write_text(content)
        copy.write_text(content)
        
        result = DedupResult(
            groups=[
                DuplicateGroup(
                    hash="abc123",
                    size=len(content),
                    files=[original, copy],
                )
            ],
            duplicates_found=1,
        )
        
        result = handle_duplicates(result, "delete", tmp_path)
        
        assert result.duplicates_handled == 1
        assert original.exists()  # Original kept
        assert not copy.exists()  # Duplicate deleted
    
    def test_handle_move(self, tmp_path: Path) -> None:
        """Test moving duplicate files."""
        content = "Duplicate content"
        original = tmp_path / "original.txt"
        copy = tmp_path / "copy.txt"
        original.write_text(content)
        copy.write_text(content)
        
        result = DedupResult(
            groups=[
                DuplicateGroup(
                    hash="abc123",
                    size=len(content),
                    files=[original, copy],
                )
            ],
            duplicates_found=1,
        )
        
        result = handle_duplicates(result, "move", tmp_path)
        
        assert result.duplicates_handled == 1
        assert original.exists()  # Original kept in place
        assert not copy.exists()  # Duplicate moved
        assert (tmp_path / "Duplicates" / "copy.txt").exists()  # Moved to Duplicates
    
    def test_handle_report(self, tmp_path: Path) -> None:
        """Test that report action doesn't modify files."""
        content = "Duplicate content"
        original = tmp_path / "original.txt"
        copy = tmp_path / "copy.txt"
        original.write_text(content)
        copy.write_text(content)
        
        result = DedupResult(
            groups=[
                DuplicateGroup(
                    hash="abc123",
                    size=len(content),
                    files=[original, copy],
                )
            ],
            duplicates_found=1,
        )
        
        result = handle_duplicates(result, "report", tmp_path)
        
        assert result.duplicates_handled == 0
        assert original.exists()
        assert copy.exists()  # Both files still exist
