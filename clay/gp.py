"""
Google Play Music integration via gmusicapi.
"""
# pylint: disable=broad-except
# pylint: disable=C0103
# pylint: disable=too-many-arguments
# pylint: disable=invalid-name
from threading import Thread, Lock

from gmusicapi.clients import Mobileclient

from clay.eventhook import EventHook


def asynchronous(func):
    """
    Decorates a function to become asynchronous.

    Once called, runs original function in a new Thread.

    Must be called with a 'callback' argument that will be called
    once thread with original function finishes. Receives two args:
    result and error.

    - "result" contains function return value or None if there was an exception.
    - "error" contains None or Exception if there was one.
    """
    def wrapper(*args, **kwargs):
        """
        Inner function.
        """
        callback = kwargs.pop('callback')
        extra = kwargs.pop('extra', dict())

        def process():
            """
            Thread body.
            """
            try:
                result = func(*args, **kwargs)
            except Exception as error:
                callback(None, error, **extra)
            else:
                callback(result, None, **extra)

        Thread(target=process).start()
    return wrapper


def synchronized(func):
    """
    Decorates a function to become thread-safe by preventing
    it from being executed multiple times before previous calls end.

    Lock is acquired on entrance and is released on return or Exception.
    """
    lock = Lock()

    def wrapper(*args, **kwargs):
        """
        Inner function.
        """
        try:
            lock.acquire()
            return func(*args, **kwargs)
        finally:
            lock.release()

    return wrapper


class Track(object):
    """
    Model that represents single track from Google Play Music.
    """
    TYPE_UPLOADED = 'uploaded'
    TYPE_STORE = 'store'

    def __init__(self, track_id, title, artist, duration, track_type):
        self._id = track_id
        self.title = title
        self.artist = artist
        self.duration = duration
        self.type = track_type

    @property
    def id(self):
        """
        "id" or "track_id" of this track.
        """
        return self._id

    @classmethod
    def from_data(cls, data, many=False):
        """
        Construct and return one or many :class:`.Track` instances
        from Google Play Music API response.
        """
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
            track_id=track_id,
            title=data['title'],
            artist=data['artist'],
            duration=int(data['durationMillis']),
            track_type=track_type
        )

    def get_url(self, callback):
        """
        Gets playable stream URL for this track.

        "callback" is called with "(url, error)" args after URL is fetched.

        Keep in mind this URL is valid for a limited time.
        """
        GP.get().get_stream_url_async(self.id, callback=callback, extra=dict(track=self))

    @synchronized
    def create_station(self):
        """
        Creates a new station from this :class:`.Track`.

        Returns :class:`.Station` instance.
        """
        station_id = GP.get().mobile_client.create_station(
            name=u'Station - {}'.format(self.title),
            track_id=self.id
        )
        station = Station(station_id)
        station.load_tracks()
        return station

    create_station_async = asynchronous(create_station)


class Artist(object):
    """
    Model that represents artist.
    """
    def __init__(self, artist_id, name):
        self._id = artist_id
        self.name = name

    @property
    def id(self):
        """
        Artist ID.
        """
        return self._id

    @classmethod
    def from_data(cls, data, many=False):
        """
        Construct and return one or many :class:`.Artist` instances
        from Google Play Music API response.
        """
        if many:
            return [cls.from_data(one) for one in data]

        return Artist(
            artist_id=data['artistId'],
            name=data['name']
        )


class Playlist(object):
    """
    Model that represents remotely stored (Google Play Music) playlist.
    """
    def __init__(self, playlist_id, name, tracks):
        self._id = playlist_id
        self.name = name
        self.tracks = tracks

    @property
    def id(self):
        """
        Playlist ID.
        """
        return self._id

    @classmethod
    def from_data(cls, data, many=False):
        """
        Construct and return one or many :class:`.Playlist` instances
        from Google Play Music API response.
        """
        if many:
            return [cls.from_data(one) for one in data]

        return Playlist(
            playlist_id=data['id'],
            name=data['name'],
            tracks=cls.playlist_items_to_tracks(data['tracks'])
        )

    @classmethod
    def playlist_items_to_tracks(cls, playlist_tracks):
        """
        Converts Google Play Music API response with playlist tracks data
        into list of :class:`Track` instances. Uses "My library" cache
        to fulfil missing track IDs (Google does not provide proper track IDs
        for tracks that are in both playlist and "my library").
        """
        results = []
        cached_tracks_map = GP.get().get_cached_tracks_map()
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
    """
    Model that represents specific station on Google Play Music.
    """
    def __init__(self, station_id):
        self._id = station_id
        self._tracks = []
        self._tracks_loaded = False

    @property
    def id(self):
        """
        Station ID.
        """
        return self._id

    def load_tracks(self):
        """
        Fetch tracks related to this station and
        populate it with :class:`Track` instances.
        """
        data = GP.get().mobile_client.get_station_tracks(self.id, 100)
        self._tracks = Track.from_data(data, many=True)
        self._tracks_loaded = True

    def get_tracks(self):
        """
        Return a list of tracks in this station.
        """
        assert self._tracks_loaded, 'Must call ".load_tracks()" before ".get_tracks()"'
        return self._tracks


