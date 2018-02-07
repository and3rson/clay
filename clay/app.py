#!/usr/bin/env python3
# pylint: disable=wrong-import-position
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-public-methods
"""
Main app entrypoint.
"""

import sys
sys.path.insert(0, '.')  # noqa


import argparse
import os
import urwid

from clay import meta
from clay.player import Player
from clay.playbar import PlayBar
from clay.pages.debug import DebugPage
from clay.pages.mylibrary import MyLibraryPage
from clay.pages.myplaylists import MyPlaylistsPage
from clay.pages.playerqueue import QueuePage
from clay.pages.search import SearchPage
from clay.pages.settings import SettingsPage
from clay.settings import Settings
from clay.notifications import NotificationArea
from clay.gp import GP


BG = '#222'

PALETTE = [
    (None, '', '', '', '#FFF', BG),
    ('default', '', '', '', '#FFF', BG),
    ('logo', '', '', '', '#F54', BG),

    ('bg', '', '', '', '#FFF', '#222'),
    ('primary', '', '', '', '#F54', '#FFF'),
    ('secondary', '', '', '', '#17F', '#FFF'),
    ('selected', '', '', '', '#FFF', '#444'),
    ('primary_inv', '', '', '', '#FFF', '#17F'),
    ('secondary_inv', '', '', '', '#FFF', '#F17'),
    ('progress', '', '', '', '#FFF', '#F54'),
    ('progress_remaining', '', '', '', '#FFF', '#444'),

    ('progressbar_done', '', '', '', '#F54', BG),
    ('progressbar_done_paused', '', '', '', '', BG),
    ('progressbar_remaining', '', '', '', '#222', BG),

    ('title-idle', '', '', '', '', BG),
    ('title-playing', '', '', '', '#F54', BG),

    ('panel', '', '', '', '#FFF', '#222'),
    ('panel_focus', '', '', '', '#FFF', '#F54'),
    ('panel_divider', '', '', '', '#444', '#222'),
    ('panel_divider_focus', '', '', '', '#444', '#F54'),

    ('line1', '', '', '', '#FFF', BG),
    ('line1_focus', '', '', '', '#FFF', '#333'),
    ('line1_active', '', '', '', '#F54', BG),
    ('line1_active_focus', '', '', '', '#F54', '#333'),
    ('line2', '', '', '', '#AAA', BG),
    ('line2_focus', '', '', '', '#AAA', '#333'),

    ('input', '', '', '', '#FFF', '#444'),
    ('input_focus', '', '', '', '#FFF', '#F54'),

    ('flag', '', '', '', '#AAA', BG),
    ('flag-active', '', '', '', '#F54', BG),

    ('notification', '', '', '', '#F54', '#222'),
]


