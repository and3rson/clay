"""
Notification widgets.
"""
import urwid


class _Notification(urwid.Columns):
    """
    Single notification widget.
    Can be updated or closed.
    """
    TEMPLATE = u' \u26A1 {}'

    def __init__(self, area, notification_id, message):
        self.area = area
        self._id = notification_id
        self.text = urwid.Text('')
        self._set_text(message)
        super(_Notification, self).__init__([
            urwid.AttrWrap(
                urwid.Columns([
                    self.text,
                    ('pack', urwid.Text('[Hit ESC to close] '))
                ]),
                'notification'
            )
        ])

    @property
    def id(self):  # pylint: disable=invalid-name
        """
        Notification ID.
        """
        return self._id

    def _set_text(self, message):
        """
        Set contents for this notification.
        """
        message = message.split('\n')
        message = '\n'.join([
            message[0]
        ] + ['    {}'.format(line) for line in message[1:]])
        self.text.set_text(_Notification.TEMPLATE.format(message))

    def update(self, message):
        """
        Update notification message.
        """
        self._set_text(message)
        if not self.is_alive:
            self.area.append_notification(self)
        self.area.app.redraw()

    @property
    def is_alive(self):
        """
        Return True if notification is currently visible.
        """
        for notification, _ in self.area.contents:
            if notification is self:
                return True
        return False

    def close(self):
        """
        Close notification.
        """
        for notification, props in reversed(self.area.contents):
            if notification is self:
                self.area.contents.remove((notification, props))

        if self.area.app is not None:
            self.area.app.redraw()


class _NotificationArea(urwid.Pile):
    """
    Notification area widget.
    """

    def __init__(self):
        self.app = None
        self.last_id = 0
        self.notifications = {}
        super(_NotificationArea, self).__init__([])

    def set_app(self, app):
        """
        Set app instance.

        Required for proper screen redraws when
        new notifications are created asynchronously.
        """
        self.app = app

    def notify(self, message):
        """
        Create new notification with message.
        """
        self.last_id += 1
        notification = _Notification(self, self.last_id, message)
        self.append_notification(notification)
        return notification

    def append_notification(self, notification):
        """
        Append an existing notification (that was probably closed).
        """
        self.contents.append(
            (
                notification,
                ('weight', 1)
            )
        )
        if self.app is not None:
            self.app.redraw()

    def close_all(self):
        """
        Close all notifications.
        """
        while self.contents:
            self.contents[0][0].close()

    def close_newest(self):
        """
        Close newest notification
        """
        if not self.contents:
            return
        self.contents[-1][0].close()


notification_area = _NotificationArea()  # pylint: disable=invalid-name
