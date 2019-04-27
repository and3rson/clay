"""
PlayBar widget.
"""
# pylint: disable=too-many-instance-attributes
import urwid

from clay.core import settings_manager, meta
from clay.playback.player import get_player


player = get_player()  # pylint: disable=invalid-name


class ProgressBar(urwid.Widget):
    """
    Thin progress bar.
    """
    _sizing = frozenset([urwid.FLOW])

    # CHARS = u'\u2580'
    # CHARS = u'\u2581'
    CHARS = u'\u2501'

    def __init__(self):
        self.value = 0
        self.done_style = 'progressbar_done'
        super(ProgressBar, self).__init__()

    def render(self, size, focus=False):
        """
        Render canvas.
        """
        (width,) = size
        text = urwid.Text('foo', urwid.LEFT, urwid.CLIP)

        frac = width * self.value
        whole = int(frac)

        text.set_text([
            (
                self.done_style,
                whole * ProgressBar.CHARS[-1]
                # + ProgressBar.CHARS[partial]
            ),
            (
                'progressbar_remaining',
                (width - whole) * ProgressBar.CHARS[-1]
            )
        ])
        return text.render(size, focus)

    @staticmethod
    def rows(*_):
        """
        Return number of rows required for rendering.
        """
        return 1

    def set_progress(self, value):
        """
        Set progress value in range [0..1].
        """
        self.value = value
        self._invalidate()

    def set_done_style(self, done_style):
        """
        Set style for "done" part.
        """
        self.done_style = done_style


class PlayBar(urwid.Pile):
    """
    A widget that shows currently played track, playback progress and flags.
    """
    _unicode = settings_manager.get('unicode', 'clay_settings')
    ROTATING = u'|' u'/' u'\u2014' u'\\'
    RATING_ICONS = {0: ' ',
                    1: u'\U0001F593' if _unicode else '-',
                    4: u'\U0001F592' if _unicode else '+',
                    5: u'\U0001F592' if _unicode else '+'}

    def __init__(self, app):
        # super(PlayBar, self).__init__(*args, **kwargs)
        self.app = app
        self.rotating_index = 0
        self.text = urwid.Text('', align=urwid.LEFT)
        self.flags = [
        ]
        self.progressbar = ProgressBar()

        self.shuffle_el = urwid.AttrWrap(urwid.Text(u' \u22cd SHUF '), 'flag')
        self.repeat_el = urwid.AttrWrap(urwid.Text(u' \u27f2 REP '), 'flag')
        self.repeat_one_el = urwid.AttrWrap(urwid.Text(' 1 ONE'), 'flag')

        self.infobar = urwid.Columns([
            self.text,
            ('pack', self.shuffle_el),
            ('pack', self.repeat_one_el),
            ('pack', self.repeat_el)
        ])
        super(PlayBar, self).__init__([
            ('pack', self.progressbar),
            ('pack', self.infobar),
        ])
        self.update()

        player.media_position_changed += self.update
        player.media_state_changed += self.update
        player.media_state_stopped += self.stop
        player.track_changed += self.update
        player.playback_flags_changed += self.update

    def get_rotating_bar(self):
        """
        Return a spinner char for current rotating_index.
        """
        return PlayBar.ROTATING[self.rotating_index % len(PlayBar.ROTATING)]

    @staticmethod
    def get_style():
        """
        Return the style for current playback state.
        """
        if player.loading or player.playing:
            return 'title-playing'
        return 'title-idle'

    def get_text(self):
        """
        Return text for display in this bar.
        """
        track = player.get_current_track()
        if track is None:
            return u'{} {}'.format(
                meta.APP_NAME,
                meta.VERSION_WITH_CODENAME
            )
        progress = player.play_progress_seconds
        total = player.length_seconds
        return (self.get_style(), u' {} {} - {} {} [{:02d}:{:02d} / {:02d}:{:02d}]'.format(
            # u'|>' if player.is_playing else u'||',
            # self.get_rotating_bar(),
            u'\u2505' if player.loading
            else u'\u25B6' if player.playing
            else u'\u25A0',
            track.artist,
            track.title,
            self.RATING_ICONS[track.rating],
            progress // 60,
            progress % 60,
            total // 60,
            total % 60,
        ))

    def update(self, *_):
        """
        Force update of this widget.
        Called when something unrelated to completion value changes,
        e.g. current track or playback flags.
        """
        self.text.set_text(self.get_text())
        self.progressbar.set_progress(player.play_progress)
        self.progressbar.set_done_style(
            'progressbar_done'
            if player.playing
            else 'progressbar_done_paused'
        )
        self.shuffle_el.attr = 'flag-active' \
            if player.random \
            else 'flag'
        self.repeat_one_el.attr = 'flag-active' \
            if player.repeat_one \
            else 'flag'
        self.repeat_el.attr = 'flag-active' \
            if player.repeat_queue \
            else 'flag'
        self.app.redraw()

    def stop(self, *_):
        """
        Force update of this widget.
        Only runs when the queue is entirely cleared.
        """
        self.text.set_text("")
        self.progressbar.set_progress(0)
        self.progressbar.set_done_style('progressbar_done')
        self.shuffle_el.attr = 'flag-active' \
            if player.random \
            else 'flag'
        self.repeat_el.attr = 'flag-active' \
            if player.repeat_one \
            else 'flag'
        self.app.redraw()


    def tick(self):
        """
        Increase rotating index & trigger redraw.
        """
        self.rotating_index += 1
        self.update()
