# This file is part of Clay.
# Copyright (C) 2018, Andrew Dunbai & Clay Contributors
#
# Clay is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Clay is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Clay. If not, see <https://www.gnu.org/licenses/>.
"""
This file contains the classes and methods for dealing with Google Play Playlists
"""
from __future__ import print_function
from gmusicapi.clients import Mobileclient
from clay.core import EventHook
from clay.core.log import logger

from .artist import Artist
from .track import Track
from .playlist import Playlist, LikedSongs
from .station import Station, IFLStation
from .search import SearchResults
from .utils import synchronized, asynchronous, Source


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
        self.cached_artists = {}
        self.cached_albums = {}
        self.liked_songs = LikedSongs()

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
        self.cached_artist = None
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
    def get_artist_info(self, artist_id):
        """
        Get the artist info
        """
        return self.mobile_client.get_artist_info(artist_id, max_rel_artist=0, max_top_tracks=15)

    @synchronized
    def get_album_tracks(self, album_id):
        """
        Get album tracks
        """
        return self.mobile_client.get_album_info(album_id, include_tracks=True)['tracks']

    @synchronized
    def add_artist(self, artist_id, name):
        """
        Creates or lookup an artist object and return it.

        Args:
           artist_id (`str`): The Artist id given by Google Play Music

        Returns:
           The artist class
        """
        lname = name.lower()
        if lname not in self.cached_artists:
            self.cached_artists[lname] = Artist(artist_id, name)

        return self.cached_artists[lname]

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
        self.cached_tracks = Track.from_data(data, Source.library, True)

        return self.cached_tracks

    get_all_tracks_async = asynchronous(get_all_tracks)

    def get_stream_url(self, stream_id):
        """
        Returns playable stream URL of track by id.
        """
        return self.mobile_client.get_stream_url(stream_id)

    get_stream_url_async = asynchronous(get_stream_url)

    def increment_song_playcount(self, track_id):
        """
        increments the playcount of a song with a given `track_id` by one

        Args:
           track_id (`int`): The track id of the song to increment the playcount

        Returns:
           Nothing
        """
        gp.mobile_client.increment_song_playcount(track_id)

    increment_song_playcount_async = asynchronous(increment_song_playcount)

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
        self.cached_stations.insert(0, IFLStation())
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
        self.refresh_liked_songs()
        self.cached_playlists.insert(0, self.liked_songs)
        return self.cached_playlists

    get_all_user_playlist_contents_async = (  # pylint: disable=invalid-name
        asynchronous(get_all_user_playlist_contents)
    )

    def refresh_liked_songs(self, **_):
        """
        Refresh the liked songs playlist
        """
        self.liked_songs.refresh_tracks(self.mobile_client.get_promoted_songs())

    refresh_liked_songs_async = asynchronous(refresh_liked_songs)

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
            if any_id in (track.id_, track.nid, track.store_id):
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

gp = _GP()
