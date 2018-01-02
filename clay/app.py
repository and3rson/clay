#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
# pylint: disable=too-many-instance-attributes
"""
Main app entrypoint.
"""

import sys
sys.path.append('.')  # noqa

import urwid

from clay.player import player
from clay.widgets import PlayProgress
from clay.pages import StartUp
from clay.mylibrary import MyLibrary
from clay.myplaylists import MyPlaylists
from clay.playerqueue import Queue
from clay.settings import Settings
from clay.notifications import NotificationArea
# from clay import hotkeys

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

        def set_active(self, active):
            """
            Mark tab visually as active.
            """
            self.set_text(
                [('panel_focus' if active else 'panel', self.get_title())]
            )

        def get_title(self):
            """
            Render tab title.
            """
            return ' {} {} '.format(
                self.page.key,
                self.page.name
            )

    def __init__(self):
        self.pages = [
            StartUp(self),
            MyLibrary(self),
            MyPlaylists(self),
            Queue(self),
            Settings(self)
        ]
        self.tabs = [
            AppWidget.Tab(page)
            for page
            in self.pages
            if hasattr(page, 'key')
        ]
        NotificationArea.set_app(self)
        self.header = urwid.Pile([
            # urwid.Divider('\u2500'),
            urwid.AttrWrap(urwid.Columns([
                ('pack', tab)
                for tab
                in self.tabs
            ], dividechars=1), 'panel'),
            NotificationArea.get()
            # urwid.Divider('\u2500')
        ])
        self.seekbar = PlayProgress(
            'progress_remaining',
            'progress',
            current=0,
            done=100
        )
        self.shuffle_el = urwid.AttrWrap(urwid.Text(' ⋍ SHUF '), 'flag')
        self.repeat_el = urwid.AttrWrap(urwid.Text(' ⟲ REP '), 'flag')
        self.panel = urwid.Pile([
            urwid.Columns([
                urwid.Divider('\u2500'),
                ('pack', self.shuffle_el),
                # ('pack', urwid.Text(' ')),
                ('pack', self.repeat_el)
            ]),
            self.seekbar
        ])
        self.current_page = self.pages[0]
        super(AppWidget, self).__init__(
            header=self.header,
            footer=self.panel,
            body=self.current_page
        )

        self.loop = None

        player.media_position_changed += self.media_position_changed
        player.media_state_changed += self.media_state_changed
        player.track_changed += self.track_changed
        player.playback_flags_changed += self.playback_flags_changed

    def set_loop(self, loop):
        """
        Assign a MainLoop to this app.
        """
        self.loop = loop

    def media_position_changed(self, progress):
        """
        Update slider in seekbar.
        Called when current play position changes.
        """
        if progress < 0:
            progress = 0
        self.seekbar.set_completion(progress * 100)
        self.loop.draw_screen()

    def media_state_changed(self, _):
        """
        Update seekbar.
        Called when playback is paused/unpaused.
        """
        self.seekbar.update()

    def track_changed(self, track):
        """
        Update displayed track in seekbar.
        Called when current track changes.
        """
        self.seekbar.set_track(track)

    def playback_flags_changed(self):
        """
        Update seekbar flags.
        Called when random/repeat flags change.
        """
        self.shuffle_el.attr = 'flag-active' \
            if player.get_is_random() \
            else 'flag'
        self.repeat_el.attr = 'flag-active' \
            if player.get_is_repeat_one() \
            else 'flag'
        self.seekbar.update()

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

        if hasattr(page, 'start'):
            page.start()

    def redraw(self):
        """
        Redraw screen.
        Needs to be called by other widgets if UI was changed from a different thread.
        """
        if self.loop:
            self.loop.draw_screen()

    def keypress(self, size, key):
        """
        Handle keypress.
        Can switch tabs, control playbackm, flags, notifications and app state.
        """
        for tab in self.tabs:
            if 'meta {}'.format(tab.page.key) == key:
                self.set_page(tab.page.__class__.__name__)
                return

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
        elif key == 'ctrl q':
            sys.exit(0)
        elif key == 'esc':
            NotificationArea.close_all()
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
