class EventBus:
    def __init__(self):
        self._events = {}

    def on(self, name, func):
        self._events.setdefault(name, []).append(func)

    async def emit(self, name, *args, **kwargs):
        for fn in self._events.get(name, []):
            res = fn(*args, **kwargs)
            if hasattr(res, "__await__"):
                await res
