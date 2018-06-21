"""
On-screen display stuff.
"""
from clay.notifications import notification_area
from clay import meta

IS_INIT = False

try:
    from dbus import SessionBus, Interface
    IS_INIT = True
except ImportError:
    ERROR_MESSAGE = 'Could not import dbus. OSD notifications will be disabled.'
except Exception as exception:
    ERROR_MESSAGE = 'Error while importing dbus: \'{}\''.format(str(exception))

if not IS_INIT:
    notification_area.notify(ERROR_MESSAGE)


class _OSDManager(object):
    """
    Manages OSD notifications via DBus.
    """
    def __init__(self):
        self._last_id = 0

        if IS_INIT:
            self.bus = SessionBus()
            self.notifcations = self.bus.get_object(
                "org.freedesktop.Notifications",
                "/org/freedesktop/Notifications"
            )
            self.notify_interface = Interface(self.notifcations, "org.freedesktop.Notifications")

    def notify(self, title, message):
        """
        Create new or update existing notification.
        """
        if IS_INIT:
            self._last_id = self.notify_interface.Notify(
                meta.APP_NAME,
                self._last_id,
                'audio-headphones',
                title,
                message,
                [],
                dict(),
                5000
            )


osd_manager = _OSDManager()  # pylint: disable=invalid-name
