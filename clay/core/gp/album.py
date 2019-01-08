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
A file containing the classes and methods for Google Music Albums
"""
from . import client
from .track import Track
from .utils import Source


class Album(object):
    """
    A model that represents Google Play Music albums
    """
    def __init__(self, artist, data):
        self._id = data['albumId']
        self._original_data = data
        self._tracks = None
        self.icon = '\U0001F3B6'
        self.album_url = data.get('albumArtRef', "")
        self.artist = artist
        self.explicit_rating = int(data.get('explictType', 0))
        self.name = data['name']
        self.year = int(data.get('year', 1970))
        self.sorted = False

    def __str__(self):
        return self.name

    def __lt__(self, other):
        return self.name < other.name

    def add_track(self, track):
        """
        Adds an track to the album
        """
        if self._tracks is None:
            self._tracks = []

        self._tracks.append(track)

    @property
    def tracks(self):
        """
        Get the (cached) tracks of this album

        Returns:
          Returns the tracks associated with this album
        """
        if self._tracks is None:
            self._tracks = Track.from_data(client.gp.get_album_tracks(self._id),
                                           Source.album,
                                           many=True)
        if not self.sorted:
            self._tracks.sort(key=lambda track: track.track_number)
            self.sorted = True

        return self._tracks


class AllSongs(Album):
    """
    A model representing all songs by an artist
    """
    def __init__(self, artist, albums):
        self._id = 'ALL'
        self._albums = albums
        self.artist = artist
        self.icon = '\u224C'
        self.year = 2018   # TODO
        self.album_url = None  # TODO
        self.name = "All Songs"
        self._tracks = None
        self.refresh = False
        self.sorted = True

    @property
    def tracks(self):
        # Could this be done faster?
        if self._tracks is None or self.refresh:
            tracks = []
            for album in self._albums:
                tracks += album.tracks
            self._tracks = tracks
            self.refresh = False
        return self._tracks


class TopSongs(Album):
    """
    An artists top rated songs
    """
    def __init__(self, artist, tracks):
        self._id = 'TOP'
        self._tracks = tracks
        self.artist = artist
        self.icon = '\u2605'
        self.year = 2018  # TODO
        self.album_url = None  # TODO
        self.name = "Top Songs"
        self.sorted = True
