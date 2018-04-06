"""
Google Play Music integration via gmusicapi.
"""
# pylint: disable=broad-except
# pylint: disable=protected-access
from __future__ import print_function
from threading import Thread, Lock
from uuid import UUID

from gmusicapi.clients import Mobileclient

from clay.eventhook import EventHook
from clay.log import logger

STATION_FETCH_LEN = 50


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

    SOURCE_LIBRARY = 'library'
    SOURCE_STATION = 'station'
    SOURCE_PLAYLIST = 'playlist'
    SOURCE_SEARCH = 'search'

    def __init__(  # pylint: disable=too-many-arguments
            self,
            title, artist, duration, source,
            library_id=None, store_id=None, playlist_item_id=None,
            album_name=None, album_url=None, original_data=None
    ):
        self.title = title
        self.artist = artist
        self.duration = duration
        self.source = source

        self.cached_url = None

        self.library_id = library_id
        self.store_id = store_id
        self.playlist_item_id = playlist_item_id

        self.album_name = album_name
        self.album_url = album_url

        self.original_data = original_data

    @property
    def id(self):  # pylint: disable=invalid-name
        """
        Return ID for this track.
        """
        if self.library_id:
            return self.library_id
        return self.store_id

    @property
    def filename(self):
        """
        Return a filename for this track.
        """
        return self.store_id + '.mp3'

    def __eq__(self, other):
        return (
            (self.library_id and self.library_id == other.library_id) or
            (self.store_id and self.store_id == other.store_id) or
            (self.playlist_item_id and self.playlist_item_id == other.playlist_item_id)
        )

    @classmethod
    def _from_search(cls, data):
        """
        Create track from search result data.
        """
        # Data contains a nested track representation.
        return Track(
            title=data['track']['title'],
            artist=data['track']['artist'],
            duration=int(data['track']['durationMillis']),
            source=cls.SOURCE_SEARCH,
            store_id=data['track']['storeId'],  # or data['trackId']
            album_name=data['track']['album'],
            album_url=data['track']['albumArtRef'][0]['url'],
            original_data=data
        )

    @classmethod
    def _from_station(cls, data):
        """
        Create track from station track data.
        """
        # Station tracks have all the info in place.
        return Track(
            title=data['title'],
            artist=data['artist'],
            duration=int(data['durationMillis']),
            source=cls.SOURCE_STATION,
            store_id=data['storeId'],
            album_name=data['album'],
            album_url=data['albumArtRef'][0]['url'],
            original_data=data
        )

    @classmethod
    def _from_library(cls, data):
        """
        Create track from library track data.
        """
        # Data contains all info about track
        # including ID in library and ID in store.
        UUID(data['id'])
        return Track(
            title=data['title'],
            artist=data['artist'],
            duration=int(data['durationMillis']),
            source=cls.SOURCE_LIBRARY,
            store_id=data['storeId'],
            library_id=data['id'],
            album_name=data['album'],
            album_url=data['albumArtRef'][0]['url'],
            original_data=data
        )

    @classmethod
    def _from_playlist(cls, data):
        """
        Create track from playlist track data.
        """
        if 'track' in data:
            # Data contains a nested track representation that can be used
            # to construct new track.
            return Track(
                title=data['track']['title'],
                artist=data['track']['artist'],
                duration=int(data['track']['durationMillis']),
                source=cls.SOURCE_PLAYLIST,
                store_id=data['track']['storeId'],  # or data['trackId']
                playlist_item_id=data['id'],
                album_name=data['track']['album'],
                album_url=data['track']['albumArtRef'][0]['url'],
                original_data=data
            )
        # We need to find a track in Library by trackId.
        UUID(data['trackId'])
        track = gp.get_track_by_id(data['trackId'])
        return Track(
            title=track.title,
            artist=track.artist,
            duration=track.duration,
            source=cls.SOURCE_PLAYLIST,
            store_id=track.store_id,
            album_name=track.album_name,
            album_url=track.album_url,
            original_data=data
        )

    _CREATE_TRACK = {
        SOURCE_SEARCH: '_from_search',
        SOURCE_STATION: '_from_station',
        SOURCE_LIBRARY: '_from_library',
        SOURCE_PLAYLIST: '_from_playlist',
    }

    @classmethod
    def from_data(cls, data, source, many=False):
        """
        Construct and return one or many :class:`.Track` instances
        from Google Play Music API response.
        """
        if many:
            return [
                track
                for track
                in [cls.from_data(one, source) for one in data]
                if track is not None
            ]

        try:
            return getattr(cls, cls._CREATE_TRACK[source])(data)
        except Exception as error:  # pylint: disable=bare-except
            logger.error(
                'Failed to parse track data: %s, failing data: %s',
                repr(error),
                data
            )
            # TODO: Fix this.
            # print('Failed to create track from data.')
            # print('Failing payload was:')
            # print(data)
            # raise Exception(
            #     'Failed to create track from data. Original error: {}. Payload: {}'.format(
            #         str(error),
            #         data
            #     )
            # )
            return None

        raise AssertionError()

    def get_url(self, callback):
        """
        Gets playable stream URL for this track.

        "callback" is called with "(url, error)" args after URL is fetched.

        Keep in mind this URL is valid for a limited time.
        """
        def on_get_url(url, error):
            """
            Called when URL is fetched.
            """
            self.cached_url = url
            callback(url, error, self)

        if gp.is_subscribed:
            track_id = self.store_id
        else:
            track_id = self.library_id
        gp.get_stream_url_async(track_id, callback=on_get_url)

    @synchronized
    def create_station(self):
        """
        Creates a new station from this :class:`.Track`.

        Returns :class:`.Station` instance.
        """
        station_name = u'Station - {}'.format(self.title)
        station_id = gp.mobile_client.create_station(
            name=station_name,
            track_id=self.store_id
        )
        station = Station(station_id, station_name)
        station.load_tracks()
        return station

    create_station_async = asynchronous(create_station)

    def add_to_my_library(self):
        """
        Add a track to my library.
        """
        return gp.add_to_my_library(self)

    add_to_my_library_async = asynchronous(add_to_my_library)

    def remove_from_my_library(self):
        """
        Remove a track from my library.
        """
        return gp.remove_from_my_library(self)

    remove_from_my_library_async = asynchronous(remove_from_my_library)

    def __str__(self):
        return u'<Track "{} - {}" from {}>'.format(
            self.artist,
            self.title,
            self.source
        )

    __repr__ = __str__


