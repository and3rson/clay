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
    notrack = '/org/mpris/MediaPlayer2/TrackList/NoTrack'

    def __init__(self):
        self._stopped = False

    @staticmethod
    def get_metadata(track):
        """
        Returns the metadata for a specific track
        """
        if not track:
            return {'mpris:trackid': Variant('s', MPRIS2.notrack),
                    'mpris:artUrl': Variant('s', "file://"),
                    'mpris:title': Variant('s', 'None'),
                    'mpris:artist': Variant('s', 'None'),
                    'mpris:album': Variant('s', 'None'),
                    'mpris:url': Variant('s', 'https://')}
        else:
            return {'mpris:trackid': Variant('s', track.queue_id),
                    'mpris:artUrl': Variant('s', track.artist_art_url),
                    'xesam:title': Variant('s', track.title),
                    'xesam:artist': Variant('s', track.artist),
                    'xesam:album': Variant('s', track.album_name),
                    'xesam:url': Variant('s', track.cached_url if track.cached_url else 'https://')}

    # The following is an implementation of the MediaPlayer2 interface
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

    ####################################################################
    # The following is an implementation of the MPRIS2 Player Protocol #
    ####################################################################

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

        return self.get_metadata(track)

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
        # TODO fix
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
        return player.time

    # The following are custom additions to the protocol for features that clay supports
    def Mute(self):
        """
        Mutes or unmutes the volume.
        """
        player.mute()

    ######################################################
    # An implementation of the MPRIS2 tracklist protocol #
    ######################################################

    def GetTracksMetadata(self, track_ids):
        """
        Gets all the metadata avaliable for a set of tracks.
        """
        queue = player.get_queue_tracks()

        if queue == [] or track_ids == []:
            return [{}]

        return [self.get_metadata(track_ids) for track in queue
                if track.queue_id in track_ids]

    def AddTrack(uri, after_track, set_as_current):
        """!!Warning!!

        This method doesn't do anything since it doesn't make any
        sense in the context of Clay.
        """
        pass

    def RemoveTrack(self, track_id):
        """
        Removes track from the current queue
        """
        if track_id == self.notrack:
            return

        track_id = track_id[16:]
        tracks = player.get_queue_tracks()

        for track in tracks:
            if track_id == track.queue_id:
                player.remove_from_queue(track)
                return

    def GoTo(self, track_id):
        """
        Skip to the specified track to skip to.

        If the track is not in the queue it does nothing.
        """
        if track_id == self.notrack:
            return

        track_id = track_id[16:]
        tracks = player.get_queue_tracks()

        for index, track in enumerate(tracks):
            if track_id == track.queue_id:
                player.load_queue(tracks, index)

    TrackListReplaced = signal()
    TrackAdded = signal()
    TrackRemoved = signal()
    TrackMetadataChanged = signal()

    @property
    def Tracks(self):
        """
        A property which returns only the queue ids
        """
        tracks = player.get_queue_tracks()

        if tracks == []:
            return [self.notrack]
        else:
            return [track.queue_id for track in tracks]

    def CanEditTracks(self):
        """
        If this is false, calling AddTrack or RemoveTrack will have no effect.
        """
        return True

    ##################################################################################
    # Extensions to the MPRIS2 protocol for extra features or idiosyncronies of Clay. #
    ##################################################################################

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


def load_xml(name):
    return pkg_resources.resource_string(__name__, "mpris/org.mpris.MediaPlayer2" + name + ".xml")\
        .decode("utf-8")


bus = SessionBus()
MPRIS2.dbus = [load_xml(file_) for file_ in ["", ".Player", ".TrackList", ".Playlists"]]
mpris2_manager = MPRIS2()

try:
    bus.publish("org.mpris.MediaPlayer2.clay", mpris2_manager,
                ('/org/mpris/MediaPlayer2', mpris2_manager),
                ('/org/mpris/MediaPlayer2/Player', mpris2_manager),
                ('/org/mpris/MediaPlayer2/TrackList', mpris2_manager))
             #   ('Clay', clay))

except RuntimeError as e:
    print(e)
    print("An another instance of Clay is already running so we can't start MPRIS2")
