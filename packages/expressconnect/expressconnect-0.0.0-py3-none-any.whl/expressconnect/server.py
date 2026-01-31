import asyncio
import websockets
from .events import Event

class Server:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.on_message = Event()
        self.on_connect = Event()
        self.clients = set()

    async def _handler(self, websocket):
        self.clients.add(websocket)
        self.on_connect.fire(websocket)

        try:
            async for message in websocket:
                self.on_message.fire("user", message)
                await self.broadcast(message)
        finally:
            self.clients.remove(websocket)

    async def broadcast(self, msg):
        for client in self.clients:
            await client.send(msg)

    def run(self):
        asyncio.run(
            websockets.serve(self._handler, self.host, self.port)
        )