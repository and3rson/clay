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
A file containing the classes and methods for Google Music Artists
"""
from . import client
from .track import Track
from .album import Album, AllSongs, TopSongs
from .utils import Source

class Artist(object):
    """
    Model that represents an artist.
    """
    def __init__(self, artist_id, name):
        self._id = artist_id
        self._original_data = None
        self._albums = None
        self.name = name

    def __str__(self):
        return self.name

    def __lt__(self, other):
        return self.name < other.name

    @property
    def albums(self):
        """
        Return the albums by an artist
        """
        if self._original_data is None:
            self._original_data = client.gp.get_artist_info(self._id)
            albums = [Album(self, album) for album in self._original_data['albums']]
            albums.sort()
            albums.insert(0, TopSongs(self, Track.from_data(self._original_data['topTracks'],
                                                            Source.album, many=True)))
            albums.insert(1, AllSongs(self, albums.copy()))
            self._albums = albums

        return self._albums  #: Warning: passes by reference for efficiency

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
