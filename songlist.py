# -*- coding: utf-8 -*-
import urwid
from player import player


class SongListItem(urwid.Pile):
    signals = ['activate']

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

    def __init__(self, track, index):
        self.track = track
        self.index = index
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
        return super(SongListItem, self).keypress(size, key)

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
        self.walker = urwid.SimpleFocusListWalker([
            urwid.Text('\n  Loading song list...', align='center')
        ])

        player.track_changed += self.track_changed
        player.media_state_changed += self.media_state_changed

        return super(SongListBox, self).__init__(self.walker)

    def tracks_to_songlist(self, tracks):
        current_track = player.get_current_track()
        items = []
        for index, track in enumerate(tracks):
            songitem = SongListItem(track, index)
            if current_track is not None and current_track.id == track.id:
                songitem.set_state(SongListItem.STATE_PLAYING)
            urwid.connect_signal(songitem, 'activate', self.item_activated)
            items.append(songitem)
        return items

    def item_activated(self, songitem):
        player.load_queue(self.tracks, songitem.index)

    def track_changed(self, track):
        for songitem in self.walker:
            if songitem.track.id == track.id:
                songitem.set_state(SongListItem.STATE_PLAYING)
            elif songitem.state != SongListItem.STATE_IDLE:
                songitem.set_state(SongListItem.STATE_IDLE)

    def media_state_changed(self, is_playing):
        current_track = player.get_current_track()
        if current_track is None:
            return

        for songitem in self.walker:
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
        self.walker[:] = self.tracks_to_songlist(self.tracks)
        # self.walker.set_focus(5)

    # def keypress(self, size, key):
    #     # print(key)
    #     super().keypress(size, key)
    #     # if key == 'up':
    #     #     self.walker.set_focus(

