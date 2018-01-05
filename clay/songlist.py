"""
Components for song listing.
"""
# pylint: disable=too-many-arguments
import urwid
from clay.player import Player


class SongListItem(urwid.Pile):
    """
    Widget that represents single song item.
    """
    signals = [
        'activate',
        'append-requested',
        'unappend-requested',
        'station-requested'
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
        """
        Set state for this song.
        Possible choices are:

        - :attr:`.SongListItem.STATE_IDLE`
        - :attr:`.SongListItem.STATE_LOADING`
        - :attr:`.SongListItem.STATE_PLAYING`
        - :attr:`.SongListItem.STATE_PAUSED`
        """
        self.state = state
        self.update_text()

    @staticmethod
    def get_state_icon(state):
        """
        Get icon char for specific state.
        """
        return SongListItem.STATE_ICONS[state]

    def update_text(self):
        """
        Update text of this item from the attached track.
        """
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
        """
        Handle keypress.
        """
        if key == 'enter':
            urwid.emit_signal(self, 'activate', self)
            return None
        elif key == 'ctrl a':
            urwid.emit_signal(self, 'append-requested', self)
        elif key == 'ctrl u':
            if not self.is_currently_played:
                urwid.emit_signal(self, 'unappend-requested', self)
        elif key == 'ctrl p':
            urwid.emit_signal(self, 'station-requested', self)
        return super(SongListItem, self).keypress(size, key)

    def mouse_event(self, size, event, button, col, row, focus):
        """
        Handle mouse event.
        """
        if button == 1 and focus:
            urwid.emit_signal(self, 'activate', self)
            return None
        return super(SongListItem, self).mouse_event(size, event, button, col, row, focus)

    @property
    def is_currently_played(self):
        """
        Return ``True`` if song is in state :attr:`.SongListItem.STATE_PLAYING`
        or :attr:`.SongListItem.STATE_PAUSED`.
        """
        return self.state in (
            SongListItem.STATE_PLAYING,
            SongListItem.STATE_PAUSED
        )

    def set_index(self, index):
        """
        Set numeric index for this item.
        """
        self.index = index
        self.update_text()


class SongListBox(urwid.ListBox):
    """
    Displays :class:`.SongListItem` instances.
    """
    signals = ['activate']

    def __init__(self, app):
        self.app = app

        self.current_item = None
        self.tracks = []
        self.walker = urwid.SimpleFocusListWalker([])

        player = Player.get()
        player.track_changed += self.track_changed
        player.media_state_changed += self.media_state_changed

        super(SongListBox, self).__init__(self.walker)

    def set_placeholder(self, text):
        """
        Clear list and add one placeholder item.
        """
        self.walker[:] = [urwid.Text(text, align='center')]

    def tracks_to_songlist(self, tracks):
        """
        Convert list of track data items into list of :class:`.SongListItem` instances.
        """
        current_track = Player.get().get_current_track()
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
            urwid.connect_signal(
                songitem, 'station-requested', self.item_station_requested
            )
            items.append(songitem)
        return (items, current_index)

    def item_activated(self, songitem):
        """
        Called when specific song item is activated.
        Toggles track playback state or loads entire playlist
        that contains current track into player queue.
        """
        player = Player.get()
        if songitem.is_currently_played:
            player.play_pause()
        else:
            player.load_queue(self.tracks, songitem.index)

    @staticmethod
    def item_append_requested(songitem):
        """
        Called when specific item emits *append-requested* item.
        Appends track to player queue.
        """
        Player.get().append_to_queue(songitem.track)

    @staticmethod
    def item_unappend_requested(songitem):
        """
        Called when specific item emits *remove-requested* item.
        Removes track from player queue.
        """
        Player.get().remove_from_queue(songitem.track)

    @staticmethod
    def item_station_requested(songitem):
        """
        Called when specific item emits *station-requested* item.
        Requests new station creation.
        """
        Player.get().create_station_from_track(songitem.track)

    def track_changed(self, track):
        """
        Called when new track playback is started.
        Marks corresponding song item (if found in this song list) as currently played.
        """
        for i, songitem in enumerate(self.walker):
            if isinstance(songitem, urwid.Text):
                continue
            if songitem.track.id == track.id:
                songitem.set_state(SongListItem.STATE_PLAYING)
                self.set_focus(i)
            elif songitem.state != SongListItem.STATE_IDLE:
                songitem.set_state(SongListItem.STATE_IDLE)

    def media_state_changed(self, is_playing):
        """
        Called when player media state changes.
        Updates corresponding song item state (if found in this song list).
        """
        current_track = Player.get().get_current_track()
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

    def populate(self, tracks):
        """
        Display a list of :class:`clay.player.Track` instances in this song list.
        """
        self.tracks = tracks
        self.walker[:], current_index = self.tracks_to_songlist(self.tracks)
        self.update_indexes()
        if current_index is not None:
            self.walker.set_focus(current_index)

    def append_track(self, track):
        """
        Convert a track into :class:`.SongListItem` instance and appends it into this song list.
        """
        tracks, _ = self.tracks_to_songlist([track])
        self.walker.append(tracks[0])
        self.update_indexes()

    def remove_track(self, track):
        """
        Remove a song item that matches *track* from this song list (if found).
        """
        for songlistitem in self.walker:
            if songlistitem.track == track:
                self.walker.remove(songlistitem)
        self.update_indexes()

    def update_indexes(self):
        """
        Update indexes of all song items in this song list.
        """
        for i, songlistitem in enumerate(self.walker):
            songlistitem.set_index(i)

    def mouse_event(self, size, event, button, col, row, focus):
        """
        Handle mouse event.
        """
        if button == 4:
            self.keypress(size, 'up')
        elif button == 5:
            self.keypress(size, 'down')
        else:
            super(SongListBox, self).mouse_event(size, event, button, col, row, focus)
