from typing import List
from .base_websocket_client import BaseWebsocketClient

class CryptoWebsockets(BaseWebsocketClient):
    def __init__(self, tickers: List[str], api_key: str, 
                 uri: str = "wss://crypto.financialmodelingprep.com") -> None:
        super().__init__(tickers, api_key, uri)
