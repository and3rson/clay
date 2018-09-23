"""
An abstract class for playback

Copyright (c) 2018, Valentijn van de Beek
"""
from random import randint
import json
import os

try:  # Python 3.x
    from urllib.request import urlopen
except ImportError:  # Python 2.x
    from urllib2 import urlopen


from clay.core import meta, settings_manager, logger, EventHook, osd_manager, mpris2

class _Queue(object):
    """
    Model that represents player queue (local playlist),
    i.e. list of tracks to be played.

    Queue is used by :class:`.Player` to choose tracks for playback.

    Queue handles shuffling & repeating.

    Can be populated with :class:`clay.core.gp.Track` instances.
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
        #if self.current_track_index is None:
            #self.current_track_index = 0
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
        Return current :class:`clay.core.gp.Track`
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
        if (self.current_track_index) >= len(self.tracks):
            self.current_track_index = 0

        return self.get_current_track()

    def prev(self, force=False):
        """
        Revert to the last song and return it.

        If *force* is ``True`` then tracks will be changed event if
        tracks repition is enabled. Otherwise current tracks may be
        yielded again.

        Manual tracks switching calls this method with ``force=True``.
        """
        if self._played_tracks == []:
            return None

        if self.repeat_one and not force:
            mpris2.mpris2_manager.Seeked.emit(0)
            return self.get_current_track()

        self.current_track_index = self._played_tracks.pop()
        return self.get_current_track()

    def get_tracks(self):
        """
        Return current queue, i.e. a list of :class:`Track` instances.
        """
        return self.tracks

class AbstractPlayer:
    """
    Defines the basic functions used by every player.
    """
    media_position_changed = EventHook()
    media_state_changed = EventHook()
    media_state_stopped = EventHook()
    track_changed = EventHook()
    playback_flags_changed = EventHook()
    queue_changed = EventHook()
    track_appended = EventHook()
    track_removed = EventHook()

    def __init__(self):
        self._create_station_notification = None
        self.queue = _Queue()

        # Add notification actions that we are going to use.
        osd_manager.add_to_action("media-skip-backward", "Previous", lambda: self.prev(force=True))
        osd_manager.add_to_action("media-playback-pause", "Pause", self.play_pause)
        osd_manager.add_to_action("media-playback-start", "Play", self.play_pause)
        osd_manager.add_to_action("media-skip-forward", "next", self.next)


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
                loading=self.loading,
                playing=self.playing,
                artist=track.artist,
                title=track.title,
                progress=self.play_progress_seconds,
                length=self.length_seconds,
                album_name=track.album_name,
                album_url=track.album_url
            )
        with open('/tmp/clay.json', 'w') as statefile:
            statefile.write(json.dumps(data, indent=4))

    def load_queue(self, data, current_index=None):
        """
        Load queue & start playback

        See :meth:`._Queue.load`
        """
        self.queue.load(data, current_index)
        self.queue_changed.fire()
        self.play()

    def append_to_queue(self, track):
        """
        Append track to queue.
        Fires :attr:`.track_appended` event

        See :meth:`._Queue.append`
        """
        self.queue.append(track)
        self.track_appended.fire(track)

    def remove_from_queue(self, track):
        """
        Remove track from queue
        Fires :attr:`.trac_removed` event.

        See :meth:`._Queue.remove`
        """
        self.queue.remove(track)
        self.track_removed.fire(track)

    def create_station_from_track(self, track):
        """
        Request creation of new station from some track.

        Runs in background.
        """
        track.create_station_async(callback=self._create_station_ready)
        #raise NotImplementedError

    @property
    def random(self):
        """
        Returns:
           Whether the track selection is random
        """
        return self.queue.random

    @random.setter
    def random(self, value):
        """
        Enable or disable random track selection

        Args:
           value (`bool`):  Whether random track selection should be enabled or disabled.
        """
        self.queue.random = value
        self.playback_flags_changed.fire()

    @property
    def repeat_one(self):
        """
        Returns:
           Whether single track repition is enabled.
        """
        return self.queue.repeat_one

    @repeat_one.setter
    def repeat_one(self, value):
        """
        Enables or disabled single track repition
        """
        self.queue.repeat_one = value
        self.playback_flags_changed.fire()

    def get_queue_tracks(self):
        """
        Return :attr:`.Queue.get_tracks`
        """
        return self.queue.get_tracks()

    def play(self):
        """
        Pick the current track from the queue and requests the media stream url.
        Should complete in the background.
        """
        raise NotImplementedError

    def _download_track(self, url, error, track):
        if error:
            logger.error(
                "failed to request media URL for track %s: %s",
                track.original_data,
                str(error)
            )
            return

        response = urlopen(url)
        path = settings_manager.save_file_to_cache(track.filename, response.read())
        self._ready_track(path, None, track)

    @property
    def loading(self):
        return self._loading

    @property
    def playing(self):
        raise NotImplementedError

    # Implement as a setter instead?
    def play_pause(self):
        """
        Toggle playback, i.e. play if pause or pause if playing.
        """
        raise NotImplementedError

    @property
    def play_progress(self):
        """
        Return current playback position in range ``[0;1]`` (``float``)
        """
        raise NotImplementedError

    @property
    def play_progress_seconds(self):
        """
        Return the current playback position in seconds (``int``)
        """
        raise NotImplementedError

    @property
    def time(self):
        """
        Returns:
           Get their current movie length in microseconds
e        """
        raise NotImplementedError

    def _seeked(self):
        mpris2.mpris2_manager.Seeked.emit(self.time)

    @time.setter
    def time(self, time):
        """
        Sets the current time in microseconds.
        This is a pythonic alternative to seeking using absolute times instead of percentiles.

        Args:
           time: Time in microseconds.
        """
        raise NotImplementedError

    @property
    def volume(self):
        """
        Returns:
           The current volume of in percentiles (0 = mute, 100 = 0dB)
        """
        raise NotImplementedError

    @volume.setter
    def volume(self, volume):
        """
        Args:
           volume: the volume in percentiles (0 = mute, 1000 = 0dB)

        Returns:
           The current volume of in percentiles (0 = mute, 100 = 0dB)
        """
        raise NotImplementedError

    def mute(self):
        """
        Mutes or unmutes the volume
        """
        raise NotImplementedError

    @property
    def length(self):
        """
        Returns:
          The current playback position in microseconds
        """
        raise NotImplementedError

    @property
    def length_seconds(self):
        """
        Return currently played track's length in seconds (``int``).
        """
        raise NotImplementedError

    def next(self, force=False):
        """
        Advance to next track in queue.
        See :meth:`._Queue.next`
        """
        self.queue.next(force)
        self.play()

    def prev(self, force=False):
        """
        Advance to their previous track in their queue
        seek :meth:`._Queue.prev`
        """
        self.queue.prev(force)
        self.play()

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
        raise NotImplementedError

    def seek_absolute(self, position):
        """
        Seek to absolute position.
        *position* must be a ``float`` in range ``[0;1]``.
        """
        raise NotImplementedError

    @staticmethod
    def get_equalizer_freqs():
        """
        Return a list of equalizer frequencies for each band.
        """
        raise NotImplementedError

    def get_equalizer_amps(self):
        """
        Return a list of equalizer amplifications for each band.
        """
        raise NotImplementedError

    def set_equalizer_value(self, index, amp):
        """
        Set equalizer amplification for specific band.
        """
        raise NotImplementedError

    def set_equalizer_values(self, amps):
        """
        Set a list of equalizer amplifications for each band.
        """
        raise NotImplementedError

player = AbstractPlayer() # pylint: disable=invalid-name
