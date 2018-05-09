#!/usr/bin/env python3
# pylint: disable=wrong-import-position
"""
Main app entrypoint.
"""

import sys
sys.path.insert(0, '.')  # noqa


import argparse
import os
import urwid

from clay import meta
from clay.player import player
from clay.playbar import PlayBar
from clay.pages.debug import DebugPage
from clay.pages.mylibrary import MyLibraryPage
from clay.pages.myplaylists import MyPlaylistsPage
from clay.pages.mystations import MyStationsPage
from clay.pages.playerqueue import QueuePage
from clay.pages.search import SearchPage
from clay.pages.settings import SettingsPage
from clay.settings import settings
from clay.notifications import notification_area
from clay.gp import gp
from clay.hotkeys import hotkey_manager


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
            MyLibraryPage(self),
            MyPlaylistsPage(self),
            MyStationsPage(self),
            QueuePage(self),
            SearchPage(self),
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

        self.set_page('MyLibraryPage')
        self.log_in()

    def log_in(self, use_token=True):
        """
        Called when this page is shown.

        Request user authorization.
        """
        authtoken, device_id, username, password = [
            settings.get(key, "play_settings")
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

        with settings.edit() as config:
            config['play_settings']['authtoken'] = gp.get_authtoken()

        self._login_notification.close()

    def set_loop(self, loop):
        """
        Assign a MainLoop to this app.
        """
        self.loop = loop

    def set_page(self, classname):
        """
        Switch to a different tab.
        """
        page = [page for page in self.pages if page.__class__.__name__ == classname][0]
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
        for tab in self.tabs:
            if 'meta {}'.format(tab.page.key) == key:
                self.set_page(tab.page.__class__.__name__)
                return

        hotkey_manager.keypress("global", self, super(AppWidget, self), size, key)

    @staticmethod
    def seek_start():
        """
        Seek to the start of the song.
        """
        player.seek_absolute(0)

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
        player.set_random(not player.get_is_random())

    @staticmethod
    def toggle_repeat_one():
        """
        Toggle repeat mode.
        """
        player.set_repeat_one(not player.get_is_repeat_one())

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


class MultilineVersionAction(argparse.Action):
    """
    An argparser action for multiple lines so we can display the copyright notice
    Based on: https://stackoverflow.com/a/41147122
    """
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")

        self.prog = os.path.basename(sys.argv[0])
        super(MultilineVersionAction, self).__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.exit(message=meta.COPYRIGHT_MESSAGE)


def main():
    """
    Application entrypoint.

    This function is required to allow Clay to be ran as application when installed via setuptools.
    """
    parser = argparse.ArgumentParser(
        prog=meta.APP_NAME,
        description=meta.DESCRIPTION,
        epilog="This project is neither affiliated nor endorsed by Google."
    )

    parser.add_argument("-v", "--version", action=MultilineVersionAction)

    keybinds_group = parser.add_mutually_exclusive_group()

    keybinds_group.add_argument(
        "--with-x-keybinds",
        help="define global X keybinds (requires Keybinder and PyGObject)",
        action='store_true'
    )

    keybinds_group.add_argument(
        "--without-x-keybinds",
        help="Don't define global keybinds (overrides configuration file)",
        action='store_true'
    )

    args = parser.parse_args()

    if args.version:
        exit(0)

    if (args.with_x_keybinds or settings.get('x_keybinds', 'clay_settings')) \
       and not args.without_x_keybinds:
        player.enable_xorg_bindings()

    # Create a 256 colour palette.
    palette = [(name, '', '', '', res['foreground'], res['background'])
               for name, res in settings.colours_config.items()]

    try:
        from setproctitle import setproctitle
    except ImportError:
        pass
    else:
        setproctitle('clay')

    # Run the actual program
    app_widget = AppWidget()
    loop = urwid.MainLoop(app_widget, palette)
    app_widget.set_loop(loop)
    loop.screen.set_terminal_properties(256)
    loop.run()


if __name__ == '__main__':
    main()
