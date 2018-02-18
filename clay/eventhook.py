"""
Events implemetation for signal handling.
"""


class EventHook(object):
    """
    Event that can have handlers attached.
    """
    def __init__(self):
        self.event_handlers = []

    def __iadd__(self, handler):
        """
        Add event handler.
        """
        self.event_handlers.append(handler)
        return self

    def __isub__(self, handler):
        """
        Remove event handler.
        """
        self.event_handlers.remove(handler)
        return self

    def fire(self, *args, **kwargs):
        """
        Execute all handlers.
        """
        for handler in self.event_handlers:
            handler(*args, **kwargs)
