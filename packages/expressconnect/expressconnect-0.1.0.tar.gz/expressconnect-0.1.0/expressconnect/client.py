import asyncio
import websockets
import threading
from .events import EventBus

class Client:
    def __init__(self, uri):
        self.uri = uri
        self.ws = None
        self.loop = None
        self.events = EventBus()
        self.tasks = set()

    async def _connect(self):
        self.ws = await websockets.connect(self.uri)
        await self.events.emit("connect", self.ws)
        async for msg in self.ws:
            await self.events.emit("message", msg)

    async def run_async(self):
        await self._connect()

    def run(self):
        def runner():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._connect())

        threading.Thread(target=runner, daemon=True).start()

    async def send(self, msg):
        await self.ws.send(msg)

    async def ping(self, msg="ping"):
        await self.send(msg)

    def listen(self, fn):
        self.events.on("message", fn)

    def createtask(self, coro):
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task

    def endtask(self, task):
        task.cancel()

    def multitaskinit(self, *coros):
        return [self.createtask(c) for c in coros]

    def endmultitask(self):
        for t in list(self.tasks):
            t.cancel()
        self.tasks.clear()

    def multitask(self, *coros):
        return self.multitaskinit(*coros)
