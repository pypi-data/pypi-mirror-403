import json
from typing import Dict, Any, Optional
import importlib.resources as pkg_resources

class ConfigManager:
    """
    Loads and caches a JSON configuration file.
    If no config_file is provided, loads the default configuration
    from the package resource fmp_endpoints.json.
    """
    def __init__(self, config_file: Optional[str] = None) -> None:
        self.config_file = config_file
        self._config: Optional[Dict[str, Any]] = None

    def get(self) -> Dict[str, Any]:
        if self._config is None:
            if self.config_file is None:
                # Load default configuration from package resources.
                with pkg_resources.open_text("fmpstab", "fmpstab_endpoints.json") as f:
                    self._config = json.load(f)
            else:
                with open(self.config_file, "r") as f:
                    self._config = json.load(f)
        return self._config

    def reload(self) -> Dict[str, Any]:
        """Force reload of the configuration file."""
        if self.config_file is None:
            with pkg_resources.open_text("fmpstab", "fmpstab_endpoints.json") as f:
                self._config = json.load(f)
        else:
            with open(self.config_file, "r") as f:
                self._config = json.load(f)
        return self._config
