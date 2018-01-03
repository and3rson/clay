import urwid

from clay.player import player


class PlayBar(urwid.ProgressBar):
    def __init__(self, *args, **kwargs):
        super(PlayBar, self).__init__(*args, **kwargs)
        self.track = None

    def get_text(self):
        if self.track is None:
            return u'Idle'
        progress = player.get_play_progress_seconds()
        total = player.get_length_seconds()
        return u' {} {} - {} [{:02d}:{:02d} / {:02d}:{:02d}]'.format(
            # u'|>' if player.is_playing else u'||',
            u'\u25B6' if player.is_playing else u'\u25A0',
            self.track.artist,
            self.track.title,
            progress // 60,
            progress % 60,
            total // 60,
            total % 60,
        )

    def set_track(self, track):
        self.track = track

    def update(self):
        self._invalidate()

    def render(self, size, focus=False):
        """
        Render the progress bar - fixed implementation.
        For details see https://github.com/urwid/urwid/pull/261
        """
        (maxcol,) = size
        txt = urwid.Text(self.get_text(), self.text_align, urwid.widget.CLIP)
        c = txt.render((maxcol,))

        cf = float(self.current) * maxcol / self.done
        ccol_dirty = int(cf)
        ccol = len(c._text[0][:ccol_dirty].decode(
            'utf-8', 'ignore'
        ).encode(
            'utf-8'
        ))
        cs = 0
        if self.satt is not None:
            cs = int((cf - ccol) * 8)
        if ccol < 0 or (ccol == 0 and cs == 0):
            c._attr = [[(self.normal, maxcol)]]
        elif ccol >= maxcol:
            c._attr = [[(self.complete, maxcol)]]
        elif cs and c._text[0][ccol] == " ":
            t = c._text[0]
            cenc = self.eighths[cs].encode("utf-8")
            c._text[0] = t[:ccol] + cenc + t[ccol + 1:]
            a = []
            if ccol > 0:
                a.append((self.complete, ccol))
            a.append((self.satt, len(cenc)))
            if maxcol - ccol - 1 > 0:
                a.append((self.normal, maxcol - ccol - 1))
            c._attr = [a]
            c._cs = [[(None, len(c._text[0]))]]
        else:
            c._attr = [[(self.complete, ccol),
                        (self.normal, maxcol - ccol)]]
        return c

