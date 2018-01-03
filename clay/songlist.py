import urwid
from clay.player import player


class SongListItem(urwid.Pile):
    signals = [
        'activate',
        'append-requested',
        'unappend-requested'
    ]

    STATE_IDLE = 0
    STATE_LOADING = 1
    STATE_PLAYING = 2
    STATE_PAUSED = 3

    STATE_ICONS = {
        0: ' ',
        1: u'\u2505',
        2: u'\u25B6',
        3: u'\u25A0'
    }

    def __init__(self, track):
        self.track = track
        self.index = 0
        self.state = SongListItem.STATE_IDLE
        self.line1 = urwid.SelectableIcon('', cursor_position=6)
        self.line1.set_layout('left', 'clip', None)
        self.line2 = urwid.AttrWrap(
            urwid.Text('', wrap='clip'),
            'line2'
        )
        self.content = urwid.AttrWrap(
            urwid.Pile([
                self.line1,
                self.line2
            ]),
            'line1',
            'line1_focus'
        )

        super(SongListItem, self).__init__([
            self.content
        ])
        self.update_text()

    def set_state(self, state):
        self.state = state
        self.update_text()

    def get_state_icon(self, state):
        return SongListItem.STATE_ICONS[state]

    def update_text(self):
        self.line1.set_text(
            u'{index:3d} {icon} {title} [{minutes:02d}:{seconds:02d}]'.format(
                index=self.index + 1,
                icon=self.get_state_icon(self.state),
                title=self.track.title,
                minutes=self.track.duration // (1000 * 60),
                seconds=(self.track.duration // 1000) % 60
            )
        )
        self.line2.set_text(
            u'      {}'.format(self.track.artist)
        )
        if self.state == SongListItem.STATE_IDLE:
            self.content.set_attr('line1')
            self.content.set_focus_attr('line1_focus')
        else:
            self.content.set_attr('line1_active')
            self.content.set_focus_attr('line1_active_focus')

    def keypress(self, size, key):
        if key == 'enter':
            urwid.emit_signal(self, 'activate', self)
            return
        elif key == 'ctrl a':
            urwid.emit_signal(self, 'append-requested', self)
        elif key == 'ctrl u':
            if not self.is_currently_played:
                urwid.emit_signal(self, 'unappend-requested', self)
        return super(SongListItem, self).keypress(size, key)

    def mouse_event(self, size, event, button, x, y, focus):
        if button == 1 and focus:
            urwid.emit_signal(self, 'activate', self)
            return
        return super().mouse_event(size, event, button, x, y, focus)

    @property
    def is_currently_played(self):
        return self.state in (
            SongListItem.STATE_PLAYING,
            SongListItem.STATE_PAUSED
        )

    def set_index(self, index):
        self.index = index
        self.update_text()

    # def render(self, size, focus=False):
    #     # if focus:
    #     #     self.line1.attr = 'line1_focus'
    #     #     self.line2.attr = 'line2_focus'
    #     # else:
    #     #     self.line1.attr = 'line1'
    #     #     self.line2.attr = 'line2'
    #     urwid.Pile.render(self, size, focus)


class SongListBox(urwid.ListBox):
    signals = ['activate']

    def __init__(self, app):
        self.app = app

        self.current_item = None
        self.tracks = []
        self.walker = urwid.SimpleFocusListWalker([])

        player.track_changed += self.track_changed
        player.media_state_changed += self.media_state_changed

        return super(SongListBox, self).__init__(self.walker)

    def set_placeholder(self, text):
        self.walker[:] = [urwid.Text(text, align='center')]

    def tracks_to_songlist(self, tracks):
        current_track = player.get_current_track()
        items = []
        current_index = None
        for index, track in enumerate(tracks):
            songitem = SongListItem(track)
            if current_track is not None and current_track.id == track.id:
                songitem.set_state(SongListItem.STATE_PLAYING)
                if current_index is None:
                    current_index = index
            urwid.connect_signal(
                songitem, 'activate', self.item_activated
            )
            urwid.connect_signal(
                songitem, 'append-requested', self.item_append_requested
            )
            urwid.connect_signal(
                songitem, 'unappend-requested', self.item_unappend_requested
            )
            items.append(songitem)
        return (items, current_index)

    def item_activated(self, songitem):
        if songitem.is_currently_played:
            player.play_pause()
        else:
            player.load_queue(self.tracks, songitem.index)

    def item_append_requested(self, songitem):
        player.append_to_queue(songitem.track)

    def item_unappend_requested(self, songitem):
        player.remove_from_queue(songitem.track)

    def track_changed(self, track):
        for i, songitem in enumerate(self.walker):
            if isinstance(songitem, urwid.Text):
                continue
            if songitem.track.id == track.id:
                songitem.set_state(SongListItem.STATE_PLAYING)
                self.set_focus(i)
            elif songitem.state != SongListItem.STATE_IDLE:
                songitem.set_state(SongListItem.STATE_IDLE)

    def media_state_changed(self, is_playing):
        current_track = player.get_current_track()
        if current_track is None:
            return

        for songitem in self.walker:
            if isinstance(songitem, urwid.Text):
                continue
            if songitem.track.id == current_track.id:
                songitem.set_state(
                    SongListItem.STATE_PLAYING
                    if is_playing
                    else SongListItem.STATE_PAUSED
                )
        self.app.redraw()

        # if self.current_item:
        #     self.current_item.set_state(SongList.Song.State.IDLE)
        # self.current_item = item
        # item.set_state(SongList.Song.State.LOADING)
        # gp.get_stream_url(
        #     item.data['id'],
        #     callback=self.got_stream_url, extra=dict(item=item)
        # )

    # def got_stream_url(self, url, e, item):
    #     if item != self.current_item:
    #         # Another song play requested while we were fetching stream URL
    #         return
    #     if e:
    #         raise e
    #     item.set_state(SongList.Song.State.PLAYING)
    #     player.play(url)
    #     # urwid.emit_signal(self, 'activate', item)

    def populate(self, tracks):
        self.tracks = tracks
        self.walker[:], current_index = self.tracks_to_songlist(self.tracks)
        self.update_indexes()
        if current_index is not None:
            self.walker.set_focus(current_index)

    def append_track(self, track):
        tracks, current_index = self.tracks_to_songlist([track])
        self.walker.append(tracks[0])
        self.update_indexes()

    def remove_track(self, track):
        for songlistitem in self.walker:
            if songlistitem.track == track:
                self.walker.remove(songlistitem)
        self.update_indexes()

    def update_indexes(self):
        for i, songlistitem in enumerate(self.walker):
            songlistitem.set_index(i)

    # def keypress(self, size, key):
    #     # print(key)
    #     super().keypress(size, key)
    #     # if key == 'up':
    #     #     self.walker.set_focus(

    def mouse_event(self, size, event, button, x, y, focus):
        if button == 4:
            self.keypress(size, 'up')
        elif button == 5:
            self.keypress(size, 'down')
        else:
            super().mouse_event(size, event, button, x, y, focus)

