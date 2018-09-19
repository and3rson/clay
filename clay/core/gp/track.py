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
This file contains the classes and functions for gmusic track
"""
try:
    from PIL import Image
except ImportError:
    Image = None

from urllib.request import urlopen
from io import BytesIO
from uuid import UUID
from hashlib import sha1

from clay.core.settings import settings_manager
from clay.core.log import logger
from . import station, client
from .utils import synchronized, asynchronous, Type, Source


class Track(object):
    """
    Model that represents single track from Google Play Music.
    """
    def __init__(self, source, data):
        # In playlist items and user uploaded songs the storeIds are missing so
        self.store_id = (data['storeId'] if 'storeId' in data else data.get('id'))
        self.playlist_item_id = (UUID(data['id']) if source == Source.playlist else None)
        self.library_id = (UUID(data['id']) if source == Source.library else None)

        # To filter out the playlist items we need to reassign the store_id when fetching the track
        if 'track' in data:
            data = data['track']
            self.store_id = data['storeId']

        artist_art_ref = next(iter(sorted(
            [
                ref
                for ref
                in data.get('artistArtRef', [])
            ],
            key=lambda x: x['aspectRatio']
        )), None)
        self.title = data['title']
        if 'artistId' in data:
            self.artist = client.gp.add_artist(data['artistId'][0], data['artist'])
        else:
            self.artist = data['artist']
            # TODO: How to deal with uploaded music
            # client.gp.add_artist(UUID().hex, data['artist'])

        #self.artist = client.gp.add_artist(data['artistId'][0])
        self.duration = int(data['durationMillis'])
        self.rating = (int(data['rating']) if 'rating' in data else 0)
        self.source = source
        self.cached_url = None
        self.artist_art_url = None
        self.artist_art_filename = None
        if artist_art_ref is not None:
            self.artist_art_url = artist_art_ref['url']
            self.artist_art_filename = sha1(
                self.artist_art_url.encode('utf-8')
            ).hexdigest() + u'.jpg'
        self.explicit_rating = (int(data['explicitType'] if 'explicitType' in data else 0))

        if self.rating == 5:
            client.gp.cached_liked_songs.add_liked_song(self)

        # User uploaded songs miss a store_id
        self.album_name = data['album']
        self.album_url = (data['albumArtRef'][0]['url'] if 'albumArtRef' in data else "")

        self.original_data = data


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
    def from_data(cls, data, source, many=False):
        """
        Construct and return one or many :class:`.Track` instances
        from Google Play Music API response.
        """
        if many:
            return [track for track in
                    [cls.from_data(one, source) for one in data]
                    if track is not None]
        try:
            if source == Source.playlist and 'track' not in data:
                track = client.gp.get_track_by_id(UUID(data['trackId']))
            else:
                track = Track(source, data)

            return track
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

        if client.gp.is_subscribed:
            track_id = self.store_id
        else:
            track_id = str(self.library_id)
        client.gp.get_stream_url_async(track_id, callback=on_get_url)

    @synchronized
    def get_artist_art_filename(self):
        """
        Return artist art filename, None if this track doesn't have any.
        Downloads if necessary.
        """
        if self.artist_art_url is None:
            return None

        if not settings_manager.get_is_file_cached(self.artist_art_filename):
            response = urlopen(self.artist_art_url)
            data = response.read()
            if Image:
                image = Image.open(BytesIO(data))
                image.thumbnail((128, 128))
                out = BytesIO()
                image = image.convert('RGB')
                image.save(out, format='JPEG')
                data = out.getvalue()
            settings_manager.save_file_to_cache(self.artist_art_filename, data)

        return settings_manager.get_cached_file_path(self.artist_art_filename)

    # get_artist_arg_filename_async = asynchronous(get_artist_art_filename)

    @synchronized
    def create_station(self):
        """
        Creates a new station from this :class:`.Track`.

        Returns :class:`.Station` instance.
        """
        station_name = u'Station - {}'.format(self.title)
        station_id = client.gp.mobile_client.create_station(
            name=station_name,
            track_id=self.store_id
        )
        station = station.Station(station_id, station_name)
        station.load_tracks()
        return station

    create_station_async = asynchronous(create_station)

    def add_to_my_library(self):
        """
        Add a track to my library.
        """
        return client.gp.add_to_my_library(self)

    add_to_my_library_async = asynchronous(add_to_my_library)

    def remove_from_my_library(self):
        """
        Remove a track from my library.
        """
        return client.gp.remove_from_my_library(self)

    remove_from_my_library_async = asynchronous(remove_from_my_library)

    def rate_song(self, rating):
        """
        Rate the song either 0 (no thumb), 1 (down thumb) or 5 (up thumb).
        gp.mobile_client.rate_songs(self.original_data, rating)
        """
        self.original_data['rating'] = rating
        self.rating = rating

        if rating == 5:
            client.gp.cached_liked_songs.add_liked_song(self)

    def __repr__(self):
        return u'<Track "{} - {}" from {}>'.format(
            self.artist,
            self.title,
            self.source
        )
