"""
An implementation of the Clay player using VLC

Copyright (c) 2018, Clay Contributors
"""
from ctypes import CFUNCTYPE, c_void_p, c_int, c_char_p
from clay.core import osd_manager, logger, meta, settings_manager

from . import libvlc as vlc
from .abstract import AbstractPlayer


#+pylint: disable=unused-argument
def _dummy_log(data, level, ctx, fmt, args):
    """
    A dummy callback function for VLC so it doesn't write to stdout.
    Should probably do something in the future
    """
    pass
#+pylint: enable=unused-argument


class VLCPlayer(AbstractPlayer):
    """
    Interface to libVLC. Uses Queue as a playback plan.
    Emits various events if playback state, tracks or play flags change.

    Singleton.
    """

    def __init__(self):
        self.instance = vlc.Instance()
        print_func = CFUNCTYPE(c_void_p,
                               c_void_p,  # data
                               c_int,     # level
                               c_void_p,  # context
                               c_char_p,  # fmt
                               c_void_p)  # args

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
        AbstractPlayer.__init__(self)


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

#    def create_station_from_track(self, track):
#        """
#        Request creation of new station from some track.
#        Runs in background.
#        """
#        #self._create_station_notification = notification_area.notify('Creating station...')
#        track.create_station_async(callback=self._create_station_from_track_ready)

    def _create_station_ready(self, station, error):
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

    def play(self):
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

        if settings_manager.get('download_tracks', 'play_settings') or \
           settings_manager.get_is_file_cached(track.filename):
            path = settings_manager.get_cached_file_path(track.filename)

            if path is None:
                logger.debug('Track %s not in cache, downloading...', track.store_id)
                track.get_url(callback=self._download_track)
            else:
                logger.debug('Track %s in cache, playing', track.store_id)
                self._play_ready(path, None, track)
        else:
            logger.debug('Starting to stream %s', track.store_id)
            track.get_url(callback=self._play_ready)

    def _play_ready(self, url, error, track):
        """
        Called once track's media stream URL request completes.
        If *error* is ``None``, tell libVLC to play media by *url*.
        """
        self._is_loading = False
        if error:
            #notification_area.notify('Failed to request media URL: {}'.format(str(error)))
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

        osd_manager.notify(track)

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

player = VLCPlayer() # pylint: disable=invalid-name
