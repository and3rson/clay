"""
Library page.
"""
import urwid

from clay.gp import gp
from clay.songlist import SongListBox
from clay.notifications import notification_area
from clay.pages.page import AbstractPage


class MyLibraryPage(urwid.Columns, AbstractPage):
    """
    My library page.

    Displays :class:`clay.songlist.SongListBox` with all songs in library.
    """
    @property
    def name(self):
        return 'Library'

    @property
    def key(self):
        return 1

    def __init__(self, app):
        self.app = app
        self.songlist = SongListBox(app)
        self.notification = None

        gp.auth_state_changed += self.get_all_songs
        gp.caches_invalidated += self.get_all_songs

        super(MyLibraryPage, self).__init__([
            self.songlist
        ])

    def on_get_all_songs(self, tracks, error):
        """
        Called when all library songs are fetched from server.
        Populate song list.
        """
        if error:
            notification_area.notify('Failed to load my library: {}'.format(str(error)))
            return
        self.songlist.populate(tracks)
        self.app.redraw()

    def get_all_songs(self, *_):
        """
        Called when auth state changes or GP caches are invalidated.
        """
        if gp.is_authenticated:
            self.songlist.set_placeholder(u'\n \uf01e Loading song list...')

            gp.get_all_tracks_async(callback=self.on_get_all_songs)
            self.app.redraw()

    def activate(self):
        pass