class Artist(object):
    """
    Model that represents artist.
    """
    def __init__(self, artist_id, name):
        self._id = artist_id
        self.name = name

    @property
    def id(self):  # pylint: disable=invalid-name
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


class Station(object):
    """
    Model that represents specific station on Google Play Music.
    """
    def __init__(self, station_id, name):
        self.name = name
        self._id = station_id
        self._tracks = []
        self._tracks_loaded = False

    @property
    def id(self):  # pylint: disable=invalid-name
        """
        Station ID.
        """
        return self._id

    def load_tracks(self):
        """
        Fetch tracks related to this station and
        populate it with :class:`Track` instances.
        """
        data = gp.mobile_client.get_station_tracks(self.id, STATION_FETCH_LEN)
        self._tracks = Track.from_data(data, Track.SOURCE_STATION, many=True)
        self._tracks_loaded = True
        return self

    load_tracks_async = asynchronous(load_tracks)

    def get_tracks(self):
        """
        Return a list of tracks in this station.
        """
        assert self._tracks_loaded, 'Must call ".load_tracks()" before ".get_tracks()"'
        return self._tracks

    @classmethod
    def from_data(cls, data, many=False):
        """
        Construct and return one or many :class:`.Station` instances
        from Google Play Music API response.
        """
        if many:
            return [cls.from_data(one) for one in data if one['inLibrary']]

        return Station(
            station_id=data['id'],
            name=data['name']
        )


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
            tracks=Track.from_data(data['song_hits'], Track.SOURCE_SEARCH, many=True),
            artists=Artist.from_data([
                item['artist']
                for item
                in data['artist_hits']
            ], many=True)
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


class Playlist(object):
    """
    Model that represents remotely stored (Google Play Music) playlist.
    """
    def __init__(self, playlist_id, name, tracks):
        self._id = playlist_id
        self.name = name
        self.tracks = tracks

    @property
    def id(self):  # pylint: disable=invalid-name
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
            tracks=Track.from_data(data['tracks'], Track.SOURCE_PLAYLIST, many=True)
        )


