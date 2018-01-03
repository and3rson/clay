import urwid
from clay.gp import gp
from clay.songlist import SongListBox
from clay.notifications import NotificationArea


class MyPlaylistListItem(urwid.Columns):
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
        super(MyPlaylistListItem, self).__init__([self.content])

    def keypress(self, size, key):
        if key == 'enter':
            urwid.emit_signal(self, 'activate', self)
            return
        return super(MyPlaylistListItem, self).keypress(size, key)

    def get_tracks(self):
        return self.playlist.tracks


class MyPlaylistListBox(urwid.ListBox):
    signals = ['activate']

    def __init__(self, app):
        self.app = app

        self.walker = urwid.SimpleListWalker([
            urwid.Text('Not ready')
        ])

        gp.auth_state_changed += self.auth_state_changed

        super(MyPlaylistListBox, self).__init__(self.walker)

    def auth_state_changed(self, is_auth):
        self.walker[:] = [
            urwid.Text(u'\n \uf01e Loading playlists...', align='center')
        ]

        gp.get_all_user_playlist_contents(callback=self.on_get_playlists)

    def on_get_playlists(self, playlists, error):
        if error:
            NotificationArea.notify('Failed to get playlists: {}'.format(str(error)))
            return
            # self.app.set_page(
            #     'Error',
            #     str(error)
            # )
            # return

        items = []
        for playlist in playlists:
            myplaylistlistitem = MyPlaylistListItem(playlist)
            urwid.connect_signal(
                myplaylistlistitem, 'activate', self.item_activated
            )
            items.append(myplaylistlistitem)

        self.walker[:] = items

        self.app.redraw()

    def item_activated(self, myplaylistlistitem):
        urwid.emit_signal(self, 'activate', myplaylistlistitem)


class MyPlaylists(urwid.Columns):
    name = 'Playlists'
    key = 2

    def __init__(self, app):
        self.app = app

        self.myplaylistlist = MyPlaylistListBox(app)
        self.songlist = SongListBox(app)
        self.songlist.set_placeholder('\n Select a playlist.')

        urwid.connect_signal(
            self.myplaylistlist, 'activate', self.myplaylistlistitem_activated
        )

        return super(MyPlaylists, self).__init__([
            self.myplaylistlist,
            self.songlist
        ])

    def myplaylistlistitem_activated(self, myplaylistlistitem):
        self.songlist.populate(
            myplaylistlistitem.get_tracks()
        )

