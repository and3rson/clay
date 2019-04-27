"""
Components for song listing.
"""
# pylint: disable=too-many-arguments
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-public-methods
from operator import lt, gt
from string import digits

try:
    # Python 3.x
    from string import ascii_letters
except ImportError:
    # Python 2.x
    from string import letters as ascii_letters
import urwid

from clay.core import gp, settings_manager
from clay.playback.player import get_player

from .notifications import notification_area
from .hotkeys import hotkey_manager
from .clipboard import copy


player = get_player()  # pylint: disable=invalid-name


class SongListItem(urwid.Pile):
    """
    Widget that represents single song item.
    """
    _unicode = settings_manager.get('unicode', 'clay_settings')
    signals = [
        'activate',
        'play',
        'append-requested',
        'unappend-requested',
        'clear-queue',
        'station-requested',
        'context-menu-requested'
    ]

    STATE_IDLE = 0
    STATE_LOADING = 1
    STATE_PLAYING = 2
    STATE_PAUSED = 3

    LINE1_ATTRS = {
        STATE_IDLE: ('line1', 'line1_focus'),
        STATE_LOADING: ('line1_active', 'line1_active_focus'),
        STATE_PLAYING: ('line1_active', 'line1_active_focus'),
        STATE_PAUSED: ('line1_active', 'line1_active_focus')
    }
    LINE2_ATTRS = {
        STATE_IDLE: ('line2', 'line2_focus'),
        STATE_LOADING: ('line2', 'line2_focus'),
        STATE_PLAYING: ('line2', 'line2_focus'),
        STATE_PAUSED: ('line2', 'line2_focus')
    }

    STATE_ICONS = {
        0: ' ',
        1: u'\u2505',
        2: u'\u25B6',
        3: u'\u25A0'
    }

    RATING_ICONS = {
        0: ' ',
        1: u'\U0001F593' if _unicode else '-',
        2: u'\U0001F593' if _unicode else '2',
        3: u'\U0001F593' if _unicode else '3',
        4: u'\U0001F593' if _unicode else '4',
        5: u'\U0001F592' if _unicode else '+'
    }

    EXPLICIT_ICONS = {
        0: ' ',  # not actually used?
        1: u'\U0001F174' if _unicode else '[E]',
        2: ' ',
        3: ' '
    }

    def __init__(self, track):
        self.track = track
        self.rating = self.RATING_ICONS[track.rating]
        self.explicit = self.EXPLICIT_ICONS[track.explicit_rating]
        self.index = 0
        self.state = SongListItem.STATE_IDLE
        self.line1_left = urwid.SelectableIcon('', cursor_position=1000)
        self.line1_left.set_layout('left', 'clip', None)
        self.line1_right = urwid.Text('x')
        self.line1 = urwid.Columns([
            self.line1_left,
            ('pack', self.line1_right),
            ('pack', urwid.Text(' '))
        ])
        self.line2 = urwid.Text('', wrap='clip')

        self.line1_wrap = urwid.AttrWrap(self.line1, 'line1')
        self.line2_wrap = urwid.AttrWrap(self.line2, 'line2')

        self.content = urwid.Pile([
            self.line1_wrap,
            self.line2_wrap,
            urwid.Text('')
        ])

        self.is_focused = False

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
        self.line1_left.set_text(
            u'{index:3d} {icon} {title} [{minutes:02d}:{seconds:02d}]'.format(
                index=self.index + 1,
                icon=self.get_state_icon(self.state),
                title=self.track.title,
                minutes=self.track.duration // (1000 * 60),
                seconds=(self.track.duration // 1000) % 60,
            )
        )

        if settings_manager.get_is_file_cached(self.track.filename):
            self.line1_right.set_text(u' \u25bc Cached')
        else:
            self.line1_right.set_text(u'')

        self.line1_right.set_text(u'{explicit} {rating}'.format(explicit=self.explicit,
                                                                rating=self.rating))

        self.line2.set_text(
            u'      {} \u2015 {}'.format(self.track.artist, self.track.album_name)
        )
        self.line1_wrap.set_attr(SongListItem.LINE1_ATTRS[self.state][self.is_focused])
        self.line2_wrap.set_attr(SongListItem.LINE2_ATTRS[self.state][self.is_focused])

    @property
    def full_title(self):
        """
        Return song artist and title.
        """
        return u'{} - {} {}'.format(
            self.track.artist,
            self.track.title,
            self.rating
        )

    def keypress(self, size, key):
        """
        Handle keypress.
        """
        return hotkey_manager.keypress("song_item", self, super(SongListItem, self), size, key)

    def mouse_event(self, size, event, button, col, row, focus):
        """
        Handle mouse event.
        """
        if button == 1 and focus:
            urwid.emit_signal(self, 'activate', self)
            return None
        return super(SongListItem, self).mouse_event(size, event, button, col, row, focus)

    def thumbs_up(self):
        """
        Thumb the currently selected song up.
        """
        self.track.rate_song((0 if self.track.rating == 5 else 5))

    def thumbs_down(self):
        """
        Thumb the currently selected song down.
        """
        self.track.rate_song((0 if self.track.rating == 1 else 1))

    def _send_signal(self, signal):
        urwid.emit_signal(self, signal, self)

    def activate(self):
        """
        Add the entire list to queue and begin playing
        """
        self._send_signal("activate")

    def clear_queue(self):
        """
        Removes all the songs from the queue.
        """
        self.set_state(SongListItem.STATE_IDLE)
        self.is_focused = False
        self._send_signal("clear-queue")

    def play(self):
        """
        Play this song.
        """
        self._send_signal("play")

    def append(self):
        """
        Add this song to the queue.
        """
        self._send_signal("append-requested")

    def unappend(self):
        """
        Remove this song from the queue.
        """
        if not self.is_currently_played:
            self._send_signal("unappend-requested")

    def request_station(self):
        """
        Create a Google Play Music radio for this song.
        """
        self._send_signal("station-requested")

    def show_context_menu(self):
        """
        Display the context menu for this song.
        """
        self._send_signal("context-menu-requested")

    @property
    def is_currently_played(self):
        """
        Return ``True`` if song is in state :attr:`.SongListItem.STATE_PLAYING`
        or :attr:`.SongListItem.STATE_PAUSED`.
        """
        return self.state in (
            SongListItem.STATE_LOADING,
            SongListItem.STATE_PLAYING,
            SongListItem.STATE_PAUSED
        )

    def set_index(self, index):
        """
        Set numeric index for this item.
        """
        self.index = index
        self.update_text()

    def render(self, size, focus=False):
        """
        Render widget & set focused state.
        """
        self.is_focused = focus
        self.update_text()
        return super(SongListItem, self).render(size, focus)


class SongListBoxPopup(urwid.LineBox):
    """
    Widget that represents context popup for a song item.
    """
    signals = ['close']

    def __init__(self, songitem):
        self.songitem = songitem
        self.options = [
            urwid.AttrWrap(
                urwid.Text(' ' + songitem.full_title),
                'panel'
            ),
            urwid.AttrWrap(
                urwid.Text(' Source: {}'.format(songitem.track.source)),
                'panel_divider'
            ),
            urwid.AttrWrap(
                urwid.Text(' StoreID: {}'.format(songitem.track.id)),
                'panel_divider'
            )
        ]

        if not gp.get_track_by_id(songitem.track.id):
            self._add_item('Add to library', self.add_to_my_library)
        else:
            self._add_item('Remove from library', self.remove_from_my_library)

        self._add_item('Create station', self.create_station)

        if self.songitem.track in player.get_queue_tracks():
            self._add_item('Remove from queue', self.remove_from_queue)
        else:
            self._add_item('Append to queue', self.append_to_queue)

        if self.songitem.track.cached_url is not None:
            self._add_item('Copy URL to clipboard', self.copy_url)

        self.options.append(
            urwid.AttrWrap(
                urwid.Button('Close', on_press=self.close),
                'panel',
                'panel_focus'))

        super(SongListBoxPopup, self).__init__(
            urwid.Pile(self.options)
        )

    def _add_item(self, name, func):
        """
        Add an item to the list with a divider.

        Args:
           name (str): The name of the option
           func: The function to call afterwards
        """
        self.options.append(
            urwid.AttrWrap(
                urwid.Divider(u'\u2500'),
                'panel_divider',
                'panel_divider_focus'))

        self.options.append(
            urwid.AttrWrap(
                urwid.Button(name, on_press=func),
                'panel',
                'panel_focus'))

    def add_to_my_library(self, _):
        """
        Add related track to my library.
        """
        def on_add_to_my_library(result, error):
            """
            Show notification with song addition result.
            """
            if error or not result:
                notification_area.notify('Error while adding track to my library: {}'.format(
                    str(error) if error else 'reason is unknown :('
                ))
            else:
                notification_area.notify('Track added to library!')
        self.songitem.track.add_to_my_library_async(callback=on_add_to_my_library)
        self.close()

    def remove_from_my_library(self, _):
        """
        Removes related track to my library.
        """
        def on_remove_from_my_library(result, error):
            """
            Show notification with song removal result.
            """
            if error or not result:
                notification_area.notify('Error while removing track from my library: {}'.format(
                    str(error) if error else 'reason is unknown :('
                ))
            else:
                notification_area.notify('Track removed from library!')
        self.songitem.track.remove_from_my_library_async(callback=on_remove_from_my_library)
        self.close()

    def append_to_queue(self, _):
        """
        Appends related track to queue.
        """
        player.append_to_queue(self.songitem.track)
        self.close()

    def remove_from_queue(self, _):
        """
        Removes related track from queue.
        """
        player.remove_from_queue(self.songitem.track)
        self.close()

    def create_station(self, _):
        """
        Create a station from this track.
        """
        player.create_station_from_track(self.songitem.track)
        self.close()

    def copy_url(self, _):
        """
        Copy URL to clipboard.
        """
        copy(self.songitem.track.cached_url)
        self.close()

    def close(self, *_):
        """
        Close this menu.
        """
        urwid.emit_signal(self, 'close')


class SongListBox(urwid.Frame):
    """
    Displays :class:`.SongListItem` instances.
    """
    signals = ['activate']

    def __init__(self, app, ):
        self.app = app

        self.current_item = None
        self.tracks = []
        self.tracks_walker = urwid.SimpleFocusListWalker([])
        self.walker = urwid.SimpleFocusListWalker([])

        player.track_changed += self.track_changed
        player.media_state_changed += self.media_state_changed

        self.list_box = urwid.ListBox(self.walker)
        self.filter_prefix = '> '
        self.filter_query = ''
        self.filter_box = urwid.Text('')
        self.filter_info = urwid.Text('')
        self.filter_panel = urwid.Columns([
            self.filter_box,
            ('pack', self.filter_info)
        ])
        self.content = urwid.Pile([
            self.list_box,
        ])

        self.overlay = urwid.Overlay(
            top_w=None,
            bottom_w=self.content,
            align='center',
            valign='middle',
            width=50,
            height='pack'
        )

        self.popup = None

        super(SongListBox, self).__init__(
            body=self.content
        )

    def start_filtering(self):
        """
        Starts filtering the song view
        """
        if not hotkey_manager.filtering:
            self.content.contents = [
                (self.list_box, ('weight', 1)),
                (self.filter_panel, ('pack', None))
            ]
            self.app.append_cancel_action(self.end_filtering)
            self.filter_query = ''
            hotkey_manager.filtering = True
            self.tracks_walker[:] = self.walker

            self.filter_box.set_text(self.filter_prefix)

    def perform_filtering(self, char):
        """
        Enter filtering mode (if not entered yet) and filter stuff.
        """
        if char == 'backspace':
            if self.filter_query == "":
                self.end_filtering()
                return
            self.filter_query = self.filter_query[:-1]
        else:
            self.filter_query += char
        self.filter_box.set_text(self.filter_prefix + self.filter_query)

        matches = self.get_filtered_items()
        self.filter_info.set_text('{} matches'.format(len(matches)))
        self.walker[:] = matches
        self.walker.set_focus(0)

        if self.app.current_page.slug == 'library':
            self.update_indexes()

    def get_filtered_items(self):
        """
        Get song items that match the search query.
        """
        matches = []
        for songitem in self.tracks_walker:
            if not isinstance(songitem, SongListItem):
                continue
            if self.filter_query.lower() in songitem.full_title.lower():
                matches.append(songitem)
        return matches

    def end_filtering(self):
        """
        Exit filtering mode.
        """
        if self.filter_box.text == '':
            return
        self.content.contents = [
            (self.list_box, ('weight', 1))
        ]
        hotkey_manager.filtering = False
        self.filter_box.set_text('')
        self.filter_info.set_text('')
        self.walker[:] = self.tracks_walker

    def set_placeholder(self, text):
        """
        Clear list and add one placeholder item.
        """
        self.walker[:] = [urwid.Text(text, align='center')]

    def tracks_to_songlist(self, tracks):
        """
        Convert list of track data items into list of :class:`.SongListItem` instances.
        """
        current_track = player.get_current_track()
        items = []
        current_index = None
        for index, track in enumerate(tracks):
            songitem = SongListItem(track)
            if current_track is not None and current_track == track:
                songitem.set_state(SongListItem.STATE_LOADING)
                if current_index is None:
                    current_index = index
            urwid.connect_signal(
                songitem, 'activate', self.item_activated
            )

            urwid.connect_signal(
                songitem, 'play', self.item_play_pause
            )
            urwid.connect_signal(
                songitem, 'append-requested', self.item_append_requested
            )
            urwid.connect_signal(
                songitem, 'unappend-requested', self.item_unappend_requested
            )
            urwid.connect_signal(
                songitem, 'clear-queue', self.clear_queue
            )
            urwid.connect_signal(
                songitem, 'station-requested', self.item_station_requested
            )
            urwid.connect_signal(
                songitem, 'context-menu-requested', self.context_menu_requested
            )
            items.append(songitem)
        return (items, current_index)

    def item_play_pause(self, songitem):
        """
        Called when you want to start playing a song.
        """
        if songitem.is_currently_played:
            player.play_pause()

    def item_activated(self, songitem):
        """
        Called when specific song item is activated.
        Toggles track playback state or loads entire playlist
        that contains current track into player queue.
        """
        page = self.app.current_page
        if songitem.is_currently_played:
            player.play_pause()
        elif page.slug == 'queue':
            player.goto_track(songitem.track)
        # There are some pages like search library where overwriting the queue
        # doesn't make much sense. We can also assume that someone searching
        # for a specific song also wants to append it.
        elif page.append or hotkey_manager.filtering:
            self.item_append_requested(songitem)
        else:
            player.load_queue(self.tracks, songitem.index)

        if hotkey_manager.filtering and page.slug != 'search':
            self.walker[:] = self.get_filtered_items()

    @staticmethod
    def item_append_requested(songitem):
        """
        Called when specific item emits *append-requested* item.
        Appends track to player queue.
        """
        player.append_to_queue(songitem.track)

    @staticmethod
    def item_unappend_requested(songitem):
        """
        Called when specific item emits *remove-requested* item.
        Removes track from player queue.
        """
        player.remove_from_queue(songitem.track)

    @staticmethod
    def item_station_requested(songitem):
        """
        Called when specific item emits *station-requested* item.
        Requests new station creation.
        """
        player.create_station_from_track(songitem.track)

    def context_menu_requested(self, songitem):
        """
        Show context menu.
        """
        self.popup = SongListBoxPopup(songitem)
        self.app.append_cancel_action(self.popup.close)
        self.overlay.top_w = self.popup
        urwid.connect_signal(self.popup, 'close', self.hide_context_menu)
        self.contents['body'] = (self.overlay, None)

    @property
    def is_context_menu_visible(self):
        """
        Return ``True`` if context menu is currently being shown.
        """
        return self.contents['body'][0] is self.overlay

    def hide_context_menu(self):
        """
        Hide context menu.
        """
        if self.popup is not None and self.is_context_menu_visible:
            self.contents['body'] = (self.content, None)
            self.app.unregister_cancel_action(self.popup.close)
            self.popup = None

    def track_changed(self, track):
        """
        Called when new track playback is started.
        Marks corresponding song item (if found in this song list) as currently played.
        """
        for i, songitem in enumerate(self.walker):
            if isinstance(songitem, urwid.Text):
                continue
            if songitem.track == track or \
               (self.app.current_page.slug != 'queue' and songitem.track.id is track.id):
                songitem.set_state(SongListItem.STATE_LOADING)
                self.walker.set_focus(i)
            elif songitem.state != SongListItem.STATE_IDLE:
                songitem.set_state(SongListItem.STATE_IDLE)

    def media_state_changed(self, is_loading, is_playing):
        """
        Called when player media state changes.
        Updates corresponding song item state (if found in this song list).
        """
        current_track = player.get_current_track()
        if current_track is None:
            return

        for songitem in self.walker:
            if isinstance(songitem, urwid.Text):
                continue
            if songitem.track == current_track:
                songitem.set_state(
                    SongListItem.STATE_LOADING
                    if is_loading
                    else SongListItem.STATE_PLAYING
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
        elif len(self.walker) >= 1:
            self.walker.set_focus(0)

    def clear_queue(self, _):
        """
        Removes all tracks from the queue
        """
        self.current_item = None
        self.walker.set_focus(0)
        player.clear_queue()

    def append_track(self, track):
        """
        Convert a track into :class:`.SongListItem` instance and appends it into this song list.
        """
        tracks, _ = self.tracks_to_songlist([track])
        self.walker.append(tracks[0])
        self.update_indexes()

    def remove_track(self, track, ):
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

    def keypress(self, size, key):
        return hotkey_manager.keypress("song_view", self, super(SongListBox, self), size, key)

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
