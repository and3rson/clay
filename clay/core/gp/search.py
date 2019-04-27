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
This file contains the classes and methods for dealing with Google Play Searches
"""
from .utils import Source
from .artist import Artist
from .track import Track

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
            tracks=Track.from_data(data['song_hits'], Source.search, many=True),
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
