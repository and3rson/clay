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
from hashlib import sha1
from uuid import UUID

from clay.core.settings import settings_manager
from clay.core.log import logger
from . import station, client
from .utils import synchronized, asynchronous, Source


class Track(object):
    """
    Model that represents single track from Google Play Music.
    """
    def __init__(self, source, data):
        # In playlist items and user uploaded songs the storeIds are missing so
        self.id_ = data.get('id')
        self.nid = data.get('nid')  # I am  not sure what this is for.
        self.store_id = data.get('storeId')

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
        self.artist = data['artist']
        self.genre = data.get('genre', '')
        self.play_count = data.get('playCount')

        # User uploaded songs miss a store_id
        self.album_name = data.get('album', '')
        self.album_id = data.get('albumId', '')
        self.album_url = (data['albumArtRef'][0]['url'] if 'albumArtRef' in data else "")
        self.track_number = data['trackNumber']

        if source == Source.library:
            name = (data['albumArtist'] if data['albumArtist'] != '' else self.artist)

            if 'artistId' in data and data['artistId'] != "":
                self.album_artist = client.gp.add_artist(data['artistId'][0], name)
            else:
                self.album_artist = client.gp.add_artist(None, name)

            album = client.gp.add_album_song(self.album_name, self.album_name, self)
            self.album_artist.add_album(album)

        self.duration = int(data['durationMillis'])
        self.rating = int(data.get('rating', 0))
        self.queue_id = None
        self.source = source
        self.cached_url = None
        self.artist_art_url = ''
        self.artist_art_filename = None

        if artist_art_ref is not None:
            self.artist_art_url = artist_art_ref['url']
            self.artist_art_filename = sha1(
                self.artist_art_url.encode('utf-8')
            ).hexdigest() + u'.jpg'
        self.explicit_rating = int(data.get('explicitType', 0))

        # Songs that are uploaded are not send in the promoted_songs
        # call so we need to manually add them.
        if self.store_id is None and 'lastRatingChangeTimestamp' in data:
            client.gp.liked_songs.add_liked_song(self)

        self.original_data = data

    @property
    def id(self):  # pylint: disable=invalid-name
        """
        Return ID for this track.
        """
        if self.source == Source.library:
            id_ = self.id_
        elif self.store_id is None:
            id_ = self.nid
        else:
            id_ = self.store_id

        return id_

    @property
    def filename(self):
        """
        Return a filename for this track.
        """
        return self.id + '.mp3'

    def __eq__(self, other):
        return self.id == other.id and self.queue_id == other.queue_id

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

    def increment_playcount(self, callback=None):
        """
        Increments the gmusic playcount of the track by one.

        Arguments:
           callback: The callback to run after playcount is incremented (optional)

        Returns:
           Nothing
        """
        client.gp.increment_song_playcount_async(self.id, callback=callback)

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
            url = url.replace('https', 'http')
            logger.debug(url)
            self.cached_url = url
            callback(url, error, self)

        client.gp.get_stream_url_async(self.id, callback=on_get_url)

    @synchronized
    def get_artist_art_filename(self):
        """
        Return artist art filename, None if this track doesn't have any.
        Downloads if necessary.
        """
        if self.artist_art_url == '':
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
        station_ = station.Station(station_id, station_name)
        station_.load_tracks()
        return station_

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
        client.gp.mobile_client.rate_songs(self.original_data, rating)
        client.gp.refresh_liked_songs()

    def __repr__(self):
        return u'<Track "{} - {}" from {}>'.format(
            self.artist,
            self.title,
            self.source
        )
