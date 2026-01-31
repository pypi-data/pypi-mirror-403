import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

CONFIG_DIR = Path.home() / ".nexula"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
PROJECT_CONFIG = ".nexula.yaml"


class Config:
    def __init__(self):
        self.config_dir = CONFIG_DIR
        self.config_file = CONFIG_FILE
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Ensure config directory exists with proper permissions"""
        self.config_dir.mkdir(mode=0o700, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """Load global config"""
        if not self.config_file.exists():
            return {}
        with open(self.config_file, "r") as f:
            return yaml.safe_load(f) or {}

    def save(self, data: Dict[str, Any]):
        """Save global config"""
        with open(self.config_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
        os.chmod(self.config_file, 0o600)

    def get_api_key(self) -> Optional[str]:
        """Get stored API key"""
        config = self.load()
        return config.get("api_key")

    def set_api_key(self, api_key: str):
        """Store API key securely"""
        config = self.load()
        config["api_key"] = api_key
        self.save(config)

    def get_api_url(self) -> str:
        """Get API URL"""
        config = self.load()
        return config.get("api_url", "https://api.nexula.one/api/v1")

    def set_api_url(self, url: str):
        """Set API URL"""
        config = self.load()
        config["api_url"] = url
        self.save(config)

    def clear(self):
        """Clear all config"""
        if self.config_file.exists():
            self.config_file.unlink()

    def load_project_config(self) -> Dict[str, Any]:
        """Load project-level config"""
        project_file = Path.cwd() / PROJECT_CONFIG
        if not project_file.exists():
            return {}
        with open(project_file, "r") as f:
            return yaml.safe_load(f) or {}

    def save_project_config(self, data: Dict[str, Any]):
        """Save project-level config"""
        project_file = Path.cwd() / PROJECT_CONFIG
        with open(project_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    def get_project_id(self) -> Optional[int]:
        """Get current project ID"""
        config = self.load_project_config()
        return config.get("project_id")

    def get_workspace_id(self) -> Optional[int]:
        """Get current workspace ID"""
        config = self.load_project_config()
        return config.get("workspace_id")


config = Config()
