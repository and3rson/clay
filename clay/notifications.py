"""
Notification widgets.
"""
# pylint: disable=invalid-name
import urwid


class Notification(urwid.Columns):
    """
    Single notification widget.
    Can be updated or closed.
    """
    TEMPLATE = u' \u26A1 {}'

    def __init__(self, area, notification_id, message):
        self.area = area
        self._id = notification_id
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

    @property
    def id(self):
        """
        Notification ID.
        """
        return self._id

    def update(self, message):
        """
        Update notification message.
        """
        message = message.split('\n')
        message = '\n'.join([
            message[0]
        ] + ['    {}'.format(line) for line in message[1:]])
        self.text.set_text(Notification.TEMPLATE.format(message))
        self.area.__class__.app.redraw()

    def close(self):
        """
        Close notification.
        """
        for notification, props in reversed(self.area.contents):
            if notification is self:
                self.area.contents.remove((notification, props))


class NotificationArea(urwid.Pile):
    """
    Notification area widget.
    """
    instance = None
    app = None

    def __init__(self):
        assert self.__class__.instance is None, 'Can be created only once!'
        self.last_id = 0
        self.notifications = {}
        super(NotificationArea, self).__init__([])

    @classmethod
    def get(cls):
        """
        Create new :class:`.NotificationArea` instance or return existing one.
        """
        if cls.instance is None:
            cls.instance = NotificationArea()

        return cls.instance

    @classmethod
    def set_app(cls, app):
        """
        Set app instance.

        Required for proper screen redraws when
        new notifications are created asynchronously.
        """
        cls.app = app

    @classmethod
    def notify(cls, message):
        """
        Create new notification with message.
        This is a class method.
        """
        return cls.get().do_notify(message)

    @classmethod
    def close_all(cls):
        """
        Close all notfiications.
        This is a class method.
        """
        cls.get().do_close_all()

    @classmethod
    def close_newest(cls):
        """
        Close newest notification.
        This is a class method.
        """
        cls.get().do_close_newest()

    def do_notify(self, message):
        """
        Create new notification with message.
        """
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

    def do_close_all(self):
        """
        Close all notifications.
        """
        while self.contents:
            self.contents[0][0].close()

    def do_close_newest(self):
        """
        Close newest notification
        """
        if not self.contents:
            return
        self.contents[-1][0].close()
