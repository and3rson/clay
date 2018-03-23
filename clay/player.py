"""
Media player built using libVLC.
"""
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-public-methods
from random import randint
from ctypes import CFUNCTYPE, c_void_p, c_int, c_char_p
import json
import os

try:  # Python 3.x
    from urllib.request import urlopen
except ImportError:  # Python 2.x
    from urllib2 import urlopen

from clay import vlc, meta
from clay.eventhook import EventHook
from clay.notifications import notification_area
from clay.settings import settings
from clay.log import logger


class _Queue(object):
    """
    Model that represents player queue (local playlist),
    i.e. list of tracks to be played.

    Queue is used by :class:`.Player` to choose tracks for playback.

    Queue handles shuffling & repeating.

    Can be populated with :class:`clay.gp.Track` instances.
    """
    def __init__(self):
        self.random = False
        self.repeat_one = False

        self.tracks = []
        self._played_tracks = []
        self.current_track_index = None

    def load(self, tracks, current_track_index=None):
        """
        Load list of tracks into queue.

        *current_track_index* can be either ``None`` or ``int`` (zero-indexed).
        """
        self.tracks = tracks[:]
        if (current_track_index is None) and self.tracks:
            current_track_index = 0
        self.current_track_index = current_track_index

    def append(self, track):
        """
        Append track to playlist.
        """
        self.tracks.append(track)

    def remove(self, track):
        """
        Remove track from playlist if is present there.
        """
        if track not in self.tracks:
            return

        index = self.tracks.index(track)
        self.tracks.remove(track)
        if self.current_track_index is None:
            return
        if index < self.current_track_index:
            self.current_track_index -= 1

    def get_current_track(self):
        """
        Return current :class:`clay.gp.Track`
        """
        if self.current_track_index is None:
            return None
        return self.tracks[self.current_track_index]

    def next(self, force=False):
        """
        Advance to the next track and return it.

        If *force* is ``True`` then track will be changed even if
        track repetition is enabled. Otherwise current track may be yielded
        again.

        Manual track switching calls this method with ``force=True`` while
        :class:`.Player` end-of-track event will call it with ``force=False``.
        """
        if self.current_track_index is None:
            if not self.tracks:
                return None
            self.current_track_index = self.tracks[0]
        else:
            self._played_tracks.append(self.current_track_index)

        if self.repeat_one and not force:
            return self.get_current_track()

        if self.random:
            self.current_track_index = randint(0, len(self.tracks) - 1)
            return self.get_current_track()

        self.current_track_index += 1
        if (self.current_track_index + 1) >= len(self.tracks):
            self.current_track_index = 0

        return self.get_current_track()

    def prev(self, force=False):
        """
        Revert to their last song and return it.

        If *force* is ``True`` then tracks will be changed event if
        tracks repition is enabled. Otherwise current tracks may be
        yielded again.

        Manual tracks switching calls this method with ``force=True``.
        """
        if self._played_tracks == []:
            return None

        if self.repeat_one and not force:
            return self.get_current_track()

        self.current_track_index = self._played_tracks.pop()
        return self.get_current_track()

    def get_tracks(self):
        """
        Return current queue, i.e. a list of :class:`Track` instances.
        """
        return self.tracks

#+pylint: disable=unused-argument
def _dummy_log(data, level, ctx, fmt, args):
    """
    A dummy callback function for VLC so it doesn't write to stdout.
    Should probably do something in the future
    """
    pass
#+pylint: disable=unused-argument

