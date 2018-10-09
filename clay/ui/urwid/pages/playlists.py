"""
Components for " playlists" page.
"""
import urwid

from .page import AbstractPage, AbstractListBox, AbstractListItem
from clay.core import gp
from clay.ui.urwid import SongListBox, notification_area, hotkey_manager

class PlaylistListBox(AbstractListBox):
    """
    List of playlists.
    """
    def __init__(self, app, icon):
        super(PlaylistListBox, self).__init__(app, icon)

    def auth_state_changed(self, is_auth):
        """
        Called when auth state changes (e. g. user is logged in).
        Requests fetching of playlists.
        """
        if is_auth:
            self.walker[:] = [
                urwid.Text(u'\n \uf01e Loading playlists...', align='center')
            ]
            gp.get_all_user_playlist_contents_async(callback=self.populate)

class PlaylistsPage(urwid.Columns, AbstractPage):
    """
    Playlists page.

    Contains two parts:

    - List of playlists (:class:`.PlaylistListBox`)
    - List of songs in selected playlist (:class:`clay:songlist:SongListBox`)
    """
    @property
    def name(self):
        return 'Playlists'

    @property
    def key(self):
        return 4

    @property
    def slug(self):
        """
        Return page ID (str).
        """
        return "playlists"

    def __init__(self, app):
        self.app = app

        self.playlistlist = PlaylistListBox(app, '\u2630')
        self.songlist = SongListBox(app)
        self.songlist.set_placeholder('\n Select a playlist.')

        urwid.connect_signal(
            self.playlistlist, 'activate', self.playlist_activated
        )

        super(PlaylistsPage, self).__init__([
            self.playlistlist,
            self.songlist
        ])

    def playlist_activated(self, playlist):
        """
        Called when specific playlist is selected.
        Populates songlist with tracks from the selected playlist.
        """
        self.songlist.populate(playlist.tracks)

    def activate(self):
        pass
