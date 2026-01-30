import os
from pathlib import Path

import toml


class TUIConfig:
    """TUI configuration using XDG Base Directory."""

    @staticmethod
    def get_config_path() -> Path:
        """Get config file path following XDG spec."""
        xdg_config_home = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        config_dir = Path(xdg_config_home) / "flux-config"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.toml"

    @staticmethod
    def load() -> dict:
        """Load configuration from file."""
        config_path = TUIConfig.get_config_path()
        if config_path.exists():
            return toml.load(config_path)
        return {}

    @staticmethod
    def save(config: dict) -> None:
        """Save configuration to file."""
        config_path = TUIConfig.get_config_path()
        with open(config_path, "w") as f:
            toml.dump(config, f)

    @staticmethod
    def get_ssh_key_path() -> str | None:
        """Get SSH key path from config or environment variable."""
        env_key = os.getenv("FLUX_CONFIG_SSH_KEY")
        if env_key:
            return env_key

        config = TUIConfig.load()
        return config.get("ssh", {}).get("key_path")
