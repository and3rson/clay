from random import randint

# import dbus
import json

import vlc
from eventhook import EventHook
import gp
from gp import gp


class Track(object):
    def __init__(self, id, title, artist, duration):
        self.id = id
        self.title = title
        self.artist = artist
        self.duration = duration

    @classmethod
    def from_data(cls, data, many=False):
        if many:
            return [cls.from_data(one) for one in data]

        return Track(
            id=data['id'],
            title=data['title'],
            artist=data['artist'],
            duration=int(data['durationMillis'])
        )

    def get_url(self, callback):
        gp.get_stream_url(self.id, callback=callback, extra=dict(track=self))


class Playlist(object):
    def __init__(self):
        self.random = False
        self.repeat_one = False

        self.tracks = []
        self.current_track = None

    def load(self, tracks, current_track=None):
        self.tracks = tracks[:]
        if current_track is None and len(self.tracks):
            current_track = self.tracks[0]
        self.current_track = current_track

    def get_current_track(self):
        if self.current_track is None:
            return None
        return self.tracks[self.current_track]

    def next(self, force=False):
        if self.current_track is None:
            if not len(self.tracks):
                return None
            self.current_track = self.tracks[0]

        if self.repeat_one and not force:
            return self.get_current_track()

        if self.random:
            self.current_track = randint(0, len(self.tracks) - 1)
            return self.get_current_track()

        self.current_track += 1
        if (self.current_track + 1) >= len(self.tracks):
            self.current_track = 0

        return self.get_current_track()

    def get_tracks(self):
        return self.tracks


class Player(object):
    media_position_changed = EventHook()
    media_state_changed = EventHook()
    track_changed = EventHook()
    playback_flags_changed = EventHook()

    def __init__(self):
        self.mp = vlc.MediaPlayer()
        # self.bus = dbus.SessionBus()
        # try:
        #     self.obj = self.bus.get_object('org.awesomewm.awful', '/org/dunai/clay')
        # except dbus.DBusException as e:
        #     print(e)
        #     self.interface = None
        # else:
        #     self.interface = dbus.Interface(self.obj, 'org.dunai.clay')
        # self.statusfile = open('/tmp/clay.json', 'w')

        self.mp.event_manager().event_attach(
            vlc.EventType.MediaPlayerPlaying,
            self._media_state_changed
        )
        self.mp.event_manager().event_attach(
            vlc.EventType.MediaPlayerPaused,
            self._media_state_changed
        )
        self.mp.event_manager().event_attach(
            vlc.EventType.MediaPlayerEndReached,
            self._media_end_reached
        )
        self.mp.event_manager().event_attach(
            vlc.EventType.MediaPlayerPositionChanged,
            self._media_position_changed
        )

        self.playlist = Playlist()

    def broadcast_state(self):
        track = self.playlist.get_current_track()
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
                playing=self.is_playing,
                artist=track.artist,
                title=track.title,
                progress=self.get_play_progress_seconds(),
                length=self.get_length_seconds()
            )
        with open('/tmp/clay.json', 'w') as f:
            f.write(json.dumps(data, indent=4))

    def _media_state_changed(self, e):
        self.broadcast_state()
        self.media_state_changed.fire(self.is_playing)

    def _media_end_reached(self, e):
        self.next()

    def _media_position_changed(self, e):
        self.broadcast_state()
        self.media_position_changed.fire(
            self.get_play_progress()
        )

    def load_playlist(self, data, current_index):
        self.playlist.load(data, current_index)
        self._play()

    def get_is_random(self):
        return self.playlist.random

    def get_is_repeat_one(self):
        return self.playlist.repeat_one

    def set_random(self, value):
        self.playlist.random = value
        self.playback_flags_changed.fire()

    def set_repeat_one(self, value):
        self.playlist.repeat_one = value
        self.playback_flags_changed.fire()

    def get_queue(self):
        return self.playlist.get_tracks()

    def _play(self):
        track = self.playlist.get_current_track()
        if track is None:
            return
        track.get_url(callback=self._play_ready)
        self.broadcast_state()
        self.track_changed.fire(track)

    def _play_ready(self, url, error, track):
        if error:
            raise error
        self.mp.set_media(vlc.Media(url))
        self.mp.play()

    @property
    def is_playing(self):
        return self.mp.get_state() == vlc.State.Playing

    def play_pause(self):
        if self.is_playing:
            self.mp.pause()
        else:
            self.mp.play()

    def get_play_progress(self):
        return self.mp.get_position()

    def get_play_progress_seconds(self):
        return int(self.mp.get_position() * self.mp.get_length() / 1000)

    def get_length_seconds(self):
        return int(self.mp.get_length() // 1000)

    def next(self, force=False):
        self.playlist.next(force)
        self._play()

    def get_current_track(self):
        return self.playlist.get_current_track()

    # def prev(self):
    #     self.playlist.prev()
    #     self._play()

    def seek(self, delta):
        self.mp.set_position(self.get_play_progress() + delta)


player = Player()

