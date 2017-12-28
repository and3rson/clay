import urwid
from gp import gp
from player import Track
from songlist import SongListBox


class PlaylistListItem(urwid.Columns):
    signals = ['activate']

    def __init__(self, data):
        self.data = data
        self.content = urwid.AttrWrap(
            urwid.SelectableIcon('  {} ({})'.format(
                self.data['name'],
                len(self.data['tracks'])
            ), cursor_position=3),
            'default',
            'selected'
        )
        super().__init__([self.content])

    def keypress(self, size, key):
        if key == 'enter':
            urwid.emit_signal(self, 'activate', self)
            return
        return super().keypress(size, key)

    def get_tracks(self):
        return Track.from_data([
            item['track']
            for item
            in self.data['tracks']
        ], many=True)


class PlaylistListBox(urwid.ListBox):
    signals = ['activate']

    def __init__(self, app):
        self.app = app

        self.walker = urwid.SimpleListWalker([
            urwid.Text('Loading playlists...')
        ])

        gp.get_all_user_playlist_contents(callback=self.on_get_playlists)

        super().__init__(self.walker)

    def on_get_playlists(self, playlists, error):
        if error:
            self.app.set_page(
                'Error',
                str(error)
            )
            return

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
        urwid.emit_signal(self, 'activate', playlistlistitem)


class MyPlaylists(urwid.Columns):
    name = 'Playlists'
    key = 2

    def __init__(self, app):
        self.app = app

        self.playlistlist = PlaylistListBox(app)
        self.songlist = SongListBox(app)
        self.songlist.populate([])

        urwid.connect_signal(
            self.playlistlist, 'activate', self.playlistlistitem_activated
        )

        return super().__init__([
            self.playlistlist,
            self.songlist
        ])

    def playlistlistitem_activated(self, playlistlistitem):
        self.songlist.populate(
            playlistlistitem.get_tracks()
        )

