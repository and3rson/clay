import urwid
import sys

from clay.core import gp, settings_manager
from clay.playback.player import get_player

from .clipboard import copy
from .hotkeys import hotkey_manager
from .notifications import notification_area
from .playbar import PlayBar
from .songlist import SongListBox
from .pages import *


player = get_player()  # pylint: disable=invalid-name


class AppWidget(urwid.Frame):
    """
    Root widget.

    Handles tab switches, global keypresses etc.
    """
    class Tab(urwid.Text):
        """
        Represents a single tab in header tabbar.
        """
        def __init__(self, page):
            self.page = page
            super(AppWidget.Tab, self).__init__(
                self.get_title()
            )
            self.set_active(False)

        def set_active(self, active):
            """
            Mark tab visually as active.
            """
            self.set_text(
                [
                    ('panel_divider_focus' if active else 'panel_divider', u'\u23b8 '),
                    ('panel_focus' if active else 'panel', self.get_title() + '  ')
                ]
            )

        def get_title(self):
            """
            Render tab title.
            """
            return '{} {}'.format(
                self.page.key,
                self.page.name
            )

    def __init__(self):
        self.pages = [
            DebugPage(self),
            LibraryPage(self),
            ArtistsPage(self),
            AlbumsPage(self),
            StationsPage(self),
            PlaylistsPage(self),
            SearchPage(self),
            QueuePage(self),
            SettingsPage(self)
        ]
        self.tabs = [AppWidget.Tab(page) for page in self.pages]
        self.current_page = None
        self.loop = None

        notification_area.set_app(self)
        self._login_notification = None

        self._cancel_actions = []

        self.header = urwid.Pile([
            urwid.AttrWrap(urwid.Columns([
                ('pack', tab)
                for tab
                in self.tabs
            ], dividechars=0), 'panel'),
            notification_area
        ])
        self.playbar = PlayBar(self)
        super(AppWidget, self).__init__(
            header=self.header,
            footer=self.playbar,
            body=urwid.Filler(urwid.Text('Loading...', align='center'))
        )

        self.set_page('library')
        self.log_in()

    def log_in(self, use_token=True):
        """
        Called when this page is shown.

        Request user authorization.
        """
        authtoken, device_id, username, password = [
            settings_manager.get(key, "play_settings")
            for key
            in ('authtoken', 'device_id', 'username', 'password')
        ]

        if self._login_notification:
            self._login_notification.close()
        if use_token and authtoken:
            self._login_notification = notification_area.notify('Using cached auth token...')
            gp.use_authtoken_async(
                authtoken,
                device_id,
                callback=self.on_check_authtoken
            )
        elif username and password and device_id:
            self._login_notification = notification_area.notify('Logging in...')
            gp.login_async(
                username,
                password,
                device_id,
                callback=self.on_login
            )
        else:
            self._login_notification = notification_area.notify(
                'Please set your credentials on the settings page.'
            )

    def on_check_authtoken(self, success, error):
        """
        Called once cached auth token is validated.
        If *error* is ``None`` and *success* is ``True``, switch app to "My library" page.
        Otherwise attemt to log in via credentials.
        """
        if error:
            self._login_notification.update(
                'Failed to use cached auth token: {}'.format(str(error))
            )
            self.log_in(False)
        elif not success:
            self._login_notification.update(
                'Failed to use cached auth token, proceeding to normal auth.'
            )
            self.log_in(False)
        else:
            self._login_notification.close()

    def on_login(self, success, error):
        """
        Called once user authorization finishes.
        If *error* is ``None`` and *success* is ``True``, switch app to "My library" page.
        """
        if error:
            self._login_notification.update('Failed to log in: {}'.format(str(error)))
            return

        if not success:
            self._login_notification.update(
                'Google Play Music login failed (API returned false)'
            )
            return

        with settings_manager.edit() as config:
            config['play_settings']['authtoken'] = gp.get_authtoken()

        self._login_notification.close()

    def set_loop(self, loop):
        """
        Assign a MainLoop to this app.
        """
        self.loop = loop

    def set_page(self, slug):
        """
        Switch to a different tab.
        """
        try:
            self.current_page.songlist.end_filtering()
        except AttributeError as e:
            pass

        page = [page for page in self.pages if page.slug == slug][0]
        self.current_page = page
        self.contents['body'] = (page, None)

        for tab in self.tabs:
            tab.set_active(False)
            if tab.page == page:
                tab.set_active(True)

        self.redraw()

        page.activate()

    def redraw(self):
        """
        Redraw screen.
        Needs to be called by other widgets if UI was changed from a different thread.
        """
        if self.loop:
            self.loop.draw_screen()

    def append_cancel_action(self, action):
        """
        Notify app about an action that can be cancelled by adding it to the action stack.
        It will be called once when "Escape" key is hit.
        """
        self._cancel_actions.append(action)

    def unregister_cancel_action(self, action):
        """
        Remove cancel action from action stack.
        """
        if action in self._cancel_actions:
            self._cancel_actions.remove(action)

    def keypress(self, size, key):
        """
        Handle keypress.
        Can switch tabs, control playback, flags, notifications and app state.
        """
        hotkey_manager.keypress("global", self, super(AppWidget, self), size, key)
        return None

    def show_debug(self):
        """ Show debug page. """
        self.set_page('debug')

    def show_library(self):
        """ Show library page. """
        self.set_page('library')

    def show_artists(self):
        """ Show artist page"""
        self.set_page('artists')

    def show_albums(self):
        """Show album page"""
        self.set_page('albums')

    def show_playlists(self):
        """ Show playlists page. """
        self.set_page('playlists')

    def show_stations(self):
        """ Show stations page. """
        self.set_page('stations')

    def show_queue(self):
        """ Show queue page. """
        self.set_page('queue')

    def show_search(self):
        """ Show search page. """
        self.set_page('search')

    def show_settings(self):
        """ Show settings page. """

        self.set_page('settings')

    @staticmethod
    def play_pause():
        """
        Toggle play/pause.
        """
        player.play_pause()

    @staticmethod
    def next_song():
        """
        Play next song.
        """
        player.next(True)

    @staticmethod
    def prev_song():
        """
        Play the previous song.
        """
        player.prev(True)

    @staticmethod
    def seek_backward():
        """
        Seek 5% backward.
        """
        player.seek(-0.05)

    @staticmethod
    def seek_forward():
        """
        Seek 5% forward.
        """
        player.seek(0.05)

    @staticmethod
    def toggle_shuffle():
        """
        Toggle random playback.
        """
        player.random = not player.random

    @staticmethod
    def toggle_repeat_one():
        """
        Toggle repeat mode.
        """
        player.repeat_one = not player.repeat_one

    @staticmethod
    def toggle_repeat_queue():
        """
        Toggle queue repeat
        """
        player.repeat_queue = not player.repeat_queue

    def quit(self):
        """
        Quit app.
        """
        self.loop = None
        sys.exit(0)

    def handle_escape(self):
        """
        Run escape actions. If none are pending, close newest notification.
        """
        try:
            action = self._cancel_actions.pop()
        except IndexError:
            notification_area.close_newest()
        else:
            action()


def main():
    """
    Application entrypoint.

    This function is required to allow Clay to be ran as application when installed via setuptools.
    """

    # Create a 256 colour palette.
    palette = [(name, '', '', '', res['foreground'], res['background'])
               for name, res in settings_manager.colours_config.items()]


    # Run the actual program
    app_widget = AppWidget()
    loop = urwid.MainLoop(app_widget, palette, event_loop=urwid.GLibEventLoop())
    app_widget.set_loop(loop)
    loop.screen.set_terminal_properties(256)
    loop.run()
