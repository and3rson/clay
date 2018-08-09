"""
On-screen display stuff.
"""
from threading import Thread

from clay.notifications import notification_area
from clay import meta

IS_INIT = False

try:
    from dbus import SessionBus, Interface
    IS_INIT = True
except ImportError:
    ERROR_MESSAGE = 'Could not import dbus. OSD notifications will be disabled.'
except Exception as exception:  # pylint: disable=broad-except
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

    def notify(self, track):
        """
        Create new or update existing notification.
        """
        if IS_INIT:
            thread = Thread(target=self._notify, args=(track,))
            thread.daemon = True
            thread.start()

    def _notify(self, track):
        artist_art_filename = track.get_artist_art_filename()
        self._last_id = self.notify_interface.Notify(
            meta.APP_NAME,
            self._last_id,
            artist_art_filename if artist_art_filename is not None else 'audio-headphones',
            track.title,
            u'by {}\nfrom {}'.format(track.artist, track.album_name),
            [],
            dict(),
            5000
        )


osd_manager = _OSDManager()  # pylint: disable=invalid-name
