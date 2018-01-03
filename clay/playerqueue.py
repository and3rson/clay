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
        player.queue_changed += self.queue_changed
        player.track_appended += self.track_appended
        player.track_removed += self.track_removed

        return super(Queue, self).__init__([
            self.songlist
        ])

    def queue_changed(self):
        self.songlist.populate(player.get_queue())

    def track_appended(self, track):
        self.songlist.append_track(track)

    def track_removed(self, track):
        self.songlist.remove_track(track)

