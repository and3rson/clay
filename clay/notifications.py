import urwid


class NotificationArea(urwid.Pile):
    instance = None
    app = None

    TEMPLATE = ' \u26A1 {}'

    def __init__(self):
        super().__init__([])

    @classmethod
    def get(cls):
        if cls.instance is None:
            cls.instance = NotificationArea()

        return cls.instance

    @classmethod
    def set_app(cls, app):
        cls.app = app

    @classmethod
    def notify(cls, message):
        cls.instance._notify(message)

    @classmethod
    def close_all(cls):
        cls.instance._close_all()

    def _notify(self, message):
        text = urwid.Text(self.__class__.TEMPLATE.format(message))
        self.contents.append(
            (
                urwid.AttrWrap(
                    urwid.Columns([
                        text,
                        ('pack', urwid.Text('[Hit ESC to close] '))
                    ]),
                    'notification'
                ),
                ('weight', 1)
            )
        )
        self.__class__.app.redraw()

    def _close_all(self):
        self.contents[:] = []

