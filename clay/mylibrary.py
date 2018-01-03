import urwid
from clay.gp import gp
from clay.songlist import SongListBox
from clay.notifications import NotificationArea


class MyLibrary(urwid.Columns):
    name = 'Library'
    key = 1

    def __init__(self, app):
        self.app = app
        self.songlist = SongListBox(app)
        self.notification = None

        gp.auth_state_changed += self.auth_state_changed

        return super(MyLibrary, self).__init__([
            self.songlist
        ])

    def on_get_all_songs(self, tracks, error):
        if error:
            NotificationArea.notify('Failed to load my library: {}'.format(str(error)))
            return
        # self.notification.close()
        self.songlist.populate(tracks)
        self.app.redraw()

    def auth_state_changed(self, is_auth):
        if is_auth:
            self.songlist.set_placeholder(u'\n \uf01e Loading song list...')

            gp.get_all_tracks(callback=self.on_get_all_songs)

            # self.notification = NotificationArea.notify('Loading library...')

