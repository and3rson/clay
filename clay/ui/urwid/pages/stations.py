"""
Components for " stations" page.
"""
import urwid

from .page import AbstractPage, AbstractListBox
from clay.core import gp
from clay.ui.urwid import SongListBox, notification_area


class StationListBox(AbstractListBox):
    """
    List of stations.
    """
    def __init__(self, app, icon):
        super(StationListBox, self).__init__(app, icon)

    def auth_state_changed(self, is_auth):
        """
        Called when auth state changes (e. g. user is logged in).
        Requests fetching of station.
        """
        if is_auth:
            self.walker[:] = [
                urwid.Text(u'\n \uf01e Loading stations...', align='center')
            ]

            gp.get_all_user_station_contents_async(callback=self.populate)


class StationsPage(urwid.Columns, AbstractPage):
    """
    Stations page.

    Contains two parts:

    - List of stations (:class:`.StationBox`)
    - List of songs in selected station (:class:`clay:songlist:SongListBox`)
    """
    @property
    def name(self):
        return 'Stations'

    @property
    def key(self):
        return 4

    @property
    def slug(self):
        """
        Return page ID (str).
        """
        return "stations"

    def __init__(self, app):
        self.app = app

        self.stationlist = StationListBox(app, '\u2708')
        self.songlist = SongListBox(app)
        self.songlist.set_placeholder('\n Select a station.')

        urwid.connect_signal(
            self.stationlist, 'activate', self.station_activated
        )

        super(StationsPage, self).__init__([
            self.stationlist,
            self.songlist
        ])

    def station_activated(self, station):
        """
        Called when specific station  is selected.
        Requests fetching of station tracks
        """
        self.songlist.set_placeholder(u'\n \uf01e Loading station tracks...')
        station.load_tracks_async(callback=self.on_station_loaded)

    def on_station_loaded(self, station, error):
        """
        Called when station  tracks  fetch completes.
        Populates songlist with tracks from the selected station.
        """
        if error:
            notification_area.notify('Failed to get station tracks: {}'.format(str(error)))

        self.songlist.populate(
            station.get_tracks()
        )
        self.app.redraw()

    def activate(self):
        pass
