"""Configuration management for caffeine."""

import json
import os
from pathlib import Path
from typing import Optional


def get_config_dir() -> Path:
    """Get the configuration directory path.
    
    Uses ~/.config/caffeine on Unix-like systems.
    """
    # Check for XDG_CONFIG_HOME first (Linux standard)
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        config_dir = Path(xdg_config) / "caffeine"
    else:
        # Default to ~/.config/caffeine
        config_dir = Path.home() / ".config" / "caffeine"
    
    return config_dir


def get_config_file() -> Path:
    """Get the configuration file path."""
    return get_config_dir() / "config.json"


def load_config() -> dict:
    """Load configuration from file.
    
    Returns:
        Configuration dictionary.
    """
    config_file = get_config_file()
    
    if not config_file.exists():
        return {}
    
    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_config(config: dict) -> None:
    """Save configuration to file.
    
    Args:
        config: Configuration dictionary to save.
    """
    config_dir = get_config_dir()
    config_file = get_config_file()
    
    # Create directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)


def get_token() -> Optional[str]:
    """Get the GitHub token.
    
    Checks in order:
    1. GITHUB_TOKEN environment variable
    2. GH_TOKEN environment variable (GitHub CLI standard)
    3. Saved config file
    
    Returns:
        GitHub token if found, None otherwise.
    """
    # Check environment variables first
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    
    # Check config file
    config = load_config()
    return config.get("github_token")


def set_token(token: str) -> None:
    """Save the GitHub token to config file.
    
    Args:
        token: GitHub personal access token.
    """
    config = load_config()
    config["github_token"] = token
    save_config(config)


def remove_token() -> bool:
    """Remove the saved GitHub token.
    
    Returns:
        True if token was removed, False if no token was saved.
    """
    config = load_config()
    if "github_token" in config:
        del config["github_token"]
        save_config(config)
        return True
    return False


def get_config_info() -> dict:
    """Get information about current configuration.
    
    Returns:
        Dictionary with config info.
    """
    token = get_token()
    config_file = get_config_file()
    
    # Determine token source
    if os.environ.get("GITHUB_TOKEN"):
        token_source = "GITHUB_TOKEN environment variable"
    elif os.environ.get("GH_TOKEN"):
        token_source = "GH_TOKEN environment variable"
    elif token:
        token_source = f"config file ({config_file})"
    else:
        token_source = None
    
    return {
        "has_token": token is not None,
        "token_source": token_source,
        "token_preview": f"{token[:4]}...{token[-4:]}" if token and len(token) > 8 else None,
        "config_file": str(config_file),
    }

