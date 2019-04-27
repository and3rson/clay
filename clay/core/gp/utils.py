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
This file contains classes and functions generally useful for Google Play Music
"""
from enum import Enum
from threading import Thread, Lock


class Type(Enum):
    """
    Type of a specific track.
    Can either be uploaded by a user or from the Google Music Store.
    """
    uploaded = 'uploaded'
    store = 'store'

class Source(Enum):
    """
    The source of the track list
    Either the library, a station, playlist or search.
    """
    library = 'library'
    station = 'station'
    playlist = 'playlist'
    search = 'search'
    album = 'album'


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

        if callback is None:
            callback = lambda *_, **__: None

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
        lock.acquire()

        try:
            return func(*args, **kwargs)
        finally:
            lock.release()

    return wrapper