class _Player(object):
    """
    Interface to libVLC. Uses Queue as a playback plan.
    Emits various events if playback state, tracks or play flags change.

    Singleton.
    """
    media_position_changed = EventHook()
    media_state_changed = EventHook()
    track_changed = EventHook()
    playback_flags_changed = EventHook()
    queue_changed = EventHook()
    track_appended = EventHook()
    track_removed = EventHook()

    def __init__(self):
        self.instance = vlc.Instance()
        print_func = CFUNCTYPE(c_void_p,
                               c_void_p, # data
                               c_int, # level
                               c_void_p, # context
                               c_char_p, # fmt
                               c_void_p) #args

        self.instance.log_set(print_func(_dummy_log), None)

        self.instance.set_user_agent(
            meta.APP_NAME,
            meta.USER_AGENT
        )

        self.media_player = self.instance.media_player_new()

        self.media_player.event_manager().event_attach(
            vlc.EventType.MediaPlayerPlaying,
            self._media_state_changed
        )
        self.media_player.event_manager().event_attach(
            vlc.EventType.MediaPlayerPaused,
            self._media_state_changed
        )
        self.media_player.event_manager().event_attach(
            vlc.EventType.MediaPlayerEndReached,
            self._media_end_reached
        )
        self.media_player.event_manager().event_attach(
            vlc.EventType.MediaPlayerPositionChanged,
            self._media_position_changed
        )

        self.equalizer = vlc.libvlc_audio_equalizer_new()
        self.media_player.set_equalizer(self.equalizer)
        self._create_station_notification = None
        self._is_loading = False
        self.queue = _Queue()

    def enable_xorg_bindings(self):
        """Enable the global X bindings using keybinder"""
        if os.environ.get("DISPLAY") is None:
            logger.debug("X11 isn't running so we can't load the global keybinds")
            return

        from clay.hotkeys import hotkey_manager
        hotkey_manager.play_pause += self.play_pause
        hotkey_manager.next += self.next
        hotkey_manager.prev += lambda: self.seek_absolute(0)

    def broadcast_state(self):
        """
        Write current playback state into a ``/tmp/clay.json`` file.
        """
        track = self.queue.get_current_track()
        if track is None:
            data = dict(
                playing=False,
                artist=None,
                title=None,
                progress=None,
                length=None
            )
        else:
            data = dict(
                loading=self.is_loading,
                playing=self.is_playing,
                artist=track.artist,
                title=track.title,
                progress=self.get_play_progress_seconds(),
                length=self.get_length_seconds(),
                album_name=track.album_name,
                album_url=track.album_url
            )
        with open('/tmp/clay.json', 'w') as statefile:
            statefile.write(json.dumps(data, indent=4))

    def _media_state_changed(self, event):
        """
        Called when a libVLC playback state changes.
        Broadcasts playback state & fires :attr:`media_state_changed` event.
        """
        assert event
        self.broadcast_state()
        self.media_state_changed.fire(self.is_loading, self.is_playing)

    def _media_end_reached(self, event):
        """
        Called when end of currently played track is reached.
        Advances to the next track.
        """
        assert event
        self.next()

    def _media_position_changed(self, event):
        """
        Called when playback position changes (this happens few times each second.)
        Fires :attr:`.media_position_changed` event.
        """
        assert event
        self.broadcast_state()
        self.media_position_changed.fire(
            self.get_play_progress()
        )

    def load_queue(self, data, current_index=None):
        """
        Load queue & start playback.
        Fires :attr:`.queue_changed` event.

        See :meth:`._Queue.load`.
        """
        self.queue.load(data, current_index)
        self.queue_changed.fire()
        self._play()

    def append_to_queue(self, track):
        """
        Append track to queue.
        Fires :attr:`.track_appended` event.

        See :meth:`._Queue.append`
        """
        self.queue.append(track)
        self.track_appended.fire(track)
        # self.queue_changed.fire()

    def remove_from_queue(self, track):
        """
        Remove track from queue.
        Fires :attr:`.track_removed` event.

        See :meth:`._Queue.remove`
        """
        self.queue.remove(track)
        self.track_removed.fire(track)

    def create_station_from_track(self, track):
        """
        Request creation of new station from some track.
        Runs in background.
        """
        self._create_station_notification = notification_area.notify('Creating station...')
        track.create_station_async(callback=self._create_station_from_track_ready)

    def _create_station_from_track_ready(self, station, error):
        """
        Called when a station is created.
        If *error* is ``None``, load new station's tracks into queue.
        """
        if error:
            self._create_station_notification.update(
                'Failed to create station: {}'.format(str(error))
            )
            return

        if not station.get_tracks():
            self._create_station_notification.update(
                'Newly created station is empty :('
            )
            return

        self.load_queue(station.get_tracks())
        self._create_station_notification.update('Station ready!')

    def get_is_random(self):
        """
        Return ``True`` if track selection from queue is randomed, ``False`` otherwise.
        """
        return self.queue.random

    def get_is_repeat_one(self):
        """
        Return ``True`` if track repetition in queue is enabled, ``False`` otherwise.
        """
        return self.queue.repeat_one

    def set_random(self, value):
        """
        Enable/disable random track selection.
        """
        self.queue.random = value
        self.playback_flags_changed.fire()

    def set_repeat_one(self, value):
        """
        Enable/disable track repetition.
        """
        self.queue.repeat_one = value
        self.playback_flags_changed.fire()

    def get_queue_tracks(self):
        """
        Return :attr:`._Queue.get_tracks`
        """
        return self.queue.get_tracks()

    def _play(self):
        """
        Pick current track from a queue and requests media stream URL.
        Completes in background.
        """
        track = self.queue.get_current_track()
        if track is None:
            return
        self._is_loading = True
        self.broadcast_state()
        self.track_changed.fire(track)

        if settings.get('download_tracks', 'play_settings') or \
           settings.get_is_file_cached(track.filename):
            path = settings.get_cached_file_path(track.filename)

            if path is None:
                logger.debug('Track %s not in cache, downloading...', track.store_id)
                track.get_url(callback=self._download_track)
            else:
                logger.debug('Track %s in cache, playing', track.store_id)
                self._play_ready(path, None, track)
        else:
            logger.debug('Starting to stream %s', track.store_id)
            track.get_url(callback=self._play_ready)

    def _download_track(self, url, error, track):
        if error:
            notification_area.notify('Failed to request media URL: {}'.format(str(error)))
            logger.error(
                'Failed to request media URL for track %s: %s',
                track.original_data,
                str(error)
            )
            return
        response = urlopen(url)
        path = settings.save_file_to_cache(track.filename, response.read())
        self._play_ready(path, None, track)

    def _play_ready(self, url, error, track):
        """
        Called once track's media stream URL request completes.
        If *error* is ``None``, tell libVLC to play media by *url*.
        """
        self._is_loading = False
        if error:
            notification_area.notify('Failed to request media URL: {}'.format(str(error)))
            logger.error(
                'Failed to request media URL for track %s: %s',
                track.original_data,
                str(error)
            )
            return
        assert track
        media = vlc.Media(url)
        self.media_player.set_media(media)

        self.media_player.play()

    @property
    def is_loading(self):
        """
        True if current libVLC state is :attr:`vlc.State.Playing`
        """
        return self._is_loading

    @property
    def is_playing(self):
        """
        True if current libVLC state is :attr:`vlc.State.Playing`
        """
        return self.media_player.get_state() == vlc.State.Playing

    def play_pause(self):
        """
        Toggle playback, i.e. play if paused or pause if playing.
        """
        if self.is_playing:
            self.media_player.pause()
        else:
            self.media_player.play()

    def get_play_progress(self):
        """
        Return current playback position in range ``[0;1]`` (``float``).
        """
        return self.media_player.get_position()

    def get_play_progress_seconds(self):
        """
        Return current playback position in seconds (``int``).
        """
        return int(self.media_player.get_position() * self.media_player.get_length() / 1000)

    def get_length_seconds(self):
        """
        Return currently played track's length in seconds (``int``).
        """
        return int(self.media_player.get_length() // 1000)

    def next(self, force=False):
        """
        Advance to next track in queue.
        See :meth:`._Queue.next`.
        """
        self.queue.next(force)
        self._play()

    def prev(self, force=False):
        """
        Advance to their previous track in their queue
        seek :meth:`._Queue.prev`
        """
        self.queue.prev(force)
        self._play()

    def get_current_track(self):
        """
        Return currently played track.
        See :meth:`._Queue.get_current_track`.
        """
        return self.queue.get_current_track()

    def seek(self, delta):
        """
        Seek to relative position.
        *delta* must be a ``float`` in range ``[-1;1]``.
        """
        self.media_player.set_position(self.get_play_progress() + delta)

    def seek_absolute(self, position):
        """
        Seek to absolute position.
        *position* must be a ``float`` in range ``[0;1]``.
        """
        self.media_player.set_position(position)

    @staticmethod
    def get_equalizer_freqs():
        """
        Return a list of equalizer frequencies for each band.
        """
        return [
            vlc.libvlc_audio_equalizer_get_band_frequency(index)
            for index
            in range(vlc.libvlc_audio_equalizer_get_band_count())
        ]

    def get_equalizer_amps(self):
        """
        Return a list of equalizer amplifications for each band.
        """
        return [
            vlc.libvlc_audio_equalizer_get_amp_at_index(
                self.equalizer,
                index
            )
            for index
            in range(vlc.libvlc_audio_equalizer_get_band_count())
        ]

    def set_equalizer_value(self, index, amp):
        """
        Set equalizer amplification for specific band.
        """
        assert vlc.libvlc_audio_equalizer_set_amp_at_index(
            self.equalizer,
            amp,
            index
        ) == 0
        self.media_player.set_equalizer(self.equalizer)

    def set_equalizer_values(self, amps):
        """
        Set a list of equalizer amplifications for each band.
        """
        assert len(amps) == vlc.libvlc_audio_equalizer_get_band_count()
        for index, amp in enumerate(amps):
            assert vlc.libvlc_audio_equalizer_set_amp_at_index(
                self.equalizer,
                amp,
                index
            ) == 0
        self.media_player.set_equalizer(self.equalizer)


player = _Player()  # pylint: disable=invalid-name
