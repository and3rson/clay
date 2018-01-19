"""
PlayBar widget.
"""
# pylint: disable=protected-access
# pylint: disable=invalid-name
import urwid

from clay.player import Player


class PlayBar(urwid.ProgressBar):
    """
    A widget that shows currently played track, playback progress and flags.
    """

    ROTATING = u'|' u'/' u'\u2014' u'\\'

    def __init__(self, *args, **kwargs):
        super(PlayBar, self).__init__(*args, **kwargs)
        self.track = None
        self.player = Player.get()
        self.rotating_index = 0

    def get_rotating_bar(self):
        """
        Return a spinner char for current rotating_index.
        """
        return PlayBar.ROTATING[self.rotating_index % len(PlayBar.ROTATING)]

    def get_text(self):
        """
        Return text for display in this bar.
        """
        if self.track is None:
            return u'Idle'
        progress = self.player.get_play_progress_seconds()
        total = self.player.get_length_seconds()
        return u' {} {} - {} [{:02d}:{:02d} / {:02d}:{:02d}]'.format(
            # u'|>' if player.is_playing else u'||',
            # self.get_rotating_bar(),
            u'\u2505' if self.player.is_loading
            else u'\u25B6' if self.player.is_playing
            else u'\u25A0',
            self.track.artist,
            self.track.title,
            progress // 60,
            progress % 60,
            total // 60,
            total % 60,
        )

    def set_track(self, track):
        """
        Set displayed track.
        """
        self.track = track
        # TODO: Call ``self.update()``?

    def update(self):
        """
        Force update of this widget.
        Called when something unrelated to completion value changes,
        e.g. current track or playback flags.
        """
        self._invalidate()

    def tick(self):
        """
        Increase rotating index & trigger redraw.
        """
        self.rotating_index += 1
        self.update()