class AppWidget(urwid.Frame):
    """
    Root widget.

    Handles tab switches, global keypresses etc.
    """

    KEYBINDS = {
        'ctrl q': 'seek_start',
        'ctrl w': 'play_pause',
        'ctrl e': 'next_song',
        'shift left': 'seek_backward',
        'shift right': 'seek_forward',
        'ctrl s': 'toggle_shuffle',
        'ctrl r': 'toggle_repeat_one',
        'ctrl x': 'quit',
        'esc': 'handle_escape_action',
        'ctrl _': 'handle_escape_action'
    }

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
            QueuePage(self),
            SearchPage(self),
            SettingsPage(self)
        ]
        self.tabs = [
            AppWidget.Tab(page)
            for page
            in self.pages
        ]

        self.current_page = None
        self.loop = None

        NotificationArea.set_app(self)
        self._login_notification = None

        self._cancel_actions = []

        self.header = urwid.Pile([
            # urwid.Divider('\u2500'),
            urwid.AttrWrap(urwid.Columns([
                ('pack', tab)
                for tab
                in self.tabs
            ], dividechars=0), 'panel'),
            NotificationArea.get()
            # urwid.Divider('\u2500')
        ])
        self.playbar = PlayBar(self)
        # self.panel = urwid.Pile([
        #     urwid.Columns([
        #         urwid.Divider(u'\u2500'),
        #     ]),
        #     self.playbar
        # ])
        # self.current_page = self.pages[0]
        super(AppWidget, self).__init__(
            header=self.header,
            footer=self.playbar,
            body=urwid.Filler(urwid.Text('Loading...', align='center'))
        )
        # self.current_page.activate()

        self.set_page('MyLibraryPage')
        self.log_in()

    def log_in(self, use_token=True):
        """
        Called when this page is shown.

        Request user authorization.
        """
        config = Settings.get_config()
        username, password, device_id, authtoken = [
            config.get(x)
            for x
            in ('username', 'password', 'device_id', 'authtoken')
        ]
        if self._login_notification:
            self._login_notification.close()
        if use_token and authtoken:
            self._login_notification = NotificationArea.notify('Using cached auth token...')
            GP.get().use_authtoken_async(
                authtoken,
                device_id,
                callback=self.on_check_authtoken
            )
        elif username and password and device_id:
            self._login_notification = NotificationArea.notify('Logging in...')
            GP.get().login_async(
                username,
                password,
                device_id,
                callback=self.on_login
            )
        else:
            self._login_notification = NotificationArea.notify(
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

        Settings.set_config(dict(authtoken=GP.get().get_authtoken()))

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

        method_name = AppWidget.KEYBINDS.get(key)
        if method_name:
            getattr(self, method_name)()
        else:
            super(AppWidget, self).keypress(size, key)

    @staticmethod
    def seek_start():
        """
        Seek to the start of the song.
        """
        Player.get().seek_absolute(0)

    @staticmethod
    def play_pause():
        """
        Toggle play/pause.
        """
        Player.get().play_pause()

    @staticmethod
    def next_song():
        """
        Play next song.
        """
        Player.get().next(True)

    @staticmethod
    def seek_backward():
        """
        Seek 5% backward.
        """
        Player.get().seek(-0.05)

    @staticmethod
    def seek_forward():
        """
        Seek 5% forward.
        """
        Player.get().seek(0.05)

    @staticmethod
    def toggle_shuffle():
        """
        Toggle random playback.
        """
        player = Player.get()
        player.set_random(not player.get_is_random())

    @staticmethod
    def toggle_repeat_one():
        """
        Toggle repeat mode.
        """
        player = Player.get()
        player.set_repeat_one(not player.get_is_repeat_one())

    @staticmethod
    def quit():
        """
        Quit app.
        """
        sys.exit(0)

    def handle_escape_action(self):
        """
        Run escape actions. If none are pending, close newest notification.
        """
        try:
            action = self._cancel_actions.pop()
        except IndexError:
            NotificationArea.close_newest()
        else:
            action()


class MultilineVersionAction(argparse.Action):
    """
    An argparser action for multiple lines so we can display the copyright notice
    Based on: https://stackoverflow.com/a/41147122
    """
    version = "0.6.2"
    author = "Andrew Dunai"

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")

        self.prog = os.path.basename(sys.argv[0])
        super(MultilineVersionAction, self).__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.exit(message=meta.COPYRIGHT_MESSAGE)


if __name__ == '__main__':
    # pylint: disable-all
    parser = argparse.ArgumentParser(
        prog=meta.APP_NAME,
        description=meta.DESCRIPTION,
        epilog="This project is neither affiliated nor endorsed by Google.")

    parser.add_argument("-v", "--version", action=MultilineVersionAction)

    parser.add_argument(
        "--with-x-keybinds",
        help="define global X keybinds (requires Keybinder and PyGObject)",
        action='store_true')

    args = parser.parse_args()

    if args.version:
        exit(0)

    if args.with_x_keybinds:
        Player.get().enable_xorg_bindings()

    # Run the actual program
    app_widget = AppWidget()
    loop = urwid.MainLoop(app_widget, PALETTE)
    app_widget.set_loop(loop)
    loop.screen.set_terminal_properties(256)
    loop.run()
