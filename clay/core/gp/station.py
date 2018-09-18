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
Contains the classes and functions for Google Music stations
"""
from . import track, client
from .utils import asynchronous, Source

class Station(object):
    """
    Model that represents specific station on Google Play Music.
    """
    FETCH_LENGTH = 50

    def __init__(self, station_id, name):
        self.name = name
        self._id = station_id
        self._tracks = []
        self._tracks_loaded = False

    def __str__(self):
        return self.name

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
        data = client.gp.mobile_client.get_station_tracks(self.id, self.FETCH_LENGTH)
        self._tracks = track.Track.from_data(data, Source.station, many=True)
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

class IFLStation(Station):
    """
    I'm feeling lucky station
    """
    def __init__(self):
        Station.__init__(self, 'IFL', "I'm Feeling Lucky")
