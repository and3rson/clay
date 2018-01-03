from gmusicapi.clients import Mobileclient
from threading import Thread, Lock
from clay.eventhook import EventHook

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
    TYPE_UPLOADED = 'uploaded'
    TYPE_STORE = 'store'

    def __init__(self, id, title, artist, duration, type):
        self.id = id
        self.title = title
        self.artist = artist
        self.duration = duration
        self.type = type

    @classmethod
    def from_data(cls, data, many=False):
        if many:
            return [cls.from_data(one) for one in data]

        if 'id' in data:
            track_id = data['id']
            track_type = 'uploaded'
        elif 'storeId' in data:
            track_id = data['storeId']
            track_type = 'store'
        else:
            raise Exception('Track is missing both "id" and "storeId"! Where does it come from?')

        return Track(
            id=track_id,
            title=data['title'],
            artist=data['artist'],
            duration=int(data['durationMillis']),
            type=track_type
        )

    def get_url(self, callback):
        gp.get_stream_url(self.id, callback=callback, extra=dict(track=self))

    @async
    @synchronized
    def create_station(self):
        station_id = gp.mc.create_station(name=u'Station - {}'.format(self.title), track_id=self.id)
        station = Station(station_id)
        station.load_tracks()
        return station


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


class Station(object):
    def __init__(self, id):
        self.id = id
        self.tracks = []

    def load_tracks(self):
        data = gp.mc.get_station_tracks(self.id, 100)
        # import json
        # raise Exception(json.dumps(data, indent=4))
        self.tracks = Track.from_data(data, many=True)

    def get_tracks(self):
        return self.tracks


class GP(object):
    def __init__(self):
        self.mc = Mobileclient()
        self.invalidate_caches()

        self.auth_state_changed = EventHook()

    def invalidate_caches(self):
        self.cached_tracks = None
        self.cached_playlists = None

    @async
    @synchronized
    def login(self, email, password, device_id):
        self.mc.logout()
        self.invalidate_caches()
        # TODO: Move device_id to settings
        prev_auth_state = self.is_authenticated
        result = self.mc.login(email, password, device_id)
        if prev_auth_state != self.is_authenticated:
            self.auth_state_changed.fire(self.is_authenticated)
        return result

    @synchronized
    def get_all_tracks_sync(self):
        if self.cached_tracks:
            return self.cached_tracks
        self.cached_tracks = Track.from_data(self.mc.get_all_songs(), True)
        return self.cached_tracks

    get_all_tracks = async(get_all_tracks_sync)

    @async
    def get_stream_url(self, id):
        return self.mc.get_stream_url(id)

    @async
    @synchronized
    def get_all_user_playlist_contents(self):
        if self.cached_playlists:
            return self.cached_playlists
        self.get_all_tracks_sync()

        self.cached_playlists = Playlist.from_data(
            self.mc.get_all_user_playlist_contents(),
            True
        )
        return self.cached_playlists

    # @async
    # @synchronized
    # def create_station(self, name, track_id=None, artist_id=None, album_id=None, genre_id=None):
    #     kwargs = dict(track_id=track_id, artist_id=artist_id, album_id=album_id, genre_id=genre_id)
    #     # kwargs = {k: v for k, v in kwargs.items() if v is not None}
    #     # if len(kwargs) != 1:
    #     #     raise Exception('Must provide one of artist_id, album_id or genre_id')
    #     station_id = Station.from_data(self.mc.create_station(name, **kwargs))
    #     return station_id

    def get_cached_tracks_map(self):
        return {track.id: track for track in self.cached_tracks}

    @property
    def is_authenticated(self):
        return self.mc.is_authenticated()


gp = GP()

