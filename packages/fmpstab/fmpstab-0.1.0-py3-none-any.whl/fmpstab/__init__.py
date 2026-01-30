"""
Financial Modeling Prep Client Library

Exposes:
    fmpstab: Unified REST API client.
    Logger: Logging utility.
    ConfigManager: Configuration loader.
    Session: HTTP session with rate limiting.
    StockWebsockets: WebSocket client for stock data.
    CryptoWebsockets: WebSocket client for crypto data.
    ForexWebsockets: WebSocket client for forex data.
"""

from .logger import Logger
from .config_manager import ConfigManager
from .dynamic import create_endpoint_method, attach_dynamic_functions
from .session import Session
from .fmpstab_client import FMPStab

from .fmpstab_websockets.stock_websocket import StockWebsockets
from .fmpstab_websockets.crypto_websocket import CryptoWebsockets
from .fmpstab_websockets.forex_websocket import ForexWebsockets

__all__ = [
    "FMPStab",
    "Logger",
    "ConfigManager",
    "Session",
    "StockWebsockets",
    "CryptoWebsockets",
    "ForexWebsockets",
]
