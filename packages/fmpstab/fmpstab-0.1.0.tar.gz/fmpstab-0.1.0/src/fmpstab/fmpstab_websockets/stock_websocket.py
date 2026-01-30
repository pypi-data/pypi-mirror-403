from typing import List
from .base_websocket_client import BaseWebsocketClient

class StockWebsockets(BaseWebsocketClient):
    def __init__(self, tickers: List[str], api_key: str, 
                 uri: str = "wss://websockets.financialmodelingprep.com") -> None:
        super().__init__(tickers, api_key, uri)
