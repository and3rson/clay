"""
Componists for "artists" page
"""
import urwid

from .page import AbstractPage
from clay.core import gp
from clay.ui.urwid import SongListBox, hotkey_manager

class ArtistListItem(urwid.Columns):
    """
    One artists in the list of artists
    """
    signals = ['activate']

    def __init__(self, artist):
        self.artist = artist
        self.text = urwid.SelectableIcon(u'  \U0001F399 {}'.format(self.artist.name))
        self.text.set_layout('left', 'clip', None)
        self.content = urwid.AttrWrap(self.text, 'default', 'selected')
        super(ArtistListItem, self).__init__([self.content])

    def keypress(self, size, key):
        """
        Handle keypresses
        """
        return hotkey_manager.keypress("artist_page", self, super(ArtistListItem, self), size, key)

    def get_albums(self):
        """
        Show the list of albums
        """
        urwid.emit_signal(self, 'activate', self.artist)

class ArtistListBox(urwid.ListBox):
    signals = ['activate_artist']

    def __init__(self, app):
        self.app = app
        self.walker = urwid.SimpleListWalker([urwid.Text('Not ready')])
        super(ArtistListBox, self).__init__(self.walker)

    def populate(self, artists):
        items = []
        for artist in sorted(artists, key=artists.__getitem__):
            artist = ArtistListItem(artists[artist])
            urwid.connect_signal(artist, 'activate', self.item_activated)
            items.append(artist)
        self.walker[:] = items
        self.app.redraw()

    def item_activated(self, artist):
        """
        What to do when an item is pressed
        """
        urwid.emit_signal(self, 'activate_artist', artist)

class AlbumListItem(urwid.Columns):
    """
    An album
    """
    signals = ['activate']

    def __init__(self, album):
        self.album = album
        self.text = urwid.SelectableIcon(u'  {} {}'.format(self.album.icon, self.album.name))
        self.text.set_layout('left', 'clip', None)
        self.content = urwid.AttrWrap(self.text, 'default', 'selected')
        super(AlbumListItem, self).__init__([self.content])

    def keypress(self, size, key):
        """
        Handle keypresses
        """
        return hotkey_manager.keypress("albums_list", self, super(AlbumListItem, self), size, key)

    def load_tracks(self):
        """
        Show the list of albums
        """
        urwid.emit_signal(self, 'activate', self.album)

class AlbumListBox(urwid.ListBox):
    signals = ['activate_album']

    def __init__(self, app):
        self.app = app
        self.walker = urwid.SimpleListWalker([urwid.Text('Not Ready')])
        super(AlbumListBox, self).__init__(self.walker)

    def populate(self, albums):
        items = []
        for album in albums:
            album = AlbumListItem(album)
            urwid.connect_signal(album, 'activate', self.item_activated)
            items.append(album)
        self.walker[:] = items
        self.app.redraw()

    def item_activated(self, album):
        urwid.emit_signal(self, 'activate_album', album)

class ArtistsPage(urwid.Columns, AbstractPage):
    """
    Playlists page.
    Contains two parts:
    - List of artists
    - List of albums by selected artist
    """
    @property
    def name(self):
        return 'Artists'

    @property
    def key(self):
        return 2

    @property
    def slug(self):
        """
        Return page ID (`str`)
        """
        return "artists"

    def __init__(self, app):
        self.app = app
        self.artistlist = ArtistListBox(app)
        self.albumlist = AlbumListBox(app)
        self.songlist = SongListBox(app)
        self.songlist.set_placeholder('\n Select an artist')

        urwid.connect_signal(self.artistlist, 'activate_artist', self.item_activated)
        urwid.connect_signal(self.albumlist, 'activate_album', self.album_activate)

        super(ArtistsPage, self).__init__([self.artistlist, self.albumlist, self.songlist])

    def item_activated(self, artist):
        self.albumlist.populate(artist.albums)

    def activate(self):
        self.artistlist.populate(gp.cached_artists)

    def album_activate(self, album):
        self.songlist.populate(album.tracks)
        self.app.redraw()
