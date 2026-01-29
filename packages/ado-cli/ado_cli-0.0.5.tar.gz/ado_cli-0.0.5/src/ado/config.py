import json
import os
from typing import Any, Dict


CONFIG_FILE = os.path.expanduser("~/.ado/config.json")


class AdoConfig:
    """Manage Azure DevOps Server configuration"""

    def __init__(self):
        self.config = self.load()

    def load(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save(self):
        """Save configuration to file"""
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
        self.save()

    def remove(self, key: str):
        """Remove configuration value"""
        if key in self.config:
            del self.config[key]
            self.save()
