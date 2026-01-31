import asyncio
import websockets

class Server:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self._clients = set()
        self._tasks = []

    # ------------------------------
    # CORE HANDLER
    # ------------------------------
    async def _handler(self, websocket, path=None):
        self._clients.add(websocket)
        try:
            async for msg in websocket:
                await self.listen(msg, websocket)
        finally:
            self._clients.remove(websocket)

    # ------------------------------
    # RUN METHODS
    # ------------------------------
    def run(self):
        asyncio.run(self.run_async())

    async def run_async(self):
        async with websockets.serve(self._handler, self.host, self.port):
            print(f"Server running on {self.host}:{self.port}")
            await self.serve_forever()

    async def _serve(self):
        await websockets.serve(self._handler, self.host, self.port)

    async def serve_forever(self):
        await asyncio.Future()  # keeps server running indefinitely

    async def repeatserve(self, times=100):
        for _ in range(times):
            await self._serve()

    def endserving(self):
        for t in self._tasks:
            t.cancel()

    # ------------------------------
    # UTILITY
    # ------------------------------
    async def listen(self, msg, websocket):
        # broadcast to all clients
        for c in self._clients:
            if c != websocket:
                await c.send(msg)

    async def ping(self):
        for c in self._clients:
            await c.ping()

    def createtask(self, coro):
        task = asyncio.create_task(coro)
        self._tasks.append(task)
        return task

    def endtask(self, task):
        task.cancel()
        if task in self._tasks:
            self._tasks.remove(task)

    def multitaskinit(self, coros):
        for c in coros:
            self.createtask(c)

    async def endmultitask(self):
        for t in self._tasks:
            t.cancel()
        self._tasks.clear()

    async def multitask(self, coros):
        await asyncio.gather(*coros)
