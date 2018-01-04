import urwid


class Notification(urwid.Columns):
    TEMPLATE = u' \u26A1 {}'

    def __init__(self, area, id, message):
        self.area = area
        self.id = id
        self.text = urwid.Text('')
        self.update(message)
        super(Notification, self).__init__([
            urwid.AttrWrap(
                urwid.Columns([
                    self.text,
                    ('pack', urwid.Text('[Hit ESC to close] '))
                ]),
                'notification'
            )
        ])

    def update(self, message):
        message = message.split('\n')
        message = '\n'.join([
            message[0]
        ] + ['    {}'.format(line) for line in message[1:]])
        self.text.set_text(Notification.TEMPLATE.format(message))

    def close(self):
        for notification, props in reversed(self.area.contents):
            if notification is self:
                self.area.contents.remove((notification, props))


class NotificationArea(urwid.Pile):
    instance = None
    app = None

    def __init__(self):
        self.last_id = 0
        self.notifications = {}
        super(NotificationArea, self).__init__([])

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
        return cls.get()._notify(message)

    @classmethod
    def close_all(cls):
        cls.get()._close_all()

    @classmethod
    def close_newest(cls):
        cls.get()._close_newest()

    def _notify(self, message):
        self.last_id += 1
        notification = Notification(self, self.last_id, message)
        self.contents.append(
            (
                notification,
                ('weight', 1)
            )
        )
        if self.__class__.app is not None:
            self.__class__.app.redraw()
        return notification

    def _close_all(self):
        while len(self.contents):
            self.contents[0][0].close()

    def _close_newest(self):
        if not len(self.contents):
            return
        self.contents[-1][0].close()

