import os
import sys
import urllib.parse
from typing import Optional, Dict, Any
import requests

from .config_manager import ConfigManager
from .logger import Logger
from .session import Session
from .dynamic import attach_dynamic_functions

class FMPStab:
    """
    Unified Financial Modeling Prep API client.
    
    Combines configuration management, HTTP session handling, dynamic endpoint methods,
    and helper functions into one class.
    
    Example:
        client = FMPStab(api_key="YOUR_API_KEY")
        response = client.profile(symbol="AAPL")
        print(response.json())
    """
    def __init__(self,
                 api_key: str,
                 config_file: Optional[str] = None,
                 base_url: Optional[str] = None,
                 logger: Optional[Logger] = None,
                 log_enabled: bool = True) -> None:
        self.api_key = api_key
        # Let ConfigManager load the default config from package resources if config_file is None.
        self.config_manager = ConfigManager(config_file)
        self.config = self.config_manager.get()
        self.base_url = base_url or self.config.get("base_url")
        if logger is None:
            logger = Logger("FMPStab", enabled=log_enabled)
        self.logger = logger
        self.session = Session(api_key, logger=logger)
        self.endpoints: Dict[str, Any] = self.config.get("endpoints", {})
        attach_dynamic_functions(self)

    def call(self, endpoint_name: str, **kwargs) -> requests.Response:
        if endpoint_name not in self.endpoints:
            raise ValueError(f"Endpoint '{endpoint_name}' not found in configuration.")
        endpoint_info = self.endpoints[endpoint_name]
        url = urllib.parse.urljoin(self.base_url, endpoint_info["path"])
        allowed = endpoint_info.get("params", {}).keys()
        params = {k: v for k, v in kwargs.items() if k in allowed}
        params["apikey"] = self.api_key
        return self.session.get(url, params=params)

    def help(self, endpoint: Optional[str] = None) -> str:
        """
        Returns help information for endpoints.
        """
        doc = ("FMPStab API Client Help\n\nUsage:\n  client.endpoint_name(param1=value1, ...)\n"
               "Example:\n  client.profile(symbol='AAPL')\n\n")
        if endpoint:
            target = next((key for key in self.endpoints if key.replace("-", "_") == endpoint), None)
            if not target:
                doc += f"Endpoint '{endpoint}' not found.\n"
            else:
                config = self.endpoints[target]
                doc += f"Help for endpoint '{target}':\n  Path: {config.get('path')}\n"
                params = config.get("params", {})
                if params:
                    doc += "  Allowed parameters:\n"
                    for param, details in params.items():
                        required = details.get("required", False)
                        param_type = details.get("type", "unknown")
                        example = details.get("example", "")
                        doc += f"    - {param} (required: {required}, type: {param_type}, example: {example})\n"
                else:
                    doc += "  No parameters defined.\n"
        else:
            for ep, config in self.endpoints.items():
                func_name = ep.replace("-", "_")
                doc += f"\nEndpoint: {func_name}\n  Path: {config.get('path')}\n"
                params = config.get("params", {})
                if params:
                    doc += "  Allowed parameters:\n"
                    for param, details in params.items():
                        required = details.get("required", False)
                        param_type = details.get("type", "unknown")
                        example = details.get("example", "")
                        doc += f"    - {param} (required: {required}, type: {param_type}, example: {example})\n"
                else:
                    doc += "  No parameters defined.\n"
            doc += "\n"
        return doc

    def man_page(self, just_name: bool = False, filename: str = "FMPStab_man_page.txt") -> str:
        main_dir = (os.path.dirname(sys.modules["__main__"].__file__)
                    if "__main__" in sys.modules and hasattr(sys.modules["__main__"], "__file__")
                    else os.getcwd())
        doc_file = os.path.join(main_dir, filename)
        if os.path.exists(doc_file):
            os.remove(doc_file)
        output = "Manual Page for FMPStab API Client Endpoints:\n"
        for ep, config in self.endpoints.items():
            func_name = ep.replace("-", "_")
            if just_name:
                output += f"\n\t{func_name}"
            else:
                output += f"\n\nEndpoint: {func_name}\n  Path: {config.get('path')}\n"
                params = config.get("params", {})
                if params:
                    output += "  Allowed parameters:\n"
                    for param, details in params.items():
                        required = details.get("required", False)
                        param_type = details.get("type", "unknown")
                        example = details.get("example", "")
                        output += f"    - {param} (required: {required}, type: {param_type}, example: {example})\n"
                else:
                    output += "  No parameters defined.\n"
        with open(doc_file, "w") as f:
            f.write(output)
        return output
