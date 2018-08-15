"""
Components for " playlists" page.
"""
import urwid

from .page import AbstractPage
from clay.core import gp
from clay.ui.urwid import SongListBox, notification_area, hotkey_manager


class PlaylistListItem(urwid.Columns):
    """
    One playlist in the list of playlists.
    """
    signals = ['activate']

    def __init__(self, playlist):
        self.playlist = playlist
        self.text = urwid.SelectableIcon(u' \u2630 {} ({})'.format(
            self.playlist.name,
            len(self.playlist.tracks)
        ), cursor_position=3)
        self.text.set_layout('left', 'clip', None)
        self.content = urwid.AttrWrap(
            self.text,
            'default',
            'selected'
        )
        super(PlaylistListItem, self).__init__([self.content])

    def keypress(self, size, key):
        """
        Handle keypress.
        """
        return hotkey_manager.keypress("playlist_page", self, super(PlaylistListItem, self),
                                       size, key)

    def start_playlist(self):
        """
        Start playing the selected playlist
        """
        urwid.emit_signal(self, 'activate', self)

    def get_tracks(self):
        """
        Returns a list of :class:`clay.gp.Track` instances.
        """
        return self.playlist.tracks


class PlaylistListBox(urwid.ListBox):
    """
    List of playlists.
    """
    signals = ['activate']

    def __init__(self, app):
        self.app = app

        self.walker = urwid.SimpleListWalker([
            urwid.Text('Not ready')
        ])
        self.notification = None

        gp.auth_state_changed += self.auth_state_changed

        super(PlaylistListBox, self).__init__(self.walker)

    def auth_state_changed(self, is_auth):
        """
        Called when auth state changes (e. g. user is logged in).
        Requests fetching of playlists.
        """
        if is_auth:
            self.walker[:] = [
                urwid.Text(u'\n \uf01e Loading playlists...', align='center')
            ]

            gp.get_all_user_playlist_contents_async(callback=self.on_get_playlists)

    def on_get_playlists(self, playlists, error):
        """
        Called when a list of playlists fetch completes.
        Populates list of playlists.
        """
        if error:
            notification_area.notify('Failed to get playlists: {}'.format(str(error)))

        items = []
        for playlist in playlists:
            playlistlistitem = PlaylistListItem(playlist)
            urwid.connect_signal(
                playlistlistitem, 'activate', self.item_activated
            )
            items.append(playlistlistitem)

        self.walker[:] = items

        self.app.redraw()

    def item_activated(self, playlistlistitem):
        """
        Called when a specific playlist is selected.
        Re-emits this event.
        """
        urwid.emit_signal(self, 'activate', playlistlistitem)


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
        return 2

    @property
    def slug(self):
        """
        Return page ID (str).
        """
        return "playlists"

    def __init__(self, app):
        self.app = app

        self.playlistlist = PlaylistListBox(app)
        self.songlist = SongListBox(app)
        self.songlist.set_placeholder('\n Select a playlist.')

        urwid.connect_signal(
            self.playlistlist, 'activate', self.playlistlistitem_activated
        )

        super(PlaylistsPage, self).__init__([
            self.playlistlist,
            self.songlist
        ])

    def playlistlistitem_activated(self, playlistlistitem):
        """
        Called when specific playlist is selected.
        Populates songlist with tracks from the selected playlist.
        """
        self.songlist.populate(
            playlistlistitem.get_tracks()
        )

    def activate(self):
        pass
