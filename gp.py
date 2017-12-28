from gmusicapi.clients import Mobileclient
from threading import Thread, Lock


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


class GP(object):
    def __init__(self):
        self.mc = Mobileclient()
        self.invalidate_caches()

    def invalidate_caches(self):
        self.cached_songs = None
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
    def get_all_songs(self):
        if self.cached_songs:
            return self.cached_songs
        self.cached_songs = self.mc.get_all_songs()
        return self.cached_songs

    @async
    def get_stream_url(self, id):
        return self.mc.get_stream_url(id)

    @async
    @synchronized
    def get_all_user_playlist_contents(self):
        if self.cached_playlists:
            return self.cached_playlists
        if not self.cached_songs:
            self.cached_songs = self.mc.get_all_songs()
        cached_songs_map = {track['id']: track for track in self.cached_songs}
        self.cached_playlists = self.mc.get_all_user_playlist_contents()
        for playlist in self.cached_playlists:
            for song in playlist['tracks']:
                if 'track' not in song:
                    song['track'] = cached_songs_map[song['trackId']]
                else:
                    song['track']['id'] = song['trackId']
        return self.cached_playlists


gp = GP()

