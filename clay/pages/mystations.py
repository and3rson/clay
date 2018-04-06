"""
Components for "My stations" page.
"""
import urwid

from clay.gp import gp
from clay.songlist import SongListBox
from clay.notifications import notification_area
from clay.pages.page import AbstractPage
from clay.hotkeys import hotkey_manager


class MyStationListItem(urwid.Columns):
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
        super(MyStationListItem, self).__init__([self.content])

    def keypress(self, size, key):
        """
        Handle keypress.
        """
        return hotkey_manager.keypress("station_page", self, super(MyStationListItem, self),
                                       size, key)

    def start_station(self):
        """
        Start playing the selected station
        """
        urwid.emit_signal(self, 'activate', self)
        return None


class MyStationListBox(urwid.ListBox):
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

        super(MyStationListBox, self).__init__(self.walker)

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
            mystationlistitem = MyStationListItem(station)
            urwid.connect_signal(
                mystationlistitem, 'activate', self.item_activated
            )
            items.append(mystationlistitem)

        self.walker[:] = items

        self.app.redraw()

    def item_activated(self, mystationlistitem):
        """
        Called when a specific station  is selected.
        Re-emits this event.
        """
        urwid.emit_signal(self, 'activate', mystationlistitem)


class MyStationsPage(urwid.Columns, AbstractPage):
    """
    Stations page.

    Contains two parts:

    - List of stations (:class:`.MyStationBox`)
    - List of songs in selected station (:class:`clay:songlist:SongListBox`)
    """
    @property
    def name(self):
        return 'Stations'

    @property
    def key(self):
        return 3

    def __init__(self, app):
        self.app = app

        self.stationlist = MyStationListBox(app)
        self.songlist = SongListBox(app)
        self.songlist.set_placeholder('\n Select a station.')

        urwid.connect_signal(
            self.stationlist, 'activate', self.mystationlistitem_activated
        )

        super(MyStationsPage, self).__init__([
            self.stationlist,
            self.songlist
        ])

    def mystationlistitem_activated(self, mystationlistitem):
        """
        Called when specific station  is selected.
        Requests fetching of station tracks
        """
        self.songlist.set_placeholder(u'\n \uf01e Loading station tracks...')
        mystationlistitem.station.load_tracks_async(callback=self.on_station_loaded)

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
