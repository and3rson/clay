import urwid
from clay.gp import gp
from clay.songlist import SongListBox


class MyLibrary(urwid.Columns):
    name = 'Library'
    key = 1

    def __init__(self, app):
        self.app = app
        self.songlist = SongListBox(app)
        self.songlist.set_placeholder('\n \uf01e Loading song list...')

        gp.get_all_tracks(callback=self.on_get_all_songs)

        return super(MyLibrary, self).__init__([
            self.songlist
        ])

    def on_get_all_songs(self, tracks, error):
        if error:
            self.app.set_page('Error', error)
            return
        self.songlist.populate(tracks)
        self.app.redraw()

