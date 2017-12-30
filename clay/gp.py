from gmusicapi.clients import Mobileclient
from threading import Thread, Lock

gp = None


def async(fn):
    def wrapper(*args, **kwargs):
        callback = kwargs.pop('callback')
        extra = kwargs.pop('extra', dict())

        def process():
            try:
                result = fn(*args, **kwargs)
            except Exception as e:
                callback(None, e, **extra)
                raise
            else:
                callback(result, None, **extra)

        Thread(target=process).start()
    return wrapper


def synchronized(fn):
    lock = Lock()

    def wrapper(*args, **kwargs):
        try:
            lock.acquire()
            return fn(*args, **kwargs)
        finally:
            lock.release()

    return wrapper


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
    def __init__(self, id, name, tracks):
        self.id = id
        self.name = name
        self.tracks = tracks

    @classmethod
    def from_data(cls, data, many=False):
        if many:
            return [cls.from_data(one) for one in data]

        return Playlist(
            id=data['id'],
            name=data['name'],
            tracks=cls.playlist_items_to_tracks(data['tracks'])
        )

    @classmethod
    def playlist_items_to_tracks(self, playlist_tracks):
        results = []
        cached_tracks_map = gp.get_cached_tracks_map()
        for playlist_track in playlist_tracks:
            if 'track' in playlist_track:
                track = dict(playlist_track['track'])
                track['id'] = playlist_track['trackId']
                track = Track.from_data(track)
            else:
                track = cached_tracks_map[playlist_track['trackId']]
            results.append(track)
        return results


class GP(object):
    def __init__(self):
        self.mc = Mobileclient()
        self.invalidate_caches()

    def invalidate_caches(self):
        self.cached_tracks = None
        self.cached_playlists = None

    @async
    @synchronized
    def login(self, email, password, device_id):
        self.mc.logout()
        self.invalidate_caches()
        # TODO: Move device_id to settings
        return self.mc.login(email, password, device_id)

    @async
    @synchronized
    def get_all_tracks(self):
        if self.cached_tracks:
            return self.cached_tracks
        self.cached_tracks = Track.from_data(self.mc.get_all_songs(), True)
        return self.cached_tracks

    @async
    def get_stream_url(self, id):
        return self.mc.get_stream_url(id)

    @async
    @synchronized
    def get_all_user_playlist_contents(self):
        if self.cached_playlists:
            return self.cached_playlists
        if not self.cached_tracks:
            self.cached_tracks = self.mc.get_all_tracks()

        self.cached_playlists = Playlist.from_data(
            self.mc.get_all_user_playlist_contents(),
            True
        )
        return self.cached_playlists

    def get_cached_tracks_map(self):
        return {track.id: track for track in self.cached_tracks}


gp = GP()

