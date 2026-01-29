"""Configuration loader for fso (File System Organizer).

Handles loading and validating the YAML configuration file,
with support for user-specific config locations on all platforms.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from platformdirs import user_config_dir

APP_NAME = "fso"

# Default configuration values
DEFAULT_CONFIG: dict = {
    "rules": {
        "Images": ["jpg", "jpeg", "png", "gif", "svg", "webp", "ico", "bmp", "tiff", "raw", "heic"],
        "Documents": ["pdf", "doc", "docx", "txt", "rtf", "odt", "xlsx", "xls", "pptx", "ppt", "csv", "epub"],
        "Archives": ["zip", "tar", "rar", "gz", "7z", "bz2", "xz", "iso"],
        "Videos": ["mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v", "mpeg", "mpg"],
        "Audio": ["mp3", "wav", "flac", "aac", "ogg", "m4a", "wma", "opus", "aiff"],
        "Code": ["py", "js", "ts", "html", "css", "json", "xml", "yaml", "yml", "md", "sh", "bat", "ps1"],
        "Executables": ["exe", "msi", "dmg", "deb", "rpm", "appimage", "apk"],
    },
    "default_folder": "Misc",
    "exclude_patterns": ["*.tmp", "*.part", "*.crdownload", "*.download", "desktop.ini", "Thumbs.db", ".DS_Store"],
}


@dataclass
class Config:
    """Configuration for file organization rules."""
    
    rules: dict[str, list[str]] = field(default_factory=dict)
    default_folder: str = "Misc"
    exclude_patterns: list[str] = field(default_factory=list)
    
    def get_destination_folder(self, extension: str) -> str:
        """Get the destination folder for a given file extension.
        
        Args:
            extension: File extension without the dot (e.g., 'jpg', 'pdf')
            
        Returns:
            The folder name where files with this extension should go.
        """
        ext_lower = extension.lower()
        for folder, extensions in self.rules.items():
            if ext_lower in [e.lower() for e in extensions]:
                return folder
        return self.default_folder
    
    def build_extension_map(self) -> dict[str, str]:
        """Build a reverse map from extension to folder for quick lookups.
        
        Returns:
            Dictionary mapping extensions to their destination folders.
        """
        ext_map: dict[str, str] = {}
        for folder, extensions in self.rules.items():
            for ext in extensions:
                ext_map[ext.lower()] = folder
        return ext_map


def get_user_config_path() -> Path:
    """Get the platform-specific user configuration directory.
    
    Returns:
        Path to the user's config file location.
        - Windows: %LOCALAPPDATA%/fso/config.yaml
        - macOS: ~/Library/Application Support/fso/config.yaml
        - Linux: ~/.config/fso/config.yaml
    """
    config_dir = Path(user_config_dir(APP_NAME, appauthor=False))
    return config_dir / "config.yaml"


def get_default_config_path() -> Path:
    """Get the path to the default config.yaml bundled with the package.
    
    Returns:
        Path to the default config file in the project root.
    """
    # Look for config.yaml in the project root (parent of fso package)
    package_dir = Path(__file__).parent
    project_root = package_dir.parent
    return project_root / "config.yaml"


def load_yaml_file(path: Path) -> Optional[dict]:
    """Load a YAML file and return its contents.
    
    Args:
        path: Path to the YAML file.
        
    Returns:
        Parsed YAML contents as a dictionary, or None if file doesn't exist.
        
    Raises:
        yaml.YAMLError: If the file contains invalid YAML.
    """
    if not path.exists():
        return None
    
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from file or use defaults.
    
    Config priority (highest to lowest):
    1. Explicit path provided via config_path argument
    2. User config in platform-specific location
    3. Default config.yaml in project root
    4. Built-in default configuration
    
    Args:
        config_path: Optional explicit path to a config file.
        
    Returns:
        Config object with loaded or default settings.
    """
    config_data: Optional[dict] = None
    
    # Try loading config in priority order
    if config_path:
        config_data = load_yaml_file(config_path)
        if config_data is None:
            raise FileNotFoundError(f"Config file not found: {config_path}")
    
    if config_data is None:
        # Try user config location
        user_config = get_user_config_path()
        config_data = load_yaml_file(user_config)
    
    if config_data is None:
        # Try default config in project root
        default_config = get_default_config_path()
        config_data = load_yaml_file(default_config)
    
    if config_data is None:
        # Use built-in defaults
        config_data = DEFAULT_CONFIG.copy()
    
    # Validate and build Config object
    return Config(
        rules=config_data.get("rules", DEFAULT_CONFIG["rules"]),
        default_folder=config_data.get("default_folder", DEFAULT_CONFIG["default_folder"]),
        exclude_patterns=config_data.get("exclude_patterns", DEFAULT_CONFIG["exclude_patterns"]),
    )


def save_user_config(config: Config) -> Path:
    """Save configuration to the user's config location.
    
    Creates the config directory if it doesn't exist.
    
    Args:
        config: Config object to save.
        
    Returns:
        Path where the config was saved.
    """
    config_path = get_user_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    config_data = {
        "rules": config.rules,
        "default_folder": config.default_folder,
        "exclude_patterns": config.exclude_patterns,
    }
    
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
    
    return config_path
