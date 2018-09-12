"""
This module defines and starts a MPRIS2 dbus interface
"""
import sys
import pkg_resources

from pydbus import SessionBus, Variant
from pydbus.generic import signal
from clay.core import meta
from clay.playback.player import get_player


player = get_player()  # pylint: disable=invalid-name


# pylint: disable=invalid-name,missing-docstring
class MPRIS2:
    """
    An object that defines and implements the MPRIS2 protocol for Clay
    """
    def __init__(self):
        self._stopped = False

    # MediaPlayer2 interface
    def Raise(self):
        pass

    # TODO: Cleanup after ourselves
    def Quit(self):
        sys.exit(0)

    @property
    def CanQuit(self):
        return True

    @property
    def Fullscreen(self):
        pass

    @Fullscreen.setter
    def Fullscreen(self, _):
        # We aren't graphical so we just ignore this call
        pass

    @property
    def CanSetFullscreen(self):
        return False

    @property
    def CanRaise(self):
        return False

    @property
    def HasTrackList(self):
        return True

    @property
    def Identity(self):
        return "Clay Player"

    @property
    def DesktopEntry(self):
        return "clay"

    @property
    def SupportedMimeTypes(self):
        return []

    @property
    def SupportedUriSchemes(self):
        return []

    # MediaPlayer2 Player interface
    def Next(self):
        """
        Goes to the next song in the queue.
        """
        player.next()

    def Previous(self):
        """
        Goes to previous in the queue
        """
        player.prev()

    def Pause(self):
        """
        Pauses the backback
        """
        if player.playing:
            player.play_pause()

    def PlayPause(self):
        """
        Toggles playback, i.e. play if pause or pause if playing
        """
        player.play_pause()

    def Stop(self):
        """
        Stops playback and returns to the beginning of the song.
        """
        self._stopped = True
        self.Pause()
        player.seek(-1)

    def Play(self):
        """
        Starts or resumes playback.
        """
        if self._stopped:
            self._stopped = False

        if not player.playing:
            player.play_pause()

    def Seek(self, offset):
        """
        Seeks forward in the current track by the specified number of microseconds.
        A negative value seeks backwards in the track until the value is current - offset
        Or if that value would be lower to zero, zero.

        Args:
           offset: the number of microseconds to seek forwards.
        """
        player.time = player.time + offset

    def SetPosition(self, track_id, position):
        """
        Sets the current position in microseconds.
        """
        pass

    Seeked = signal()

    # pylint: disable=no-else-return
    @property
    def PlaybackStatus(self):
        """
        Returns the current status of clay.
        """
        if self._stopped or player.queue.get_tracks() == []:
            return "Stopped"
        elif player.playing:
            return "Playing"
        else:
            return "Paused"

    @property
    def LoopStatus(self):
        """
        Returns:
           Whether the song is not, single or playlist looping
        """
        if player.repeat_one:
            return "Track"
        else:
            return "None"

    # TODO: We don't allow someone to control playback atm so this doesn't do anything
    @property
    def MinimumRate(self):
        return -1.0

    @property
    def MaximumRate(self):
        return 1.0

    @property
    def Rate(self):
        """
        Returns the playback rate of the current song.
        """
        return 0.0

    @property
    def Metadata(self):
        try:
            track = player.get_current_track()
        except AttributeError:
            track = None

        if track is None:
            return {}

        return {
            'mpris:trackid': Variant('o', '/org/clay/' + str(track.store_id)),
            'mpris:artUrl': Variant('s', track.artist_art_url),
            'xesam:title': Variant('s', track.title),
            'xesam:artist': Variant('s', track.artist.name),
            'xesam:album': Variant('s', track.album_name),
            'xesam:url': Variant('s', track.cached_url),
        }

    @property
    def CanPause(self):
        return player.get_current_track() is not None

    @property
    def CanPlay(self):
        return player.get_current_track() is not None

    @property
    def CanGoNext(self):
        return len(player.queue.get_tracks()) > 1

    @property
    def CanGoPrevious(self):
        #TODO fix
        return len(player.queue.get_tracks()) > 1

    @property
    def CanSeek(self):
        return player.get_current_track() is not None

    @property
    def CanControl(self):
        return True

    @property
    def Shuffle(self):
        return player.random

    @property
    def Volume(self):
        return player.volume / 100

    @Volume.setter
    def Volume(self, volume):
        # Don't blast someone's ears off because they entered the wrong thing.
        # Just enter it raw into volume since that is probably what they meant to do.
        if volume > 1.0:
            player.volume = int(volume)
        else:
            player.volume = int(volume * 100)

    @property
    def Position(self):
        # TODO: Some weird microseconds/seconds stuff. `playerctl progress` shows weird values
        # for both VLC & MPV.
        return player.play_progress

    # The following are custom additions to the protocol for features that clay supports
    def Mute(self):
        """
        Mutes or unmutes the volume.
        """
        player.mute()

    @property
    def Rating(self):
        """
        Returns:
           The rating of the current song.
        """
        try:
            return player.get_current_track().rating
        except AttributeError:
            return 0

    @Rating.setter
    def Rating(self, rating):
        """
        Takes a rating and sets the current song to that rating.

        1-2 thumbs down
        4-5 thumbs up
        0 None
        """
        try:
            player.get_current_track().rate_song(rating)
        except AttributeError:
            pass

    @property
    def Explicit(self):
        track = player.get_current_track()
        if track is None:
            return False
        else:
            return track.explicit_rating != 0

bus = SessionBus()
MPRIS2.dbus = [pkg_resources.resource_string(__name__, "mpris/org.mpris.MediaPlayer2" +name+ ".xml")
               .decode("utf-8")
               for name in ("", ".Player", ".Playlists", ".TrackList")]
mpris2_manager = MPRIS2()

try:

    bus.publish("org.mpris.MediaPlayer2.clay", mpris2_manager,
                ('/org/mpris/MediaPlayer2', mpris2_manager))
except RuntimeError as e:
    print(e)
    print("An another instance of Clay is already running so we can't start MPRIS2")
