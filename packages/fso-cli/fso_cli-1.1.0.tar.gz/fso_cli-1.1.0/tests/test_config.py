"""Tests for the config module."""

import tempfile
from pathlib import Path

import pytest
import yaml

from fso.config import (
    DEFAULT_CONFIG,
    Config,
    get_user_config_path,
    load_config,
    load_yaml_file,
)


class TestConfig:
    """Tests for the Config dataclass."""
    
    def test_get_destination_folder_known_extension(self) -> None:
        """Test that known extensions return correct folder."""
        config = Config(
            rules={"Images": ["jpg", "png"], "Documents": ["pdf", "txt"]},
            default_folder="Misc",
        )
        
        assert config.get_destination_folder("jpg") == "Images"
        assert config.get_destination_folder("png") == "Images"
        assert config.get_destination_folder("pdf") == "Documents"
        assert config.get_destination_folder("txt") == "Documents"
    
    def test_get_destination_folder_case_insensitive(self) -> None:
        """Test that extension matching is case insensitive."""
        config = Config(
            rules={"Images": ["jpg", "png"]},
            default_folder="Misc",
        )
        
        assert config.get_destination_folder("JPG") == "Images"
        assert config.get_destination_folder("Jpg") == "Images"
        assert config.get_destination_folder("PNG") == "Images"
    
    def test_get_destination_folder_unknown_extension(self) -> None:
        """Test that unknown extensions return default folder."""
        config = Config(
            rules={"Images": ["jpg"]},
            default_folder="Misc",
        )
        
        assert config.get_destination_folder("xyz") == "Misc"
        assert config.get_destination_folder("unknown") == "Misc"
    
    def test_build_extension_map(self) -> None:
        """Test building extension to folder map."""
        config = Config(
            rules={"Images": ["jpg", "png"], "Documents": ["pdf"]},
            default_folder="Misc",
        )
        
        ext_map = config.build_extension_map()
        
        assert ext_map["jpg"] == "Images"
        assert ext_map["png"] == "Images"
        assert ext_map["pdf"] == "Documents"
        assert "misc" not in ext_map


class TestLoadYamlFile:
    """Tests for the load_yaml_file function."""
    
    def test_load_existing_file(self, tmp_path: Path) -> None:
        """Test loading an existing YAML file."""
        config_file = tmp_path / "config.yaml"
        config_data = {"rules": {"Test": ["txt"]}, "default_folder": "Other"}
        
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        result = load_yaml_file(config_file)
        
        assert result is not None
        assert result["default_folder"] == "Other"
        assert result["rules"]["Test"] == ["txt"]
    
    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that nonexistent file returns None."""
        result = load_yaml_file(tmp_path / "nonexistent.yaml")
        assert result is None


class TestLoadConfig:
    """Tests for the load_config function."""
    
    def test_load_default_config(self) -> None:
        """Test loading falls back to defaults."""
        # This should use defaults if no config file exists
        config = load_config()
        
        assert config.rules is not None
        assert len(config.rules) > 0
        assert config.default_folder is not None
    
    def test_load_custom_config(self, tmp_path: Path) -> None:
        """Test loading a custom config file."""
        config_file = tmp_path / "custom.yaml"
        config_data = {
            "rules": {"CustomFolder": ["xyz"]},
            "default_folder": "CustomMisc",
            "exclude_patterns": ["*.custom"],
        }
        
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        config = load_config(config_file)
        
        assert "CustomFolder" in config.rules
        assert config.rules["CustomFolder"] == ["xyz"]
        assert config.default_folder == "CustomMisc"
        assert "*.custom" in config.exclude_patterns
    
    def test_load_nonexistent_config_raises(self, tmp_path: Path) -> None:
        """Test that explicit nonexistent config raises error."""
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yaml")
    
    def test_partial_config_uses_defaults(self, tmp_path: Path) -> None:
        """Test that missing keys use defaults."""
        config_file = tmp_path / "partial.yaml"
        config_data = {"rules": {"OnlyImages": ["jpg"]}}
        
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        config = load_config(config_file)
        
        # Custom rules are used
        assert "OnlyImages" in config.rules
        # Default folder falls back to default
        assert config.default_folder == DEFAULT_CONFIG["default_folder"]


class TestGetUserConfigPath:
    """Tests for the get_user_config_path function."""
    
    def test_returns_path_object(self) -> None:
        """Test that function returns a Path object."""
        result = get_user_config_path()
        assert isinstance(result, Path)
    
    def test_path_ends_with_config_yaml(self) -> None:
        """Test that path ends with config.yaml."""
        result = get_user_config_path()
        assert result.name == "config.yaml"
    
    def test_path_contains_fso(self) -> None:
        """Test that path contains fso directory."""
        result = get_user_config_path()
        assert "fso" in str(result)
