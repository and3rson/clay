import urwid
from gp import gp
from songlist import SongListBox
from player import Track


class MyLibrary(urwid.Columns):
    name = 'Library'
    key = 1

    def __init__(self, app):
        self.app = app
        self.songlist = SongListBox(app)

        gp.get_all_songs(callback=self.on_get_all_songs)

        return super().__init__([
            self.songlist
        ])

    def on_get_all_songs(self, results, error):
        if error:
            self.app.set_page('Error', error)
            return
        self.songlist.populate(Track.from_data(results, many=True))
        self.app.redraw()

