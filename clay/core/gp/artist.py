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

class Artist(object):
    """
    Model that represents an artist.
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
