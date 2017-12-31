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
        player.track_removed += self.track_removed

        return super().__init__([
            self.songlist
        ])

    def track_removed(self, track):
        self.songlist.remove_track(track)

