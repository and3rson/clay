#!/usr/bin/env python3
# pylint: disable=wrong-import-position
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-branches
"""
Main app entrypoint.
"""

import sys
sys.path.insert(0, '.')  # noqa
sys.path.insert(0, '/home/anderson/src/urwid')  # noqa

import urwid

from clay.player import Player
from clay.playbar import PlayBar
from clay.pages.mylibrary import MyLibraryPage
from clay.pages.myplaylists import MyPlaylistsPage
from clay.pages.playerqueue import QueuePage
from clay.pages.search import SearchPage
from clay.pages.settings import SettingsPage
from clay.settings import Settings
from clay.notifications import NotificationArea
from clay.gp import GP

PALETTE = [
    ('logo', '', '', '', '#F54', ''),

    ('bg', '', '', '', '#FFF', '#222'),
    ('primary', '', '', '', '#F54', '#FFF'),
    ('secondary', '', '', '', '#17F', '#FFF'),
    ('selected', '', '', '', '#FFF', '#444'),
    ('primary_inv', '', '', '', '#FFF', '#17F'),
    ('secondary_inv', '', '', '', '#FFF', '#F17'),
    ('progress', '', '', '', '#FFF', '#F54'),
    ('progress_remaining', '', '', '', '#FFF', '#444'),

    ('panel', '', '', '', '#FFF', '#222'),
    ('panel_focus', '', '', '', '#FFF', '#F54'),
    ('panel_divider', '', '', '', '#444', '#222'),
    ('panel_divider_focus', '', '', '', '#444', '#F54'),

    ('line1', '', '', '', '#FFF', ''),
    ('line1_focus', '', '', '', '#FFF', '#444'),
    ('line1_active', '', '', '', '#F54', ''),
    ('line1_active_focus', '', '', '', '#F54', '#444'),
    ('line2', '', '', '', '#AAA', ''),
    ('line2_focus', '', '', '', '#AAA', '#444'),

    ('input', '', '', '', '#FFF', '#444'),
    ('input_focus', '', '', '', '#FFF', '#F54'),

    ('flag', '', '', '', '#AAA', ''),
    ('flag-active', '', '', '', '#F54', ''),

    ('notification', '', '', '', '#F54', '#222'),
]


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

        NotificationArea.set_app(self)
        self._login_notification = None

        self._popup = None

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
        self.playbar = PlayBar(
            'progress_remaining',
            'progress',
            current=0,
            done=100
        )
        self.shuffle_el = urwid.AttrWrap(urwid.Text(u' \u22cd SHUF '), 'flag')
        self.repeat_el = urwid.AttrWrap(urwid.Text(u' \u27f2 REP '), 'flag')
        self.panel = urwid.Pile([
            urwid.Columns([
                urwid.Divider(u'\u2500'),
                ('pack', self.shuffle_el),
                # ('pack', urwid.Text(' ')),
                ('pack', self.repeat_el)
            ]),
            self.playbar
        ])
        # self.current_page = self.pages[0]
        super(AppWidget, self).__init__(
            header=self.header,
            footer=self.panel,
            body=urwid.Filler(urwid.Text('Loading...', align='center'))
        )
        # self.current_page.activate()

        self.loop = None

        player = Player.get()
        player.media_position_changed += self.media_position_changed
        player.media_state_changed += self.media_state_changed
        player.track_changed += self.track_changed
        player.playback_flags_changed += self.playback_flags_changed

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

    def media_position_changed(self, progress):
        """
        Update slider in playbar.
        Called when current play position changes.
        """
        if progress < 0:
            progress = 0
        self.playbar.set_completion(progress * 100)
        self.loop.draw_screen()

    def media_state_changed(self, *_):
        """
        Update playbar.
        Called when playback is paused/unpaused.
        """
        self.playbar.update()
        self.loop.draw_screen()

    def track_changed(self, track):
        """
        Update displayed track in playbar.
        Called when current track changes.
        """
        self.playbar.set_track(track)
        self.loop.draw_screen()

    def playback_flags_changed(self):
        """
        Update playbar flags.
        Called when random/repeat flags change.
        """
        player = Player.get()
        self.shuffle_el.attr = 'flag-active' \
            if player.get_is_random() \
            else 'flag'
        self.repeat_el.attr = 'flag-active' \
            if player.get_is_repeat_one() \
            else 'flag'
        self.playbar.update()
        self.loop.draw_screen()

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

    def register_popup(self, popup):
        """
        Notify app about a popup that's currently being shown.
        This is used to correctly deliver "Escape" key hit.
        """
        self._popup = popup

    def keypress(self, size, key):
        """
        Handle keypress.
        Can switch tabs, control playback, flags, notifications and app state.
        """
        for tab in self.tabs:
            if 'meta {}'.format(tab.page.key) == key:
                self.set_page(tab.page.__class__.__name__)
                return

        player = Player.get()
        if key == 'ctrl q':
            player.seek_absolute(0)
        elif key == 'ctrl w':
            player.play_pause()
        elif key == 'ctrl e':
            player.next(True)
        elif key == 'shift right':
            player.seek(0.05)
        elif key == 'shift left':
            player.seek(-0.05)
        elif key == 'ctrl s':
            player.set_random(not player.get_is_random())
        elif key == 'ctrl r':
            player.set_repeat_one(not player.get_is_repeat_one())
        elif key == 'ctrl x':
            sys.exit(0)
        elif key == 'esc' or key == 'ctrl _':
            if self._popup:
                self._popup.close()
                self._popup = None
            else:
                NotificationArea.close_newest()
        else:
            super(AppWidget, self).keypress(size, key)


def main():
    """
    Application entrypoint.
    """
    app_widget = AppWidget()
    loop = urwid.MainLoop(app_widget, PALETTE)
    app_widget.set_loop(loop)
    loop.screen.set_terminal_properties(256)
    loop.run()


if __name__ == '__main__':
    main()
