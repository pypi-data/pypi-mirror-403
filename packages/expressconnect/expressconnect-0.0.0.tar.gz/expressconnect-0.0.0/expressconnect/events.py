class Event:
    def __init__(self):
        self.handler = None

    def __call__(self, func):
        self.handler = func
        return func

    def fire(self, *args, **kwargs):
        if self.handler:
            self.handler(*args, **kwargs)