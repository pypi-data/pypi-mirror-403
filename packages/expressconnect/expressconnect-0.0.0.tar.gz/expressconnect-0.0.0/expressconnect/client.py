import asyncio
import websockets
from .events import Event

class Client:
    def __init__(self, url, username="python"):
        self.url = url
        self.username = username
        self.on_message = Event()

    async def _listen(self):
        async with websockets.connect(self.url) as ws:
            self.ws = ws
            async for msg in ws:
                self.on_message.fire(msg, self.username)

    def send(self, msg):
        asyncio.create_task(self.ws.send(msg))

    def wait(self, seconds):
        import time
        time.sleep(seconds)

    def run(self):
        asyncio.run(self._listen())