"""
Components for "Queue" page.
"""
import urwid

from .page import AbstractPage
from clay.playback.player import get_player
from clay.ui.urwid import SongListBox


player = get_player()  # pylint: disable=invalid-name


class QueuePage(urwid.Columns, AbstractPage):
    """
    Queue page.
    """
    @property
    def name(self):
        return 'Queue'

    @property
    def key(self):
        return 7

    @property
    def slug(self):
        """
        Return page ID (str).
        """
        return "queue"

    def __init__(self, app):
        self.app = app
        self.songlist = SongListBox(app)

        self.songlist.populate(player.get_queue_tracks())
        player.queue_changed += self.queue_changed
        player.track_appended += self.track_appended
        player.track_removed += self.track_removed

        super(QueuePage, self).__init__([
            self.songlist
        ])

    def queue_changed(self):
        """
        Called when player queue is changed.
        Updates this queue widget.
        """
        self.songlist.populate(player.get_queue_tracks())

    def track_appended(self, track):
        """
        Called when new track is appended to the player queue.
        Appends track to this queue widget.
        """
        self.songlist.append_track(track)

    def track_removed(self, track):
        """
        Called when a track is removed from the player queue.
        Removes track from this queue widget.
        """
        self.songlist.remove_track(track)

    def activate(self):
        pass
