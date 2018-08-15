"""
Components for " stations" page.
"""
import urwid

from .page import AbstractPage
from clay.core import gp
from clay.ui.urwid import SongListBox, notification_area, hotkey_manager

class StationListItem(urwid.Columns):
    """
    One station in the list of stations.
    """
    signals = ['activate']

    def __init__(self, station):
        self.station = station
        self.text = urwid.SelectableIcon(u' \u2708 {} '.format(
            self.station.name
        ), cursor_position=3)
        self.text.set_layout('left', 'clip', None)
        self.content = urwid.AttrWrap(
            self.text,
            'default',
            'selected'
        )
        super(StationListItem, self).__init__([self.content])

    def keypress(self, size, key):
        """
        Handle keypress.
        """
        return hotkey_manager.keypress("station_page", self, super(StationListItem, self),
                                       size, key)

    def start_station(self):
        """
        Start playing the selected station
        """
        urwid.emit_signal(self, 'activate', self)


class StationListBox(urwid.ListBox):
    """
    List of stations.
    """
    signals = ['activate']

    def __init__(self, app):
        self.app = app

        self.walker = urwid.SimpleListWalker([
            urwid.Text('Not ready')
        ])
        self.notification = None

        gp.auth_state_changed += self.auth_state_changed

        super(StationListBox, self).__init__(self.walker)

    def auth_state_changed(self, is_auth):
        """
        Called when auth state changes (e. g. user is logged in).
        Requests fetching of station.
        """
        if is_auth:
            self.walker[:] = [
                urwid.Text(u'\n \uf01e Loading stations...', align='center')
            ]

            gp.get_all_user_station_contents_async(callback=self.on_get_stations)

    def on_get_stations(self, stations, error):
        """
        Called when a list of stations fetch completes.
        Populates list of stations.
        """
        if error:
            notification_area.notify('Failed to get stations: {}'.format(str(error)))

        items = []
        for station in stations:
            stationlistitem = StationListItem(station)
            urwid.connect_signal(
                stationlistitem, 'activate', self.item_activated
            )
            items.append(stationlistitem)

        self.walker[:] = items

        self.app.redraw()

    def item_activated(self, stationlistitem):
        """
        Called when a specific station  is selected.
        Re-emits this event.
        """
        urwid.emit_signal(self, 'activate', stationlistitem)


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
        return 3

    @property
    def slug(self):
        """
        Return page ID (str).
        """
        return "stations"

    def __init__(self, app):
        self.app = app

        self.stationlist = StationListBox(app)
        self.songlist = SongListBox(app)
        self.songlist.set_placeholder('\n Select a station.')

        urwid.connect_signal(
            self.stationlist, 'activate', self.stationlistitem_activated
        )

        super(StationsPage, self).__init__([
            self.stationlist,
            self.songlist
        ])

    def stationlistitem_activated(self, stationlistitem):
        """
        Called when specific station  is selected.
        Requests fetching of station tracks
        """
        self.songlist.set_placeholder(u'\n \uf01e Loading station tracks...')
        stationlistitem.station.load_tracks_async(callback=self.on_station_loaded)

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
