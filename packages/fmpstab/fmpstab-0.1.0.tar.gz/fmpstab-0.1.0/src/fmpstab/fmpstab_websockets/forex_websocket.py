from typing import List
from .base_websocket_client import BaseWebsocketClient

class ForexWebsockets(BaseWebsocketClient):
    def __init__(self, pairs: List[str], api_key: str, 
                 uri: str = "wss://forex.financialmodelingprep.com") -> None:
        super().__init__(pairs, api_key, uri)
