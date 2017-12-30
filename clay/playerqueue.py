import urwid
from clay.songlist import SongListBox
from clay.player import player


class Queue(urwid.Columns):
    name = 'Queue'
    key = 3

    def __init__(self, app):
        self.app = app
        self.songlist = SongListBox(app)

        self.songlist.populate(player.get_queue())

        return super().__init__([
            self.songlist
        ])

