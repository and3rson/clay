"""
Componists for "artists" page
"""
import urwid

from .page import AbstractPage, AbstractListItem, AbstractListBox
from clay.core import gp
from clay.ui.urwid import SongListBox, hotkey_manager


class ArtistListBox(AbstractListBox):
    def populate(self, artists):
        items = []
        for artist in sorted(artists, key=artists.__getitem__):
            artist = AbstractListItem(artists[artist], self._icon)
            urwid.connect_signal(artist, 'activate', self.item_activated)
            items.append(artist)
        self.walker[:] = items
        self.app.redraw()


class AlbumListBox(AbstractListBox):
    def populate(self, albums):
        items = []
        for album in albums:
            album = AbstractListItem(album, album.icon)
            urwid.connect_signal(album, 'activate', self.item_activated)
            items.append(album)
        self.walker[:] = items
        self.app.redraw()


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
        self.artistlist = ArtistListBox(app, icon='\U0001F399')
        self.albumlist = AlbumListBox(app, placeholder='Select an artist')
        self.songlist = SongListBox(app)
        self.songlist.set_placeholder('\n Select an album')

        urwid.connect_signal(self.artistlist, 'activate', self.item_activated)
        urwid.connect_signal(self.albumlist, 'activate', self.album_activate)

        super(ArtistsPage, self).__init__([self.artistlist, self.albumlist, self.songlist])

    def item_activated(self, artist):
        if artist.albums is not None:
            self.albumlist.populate(artist.albums)

    def activate(self):
        self.artistlist.populate(gp.cached_artists)

    def album_activate(self, album):
        self.songlist.populate(album.tracks)
        self.app.redraw()
