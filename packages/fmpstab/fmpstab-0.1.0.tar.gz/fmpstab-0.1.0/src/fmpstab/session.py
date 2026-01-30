import requests
from typing import Optional, Dict, Any
from ratelimit import limits, sleep_and_retry
from concurrent.futures import ThreadPoolExecutor
from .logger import Logger

REQUEST_RATE = {"calls": 3000, "seconds": 60}

class Session:
    """
    Provides a persistent HTTP session with rate limiting.
    """
    def __init__(self, api_key: str, logger: Optional[Logger] = None) -> None:
        self.api_key = api_key
        self.session = requests.Session()
        self.logger = logger if logger is not None else Logger("FMPStab.Session", enabled=True)
        self.executor = ThreadPoolExecutor(max_workers=5)

    @sleep_and_retry
    @limits(calls=REQUEST_RATE["calls"], period=REQUEST_RATE["seconds"])
    def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        self.logger.info(f"HTTP GET: {url} with params {params}")
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            self.logger.info(f"Response: {response.status_code}")
            return response
        except Exception as e:
            self.logger.error(f"HTTP GET error: {e}")
            raise