class SearchResults(object):
    """
    Model that represents search results including artists & tracks.
    """
    def __init__(self, tracks, artists):
        self.artists = artists
        self.tracks = tracks

    @classmethod
    def from_data(cls, data):
        """
        Construct and return :class:`.SearchResults` instance from raw data.
        """
        return SearchResults(
            tracks=Track.from_data([item['track'] for item in data['song_hits']], many=True),
            artists=Artist.from_data([item['artist'] for item in data['artist_hits']], many=True)
        )

    def get_artists(self):
        """
        Return found artists.
        """
        return self.artists

    def get_tracks(self):
        """
        Return found tracks.
        """
        return self.tracks


class GP(object):
    """
    Interface to :class:`gmusicapi.Mobileclient`. Implements
    asynchronous API calls, caching and some other perks.

    Singleton.
    """
    # TODO: Switch to urwid signals for more explicitness?
    instance = None

    def __init__(self):
        assert self.__class__.instance is None, 'Can be created only once!'
        self.mobile_client = Mobileclient()
        self.cached_tracks = None
        self.cached_playlists = None

        self.invalidate_caches()

        self.auth_state_changed = EventHook()

    @classmethod
    def get(cls):
        """
        Create new :class:`.GP` instance or return existing one.
        """
        if cls.instance is None:
            cls.instance = GP()

        return cls.instance

    def invalidate_caches(self):
        """
        Clear cached tracks & playlists.
        """
        self.cached_tracks = None
        self.cached_playlists = None

    @synchronized
    def login(self, email, password, device_id, **_):
        """
        Log in into Google Play Music.
        """
        self.mobile_client.logout()
        self.invalidate_caches()
        prev_auth_state = self.is_authenticated
        result = self.mobile_client.login(email, password, device_id)
        if prev_auth_state != self.is_authenticated:
            self.auth_state_changed.fire(self.is_authenticated)
        return result

    login_async = asynchronous(login)

    @synchronized
    def get_all_tracks(self):
        """
        Cache and return all tracks from "My library".
        """
        if self.cached_tracks:
            return self.cached_tracks
        self.cached_tracks = Track.from_data(self.mobile_client.get_all_songs(), True)
        return self.cached_tracks

    get_all_tracks_async = asynchronous(get_all_tracks)

    def get_stream_url(self, stream_id):
        """
        Returns playable stream URL of track by id.
        """
        return self.mobile_client.get_stream_url(stream_id)

    get_stream_url_async = asynchronous(get_stream_url)

    @synchronized
    def get_all_user_playlist_contents(self, **_):
        """
        Return list of :class:`.Playlist` instances.
        """
        if self.cached_playlists:
            return self.cached_playlists
        self.get_all_tracks()

        self.cached_playlists = Playlist.from_data(
            self.mobile_client.get_all_user_playlist_contents(),
            True
        )
        return self.cached_playlists

    get_all_user_playlist_contents_async = asynchronous(get_all_user_playlist_contents)

    def get_cached_tracks_map(self):
        """
        Return a dictionary of tracks where keys are strings with track IDs
        and values are :class:`.Track` instances.
        """
        return {track.id: track for track in self.cached_tracks}

    def search(self, query):
        """
        Find tracks and return an instance of :class:`.SearchResults`.
        """
        results = self.mobile_client.search(query)
        return SearchResults.from_data(results)

    search_async = asynchronous(search)

    @property
    def is_authenticated(self):
        """
        Return True if user is authenticated on Google Play Music, false otherwise.
        """
        return self.mobile_client.is_authenticated()
