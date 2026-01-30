import json
import asyncio
from typing import List, Optional, AsyncGenerator
import websockets

class BaseWebsocketClient:
    """
    Base class for FinancialModelingPrep WebSocket clients.
    Handles connection, login, subscription, and yields messages.
    """
    def __init__(self, tickers: List[str], api_key: str, uri: str) -> None:
        self.tickers = tickers if isinstance(tickers, list) else [tickers]
        self.api_key = api_key
        self.uri = uri
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None

    async def connect(self) -> None:
        self.websocket = await websockets.connect(self.uri)
        print(f"Connected to {self.uri}")

    async def login(self) -> None:
        login_msg = {"event": "login", "data": {"apiKey": self.api_key}}
        await self.websocket.send(json.dumps(login_msg))
        print("Sent login message")

    async def subscribe(self) -> None:
        subscribe_msg = {"event": "subscribe", "data": {"ticker": self.tickers}}
        await self.websocket.send(json.dumps(subscribe_msg))
        print(f"Subscribed to tickers: {self.tickers}")

    async def run(self) -> AsyncGenerator[dict, None]:
        """
        Connects, logs in, waits for confirmation, subscribes,
        and yields messages continuously.
        """
        await self.connect()
        await self.login()
        while True:
            response = await self.websocket.recv()
            message = json.loads(response)
            if message.get("event") == "login":
                if message.get("status") == 200:
                    print("Login successful")
                    break
                else:
                    raise Exception("Login failed: " + message.get("message", "Unknown error"))
            else:
                print("Received (before login confirmation):", message)
        await self.subscribe()
        try:
            while True:
                response = await self.websocket.recv()
                data = json.loads(response)
                yield data
        except websockets.ConnectionClosed:
            print("Connection closed by the server.")
        finally:
            await self.websocket.close()
