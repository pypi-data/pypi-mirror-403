import asyncio
from .server import Server

class HostServer:
    def __init__(self):
        self.hosts = {}
        self.counter = 0

    def create(self, host="localhost", port=None):
        if port is None:
            port = 9000 + self.counter
        self.counter += 1

        server = Server(host, port)
        self.hosts[port] = server
        server.run()
        return server

    def find(self, port):
        return self.hosts.get(port)

    def end(self, port):
        srv = self.hosts.pop(port, None)
        if srv:
            srv.endserving()

    def endall(self):
        for p in list(self.hosts):
            self.end(p)

    async def repeatserve(self, times=100):
        for srv in self.hosts.values():
            await srv.repeatserve(times)
