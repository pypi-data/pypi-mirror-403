import asyncio
import threading

class CustomPython:
    def __init__(self):
        self.globals = {}
        self.tasks = set()

    def run(self, code: str, local=None):
        if local is None:
            local = {}
        exec(code, self.globals, local)
        return local

    async def run_async(self, code: str, local=None):
        if local is None:
            local = {}
        exec(
            f"async def __custom__():\n" +
            "\n".join("    " + l for l in code.splitlines()),
            self.globals,
            local
        )
        return await local["__custom__"]()

    def run_threaded(self, code):
        t = threading.Thread(target=self.run, args=(code,))
        t.daemon = True
        t.start()
        return t

    def createtask(self, coro):
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task

    def endtask(self, task):
        task.cancel()

    def endall(self):
        for t in list(self.tasks):
            t.cancel()
        self.tasks.clear()
