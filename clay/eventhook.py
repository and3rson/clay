class EventHook(object):
    def __init__(self):
        self.event_handlers = []

    def __iadd__(self, handler):
        self.event_handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.event_handlers.remove(handler)
        return self

    def fire(self, *args, **kwargs):
        for handler in self.event_handlers:
            handler(*args, **kwargs)