class _GP(object):
    """
    Interface to :class:`gmusicapi.Mobileclient`. Implements
    asynchronous API calls, caching and some other perks.

    Singleton.
    """
    # TODO: Switch to urwid signals for more explicitness?
    caches_invalidated = EventHook()

    def __init__(self):
        # self.is_debug = os.getenv('CLAY_DEBUG')
        self.mobile_client = Mobileclient()
        self.mobile_client._make_call = self._make_call_proxy(
            self.mobile_client._make_call
        )
        # if self.is_debug:
        #     self.debug_file = open('/tmp/clay-api-log.json', 'w')
        #     self._last_call_index = 0
        self.cached_tracks = None
        self.cached_playlists = None
        self.cached_stations = None

        self.invalidate_caches()

        self.auth_state_changed = EventHook()

    def _make_call_proxy(self, func):
        """
        Return a function that wraps *fn* and logs args & return values.
        """
        def _make_call(protocol, *args, **kwargs):
            """
            Wrapper function.
            """
            logger.debug('GP::{}(*{}, **{})'.format(
                protocol.__name__,
                args,
                kwargs
            ))
            result = func(protocol, *args, **kwargs)
            # self._last_call_index += 1
            # call_index = self._last_call_index
            # self.debug_file.write(json.dumps([
            #     call_index,
            #     protocol.__name__, args, kwargs,
            #     result
            # ]) + '\n')
            # self.debug_file.flush()
            return result
        return _make_call

    def invalidate_caches(self):
        """
        Clear cached tracks & playlists & stations.
        """
        self.cached_tracks = None
        self.cached_playlists = None
        self.cached_stations = None
        self.caches_invalidated.fire()

    @synchronized
    def login(self, email, password, device_id, **_):
        """
        Log in into Google Play Music.
        """
        self.mobile_client.logout()
        self.invalidate_caches()
        # prev_auth_state = self.is_authenticated
        result = self.mobile_client.login(email, password, device_id)
        # if prev_auth_state != self.is_authenticated:
        self.auth_state_changed.fire(self.is_authenticated)
        return result

    login_async = asynchronous(login)

    @synchronized
    def use_authtoken(self, authtoken, device_id):
        """
        Try to use cached token to log into Google Play Music.
        """
        # pylint: disable=protected-access
        self.mobile_client.session._authtoken = authtoken
        self.mobile_client.session.is_authenticated = True
        self.mobile_client.android_id = device_id
        del self.mobile_client.is_subscribed
        if self.mobile_client.is_subscribed:
            self.auth_state_changed.fire(True)
            return True
        del self.mobile_client.is_subscribed
        self.mobile_client.android_id = None
        self.mobile_client.session.is_authenticated = False
        self.auth_state_changed.fire(False)
        return False

    use_authtoken_async = asynchronous(use_authtoken)

    def get_authtoken(self):
        """
        Return currently active auth token.
        """
        # pylint: disable=protected-access
        return self.mobile_client.session._authtoken

    @synchronized
    def get_all_tracks(self):
        """
        Cache and return all tracks from "My library".

        Each track will have "id" and "storeId" keys.
        """
        if self.cached_tracks:
            return self.cached_tracks
        data = self.mobile_client.get_all_songs()
        self.cached_tracks = Track.from_data(data, Track.SOURCE_LIBRARY, True)
        return self.cached_tracks

    get_all_tracks_async = asynchronous(get_all_tracks)

    def get_stream_url(self, stream_id):
        """
        Returns playable stream URL of track by id.
        """
        return self.mobile_client.get_stream_url(stream_id)

    get_stream_url_async = asynchronous(get_stream_url)

    @synchronized
    def get_all_user_station_contents(self, **_):
        """
              Return list of :class:`.Station` instances.
              """
        if self.cached_stations:
            return self.cached_stations
        self.get_all_tracks()

        self.cached_stations = Station.from_data(
            self.mobile_client.get_all_stations(),
            True
        )
        return self.cached_stations

    get_all_user_station_contents_async = (  # pylint: disable=invalid-name
        asynchronous(get_all_user_station_contents)
    )

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

    get_all_user_playlist_contents_async = (  # pylint: disable=invalid-name
        asynchronous(get_all_user_playlist_contents)
    )

    def get_cached_tracks_map(self):
        """
        Return a dictionary of tracks where keys are strings with track IDs
        and values are :class:`.Track` instances.
        """
        return {track.id: track for track in self.cached_tracks}

    def get_track_by_id(self, any_id):
        """
        Return track by id or store_id.
        """
        for track in self.cached_tracks:
            if any_id in (track.library_id, track.store_id, track.playlist_item_id):
                return track
        return None

    def search(self, query):
        """
        Find tracks and return an instance of :class:`.SearchResults`.
        """
        results = self.mobile_client.search(query)
        return SearchResults.from_data(results)

    search_async = asynchronous(search)

    def add_to_my_library(self, track):
        """
        Add a track to my library.
        """
        result = self.mobile_client.add_store_tracks(track.id)
        if result:
            self.invalidate_caches()
        return result

    def remove_from_my_library(self, track):
        """
        Remove a track from my library.
        """
        result = self.mobile_client.delete_songs(track.id)
        if result:
            self.invalidate_caches()
        return result

    @property
    def is_authenticated(self):
        """
        Return True if user is authenticated on Google Play Music, false otherwise.
        """
        return self.mobile_client.is_authenticated()

    @property
    def is_subscribed(self):
        """
        Return True if user is subscribed on Google Play Music, false otherwise.
        """
        return self.mobile_client.is_subscribed


gp = _GP()  # pylint: disable=invalid-name
